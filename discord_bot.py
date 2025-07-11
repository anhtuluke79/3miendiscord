import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# === Crawl từ xosoketqua.com ===
def crawl_xsmb_xosoketqua(date_dt):
    date_str_url = date_dt.strftime("%d-%m-%Y")
    url = f"https://xosoketqua.com/xsmb-{date_str_url}.html"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "result_tab_mb"})
        if not table:
            return None
        result = {'date': date_dt.strftime("%Y-%m-%d")}
        trs = table.find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            if not tds: continue
            label = tds[0].text.strip()
            numbers = tds[1].text.strip().split('-')
            numbers = [x.strip() for x in numbers if x.strip()]
            if label.startswith("ĐB"):
                result['DB'] = numbers[0] if numbers else ""
            elif label.startswith("Nhất"):
                result['G1'] = numbers[0] if numbers else ""
            elif label.startswith("Nhì"):
                for j, num in enumerate(numbers):
                    result[f'G2_{j+1}'] = num
            elif label.startswith("Ba"):
                for j, num in enumerate(numbers):
                    result[f'G3_{j+1}'] = num
            elif label.startswith("Tư"):
                for j, num in enumerate(numbers):
                    result[f'G4_{j+1}'] = num
            elif label.startswith("Năm"):
                for j, num in enumerate(numbers):
                    result[f'G5_{j+1}'] = num
            elif label.startswith("Sáu"):
                for j, num in enumerate(numbers):
                    result[f'G6_{j+1}'] = num
            elif label.startswith("Bảy"):
                for j, num in enumerate(numbers):
                    result[f'G7_{j+1}'] = num
        return result
    except Exception as e:
        print(f"[xosoketqua] Lỗi: {e}")
        return None

# === Crawl từ xosomn.mobi (dự phòng) ===
def crawl_xsmb_xosomn(date_dt):
    date_str_url = date_dt.strftime("%d-%m-%Y")
    url = f"https://xosomn.mobi/ket-qua-xo-so-mien-bac/ngay-{date_str_url}"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"class": "bkqmienbac"})
        if not table:
            return None
        result = {'date': date_dt.strftime("%Y-%m-%d")}
        trs = table.find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            if not tds: continue
            label = tds[0].text.strip()
            numbers = tds[1].text.strip().split(' ')
            numbers = [x.strip() for x in numbers if x.strip()]
            if label.startswith("Đặc biệt"):
                result['DB'] = numbers[0] if numbers else ""
            elif label.startswith("Giải nhất"):
                result['G1'] = numbers[0] if numbers else ""
            elif label.startswith("Giải nhì"):
                for j, num in enumerate(numbers):
                    result[f'G2_{j+1}'] = num
            elif label.startswith("Giải ba"):
                for j, num in enumerate(numbers):
                    result[f'G3_{j+1}'] = num
            elif label.startswith("Giải tư"):
                for j, num in enumerate(numbers):
                    result[f'G4_{j+1}'] = num
            elif label.startswith("Giải năm"):
                for j, num in enumerate(numbers):
                    result[f'G5_{j+1}'] = num
            elif label.startswith("Giải sáu"):
                for j, num in enumerate(numbers):
                    result[f'G6_{j+1}'] = num
            elif label.startswith("Giải bảy"):
                for j, num in enumerate(numbers):
                    result[f'G7_{j+1}'] = num
        return result
    except Exception as e:
        print(f"[xosomn.mobi] Lỗi: {e}")
        return None

# === Hàm crawl tổng hợp (ưu tiên xosoketqua, fallback xosomn) ===
def crawl_xsmb_multi_source(date_dt):
    result = crawl_xsmb_xosoketqua(date_dt)
    if result:
        print(f"Lấy thành công từ xosoketqua.com: {result['date']}")
        return result
    result = crawl_xsmb_xosomn(date_dt)
    if result:
        print(f"Lấy thành công từ xosomn.mobi: {result['date']}")
        return result
    print(f"LỖI: Không crawl được ngày {date_dt.strftime('%Y-%m-%d')} ở mọi nguồn!")
    return None

