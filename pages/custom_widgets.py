# pages/custom_widgets.py
# This new file contains custom QTableWidgetItem subclasses
# to allow for proper sorting of numbers and dates in tables.

from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import QDateTime, Qt, QDate
from datetime import datetime as py_datetime

class NumericTableWidgetItem(QTableWidgetItem):
    """
    A custom QTableWidgetItem that allows for correct numerical sorting.
    It sorts based on a float value, not the string representation.
    """
    def __init__(self, value, is_currency=False):
        # Format the string for display
        if is_currency:
            display_text = f"₹{value:,.2f}"
        else:
            display_text = str(value)
            
        super().__init__(display_text)
        
        # Store the actual numeric value for sorting
        self.numeric_value = float(value)

    def __lt__(self, other):
        # This is the less-than comparison method used by sorting
        if isinstance(other, NumericTableWidgetItem):
            return self.numeric_value < other.numeric_value
        return super().__lt__(other)

class DateTimeTableWidgetItem(QTableWidgetItem):
    """
    A custom QTableWidgetItem that allows for correct date/datetime sorting.
    It sorts based on a QDateTime object, not the formatted string.
    """
    def __init__(self, iso_date_string, display_format="dd-MM-yyyy"):
        self.sort_datetime = QDateTime()
        display_text = "N/A"

        if iso_date_string:
            try:
                # Try parsing as full ISO datetime
                py_dt = py_datetime.fromisoformat(iso_date_string)
                self.sort_datetime = QDateTime(py_dt.year, py_dt.month, py_dt.day, py_dt.hour, py_dt.minute, py_dt.second)
            except ValueError:
                try:
                    # Try parsing as just a date (YYYY-MM-DD)
                    py_d = QDate.fromString(iso_date_string.split('T')[0], Qt.DateFormat.ISODate)
                    self.sort_datetime = QDateTime(py_d)
                except Exception:
                    pass # Keep default QDateTime and "N/A" text

            if self.sort_datetime.isValid():
                display_text = self.sort_datetime.toString(display_format)

        super().__init__(display_text)
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other):
        # This is the less-than comparison method used by sorting
        if isinstance(other, DateTimeTableWidgetItem):
            return self.sort_datetime < other.sort_datetime
        return super().__lt__(other)