import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import os
from dotenv import load_dotenv
from phong_thuy_dict import phong_thuy_dict
from ai_predictor_lstm import predict_loto_lstm

# Hàm gọi AI cho từng miền (hiện tại dùng chung 1 model, bạn có thể mở rộng nếu train riêng cho từng miền)
def ai_predict(mien):
    if mien == "bac":
        return predict_loto_lstm()
    # Mẫu mở rộng: elif mien == "trung": return predict_loto_lstm_trung()
    # elif mien == "nam": return predict_loto_lstm_nam()
    return ["Chưa hỗ trợ miền này"], ""

def get_phong_thuy(numbers):
    pt_list = []
    for n in numbers:
        y_nghia = phong_thuy_dict.get(n, "Chưa cập nhật ý nghĩa")
        pt_list.append(f"Số **{n}**: {y_nghia}")
    return "\n".join(pt_list)

class DuDoanView(View):
    def __init__(self, mien):
        super().__init__(timeout=60)
        self.mien = mien

    @discord.ui.button(label="🔁 Dự đoán lại", style=discord.ButtonStyle.primary)
    async def random_button(self, interaction: discord.Interaction, button: Button):
        numbers, ratio = ai_predict(self.mien)
        phongthuy = get_phong_thuy(numbers)
        embed = discord.Embed(
            title=f"🔮 Dự đoán xổ số {self.mien.capitalize()} (AI LSTM)",
            description=f"**Số đẹp:** {', '.join(numbers)}\n{ratio}\n\n{phongthuy}",
            color=discord.Color.green()
        )
        embed.set_footer(text="AI & Phong thủy cùng bạn may mắn 🤖✨")
        await interaction.response.edit_message(embed=embed, view=self)

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
        numbers, ratio = ai_predict(mien)
        phongthuy = get_phong_thuy(numbers)
        embed = discord.Embed(
            title=f"🔮 Dự đoán xổ số {mien.capitalize()} (AI LSTM)",
            description=f"**Số đẹp:** {', '.join(numbers)}\n{ratio}\n\n{phongthuy}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://i.imgur.com/gwJg5yG.png")
        embed.set_footer(text="AI & Phong thủy cùng bạn may mắn 🤖✨")
        await interaction.response.send_message(embed=embed, view=DuDoanView(mien))

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        self.tree.add_command(du_doan_xoso)

bot = MyBot()

@discord.app_commands.command(name="du_doan_xoso", description="Dự đoán xổ số 3 miền kèm phân tích phong thủy")
async def du_doan_xoso(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Hãy chọn miền bạn muốn dự đoán:",
        view=SelectMienView()
    )

@bot.event
async def on_ready():
    print(f'Đã đăng nhập bot: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Đã sync {len(synced)} lệnh slash.")
    except Exception as e:
        print(e)

# Load token từ .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
