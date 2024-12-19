import datetime
import threading
import time
import logging
import yfinance as yf

from queue import Queue
from datetime import datetime, timedelta

logger = logging.getLogger('ServiceLogger')

class MonitoringServiceBackend:
    def __init__(self, ticker, period: str = '1d', interval: str = '1m', data_queue: Queue = None):
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.data_queue = data_queue
        self.is_running = threading.Event()
        self.service_thread = None
        self.last_data_timestamp = None

    def start(self):
        if not self.is_running.is_set():
            self.is_running.set()
            self.service_thread = threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while self.is_running.is_set():
            try:
                current_data = self.get_historical_data(
                    self.ticker,
                    period=self.period,
                    interval=self.interval,
                    columns=['Close'])
                if current_data is None:
                    self.data_queue.put(None)
                else:
                    self.data_queue.put(current_data)
            except Exception as e:
                logger.error(f"Error in monitoring service: {e}")
            time.sleep(15)

    def get_historical_data(self, ticker: str, period: str = "1d", interval: str = "1m", columns: list = None):
        try:
            end_date = datetime.now()

            if self.last_data_timestamp and (end_date - self.last_data_timestamp).total_seconds() < 60:
                logger.info(f"No new data needed for {ticker}. Last data timestamp: {self.last_data_timestamp}")
                return None

            data = yf.Ticker(ticker).history(period=period, interval=interval, prepost=True)

            if columns:
                data = data[columns]

            if not data.empty:
                data.index = data.index.tz_localize(None)
                self.last_data_timestamp = data.index[-1]
                return data
            else:
                return None
        except Exception as e:
            logger.error(f"Error retrieving data: {e}")
            return None

    @staticmethod
    def calculate_start_date(end_date, period):
        period_mapping = {
            '1d': 1,
            '5d': 5,
            '1mo': 30,
            '3mo': 90,
            '6mo': 180,
            '1y': 365,
            '2y': 730,
            '5y': 1825,
            '10y': 3650,
        }

        if period in period_mapping:
            return end_date - timedelta(days=period_mapping[period])
        elif period == 'ytd':
            return end_date.replace(month=1, day=1)
        elif period == 'max':
            return None
        else:
            logger.warning(f"Unknown period: {period}. Defaulting to 1 day.")
            return end_date - timedelta(days=1)

    def stop(self):
        self.is_running.clear()