import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import os
from dotenv import load_dotenv
from phong_thuy_dict import phong_thuy_dict
from ai_predictor_lstm_seq import predict_loto_lstm_seq
from ai_predictor_lstm import predict_loto_lstm
import pandas as pd

# ======= TIỆN ÍCH PHONG THỦY =======
def get_phong_thuy(numbers):
    pt_list = []
    for n in numbers:
        y_nghia = phong_thuy_dict.get(n.zfill(2), "Chưa cập nhật ý nghĩa")
        pt_list.append(f"Số **{n.zfill(2)}**: {y_nghia}")
    return "\n".join(pt_list)

# ======= VIEW/BTN MENU DỰ ĐOÁN 3 MIỀN =======
class DuDoanView(View):
    def __init__(self, mien, mode="seq"):
        super().__init__(timeout=60)
        self.mien = mien
        self.mode = mode  # "seq": 5 số, "db": đặc biệt

    @discord.ui.button(label="🔁 Dự đoán lại", style=discord.ButtonStyle.primary)
    async def random_button(self, interaction: discord.Interaction, button: Button):
        if self.mode == "seq":
            numbers, ratio = ai_predict_5so(self.mien)
        else:
            numbers, ratio = ai_predict_db(self.mien)
        phongthuy = get_phong_thuy(numbers)
        embed = discord.Embed(
            title=f"🔮 Dự đoán xổ số {self.mien.capitalize()} ({'5 số đẹp' if self.mode=='seq' else 'Đặc biệt'})",
            description=f"**Số đẹp:** {', '.join(numbers)}\n{ratio}\n\n{phongthuy}",
            color=discord.Color.green()
        )
        embed.set_footer(text="AI & Phong thủy cùng bạn may mắn 🤖✨")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="📊 Phân tích phong thủy", style=discord.ButtonStyle.secondary)
    async def stats_button(self, interaction: discord.Interaction, button: Button):
        # Dữ liệu đã nằm trong embed rồi, có thể gửi lại cho riêng user nếu muốn
        await interaction.response.send_message(
            "Các số đẹp đã trả về đã được phân tích phong thủy ngay bên dưới! Nếu muốn tra ý nghĩa số khác, hãy dùng lệnh /phongthuy [số].",
            ephemeral=True
        )

class SelectMienView(View):
    @discord.ui.select(
        placeholder="Chọn miền xổ số...",
        options=[
            discord.SelectOption(label="Miền Bắc", value="bac", description="Dự đoán xổ số miền Bắc"),
            discord.SelectOption(label="Miền Trung", value="trung", description="Dự đoán xổ số miền Trung"),
            discord.SelectOption(label="Miền Nam", value="nam", description="Dự đoán xổ số miền Nam"),
        ],
    )
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        mien = select.values[0]
        numbers, ratio = ai_predict_5so(mien)
        phongthuy = get_phong_thuy(numbers)
        embed = discord.Embed(
            title=f"🔮 Dự đoán xổ số {mien.capitalize()} (5 số đẹp)",
            description=f"**Số đẹp:** {', '.join(numbers)}\n{ratio}\n\n{phongthuy}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://i.imgur.com/gwJg5yG.png")
        embed.set_footer(text="AI & Phong thủy cùng bạn may mắn 🤖✨")
        await interaction.response.send_message(embed=embed, view=DuDoanView(mien, mode="seq"))

# ======= HÀM AI =======
def ai_predict_5so(mien):
    # Hiện chỉ dùng chung model miền Bắc, bạn mở rộng nếu có model miền khác
    if mien == "bac":
        return predict_loto_lstm_seq()
    else:
        # Có thể thêm model riêng cho "trung", "nam"
        return predict_loto_lstm_seq()
def ai_predict_db(mien):
    # Dự đoán 1 số đặc biệt
    if mien == "bac":
        return predict_loto_lstm()
    else:
        return predict_loto_lstm()

# ======= BOT CLASS & SETUP =======
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        self.tree.add_command(du_doan_xoso)
        self.tree.add_command(du_doan_5so)
        self.tree.add_command(du_doan_db)
        self.tree.add_command(ketqua)
        self.tree.add_command(topso)
        self.tree.add_command(thongke)
        self.tree.add_command(phongthuy)
        self.tree.add_command(so_ngau_nhien)
        self.tree.add_command(reload_data)
        self.tree.add_command(train_model)

bot = MyBot()

# ======= LỆNH SLASH =======
@discord.app_commands.command(name="du_doan_xoso", description="Dự đoán xổ số 3 miền kèm phân tích phong thủy")
async def du_doan_xoso(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Hãy chọn miền bạn muốn dự đoán:",
        view=SelectMienView()
    )

