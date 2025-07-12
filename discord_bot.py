import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

# --- CRAWL XSMB từ xoso.me ---
def crawl_xsmb_xosome(csv_path='xsmb_xosome.csv', days=30):
    data = []
    for i in range(days):
        date_dt = datetime.today() - timedelta(days=i)
        date_str_url = date_dt.strftime("%Y-%m-%d")
        url = f"https://xoso.me/ket-qua-xo-so-mien-bac-ngay-{date_str_url}.html"
        try:
            resp = requests.get(url, timeout=15, headers=HEADERS)
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"class": "tblKQXSMB"})
            if not table:
                print(f"[xoso.me] Không tìm thấy bảng kết quả ngày {date_str_url}")
                continue
            result = {'date': date_dt.strftime("%Y-%m-%d")}
            for tr in table.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) < 2: continue
                label = tds[0].get_text(strip=True)
                nums = tds[1].get_text(strip=True).replace('\n', '').replace(' ', '-')
                if "Đặc biệt" in label or "ĐB" in label:
                    result["DB"] = nums
                elif "Nhất" in label:
                    result["G1"] = nums
                elif "Nhì" in label:
                    result["G2"] = nums
                elif "Ba" in label:
                    result["G3"] = nums
                elif "Tư" in label:
                    result["G4"] = nums
                elif "Năm" in label:
                    result["G5"] = nums
                elif "Sáu" in label:
                    result["G6"] = nums
                elif "Bảy" in label:
                    result["G7"] = nums
            data.append(result)
        except Exception as e:
            print(f"[xoso.me] Lỗi ngày {date_str_url}: {e}")
    if data:
        pd.DataFrame(data).to_csv(csv_path, index=False, encoding='utf-8-sig')
        return True, csv_path, data[0]['date']
    else:
        raise Exception("Không crawl được dữ liệu nào từ xoso.me!")

# --- CRAWL XSMB từ minhchinh.com ---
def crawl_xsmb_minhchinh(csv_path='xsmb_minhchinh.csv', days=30):
    def crawl_1day(ngay, thang, nam):
        date_str = f"{ngay:02d}-{thang:02d}-{nam}"
        url = f"https://www.minhchinh.com/ket-qua-xo-so-mien-bac/{date_str}.html"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        tables = soup.find_all("table")
        table = None
        for tb in tables:
            trs = tb.find_all("tr")
            if len(trs) > 7 and any('Đặc biệt' in tr.text or 'Nhất' in tr.text for tr in trs):
                table = tb
                break
        if not table:
            print(f"[minhchinh] Không tìm thấy bảng ngày {date_str}")
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

    data = []
    for i in range(days):
        date_dt = datetime.today() - timedelta(days=i)
        try:
            res = crawl_1day(date_dt.day, date_dt.month, date_dt.year)
            if res:
                data.append(res)
                print(f"[minhchinh] ✔ {res['date']}")
        except Exception as e:
            print(f"[minhchinh] Lỗi {date_dt.strftime('%d-%m-%Y')}: {e}")
    if data:
        df = pd.DataFrame(data)
        df = df.sort_values("date", ascending=False)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        return True, csv_path, data[0]['date']
    else:
        raise Exception("Không crawl được dữ liệu nào từ minhchinh.com!")

# ==== BOT SETUP ====
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID", "0"))
GUILD_ID = int(os.getenv("GUILD_ID", "0"))  # Để sync lệnh nhanh, không cần thì để 0

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Lệnh crawl từ xoso.me ---
@app_commands.command(name="crawl_xsmb_xosome", description="(Admin) Crawl dữ liệu XSMB từ xoso.me (30 ngày)")
async def crawl_xsmb_xosome_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        return
    await interaction.response.send_message("Đang crawl dữ liệu XSMB mới nhất từ xoso.me...", ephemeral=True)
    try:
        is_new, path, newest_date = crawl_xsmb_xosome('xsmb_xosome.csv', 30)
        await interaction.followup.send(f"✅ Đã crawl xong dữ liệu ({newest_date}), lưu vào `{path}`.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi crawl: {e}", ephemeral=True)

@app_commands.command(name="download_xsmb_xosome", description="(Admin) Tải file CSV dữ liệu XSMB (xoso.me)")
async def download_xsmb_xosome_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        return
    csv_path = 'xsmb_xosome.csv'
    if os.path.exists(csv_path):
        await interaction.response.send_message("Đây là file dữ liệu XSMB từ xoso.me:", ephemeral=True)
        await interaction.followup.send(file=discord.File(csv_path), ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ File dữ liệu chưa tồn tại!", ephemeral=True)

# --- Lệnh crawl từ minhchinh.com ---
@app_commands.command(name="crawl_xsmb_minhchinh", description="(Admin) Crawl dữ liệu XSMB từ minhchinh.com (30 ngày)")
async def crawl_xsmb_minhchinh_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        return
    await interaction.response.send_message("Đang crawl dữ liệu XSMB từ minhchinh.com...", ephemeral=True)
    try:
        is_new, path, newest_date = crawl_xsmb_minhchinh('xsmb_minhchinh.csv', 30)
        await interaction.followup.send(f"✅ Đã crawl xong dữ liệu ({newest_date}), lưu vào `{path}`.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi crawl: {e}", ephemeral=True)

@app_commands.command(name="download_xsmb_minhchinh", description="(Admin) Tải file CSV dữ liệu XSMB (minhchinh.com)")
async def download_xsmb_minhchinh_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        return
    csv_path = 'xsmb_minhchinh.csv'
    if os.path.exists(csv_path):
        await interaction.response.send_message("Đây là file dữ liệu XSMB từ minhchinh.com:", ephemeral=True)
        await interaction.followup.send(file=discord.File(csv_path), ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ File dữ liệu chưa tồn tại!", ephemeral=True)

@tasks.loop(hours=24)
async def auto_crawl_xsmb():
    print("[Auto Crawl] Đang crawl dữ liệu XSMB tự động (xoso.me)...")
    try:
        is_new, path, crawl_date = crawl_xsmb_xosome('xsmb_xosome.csv', 30)
        now = datetime.now().strftime('%d-%m-%Y %H:%M')
        print(f"[Auto Crawl] Đã crawl dữ liệu | {now}")
        if is_new and CHANNEL_ID:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(f"✅ Đã tự động crawl XSMB ({crawl_date}) từ xoso.me!")
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

bot.tree.add_command(crawl_xsmb_xosome_cmd)
bot.tree.add_command(download_xsmb_xosome_cmd)
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
