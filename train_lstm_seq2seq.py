import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, TimeDistributed, RepeatVector
from tensorflow.keras.callbacks import EarlyStopping

# Đọc dữ liệu
data = pd.read_csv('xs_mienbac_full.csv')
data = data.sort_values('date')

# Chỉ lấy 2 số cuối của mỗi giải DB cho nhanh
db_list = data['DB'].astype(str).str[-2:].astype(int).values

# Tạo dữ liệu chuỗi: lấy 14 ngày dự đoán 5 ngày tiếp theo (dự đoán 5 số)
n_steps_in = 14
n_steps_out = 5

X, y = [], []
for i in range(len(db_list) - n_steps_in - n_steps_out + 1):
    X.append(db_list[i:i+n_steps_in])
    y.append(db_list[i+n_steps_in:i+n_steps_in+n_steps_out])

X = np.array(X)
y = np.array(y)

# Reshape cho LSTM seq2seq
X = X.reshape((X.shape[0], n_steps_in, 1))
y = y.reshape((y.shape[0], n_steps_out, 1))

# Xây model seq2seq
model = Sequential()
model.add(LSTM(64, activation='relu', input_shape=(n_steps_in, 1)))
model.add(RepeatVector(n_steps_out))
model.add(LSTM(64, activation='relu', return_sequences=True))
model.add(TimeDistributed(Dense(1)))
model.compile(optimizer='adam', loss='mse')

# Train model
model.fit(X, y, epochs=120, batch_size=4, validation_split=0.2, 
          callbacks=[EarlyStopping(patience=10, restore_best_weights=True)])

# Lưu model
model.save('lstm_seq2seq_mb.h5')
print("Đã train & lưu model seq2seq dự đoán 5 số vào lstm_seq2seq_mb.h5")
