# dialogs/mark_as_paid_dialog.py
# UPDATED: Inherits from BaseDialog for a professional look.

import requests
from PyQt6.QtWidgets import (
    QFormLayout, QComboBox, 
    QDialogButtonBox, QDateEdit, QMessageBox
)
from PyQt6.QtCore import QDate

# NEW: Import BaseDialog
from .base_dialog import BaseDialog

# UPDATED: Inherit from BaseDialog
class MarkAsPaidDialog(BaseDialog):
     def __init__(self, parent, bill_id):
        self.parent_window = parent
        self.bill_id = bill_id
        
        # UPDATED: Set title for BaseDialog
        title = f"Record Payment for Bill #{bill_id}"
        super().__init__(title, parent)

        # UPDATED: Create a layout, but don't set it on `self`
        form_layout = QFormLayout()
        self.payment_date = QDateEdit(QDate.currentDate())
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDisplayFormat("dd-MMM-yyyy")
        
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Bank Transfer", "Cash", "Cheque", "Online"])

        form_layout.addRow("Payment Date:", self.payment_date)
        form_layout.addRow("Payment Method:", self.payment_method)

        # UPDATED: Add the form layout to the BaseDialog's content area
        self.content_layout.addLayout(form_layout)

        # UPDATED: Configure the existing button_box from BaseDialog
        self.button_box.clear()
        self.button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.submit)
        self.button_box.rejected.connect(self.reject)

     def submit(self):
        payload = {
            "payment_date": self.payment_date.date().toString("yyyy-MM-dd"),
            "payment_method": self.payment_method.currentText()
        }

        try:
            url = f"{self.parent_window.API_BASE_URL}/monthly-bills/{self.bill_id}/payment"
            response = requests.put(url, json=payload)
            response.raise_for_status()
            self.accept()
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_msg = e.response.json().get('error', str(e))
                except:
                    pass # Keep the original error
            QMessageBox.critical(self, "API Error", f"Failed to record payment: {error_msg}")