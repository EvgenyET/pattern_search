import pandas as pd
import numpy as np
import json
from datetime import datetime
import pywt  # Библиотека PyWavelets для wavelet-подхода

# === 1) Загрузка данных из датафрейма ===
# ВАЖНО: Замените 'bybit_dataframe_1d.pkl' на имя вашего актуального файла,
# в который сохраняются данные с биржи Bybit.
df = pd.read_pickle('dataframe/dataframe_bybit_btc_1h.pkl')

# Предполагаем, что колонки в df называются ['timestamp', 'open', 'high', 'low', 'close'].
# Если у вас другие названия — замените их соответствующе.
timestamps = df['timestamp'].astype(float).values
open_prices = df['open'].astype(float).values
high_prices = df['high'].astype(float).values
low_prices = df['low'].astype(float).values
close_prices = df['close'].astype(float).values

# Переводим таймстемпы в удобный формат (если таймстемпы у вас в секундах — делите на 1, а не на 1000)
dates = [datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d') for ts in timestamps]

# === 2) Подготовка данных для свечного графика ===
def prepare_candlestick_data(dates, opens, highs, lows, closes):
    data = []
    for i in range(len(dates)):
        data.append({
            'date':  dates[i],
            'open':  opens[i],
            'high':  highs[i],
            'low':   lows[i],
            'close': closes[i]
        })
    return data

main_chart_data = prepare_candlestick_data(dates, open_prices, high_prices, low_prices, close_prices)

# === 3) Параметры для поиска паттернов ===
window_size = 8             # длина паттерна
similarity_threshold = 0.75  # «процент» (порог) похожести
measure_method = 'mse'      # <-- 'mse', 'corr', 'shape', 'shape_log', 'dtw', 'wavelet', 'multiscale_corr'
price_scale = 'linear'      # <-- 'linear' или 'log'

# === Доп. функция: формирование фич для MSE (учёт тела и фитилей) ===
def prepare_candle_features(opens, highs, lows, closes):
    """
    Возвращает одномерный массив вида:
    [body1, wickUp1, wickDown1,  body2, wickUp2, wickDown2, ...]
    где:
      - body  = abs(open - close)
      - wickUp   = high - max(open, close)
      - wickDown = min(open, close) - low
    """
    out = []
    for o, h, l, c in zip(opens, highs, lows, closes):
        body = abs(o - c)
        wick_up = h - max(o, c)
        wick_down = min(o, c) - l
        out.extend([body, wick_up, wick_down])
    return np.array(out, dtype=float)

# --- Готовим паттерн для остальных методов (corr, shape, dtw, и т.д.) ---
if price_scale == 'log':
    # Логарифмический вариант для паттерна (для НЕ MSE-методов)
    log_prices = np.log(close_prices + 1e-9)
    pattern_log = log_prices[-window_size:]
    pattern_changes = np.diff(pattern_log)
else:
    # Линейные относительные изменения
    pattern_close = close_prices[-window_size:]
    pattern_changes = np.diff(pattern_close) / pattern_close[:-1]

# --- Готовим паттерн для MSE (тела + фитили) ---
pattern_opens  = open_prices[-window_size:]
pattern_highs  = high_prices[-window_size:]
pattern_lows   = low_prices[-window_size:]
pattern_closes = close_prices[-window_size:]
pattern_features_mse = prepare_candle_features(pattern_opens, pattern_highs, pattern_lows, pattern_closes)

# === 4) Функции измерения похожести (КОРОТКО О КАЖДОМ МЕТОДЕ) ===

def similarity_mse(arrayA, arrayB):
    """
    Метод 'mse':
    Теперь считает MSE между двумя любыми массивами (хоть candle-фичи, хоть что).
    Чем ближе к 1, тем «похожее».
    """
    if len(arrayA) != len(arrayB):
        return 0.0

    mse = np.mean((arrayB - arrayA) ** 2)
    denom = np.mean(arrayA ** 2)
    if denom == 0:
        return 1.0 if mse < 1e-9 else 0.0

    rel_err = mse / denom
    sim = 1 - rel_err
    if sim < 0:
        sim = 0
    if sim > 1:
        sim = 1
    return sim

def similarity_correlation(pattern_changes, window_changes):
    """
    Метод 'corr':
    Возвращает корреляцию Пирсона в [-1..1], переводим её в [0..1].
    """
    if len(pattern_changes) != len(window_changes):
        return 0.0
    corr = np.corrcoef(pattern_changes, window_changes)[0, 1]
    return (corr + 1) / 2

def similarity_shape(pattern_changes, window_changes):
    """
    Метод 'shape':
    Линейная нормализация [0..1] + корреляция Пирсона.
    """
    if len(pattern_changes) != len(window_changes):
        return 0.0

    p_min, p_max = np.min(pattern_changes), np.max(pattern_changes)
    if p_max - p_min == 0:
        return 0.0
    pattern_norm = (pattern_changes - p_min) / (p_max - p_min)

    w_min, w_max = np.min(window_changes), np.max(window_changes)
    if w_max - w_min == 0:
        return 0.0
    window_norm = (window_changes - w_min) / (w_max - w_min)

    corr = np.corrcoef(pattern_norm, window_norm)[0, 1]
    return (corr + 1) / 2

def similarity_shape_log(pattern_changes, window_changes):
    """
    Метод 'shape_log':
    Логарифмическая нормализация + корреляция Пирсона.
    """
    if len(pattern_changes) != len(window_changes):
        return 0.0

    def log_transform(arr):
        sign = np.sign(arr)
        mag  = np.log1p(np.abs(arr))
        return sign * mag

    p_log = log_transform(pattern_changes)
    w_log = log_transform(window_changes)

    p_mean, p_std = np.mean(p_log), np.std(p_log)
    w_mean, w_std = np.mean(w_log), np.std(w_log)

    if p_std == 0 or w_std == 0:
        return 0.0

    p_z = (p_log - p_mean) / p_std
    w_z = (w_log - w_mean) / w_std

    corr = np.corrcoef(p_z, w_z)[0, 1]
    return (corr + 1) / 2

# DTW
def dtw_distance(seq1, seq2):
    n, m = len(seq1), len(seq2)
    dtw_matrix = np.ones((n+1, m+1)) * np.inf
    dtw_matrix[0, 0] = 0
    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = abs(seq1[i-1] - seq2[j-1])
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i-1, j],    # удаление
                dtw_matrix[i, j-1],    # вставка
                dtw_matrix[i-1, j-1]   # совпадение
            )
    return dtw_matrix[n, m]

