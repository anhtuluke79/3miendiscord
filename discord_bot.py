import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# === Crawl 30 ngày từ xsmn.mobi ===
def crawl_xsmb_30ngay_xsmnmobi(csv_path='xs_mienbac_full.csv'):
    url = "https://xsmn.mobi/xsmb-30-ngay.html"
    resp = requests.get(url, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"class": "kqtinh"})
    if not table:
        raise Exception("Không tìm thấy bảng kết quả!")
    data = []
    trs = table.find_all("tr")
    for row in trs[1:]:
        tds = row.find_all("td")
        if not tds or len(tds) < 9:
            continue
        date = tds[0].text.strip()
        result = {"date": date}
        result['DB'] = tds[1].text.strip()
        result['G1'] = tds[2].text.strip()
        result['G2'] = tds[3].text.strip()
        result['G3'] = tds[4].text.strip()
        result['G4'] = tds[5].text.strip()
        result['G5'] = tds[6].text.strip()
        result['G6'] = tds[7].text.strip()
        result['G7'] = tds[8].text.strip()
        data.append(result)
    # Chuẩn hóa ngày sang YYYY-MM-DD
    for row in data:
        try:
            d = datetime.strptime(row['date'], "%d/%m/%Y")
            row['date'] = d.strftime("%Y-%m-%d")
        except:
            pass
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path, data[0]['date'] if data else None

# === Crawl truyền thống backup lâu năm ===
def crawl_xsmb_truyen_thong_xsmnmobi(csv_path='xsmb_truyenthong.csv', max_rows=1000):
    url = "https://xsmn.mobi/so-ket-qua-truyen-thong.html"
    resp = requests.get(url, timeout=20)
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"class": "kqtinh"})
    if not table:
        raise Exception("Không tìm thấy bảng kết quả truyền thống!")
    data = []
    trs = table.find_all("tr")
    for row in trs[1:]:
        tds = row.find_all("td")
        if not tds or len(tds) < 10:
            continue
        date = tds[0].text.strip()
        result = {"date": date}
        result['DB'] = tds[1].text.strip()
        result['G1'] = tds[2].text.strip()
        result['G2'] = tds[3].text.strip()
        result['G3'] = tds[4].text.strip()
        result['G4'] = tds[5].text.strip()
        result['G5'] = tds[6].text.strip()
        result['G6'] = tds[7].text.strip()
        result['G7'] = tds[8].text.strip()
        data.append(result)
        if len(data) >= max_rows:
            break
    # Chuẩn hóa ngày sang YYYY-MM-DD
    for row in data:
        try:
            d = datetime.strptime(row['date'], "%d/%m/%Y")
            row['date'] = d.strftime("%Y-%m-%d")
        except:
            pass
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path, data[0]['date'] if data else None

# === Fallback từng ngày từng nguồn ===
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

def crawl_xsmb_to_csv(csv_path='xs_mienbac_full.csv', days=30, notify_if_duplicate=False):
    try:
        print("[Crawl] Đang lấy 30 ngày từ xsmn.mobi...")
        path, newest_date = crawl_xsmb_30ngay_xsmnmobi(csv_path)
        print("[Crawl] Đã lấy thành công 30 ngày mới nhất từ xsmn.mobi.")
        return True, path, newest_date
    except Exception as e:
        print(f"[Crawl] Lỗi khi crawl xsmn.mobi: {e}")
        print("[Crawl] Thử lấy từng ngày từng nguồn dự phòng...")
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

# ==== BOT SETUP ====
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID", "0"))
GUILD_ID = int(os.getenv("GUILD_ID", "0"))  # Thay bằng ID server của bạn

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Slash Command ĐỊNH NGHĨA NGOÀI COG, PHẢI ĐĂNG KÝ THỦ CÔNG!
@app_commands.command(name="crawl_xsmb", description="(Admin) Crawl dữ liệu XSMB mới nhất (ưu tiên xsmn.mobi)")
async def crawl_xsmb(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        return
    await interaction.response.send_message(f"Đang crawl dữ liệu XSMB mới nhất...", ephemeral=True)
    try:
        is_new, path, newest_date = crawl_xsmb_to_csv('xs_mienbac_full.csv', 30)
        if is_new:
            await interaction.followup.send(f"✅ Đã crawl xong dữ liệu mới nhất ({newest_date}), lưu vào `{path}`.", ephemeral=True)
        else:
            await interaction.followup.send(f"ℹ️ Dữ liệu ngày hôm nay đã tồn tại trong file `{path}`, không crawl thêm.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi crawl: {e}", ephemeral=True)

@app_commands.command(name="download_xsmb", description="(Admin) Gửi file CSV dữ liệu XSMB mới nhất")
async def download_xsmb(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        return
    csv_path = 'xs_mienbac_full.csv'
    if os.path.exists(csv_path):
        await interaction.response.send_message("Đây là file dữ liệu XSMB mới nhất:", ephemeral=True)
        await interaction.followup.send(file=discord.File(csv_path), ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ File dữ liệu chưa tồn tại!", ephemeral=True)

@app_commands.command(name="crawl_truyenthong", description="(Admin) Crawl XSMB truyền thống (backup nhiều năm)")
async def crawl_truyenthong(interaction: discord.Interaction, max_rows: int = 500):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        return
    await interaction.response.send_message(f"Đang crawl dữ liệu XSMB truyền thống (tối đa {max_rows} ngày)...", ephemeral=True)
    try:
        path, newest_date = crawl_xsmb_truyen_thong_xsmnmobi('xsmb_truyenthong.csv', max_rows)
        await interaction.followup.send(f"✅ Đã crawl xong dữ liệu, lưu vào `{path}`. Ngày mới nhất: {newest_date}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi crawl: {e}", ephemeral=True)

@tasks.loop(hours=24)
async def auto_crawl_xsmb():
    print("[Auto Crawl] Đang crawl dữ liệu XSMB tự động...")
    is_new, path, crawl_date = crawl_xsmb_to_csv('xs_mienbac_full.csv', 30, notify_if_duplicate=True)
    now = datetime.now().strftime('%d-%m-%Y %H:%M')
    print(f"[Auto Crawl] {'Crawl mới' if is_new else 'Đã tồn tại'} | {now}")
    if is_new and CHANNEL_ID:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"✅ Đã tự động crawl XSMB và cập nhật dữ liệu mới nhất ({crawl_date})!")
    elif not is_new:
        print("[Auto Crawl] Đã có dữ liệu ngày mới, không crawl thêm.")

@auto_crawl_xsmb.before_loop
async def before_auto_crawl():
    await bot.wait_until_ready()
    now = datetime.utcnow()
    target = now.replace(hour=23, minute=0, second=0, microsecond=0)
    if now > target:
        target += timedelta(days=1)
    await discord.utils.sleep_until(target)

# ĐĂNG KÝ LỆNH SLASH VÀO TREE
bot.tree.add_command(crawl_xsmb)
bot.tree.add_command(download_xsmb)
bot.tree.add_command(crawl_truyenthong)

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
