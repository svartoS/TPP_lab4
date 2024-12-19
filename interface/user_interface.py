import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging

logger = logging.getLogger('ServiceLogger')

class ServiceWindow:
    def __init__(self, name, ticker, period, interval, export_callback=None):
        self.name = name
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.export_callback = export_callback

        self.root = tk.Toplevel()
        self.root.title(f"Сервис: {name} - {ticker}")
        self.data = None

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.draw_ma = tk.IntVar(value=0)
        self.draw_median_filter = tk.IntVar(value=0)
        self.draw_extremes = tk.IntVar(value=0)

        tk.Checkbutton(self.root,
                       text="Построить скользящее среднее",
                       variable=self.draw_ma,
                       command=self.update_plot_callback).pack()
        tk.Checkbutton(self.root,
                       text="Построить медианный фильтр",
                       variable=self.draw_median_filter,
                       command=self.update_plot_callback).pack()
        tk.Checkbutton(self.root,
                       text="Построить экстремумы",
                       variable=self.draw_extremes,
                       command=self.update_plot_callback).pack()

        export_button = tk.Button(self.root, text="Экспортировать в Excel", command=self._export_to_excel)
        export_button.pack()

        self.running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _export_to_excel(self):
        if self.export_callback:
            self.export_callback(self.data)
        else:
            messagebox.showwarning("No Data", "No data available to export.")

    def update_plot_callback(self):
        if self.data is not None:
            self.update_plot(self.data)

    def update_plot(self, data):
        """Обновление графика с новыми данными."""
        self.data = data
        try:
            self.ax.clear()

            if data is not None:
                self.ax.plot(data["original"].index, data["original"], label="Original Data", color='blue')

                if self.draw_ma.get() and "ma" in data:
                    self.ax.plot(data["ma"].index, data["ma"], label="Moving Average", color='red')

                if self.draw_median_filter.get() and "median" in data:
                    self.ax.plot(data["median"].index, data["median"], label="Median Filter", color='green')

                if self.draw_extremes.get() and "maxima_indices" in data and "minima_indices" in data:
                    self.ax.scatter(data["maxima_indices"], data["maxima_values"], color='red', label="Maxima",
                                    zorder=5)
                    self.ax.scatter(data["minima_indices"], data["minima_values"], color='blue', label="Minima",
                                    zorder=5)

                self.ax.legend()
                self.ax.set_title(f"График данных для {self.ticker} ({self.period})")
            else:
                logger.warning(f"Нет данных для отображения для {self.ticker}.")
                self.ax.text(0.5, 0.5, "Нет данных для отображения", fontsize=12, ha='center',
                             transform=self.ax.transAxes)

            self.canvas.draw()  # Обновление отображения
        except Exception as e:
            logger.error(f"Ошибка при обновлении графика для {self.ticker}: {e}")

    def is_alive(self):
        return self.running

    def stop(self):
        logger.info(f"Stopping window for {self.ticker}.")
        self.running = False
        self.root.destroy()

    def on_close(self):
        logger.info(f"Closing window for {self.ticker}.")
        self.stop()


class App:
    def __init__(self, root, start_callback, stop_callback):
        self.default_ticker = "MSFT"
        self.default_start = "2024-01-01"
        self.default_end = "2024-11-09"
        self.default_interval = "1m"

        self.root = root
        self.root.title("Finance app")
        self.start_callback = start_callback
        self.stop_callback = stop_callback

        ticker_entry_label = tk.Label(self.root, text="Ticker:")
        ticker_entry_label.pack()
        self.ticker_var = tk.StringVar(value=self.default_ticker)
        self.ticker_entry = tk.Entry(self.root, textvariable=self.ticker_var)
        self.ticker_entry.pack()

        period_entry_label = tk.Label(self.root, text="Choose period:")
        period_entry_label.pack()
        self.period_var = tk.StringVar(value="1d")
        period_options = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        self.period_combobox = ttk.Combobox(self.root, textvariable=self.period_var, values=period_options)
        self.period_combobox.pack()

        interval_entry_label = tk.Label(self.root, text="Choose interval:")
        interval_entry_label.pack()
        self.interval_var = tk.StringVar(value="1d")
        interval_options = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
        self.interval_combobox = ttk.Combobox(self.root, textvariable=self.interval_var, values=interval_options)
        self.interval_combobox.pack()

        self.start_button = tk.Button(root, text="Анализ", command=self._start_monitoring)
        self.start_button.pack()
        self.stop_button = tk.Button(root, text="Остановить", command=self._stop_monitoring)
        self.stop_button.pack()

        self.services = {}

    def _start_monitoring(self):
        ticker = self.ticker_entry.get()
        period = self.period_var.get()
        interval = self.interval_var.get()
        self.start_callback(ticker, period, interval)

    def _stop_monitoring(self):
        ticker = self.ticker_entry.get()
        self.stop_callback(ticker)

    @staticmethod
    def show_error(message):
        messagebox.showerror("Error", message)

    @staticmethod
    def show_warning(message):
        messagebox.showwarning("Warning", message)

    def check_services_alive(self, services):
        to_remove = []
        for ticker, (service, monitoring_service, data_queue) in services.items():
            if not service.is_alive():
                messagebox.showwarning("Service Stopped", f"Service {ticker} has stopped.")
                service.stop()
                to_remove.append(ticker)
        for ticker in to_remove:
            del services[ticker]
        self.root.after(1000, lambda: self.check_services_alive(services))