def similarity_dtw(pattern_changes, window_changes):
    """
    Метод 'dtw':
    Расстояние DTW -> перевод в похожесть [0..1].
    """
    if len(pattern_changes) == 0 or len(window_changes) == 0:
        return 0.0
    dist = dtw_distance(pattern_changes, window_changes)
    return 1 / (1 + dist)

# Wavelet
def wavelet_coeffs(series, wavelet='db4', level=3):
    return pywt.wavedec(series, wavelet, level=level)

def similarity_wavelet(pattern_changes, window_changes, wavelet='db4', level=2):
    """
    Метод 'wavelet':
    Вейвлет-анализ -> косинусное сходство -> [0..1].
    """
    if len(pattern_changes) != len(window_changes):
        return 0.0
    coeffsA = wavelet_coeffs(pattern_changes, wavelet=wavelet, level=level)
    coeffsB = wavelet_coeffs(window_changes, wavelet=wavelet, level=level)

    flatA = np.concatenate(coeffsA)
    flatB = np.concatenate(coeffsB)

    dot = np.dot(flatA, flatB)
    normA = np.linalg.norm(flatA)
    normB = np.linalg.norm(flatB)
    if normA == 0 or normB == 0:
        return 0.0

    cos_sim = dot / (normA * normB)  # [-1..1]
    return (cos_sim + 1) / 2        # [0..1]

# Многомасштабная корреляция
def moving_average(arr, w):
    if len(arr) < w:
        return np.array([])
    cum = np.cumsum(arr, dtype=float)
    cum[w:] = cum[w:] - cum[:-w]
    return cum[w - 1:] / w

