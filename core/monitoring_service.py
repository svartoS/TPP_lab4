import threading
import time
from queue import Queue
import logging
from tkinter import Tk

from core.monitoring_service_core import MonitoringServiceBackend
from data_persistance.data_persistance import export_to_excel
from data_processor.data_processor import process_data
from interface.user_interface import App, ServiceWindow

logger = logging.getLogger('ServiceLogger')

class MonitoringService:
    def __init__(self):
        self.services = {}
        self.root = Tk()
        self.app = App(self.root, self.start_monitoring, self.stop_monitoring)
        self.app.check_services_alive(self.services)

    def start(self):
        self.root.mainloop()

    def start_monitoring(self, ticker, period, interval):
        logger.info(f"Attempting to start monitoring service for {ticker}.")

        if ticker in self.services:
            logger.warning(f"Service {ticker} is already running.")
            self.app.show_warning(f"Service {ticker} is already running.")
            return

        try:
            data_queue = Queue()
            monitoring_service = self._create_monitoring_service(ticker, period, interval, data_queue)
            service_window = ServiceWindow(
                ticker,
                ticker,
                period,
                interval,
                lambda data: export_to_excel(data, f"{ticker}_exported.xlsx"))
            monitoring_service.start()

            logger.info(f"Monitoring service for {ticker} started.")

            self.services[ticker] = (service_window, monitoring_service, data_queue)
            threading.Thread(target=self.update_plot, args=(ticker,)).start()
        except Exception as e:
            logger.error(f"Failed to start service for {ticker}: {e}")
            self.app.show_error(f"Failed to start service for {ticker}.")

    @staticmethod
    def _create_monitoring_service(ticker, period, interval, data_queue):
        return MonitoringServiceBackend(ticker, period, interval, data_queue)

    def update_plot(self, ticker):
        service_window, monitoring_service, data_queue = self.services.get(ticker)
        while service_window.is_alive():
            time.sleep(0.5)
            while not data_queue.empty():
                data = data_queue.get()
                if data is not None:
                    try:
                        analyzed_data = process_data(
                            data["Close"],
                            draw_ma=True,
                            draw_median_filter=True,
                            draw_extremes=True)
                        service_window.root.after(0, service_window.update_plot, analyzed_data)
                    except Exception as e:
                        logger.error(f"Error processing data for {ticker}: {e}")
                        self.app.show_error(f"Error processing data for {ticker}: {e}")
                else:
                    logger.warning(f"No data for {ticker}.")
                    self.app.show_warning(f"No data for {ticker}.")

    def stop_monitoring(self, ticker):
        logger.info(f"Attempting to stop monitoring service for {ticker}.")

        if ticker not in self.services:
            self.app.show_warning(f"Service {ticker} is not running.")
            logger.warning(f"Service {ticker} is not running.")
            return

        try:
            service_window, monitoring_service, _ = self.services.pop(ticker)
            service_window.stop()
            monitoring_service.stop()
            logger.info(f"Service for {ticker} successfully stopped.")

        except Exception as e:
            logger.error(f"Failed to stop service for {ticker}: {e}")
            self.app.show_error(f"Failed to stop service for {ticker}.")