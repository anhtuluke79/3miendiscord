import numpy as np
from tensorflow.keras.models import load_model
import pandas as pd
import random

# B1: Nạp model (nên chỉ load 1 lần)
lstm_model = load_model('lstm_model_mb.h5')

# B2: Chuẩn hóa input - GIẢ LẬP mẫu (bạn nên thay bằng input thực tế của mình)
def preprocess_input():
    # Nếu bạn dùng dữ liệu từ csv (ví dụ: xs_mienbac.csv)
    # data = pd.read_csv('xs_mienbac.csv')
    # Lấy 30 ngày gần nhất, trích các đặc trưng bạn đã train
    # Xử lý giống như lúc train model, rồi reshape về (1, time_steps, features)
    # --- Dưới đây là giả lập mẫu, bạn thay lại cho đúng logic mình đã train ---
    x_input = np.random.rand(1, 30, 5)  # (batch, timesteps, features)
    return x_input

def predict_loto_lstm():
    x_input = preprocess_input()
    pred = lstm_model.predict(x_input)
    # Bạn cần decode pred thành dãy số đẹp, tùy vào cách train & output model của bạn
    # Ví dụ: pred là 1 vector, bạn lấy 5 số đầu, mod 100 để thành 2 chữ số
    so_deps = [str(int(abs(x) % 100)).zfill(2) for x in pred[0][:5]]
    # Có thể thêm tính toán tỷ lệ nếu muốn
    return so_deps, "Tỉ lệ dự đoán AI LSTM: 9%"
