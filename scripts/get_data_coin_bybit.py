import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import pandas as pd
from pybit.unified_trading import HTTP
import datetime as dt
import time
import pytz

# Определение глобальных переменных
CATEGORY = "linear"
SYMBOL = "BTCUSDT"
INTERVAL = 60
START_DATE = "2019-01-09"

# Преобразуем данные из ответа API в DataFrame
def format_data(response):
    data = response.get('list', None)
    if not data:
        return
    data = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])

    # Преобразование временных меток в московское время
    f = lambda x: dt.datetime.utcfromtimestamp(int(x) / 1000)
    data.index = data.timestamp.apply(f)

    # Переворачиваем (Bybit возвращает Kline в порядке от новой к старой),
    # и приводим колонки к числовым типам
    return data[::-1].apply(pd.to_numeric)

# Возвращаем временную метку последней свечи в предоставленном DataFrame.
def get_last_timestamp(df):
    return int(df.timestamp[-1:].values[0])

def show_table():
    session = HTTP(testnet=False)

    # Определяем путь к корневой папке проекта
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Формируем путь к файлу в папке dataframe
    file_path = os.path.join(base_dir, "dataframe", "dataframe_bybit_btc_1h.pkl")

    # Если файл существует, читаем существующий DataFrame и берём из него последний таймстемп
    if os.path.exists(file_path):
        df = pd.read_pickle(file_path)
        last_timestamp = get_last_timestamp(df)
        print('Файл с датафреймом уже существует. Будем догружать данные.')
    else:
        # Иначе создаём новый DataFrame и начинаем с START_DATE
        df = pd.DataFrame()
        last_timestamp = int(dt.datetime.strptime(START_DATE, "%Y-%m-%d").timestamp() * 1000)
        print('Файл отсутствует. Создаём новый DataFrame, начиная с', START_DATE)

    # Начальное значение времени для запроса
    start = last_timestamp
    interval = INTERVAL
    symbol = SYMBOL

    # === Начинаем подгружать новые данные ===
    while True:
        # Запрос к Bybit
        response = session.get_kline(category=CATEGORY, symbol=symbol, start=start, interval=interval).get('result')
        latest = format_data(response)

        # Если format_data вернул None или пустой DataFrame, значит данных больше нет
        if not isinstance(latest, pd.DataFrame) or latest.empty:
            break

        # Берём последний таймстемп из "свежего" блока
        new_last_ts = get_last_timestamp(latest)

        # Добавляем в общий DataFrame
        df = pd.concat([df, latest])

        print(f'Загружена партия данных. Последняя свеча: {dt.datetime.fromtimestamp(new_last_ts / 1000)}')

        # Если в ответе API только 1 свеча, значит достигли конца выборки
        if len(latest) == 1:
            break

        # Если таймстемп не продвигается (достигли самого конца, нет новой свечи),
        # чтобы не застрять в бесконечном цикле — выходим
        if new_last_ts == start:
            break

        # Иначе сдвигаем start на конец текущей выборки
        start = new_last_ts

        # Небольшая пауза между запросами (Bybit может иметь лимиты)
        time.sleep(0.1)

    # Удаление дубликатов по временным меткам
    df.drop_duplicates(subset=['timestamp'], keep='last', inplace=True)

    # Сбрасываем индекс (чтобы был непрерывный)
    df.reset_index(drop=True, inplace=True)

    # Сохраняем DataFrame в файл .pkl
    df.to_pickle(file_path)
    print("Датафрейм сохранён в:", file_path)

    # Для наглядности печатаем DataFrame
    print(df)

    # --- Ниже идёт отрисовка GUI-таблицы ---
    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = QWidget()
    layout = QVBoxLayout()
    model = QStandardItemModel(df.shape[0], df.shape[1])
    model.setHorizontalHeaderLabels(df.columns)

    # Установка времени в московском формате и округление turnover
    moscow_tz = pytz.timezone('Europe/Moscow')
    for row in range(df.shape[0]):
        for column in range(df.shape[1]):
            if df.columns[column] == 'timestamp':
                moscow_time = dt.datetime.utcfromtimestamp(df.iloc[row, column] / 1000).replace(tzinfo=pytz.utc).astimezone(moscow_tz)
                readable_timestamp = moscow_time.strftime('%Y-%m-%d %H:%M:%S')
                item = QStandardItem(readable_timestamp)
            elif df.columns[column] == 'turnover':
                rounded_turnover = round(df.iloc[row, column])
                item = QStandardItem(str(rounded_turnover))
            else:
                item = QStandardItem(str(df.iloc[row, column]))
            model.setItem(row, column, item)

    table_view = QTableView()
    table_view.setModel(model)
    table_view.setSortingEnabled(True)

    # Сортируем данные по столбцу с датами в порядке убывания
    index_of_timestamp_column = df.columns.get_loc("timestamp")
    table_view.sortByColumn(index_of_timestamp_column, Qt.DescendingOrder)

    # Устанавливаем ширину колонки 'timestamp'
    table_view.setColumnWidth(index_of_timestamp_column, 120)

    layout.addWidget(table_view)
    widget.setLayout(layout)
    window.setCentralWidget(widget)

    # Устанавливаем размеры окна
    window.setGeometry(100, 50, 810, 800)
    window.show()

    sys.exit(app.exec_())

# Вызываем функцию для отображения таблицы
show_table()
