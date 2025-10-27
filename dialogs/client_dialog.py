# dialogs/client_dialog.py
# UPDATED: Inherits from BaseDialog for a professional look.

import requests
from PyQt6.QtWidgets import (
    QFormLayout, QLineEdit, 
    QDialogButtonBox, QMessageBox
)
# NEW: Import BaseDialog
from .base_dialog import BaseDialog 

# UPDATED: Inherit from BaseDialog
class ClientDialog(BaseDialog):
    def __init__(self, parent=None, client_data=None):
        self.parent_window = parent
        self.client_data = client_data
        
        # UPDATED: Set title for BaseDialog
        title = "Edit Client" if client_data else "Add New Client"
        super().__init__(title, parent)
        
        self.setMinimumWidth(400)

        # UPDATED: Create a layout, but don't set it on `self`
        form_layout = QFormLayout()
        self.username = QLineEdit()
        self.company_name = QLineEdit()

        form_layout.addRow("Username:", self.username)
        form_layout.addRow("Company Name:", self.company_name)

        if client_data:
            self.username.setText(client_data.get("username", ""))
            self.username.setReadOnly(True)
            self.company_name.setText(client_data.get("company_name", ""))

        # UPDATED: Add the form layout to the BaseDialog's content area
        self.content_layout.addLayout(form_layout)

        # UPDATED: Configure the existing button_box from BaseDialog
        self.button_box.clear() # Remove default OK/Cancel
        self.button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.submit) # 'Save' maps to accepted
        self.button_box.rejected.connect(self.reject) # 'Cancel' maps to rejected

    def submit(self):
        payload = {
            "username": self.username.text(),
            "company_name": self.company_name.text()
        }

        if not payload["username"] or not payload["company_name"]:
            QMessageBox.warning(self, "Validation Error", "Username and Company Name are required.")
            return

        try:
            if self.client_data:
                url = f"{self.parent_window.API_BASE_URL}/clients/{self.client_data['client_id']}"
                response = requests.put(url, json=payload)
            else:
                url = f"{self.parent_window.API_BASE_URL}/clients"
                response = requests.post(url, json=payload)
            response.raise_for_status()
            self.accept()
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_msg = e.response.json().get('error', str(e))
                except:
                    pass # Keep the original error
            QMessageBox.critical(self, "API Error", f"Failed to save client: {error_msg}")