@discord.app_commands.command(name="du_doan_5so", description="Dự đoán 5 số liên tiếp bằng AI LSTM seq2seq")
async def du_doan_5so(interaction: discord.Interaction, mien: str):
    numbers, ratio = ai_predict_5so(mien)
    phongthuy = get_phong_thuy(numbers)
    embed = discord.Embed(
        title=f"🔮 Dự đoán 5 số đẹp {mien.capitalize()} (AI)",
        description=f"**Số đẹp:** {', '.join(numbers)}\n{ratio}\n\n{phongthuy}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, view=DuDoanView(mien, mode="seq"))

@discord.app_commands.command(name="du_doan_db", description="Dự đoán giải đặc biệt hôm nay")
async def du_doan_db(interaction: discord.Interaction, mien: str):
    numbers, ratio = ai_predict_db(mien)
    phongthuy = get_phong_thuy(numbers)
    embed = discord.Embed(
        title=f"🎯 Dự đoán giải đặc biệt {mien.capitalize()} (AI)",
        description=f"**Số đặc biệt:** {', '.join(numbers)}\n{ratio}\n\n{phongthuy}",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, view=DuDoanView(mien, mode="db"))

@discord.app_commands.command(name="ketqua", description="Tra cứu kết quả xổ số theo ngày (định dạng YYYY-MM-DD)")
async def ketqua(interaction: discord.Interaction, ngay: str):
    try:
        data = pd.read_csv('xs_mienbac_full.csv')
        row = data[data['date'] == ngay]
        if row.empty:
            await interaction.response.send_message("Không tìm thấy kết quả ngày này.", ephemeral=True)
            return
        # Show tóm tắt các giải
        msg = f"Kết quả XSMB ngày {ngay}:\n"
        for col in data.columns:
            if col != "date":
                msg += f"- {col}: {str(row.iloc[0][col])}\n"
        await interaction.response.send_message(msg)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi tra cứu: {e}", ephemeral=True)

@discord.app_commands.command(name="topso", description="Top N số về nhiều nhất trong 30 ngày")
async def topso(interaction: discord.Interaction, n: int):
    data = pd.read_csv('xs_mienbac_full.csv')
    # Gộp tất cả giải thành 1 list
    all_numbers = []
    for _, row in data.iterrows():
        for col in data.columns:
            if col != "date":
                num = str(row[col])[-2:]
                all_numbers.append(num)
    # Đếm tần suất
    from collections import Counter
    cnt = Counter(all_numbers)
    top_n = cnt.most_common(n)
    msg = "**Top số về nhiều nhất 30 ngày:**\n" + "\n".join([f"{s[0]}: {s[1]} lần" for s in top_n])
    await interaction.response.send_message(msg)

@discord.app_commands.command(name="thongke", description="Thống kê số bất kỳ đã về bao nhiêu lần trong 30 ngày")
async def thongke(interaction: discord.Interaction, so: str):
    data = pd.read_csv('xs_mienbac_full.csv')
    so = so.zfill(2)
    count = 0
    for _, row in data.iterrows():
        for col in data.columns:
            if col != "date":
                num = str(row[col])[-2:]
                if num == so:
                    count += 1
    await interaction.response.send_message(f"Số {so} đã về {count} lần trong 30 ngày gần nhất.")

@discord.app_commands.command(name="phongthuy", description="Tra ý nghĩa phong thủy của số bất kỳ")
async def phongthuy(interaction: discord.Interaction, so: str):
    so = so.zfill(2)
    y_nghia = phong_thuy_dict.get(so, "Chưa cập nhật ý nghĩa")
    embed = discord.Embed(
        title=f"🔮 Phong thủy số {so}",
        description=y_nghia,
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed)

@discord.app_commands.command(name="so_ngau_nhien", description="Random dãy số và phân tích phong thủy")
async def so_ngau_nhien(interaction: discord.Interaction):
    import random
    numbers = [str(random.randint(0,99)).zfill(2) for _ in range(5)]
    phongthuy = get_phong_thuy(numbers)
    embed = discord.Embed(
        title="✨ Số ngẫu nhiên và ý nghĩa phong thủy",
        description=f"**Số đẹp:** {', '.join(numbers)}\n\n{phongthuy}",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed)

# ======= ADMIN: Reload data & train lại model (chỉ admin) =======
@discord.app_commands.command(name="reload_data", description="(Admin) Reload lại dữ liệu xổ số từ file csv")
@commands.has_permissions(administrator=True)
async def reload_data(interaction: discord.Interaction):
    try:
        pd.read_csv('xs_mienbac_full.csv')
        await interaction.response.send_message("Đã reload lại dữ liệu thành công!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi reload: {e}", ephemeral=True)

@discord.app_commands.command(name="train_model", description="(Admin) Train lại model AI từ dữ liệu mới")
@commands.has_permissions(administrator=True)
async def train_model(interaction: discord.Interaction):
    # Gợi ý: Bạn nên train model bằng file train riêng, rồi tự động save .h5
    await interaction.response.send_message("Chức năng train lại model đang phát triển. Vui lòng train offline rồi cập nhật .h5!", ephemeral=True)

# ======= SỰ KIỆN BOT =======
@bot.event
async def on_ready():
    print(f'Đã đăng nhập bot: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Đã sync {len(synced)} lệnh slash.")
    except Exception as e:
        print(e)

# ======= CHẠY BOT =======
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
