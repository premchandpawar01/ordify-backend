# dialogs/filter_dialog.py
# UPDATED: Inherits from BaseDialog for a professional look.

import sys
from PyQt6.QtWidgets import (
    QVBoxLayout, QFormLayout, QDialogButtonBox, 
    QComboBox, QDateEdit, QWidget
)
from PyQt6.QtCore import QDate, Qt

# NEW: Import BaseDialog
from .base_dialog import BaseDialog

# UPDATED: Inherit from BaseDialog
class FilterDialog(BaseDialog):
    def __init__(self, parent, current_settings):
        # UPDATED: Set title for BaseDialog
        title = "Select Date Filter"
        super().__init__(title, parent)
        
        # --- Store results ---
        self.selected_filter_type = current_settings.get('type', 'All Time')
        self.start_date = current_settings.get('start', QDate.currentDate().addMonths(-1))
        self.end_date = current_settings.get('end', QDate.currentDate())

        # --- Create Widgets ---
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Time", "This Month", "This Week", "Custom Date Range"])
        self.filter_combo.setCurrentText(self.selected_filter_type)
        self.filter_combo.currentTextChanged.connect(self.toggle_custom_dates)

        # --- Custom Date Widgets ---
        self.custom_date_widget = QWidget()
        date_layout = QFormLayout(self.custom_date_widget)
        date_layout.setContentsMargins(0, 0, 0, 0)
        
        self.start_date_edit = QDateEdit(self.start_date)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd-MMM-yyyy")
        
        self.end_date_edit = QDateEdit(self.end_date)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd-MMM-yyyy")

        date_layout.addRow("Start Date:", self.start_date_edit)
        date_layout.addRow("End Date:", self.end_date_edit)

        # --- Layout ---
        form_layout = QFormLayout()
        form_layout.addRow("Filter by:", self.filter_combo)
        
        # UPDATED: Add widgets to the BaseDialog's content area
        self.content_layout.addLayout(form_layout)
        self.content_layout.addWidget(self.custom_date_widget)
        self.content_layout.addStretch()
        
        # UPDATED: Connect the existing button_box from BaseDialog
        # BaseDialog defaults to Ok | Cancel, which is what we want.
        self.button_box.accepted.disconnect() # Disconnect default self.accept
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)

        self.toggle_custom_dates(self.selected_filter_type)
        self.setMinimumWidth(350)

    def toggle_custom_dates(self, text):
        """Shows or hides the custom date pickers."""
        self.custom_date_widget.setVisible(text == "Custom Date Range")

    def on_accept(self):
        """Saves the selected values before accepting."""
        self.selected_filter_type = self.filter_combo.currentText()
        self.start_date = self.start_date_edit.date()
        self.end_date = self.end_date_edit.date()
        
        if self.selected_filter_type == "Custom Date Range" and self.start_date > self.end_date:
            QMessageBox.warning(self, "Invalid Range", "The start date cannot be after the end date.")
            return

        self.accept()