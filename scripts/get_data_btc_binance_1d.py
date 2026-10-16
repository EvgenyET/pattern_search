import os
import pandas as pd
from binance.client import Client
import pickle

'''Загружаем данные Биткоина с биржи Binance:'''

user_key = os.environ['BINANCE_API_KEY']
secret_key = os.environ['BINANCE_API_SECRET']
binance_client = Client(user_key, secret_key)

binance_client.futures_symbol_ticker(symbol='BTCUSDT')

binance_client.futures_historical_klines(
    symbol='BTCUSDT',
    interval='1d',  # can play with this e.g. '1h', '4h', '1w', etc.
    start_str='2017-09-08',
    end_str='2024-11-30'
)

df = pd.DataFrame(binance_client.futures_historical_klines(
    symbol='BTCUSDT',
    interval='1d',
    start_str='2017-09-08',
    end_str='2024-11-30'
))

df.head()


'''Сохраняем датафрейм BTC (с биржи Binance) на жесткий диск,
 чтобы не грузить его постоянно из сети:'''

with open('dataframe_1d.pkl', 'wb') as file:
    pickle.dump(df, file)

print('Загрузка данных дневного таймфрейма (1d) закончена.')