def multiscale_correlation(pattern_changes, window_changes, scales=[2, 5, 10]):
    """
    Метод 'multiscale_corr':
    Несколько уровней сглаживания -> усреднение корреляций.
    """
    if len(pattern_changes) != len(window_changes):
        return 0.0

    def corr01(x, y):
        if len(x) != len(y) or len(x) == 0:
            return 0.0
        c = np.corrcoef(x, y)[0, 1]
        return (c + 1) / 2

    sims = []
    base_sim = corr01(pattern_changes, window_changes)
    sims.append(base_sim)

    for w in scales:
        A_smooth = moving_average(pattern_changes, w)
        B_smooth = moving_average(window_changes, w)
        length = min(len(A_smooth), len(B_smooth))
        if length <= 0:
            sims.append(0.0)
        else:
            sim_w = corr01(A_smooth[:length], B_smooth[:length])
            sims.append(sim_w)

    return np.mean(sims)

def measure_similarity(pattern_changes, window_changes,
                       pattern_features_mse=None,
                       window_features_mse=None,
                       method='mse'):
    """
    Вызывает нужную функцию сходства.
    Важно: если method='mse', мы учитываем тело/фитили (pattern_features_mse, window_features_mse).
    Иначе - используем pattern_changes, window_changes, как раньше.
    """
    if method == 'mse':
        # Для MSE используем массивы candle-фичей
        if pattern_features_mse is None or window_features_mse is None:
            return 0.0
        return similarity_mse(pattern_features_mse, window_features_mse)
    elif method == 'corr':
        return similarity_correlation(pattern_changes, window_changes)
    elif method == 'shape':
        return similarity_shape(pattern_changes, window_changes)
    elif method == 'shape_log':
        return similarity_shape_log(pattern_changes, window_changes)
    elif method == 'dtw':
        return similarity_dtw(pattern_changes, window_changes)
    elif method == 'wavelet':
        return similarity_wavelet(pattern_changes, window_changes,
                                  wavelet='db4', level=2)
    elif method == 'multiscale_corr':
        return multiscale_correlation(pattern_changes, window_changes,
                                      scales=[2, 5, 10])
    else:
        raise ValueError(f"Неизвестный метод: {method}")

# === 5) Поиск похожих участков ===
similar_relative_indices = []
for i in range(len(close_prices) - window_size):
    window_opens  = open_prices[i : i + window_size]
    window_highs  = high_prices[i : i + window_size]
    window_lows   = low_prices[i : i + window_size]
    window_closes = close_prices[i : i + window_size]

    # Если MSE — готовим "candle features" (тело и фитили)
    if measure_method == 'mse':
        window_features_mse = prepare_candle_features(window_opens,
                                                      window_highs,
                                                      window_lows,
                                                      window_closes)
        # pattern_features_mse уже посчитаны
        sim = measure_similarity(None, None,
                                 pattern_features_mse=pattern_features_mse,
                                 window_features_mse=window_features_mse,
                                 method='mse')
    else:
        # Все остальные методы: либо логарифмические изменения, либо линейные
        if price_scale == 'log':
            window_log = np.log(window_closes + 1e-9)
            window_changes = np.diff(window_log)
        else:
            window_changes = np.diff(window_closes) / window_closes[:-1]

        sim = measure_similarity(pattern_changes, window_changes,
                                 method=measure_method)

    if sim >= similarity_threshold:
        similar_relative_indices.append(i)

# === 6) Подготовка данных для «оригинального паттерна» и «совпадений» ===
pattern_data = prepare_candlestick_data(
    dates[-window_size:],
    open_prices[-window_size:],
    high_prices[-window_size:],
    low_prices[-window_size:],
    close_prices[-window_size:]
)

matches = []
for idx in similar_relative_indices:
    match_data = prepare_candlestick_data(
        dates[idx:idx + window_size],
        open_prices[idx:idx + window_size],
        high_prices[idx:idx + window_size],
        low_prices[idx:idx + window_size],
        close_prices[idx:idx + window_size]
    )
    matches.append({
        'start_index': idx,
        'candles': match_data
    })

# === 7) Формирование итогового JSON ===
output_data = {
    'main_chart': {'prices': main_chart_data},
    'original_pattern': pattern_data,
    'matches': matches
}

with open('candlestick_patterns.json', 'w') as f:
    json.dump(output_data, f, indent=4)

print("Данные успешно сохранены в 'candlestick_patterns.json'")
