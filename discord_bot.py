import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

def crawl_xsmb_1ngay_minhchinh(ngay, thang, nam):
    date_str = f"{ngay:02d}-{thang:02d}-{nam}"
    url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-bac/{date_str}.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Tìm bảng đầu tiên có > 7 dòng và có chữ "Đặc biệt" hoặc "Nhất"
    tables = soup.find_all("table")
    table = None
    for tb in tables:
        trs = tb.find_all("tr")
        if len(trs) > 7 and any('Đặc biệt' in tr.text or 'Nhất' in tr.text for tr in trs):
            table = tb
            break

    if not table:
        print(f"[minhchinh.com] Không tìm thấy bảng kết quả ngày {date_str}!")
        return None

    result = {"date": f"{nam}-{thang:02d}-{ngay:02d}"}
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2: continue
        label = tds[0].get_text(strip=True)
        value = tds[1].get_text(" ", strip=True)
        # Chuẩn hóa tên cột
        if "Đặc biệt" in label or "ĐB" in label:
            result["DB"] = value
        elif "Nhất" in label:
            result["G1"] = value
        elif "Nhì" in label:
            result["G2"] = value
        elif "Ba" in label:
            result["G3"] = value
        elif "Tư" in label:
            result["G4"] = value
        elif "Năm" in label:
            result["G5"] = value
        elif "Sáu" in label:
            result["G6"] = value
        elif "Bảy" in label:
            result["G7"] = value
    return result

def crawl_xsmb_15ngay_minhchinh(csv_path="xsmb_15ngay_minhchinh.csv"):
    today = datetime.today()
    records = []
    for i in range(15):
        date = today - timedelta(days=i)
        try:
            row = crawl_xsmb_1ngay_minhchinh(date.day, date.month, date.year)
            if row:
                records.append(row)
                print(f"[minhchinh.com] ✔️ {date.strftime('%d-%m-%Y')}")
        except Exception as e:
            print(f"[minhchinh.com] ❌ {date.strftime('%d-%m-%Y')}: {e}")
    if records:
        df = pd.DataFrame(records)
        df = df.sort_values("date", ascending=False)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\nĐã lưu tổng hợp 15 ngày vào: {csv_path}")
        return True, csv_path, records[0]['date']
    else:
        raise Exception("Không lấy được dữ liệu ngày nào!")

# ==== BOT SETUP ====
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID", "0"))
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@app_commands.command(name="crawl_xsmb", description="(Admin) Crawl XSMB 15 ngày mới nhất từ minhchinh.com")
async def crawl_xsmb_minhchinh_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        return
    await interaction.response.send_message("Đang crawl dữ liệu XSMB 15 ngày từ minhchinh.com...", ephemeral=True)
    try:
        is_new, path, newest_date = crawl_xsmb_15ngay_minhchinh("xsmb_15ngay_minhchinh.csv")
        await interaction.followup.send(f"✅ Đã crawl xong dữ liệu ({newest_date}), lưu vào `{path}`.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi crawl: {e}", ephemeral=True)

@app_commands.command(name="download_xsmb", description="(Admin) Tải file CSV dữ liệu XSMB 15 ngày từ minhchinh.com")
async def download_xsmb_minhchinh_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        return
    csv_path = 'xsmb_15ngay_minhchinh.csv'
    if os.path.exists(csv_path):
        await interaction.response.send_message("Đây là file dữ liệu XSMB 15 ngày từ minhchinh.com:", ephemeral=True)
        await interaction.followup.send(file=discord.File(csv_path), ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ File dữ liệu chưa tồn tại!", ephemeral=True)

@tasks.loop(hours=24)
async def auto_crawl_xsmb():
    print("[Auto Crawl] Đang crawl dữ liệu XSMB tự động (minhchinh.com)...")
    try:
        is_new, path, crawl_date = crawl_xsmb_15ngay_minhchinh("xsmb_15ngay_minhchinh.csv")
        now = datetime.now().strftime('%d-%m-%Y %H:%M')
        print(f"[Auto Crawl] Đã crawl dữ liệu | {now}")
        if is_new and CHANNEL_ID:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(f"✅ Đã tự động crawl XSMB ({crawl_date}) từ minhchinh.com!")
    except Exception as e:
        print(f"[Auto Crawl] Lỗi: {e}")

@auto_crawl_xsmb.before_loop
async def before_auto_crawl():
    await bot.wait_until_ready()
    now = datetime.utcnow()
    target = now.replace(hour=23, minute=0, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    await discord.utils.sleep_until(target)

bot.tree.add_command(crawl_xsmb_minhchinh_cmd)
bot.tree.add_command(download_xsmb_minhchinh_cmd)

@bot.event
async def on_ready():
    print(f'Đã đăng nhập bot: {bot.user}')
    try:
        guild = discord.Object(id=GUILD_ID) if GUILD_ID else None
        if guild:
            synced = await bot.tree.sync(guild=guild)
            print(f"Đã sync {len(synced)} lệnh slash (theo guild).")
        else:
            synced = await bot.tree.sync()
            print(f"Đã sync {len(synced)} lệnh slash (global).")
    except Exception as e:
        print(e)
    auto_crawl_xsmb.start()

bot.run(TOKEN)
