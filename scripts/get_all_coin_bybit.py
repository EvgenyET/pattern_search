# Информация обо всех фьючерсных парах на ByBit

import sys
import requests
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

# URL эндпойнта для получения тикеров (USDT, linear futures)
url = "https://api.bybit.com/v5/market/tickers?category=linear"

# Для спотовых пар:
# https://api.bybit.com/v5/market/tickers?category=spot

# Функция для получения данных и отображения таблицы
def show_table():
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # Отладка: смотрим, что вернул API
        print("Ответ API Bybit:")
        print(data)

        # Проверяем, есть ли данные в ответе
        if "result" not in data or "list" not in data["result"]:
            print("Ошибка: API не вернул список тикеров.")
            return

        tickers = data["result"]["list"]
        if not tickers:
            print("Ошибка: API вернул пустой список тикеров.")
            return

        # Формируем данные для таблицы
        tickers_data = []
        for ticker in tickers:
            # Фильтруем по символу (например, "BTCUSDT")
            if ticker.get("symbol", "").endswith("USDT"):
                tickers_data.append({
                    "symbol": ticker.get("symbol", ""),
                    "lastPrice": ticker.get("lastPrice", ""),
                    "bid1Price": ticker.get("bid1Price", ""),
                    "ask1Price": ticker.get("ask1Price", ""),
                    "24h_change": ticker.get("price24hPcnt", ""),
                    "highPrice24h": ticker.get("highPrice24h", ""),
                    "lowPrice24h": ticker.get("lowPrice24h", "")
                })

        if not tickers_data:
            print("Ошибка: Не найдено ни одной пары с USDT.")
            return

        df = pd.DataFrame(tickers_data)

        # Создание приложения PyQt5
        app = QApplication(sys.argv)
        window = QMainWindow()
        window.setWindowTitle("Таблица тикеров USDT (Bybit API v5)")
        window.setGeometry(100, 100, 980, 900)

        central_widget = QWidget()
        layout = QVBoxLayout()
        table_view = QTableView()
        layout.addWidget(table_view)
        central_widget.setLayout(layout)
        window.setCentralWidget(central_widget)

        # Отображение данных в таблице
        model = QStandardItemModel(df.shape[0], df.shape[1])
        model.setHorizontalHeaderLabels(df.columns)

        for row in range(df.shape[0]):
            for column in range(df.shape[1]):
                item = QStandardItem(str(df.iat[row, column]))
                model.setItem(row, column, item)

        table_view.setModel(model)

        window.show()
        sys.exit(app.exec_())
    else:
        print("Ошибка при получении данных:", response.status_code)


# Вызов функции для отображения таблицы
show_table()
