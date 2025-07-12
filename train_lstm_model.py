import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping

# Đọc dữ liệu
data = pd.read_csv('xs_mienbac_full.csv')
data = data.sort_values('date')  # Đảm bảo theo đúng thứ tự thời gian

# Giả sử chỉ lấy 2 số cuối giải DB làm đầu ra, biến thành số nguyên
data['DB2'] = data['DB'].astype(str).str[-2:].astype(int)

# Tạo dữ liệu chuỗi thời gian: mỗi mẫu lấy 7 ngày trước dự đoán ngày tiếp theo
n_steps = 7

X, y = [], []
db_list = data['DB2'].values
for i in range(len(db_list) - n_steps):
    X.append(db_list[i:i + n_steps])
    y.append(db_list[i + n_steps])

X = np.array(X)  # shape: (samples, 7)
y = np.array(y)  # shape: (samples,)

# Đưa về đúng shape cho LSTM: (samples, timesteps, features)
X = X.reshape((X.shape[0], X.shape[1], 1))

# Xây model LSTM đơn giản
model = Sequential()
model.add(LSTM(32, input_shape=(n_steps, 1)))
model.add(Dense(1, activation='linear'))
model.compile(optimizer='adam', loss='mse')

# Train model
model.fit(X, y, epochs=80, batch_size=4, validation_split=0.2, 
          callbacks=[EarlyStopping(patience=10, restore_best_weights=True)])

# Lưu model
model.save('lstm_model_mb.h5')
print("Đã train & lưu model LSTM vào lstm_model_mb.h5")
