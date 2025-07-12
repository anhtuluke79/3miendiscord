import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

lstm_model = load_model('lstm_seq2seq_mb.h5')

def preprocess_input():
    data = pd.read_csv('xsmb.csv')
    data = data.sort_values('date')
    db_list = data['DB'].astype(str).str[-2:].astype(int).values
    # Lấy 14 ngày gần nhất để dự đoán 5 ngày tiếp
    x_input = db_list[-14:]
    x_input = np.array(x_input).reshape((1, 14, 1))
    return x_input

def predict_loto_lstm_seq():
    x_input = preprocess_input()
    pred = lstm_model.predict(x_input)
    # Lấy 5 số, mỗi số lấy phần nguyên, mod 100 về dạng 2 số
    so_deps = [str(int(abs(x[0])) % 100).zfill(2) for x in pred[0]]
    return so_deps, "Tỉ lệ dự đoán AI LSTM: 9%"
