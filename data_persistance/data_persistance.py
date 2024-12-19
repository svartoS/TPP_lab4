# data_persistence.py
import pandas as pd
import tkinter.messagebox as messagebox
import logging

logger = logging.getLogger('ServiceLogger')


def export_to_excel(data: pd.DataFrame, filename="exported_data.xlsx"):
    if data is not None and isinstance(data, pd.DataFrame):
        try:
            data.to_excel("output/" + filename, index=True)
            messagebox.showinfo("Export Successful", f"Data exported to {filename}")
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            messagebox.showerror("Export Error", "Failed to export data.")
    else:
        logger.warning("No valid data provided for export.")
        messagebox.showwarning("No Data", "No valid data available to export.")