# === Hàm tổng cho bot, crawl nhiều ngày và chỉ crawl nếu chưa có ngày mới ===
def crawl_xsmb_to_csv(csv_path='xs_mienbac_full.csv', days=30, notify_if_duplicate=False):
    last_date = None
    if os.path.exists(csv_path):
        try:
            df_old = pd.read_csv(csv_path)
            if not df_old.empty and 'date' in df_old.columns:
                last_date = max(df_old['date'])
        except Exception:
            pass

    data = []
    is_new = False
    for i in range(days):
        date_dt = datetime.today() - timedelta(days=i)
        date_str_csv = date_dt.strftime("%Y-%m-%d")
        if i == 0 and last_date == date_str_csv:
            if notify_if_duplicate:
                print("[Crawl] Ngày hôm nay đã có trong file CSV, không crawl thêm.")
            break
        r = crawl_xsmb_multi_source(date_dt)
        if r:
            data.append(r)
            if i == 0: is_new = True
        else:
            print(f"[Crawl] Bỏ qua ngày {date_str_csv} vì không lấy được.")
    # Gộp với dữ liệu cũ nếu có
    if os.path.exists(csv_path):
        try:
            df_old = pd.read_csv(csv_path)
            df_new = pd.DataFrame(data)
            df_all = pd.concat([df_new, df_old], ignore_index=True).drop_duplicates(subset=['date'], keep='first')
        except Exception:
            df_all = pd.DataFrame(data)
    else:
        df_all = pd.DataFrame(data)
    df_all = df_all.sort_values('date', ascending=False)
    df_all.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return is_new, csv_path, data[0]['date'] if data else None

# === Bot Setup ===
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID", "0"))  # Để 0 nếu không dùng gửi thông báo tự crawl

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== Lệnh crawl thủ công (slash command) =====
@app_commands.command(name="crawl_xsmb", description="(Admin) Crawl dữ liệu XSMB và lưu file CSV (chỉ khi có ngày mới)")
@commands.has_permissions(administrator=True)
async def crawl_xsmb(interaction: discord.Interaction, days: int = 30):
    await interaction.response.send_message(f"Đang crawl dữ liệu XSMB {days} ngày gần nhất...", ephemeral=True)
    try:
        is_new, path, newest_date = crawl_xsmb_to_csv('xs_mienbac_full.csv', days)
        if is_new:
            await interaction.followup.send(f"✅ Đã crawl xong dữ liệu ngày {newest_date}, lưu vào `{path}`.", ephemeral=True)
        else:
            await interaction.followup.send(f"ℹ️ Dữ liệu ngày hôm nay đã tồn tại trong file `{path}`, không crawl thêm.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi crawl: {e}", ephemeral=True)

# ===== Lệnh tải file CSV =====
@app_commands.command(name="download_xsmb", description="(Admin) Gửi file CSV dữ liệu XSMB mới nhất")
@commands.has_permissions(administrator=True)
async def download_xsmb(interaction: discord.Interaction):
    csv_path = 'xs_mienbac_full.csv'
    if os.path.exists(csv_path):
        await interaction.response.send_message("Đây là file dữ liệu XSMB mới nhất:", ephemeral=True)
        await interaction.followup.send(file=discord.File(csv_path), ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ File dữ liệu chưa tồn tại!", ephemeral=True)

# ===== Tự động crawl mỗi ngày (6h VN ~23h UTC) =====
@tasks.loop(hours=24)
async def auto_crawl_xsmb():
    print("[Auto Crawl] Đang crawl dữ liệu XSMB tự động...")
    is_new, path, crawl_date = crawl_xsmb_to_csv('xs_mienbac_full.csv', 30, notify_if_duplicate=True)
    now = datetime.now().strftime('%d-%m-%Y %H:%M')
    print(f"[Auto Crawl] {'Crawl mới' if is_new else 'Đã tồn tại'} | {now}")
    if is_new and CHANNEL_ID:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"✅ Đã tự động crawl XSMB và cập nhật dữ liệu ngày {crawl_date} ({now})!")
    elif not is_new:
        print("[Auto Crawl] Đã có dữ liệu ngày mới, không crawl thêm.")

@auto_crawl_xsmb.before_loop
async def before_auto_crawl():
    await bot.wait_until_ready()
    # Đợi đến 23h UTC (6h VN) lần đầu
    now = datetime.utcnow()
    target = now.replace(hour=23, minute=0, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    await discord.utils.sleep_until(target)

# ===== Setup tree, event =====
@bot.event
async def on_ready():
    print(f'Đã đăng nhập bot: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Đã sync {len(synced)} lệnh slash.")
    except Exception as e:
        print(e)
    auto_crawl_xsmb.start()

async def setup_hook():
    bot.tree.add_command(crawl_xsmb)
    bot.tree.add_command(download_xsmb)

bot.setup_hook = setup_hook

bot.run(TOKEN)
