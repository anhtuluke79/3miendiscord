import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# === Hàm crawl dữ liệu XSMB ===
def crawl_xsmb_to_csv(csv_path='xs_mienbac_full.csv', days=30):
    base_url = "https://xoso.me/ket-qua-xo-so-mien-bac-p1.php?ngay="
    data = []
    for i in range(days):
        date = (datetime.today() - timedelta(days=i)).strftime("%d-%m-%Y")
        url = base_url + date
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="kqmb")
        if not table:
            continue
        result = {'date': date}
        trs = table.find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            if tds and len(tds) > 1:
                if "Đặc biệt" in tds[0].text:
                    result['DB'] = tds[1].text.strip().replace(" ", "")
                elif "Giải nhất" in tds[0].text:
                    result['G1'] = tds[1].text.strip().replace(" ", "")
                elif "Giải nhì" in tds[0].text:
                    g2s = tds[1].text.strip().split(" ")
                    result['G2_1'] = g2s[0]
                    if len(g2s) > 1: result['G2_2'] = g2s[1]
                elif "Giải ba" in tds[0].text:
                    g3s = tds[1].text.strip().split(" ")
                    for k in range(min(6, len(g3s))):
                        result[f'G3_{k+1}'] = g3s[k]
        data.append(result)
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path

# === Bot Setup ===
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID", "0"))  # Có thể đặt ID kênh gửi thông báo trong .env

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== Lệnh slash để crawl thủ công (admin) =====
@app_commands.command(name="crawl_xsmb", description="(Admin) Crawl dữ liệu XSMB và lưu file CSV")
@commands.has_permissions(administrator=True)
async def crawl_xsmb(interaction: discord.Interaction, csv_path: str = "xs_mienbac_full.csv", days: int = 30):
    await interaction.response.send_message(f"Đang crawl dữ liệu XSMB {days} ngày gần nhất...", ephemeral=True)
    try:
        path = crawl_xsmb_to_csv(csv_path, days)
        await interaction.followup.send(f"Đã crawl xong và lưu vào file `{path}`", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Lỗi crawl: {e}", ephemeral=True)

# ===== Tự động crawl mỗi ngày (mặc định 6h sáng UTC) =====
@tasks.loop(hours=24)
async def auto_crawl_xsmb():
    # Crawl lúc bot start và mỗi 24h
    print("[Auto Crawl] Đang crawl dữ liệu XSMB tự động...")
    path = crawl_xsmb_to_csv('xs_mienbac_full.csv', 30)
    now = datetime.now().strftime('%d-%m-%Y %H:%M')
    print(f"[Auto Crawl] Đã crawl xong vào {now}, lưu {path}")
    # Thông báo vào kênh (nếu CHANNEL_ID được set)
    if CHANNEL_ID:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"✅ Đã tự động crawl XSMB và cập nhật dữ liệu ({now})!")

@auto_crawl_xsmb.before_loop
async def before_auto_crawl():
    await bot.wait_until_ready()
    # Đợi đến 6h sáng giờ Việt Nam (UTC+7), Railway chạy UTC nên 23h UTC là 6h VN
    now = datetime.utcno
