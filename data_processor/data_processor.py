import logging
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional

logger = logging.getLogger('ServiceLogger')


def moving_average(data: pd.Series, window: int = 30) -> pd.Series:
    if not isinstance(data, pd.Series):
        raise ValueError("Input data must be a pandas Series.")
    return data.rolling(window=window).mean()


def custom_moving_average(data: pd.Series, window: int = 30) -> pd.Series:
    if not isinstance(data, pd.Series):
        raise ValueError("Input data must be a pandas Series.")
    if window <= 0:
        raise ValueError("Window size must be positive.")

    filtered = np.zeros(data.size, dtype=float)
    window_buffer = np.zeros(window, dtype=float)
    for index, value in enumerate(data):
        window_buffer[index % window] = value
        filtered[index] = np.mean(window_buffer)
    return pd.Series(data=filtered, index=data.index)


def median_filter(data: pd.Series, window: int = 30) -> pd.Series:
    if not isinstance(data, pd.Series):
        raise ValueError("Input data must be a pandas Series.")
    if window <= 0 or window % 2 == 0:
        raise ValueError("Window size must be a positive odd integer.")

    return data.rolling(window=window, center=True).median()


def time_series_differential(data: pd.Series, order: int = 1) -> pd.Series:
    if not isinstance(data, pd.Series):
        raise ValueError("Input data must be a pandas Series.")
    return data.diff(periods=order)


def autocorrelation(data: pd.Series, lag: int = 1) -> float:
    if not isinstance(data, pd.Series):
        raise ValueError("Input data must be a pandas Series.")
    return data.autocorr(lag=lag)


def extreme_points(data: pd.Series, order: int = 1):
    if len(data) < 3:  # Handles case of array being to short.
        return [], [], [], []
    data_values = data.values.flat
    gen = (p2 for p1, p2, p3 in zip(data_values[:-2], data_values[1:-1], data_values[2:]) if
           (p2 - p1) * (p3 - p2) < 0.0)
    result = np.array(tuple(gen), dtype=float)
    if result.size == 0:  # If no data.
        return [], [], [], []

    # extract maxima and minima indices
    maxima_indices = []
    minima_indices = []
    maxima_values = []
    minima_values = []

    for i in range(1, len(data_values) - 1):
        if (data_values[i - 1] < data_values[i] and data_values[i + 1] < data_values[i]):
            maxima_indices.append(i)
            maxima_values.append(data_values[i])

        if (data_values[i - 1] > data_values[i] and data_values[i + 1] > data_values[i]):
            minima_indices.append(i)
            minima_values.append(data_values[i])

    return maxima_indices, maxima_values, minima_indices, minima_values

def process_data(data, draw_ma=False, draw_median_filter=False, draw_extremes=False):
    """Process data and extract analysis results"""
    if data is None:
        return None
    result = {"original": data}
    try:
        if draw_ma:
            result["ma"] = moving_average(data, window=3)

        if draw_median_filter:
            result["median"] = median_filter(data, window=3)

        if draw_extremes:
            maxima_indices, maxima_values, minima_indices, minima_values = extreme_points(data)
            result["maxima_indices"] = pd.Series(data.index[maxima_indices], index=maxima_indices) if maxima_indices else None
            result["maxima_values"] = pd.Series(maxima_values, index=maxima_indices) if maxima_indices else None
            result["minima_indices"] = pd.Series(data.index[minima_indices], index=minima_indices) if minima_indices else None
            result["minima_values"] = pd.Series(minima_values, index=minima_indices) if minima_indices else None
        return pd.DataFrame(result)
    except Exception as e:
        logger.error(f"Failed to analyze data: {e}")
        return None