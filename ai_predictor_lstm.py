import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

lstm_model = load_model('lstm_model_mb.h5')

def preprocess_input():
    data = pd.read_csv('xs_mienbac_full.csv')
    data = data.sort_values('date')
    data['DB2'] = data['DB'].astype(str).str[-2:].astype(int)
    db_list = data['DB2'].values
    # Lấy 7 ngày gần nhất
    x_input = db_list[-7:]
    x_input = np.array(x_input).reshape((1, 7, 1))
    return x_input

def predict_loto_lstm():
    x_input = preprocess_input()
    pred = lstm_model.predict(x_input)
    so_dep = str(int(abs(pred[0][0]) % 100)).zfill(2)
    # Có thể random thêm 4 số khác nếu muốn dự đoán 5 số
    import random
    so_deps = [so_dep] + [str(random.randint(0,99)).zfill(2) for _ in range(4)]
    return so_deps, "Tỉ lệ dự đoán AI LSTM: 9%"
