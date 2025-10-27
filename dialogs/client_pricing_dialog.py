# dialogs/client_pricing_dialog.py
# UPDATED: Inherits from BaseDialog for a professional look.
# UPDATED: Added QLineEdit import

import requests
from PyQt6.QtWidgets import (
    QApplication, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QDialogButtonBox, QMessageBox,
    QDoubleSpinBox, QLineEdit  # <-- ADDED QLineEdit HERE
)
# NEW: Import BaseDialog
from .base_dialog import BaseDialog

# UPDATED: Inherit from BaseDialog
class ClientPricingDialog(BaseDialog):
     def __init__(self, parent, client_id, client_name):
        self.client_id = client_id
        self.client_name = client_name
        self.parent_window = parent 
        self.original_custom_prices = {} 

        # UPDATED: Set title for BaseDialog
        title = f"Custom Pricing for {self.client_name}"
        super().__init__(title, parent)
        
        self.setMinimumSize(700, 500)

        # UPDATED: Add widgets directly to self.content_layout
        header_label = QLabel(f"Set Custom Prices for {self.client_name}", objectName="Header")
        self.content_layout.addWidget(header_label)

        instruction_label = QLabel("Enter a new price in the 'Custom Price' column to override the default. Leave blank or 0 to use the default price.")
        instruction_label.setWordWrap(True)
        self.content_layout.addWidget(instruction_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Product Name", "Default Price (₹)", "Custom Price (₹)"])
        
        # Assuming setup_table_style is in the parent (AdminDashboard)
        if hasattr(self.parent_window, 'setup_table_style'):
             self.parent_window.setup_table_style(self.table)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.content_layout.addWidget(self.table)

        # UPDATED: Configure the existing button_box from BaseDialog
        self.button_box.clear()
        self.button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close
        )
        self.button_box.accepted.connect(self.save_prices)
        self.button_box.rejected.connect(self.reject)

        self.load_data()

     def load_data(self):
        # Use parent_window to call fetch_generic_details
        all_products = self.parent_window.fetch_generic_details("/products")
        custom_prices_raw = self.parent_window.fetch_generic_details(f"/clients/{self.client_id}/pricing")

        if all_products is None or custom_prices_raw is None:
            QMessageBox.critical(self, "Error", "Could not load products or custom prices.")
            self.reject()
            return

        self.original_custom_prices = {item['product_id']: float(item['custom_price']) for item in custom_prices_raw}

        self.table.setRowCount(len(all_products))

        for row, prod in enumerate(all_products):
            product_id = prod['product_id']
            default_price = float(prod.get('price', 0.0))
            custom_price = self.original_custom_prices.get(product_id)

            self.table.setItem(row, 0, QTableWidgetItem(str(product_id)))
            self.table.setItem(row, 1, QTableWidgetItem(prod.get('name', 'N/A')))
            self.table.setItem(row, 2, QTableWidgetItem(f"{default_price:.2f}"))

            price_input = QDoubleSpinBox()
            price_input.setRange(0, 1_000_000)
            price_input.setDecimals(2)
            price_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            price_input.setToolTip("Enter custom price or leave blank/0 to use default")

            if custom_price is not None:
                price_input.setValue(custom_price)
            else:
                price_input.setSpecialValueText(" ") # Use space for placeholder
                price_input.setValue(0) # Set value to 0 for logic

            price_input.setProperty("product_id", product_id)
            self.table.setCellWidget(row, 3, price_input)
            
            # Fix for spinbox not showing placeholder on load
            if custom_price is None:
                # This line now works because QLineEdit is imported
                price_input.findChild(QLineEdit).clear() 


     def save_prices(self):
        prices_to_save = [] 
        
        for row in range(self.table.rowCount()):
            price_input_widget = self.table.cellWidget(row, 3)
            if isinstance(price_input_widget, QDoubleSpinBox):
                product_id = price_input_widget.property("product_id")
                current_value = price_input_widget.value()
                
                # Check if the value is non-zero (i.e., it's a custom price)
                is_new_custom_price = current_value > 0
                # Check if it *was* a custom price
                original_value = self.original_custom_prices.get(product_id)
                
                # Scenarios to save:
                # 1. New custom price: (original was None, current > 0)
                # 2. Changed custom price: (original was not None, current > 0, current != original)
                # 3. Removed custom price: (original was not None, current == 0)
                
                if (is_new_custom_price and current_value != original_value) or \
                   (not is_new_custom_price and original_value is not None):
                    # If current_value is 0, we send 'None' to delete the custom price
                    price_to_send = current_value if is_new_custom_price else None
                    prices_to_save.append({"product_id": product_id, "custom_price": price_to_send})


        if not prices_to_save:
             QMessageBox.information(self, "No Changes", "No custom prices were changed.")
             return

        progress_msg = QMessageBox(self)
        progress_msg.setWindowTitle("Saving Prices...")
        progress_msg.setText(f"Attempting to save {len(prices_to_save)} price changes...")
        progress_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress_msg.show()
        QApplication.processEvents()

        saved_count = 0
        error_count = 0
        
        for price_data in prices_to_save:
            try:
                url = f"{self.parent_window.API_BASE_URL}/clients/{self.client_id}/pricing"
                # Use POST to add/update, DELETE to remove
                if price_data['custom_price'] is not None:
                    response = requests.post(url, json=price_data) 
                else:
                    # Send product_id in the body for the DELETE request
                    delete_payload = {"product_id": price_data['product_id']}
                    response = requests.delete(url, json=delete_payload)
                
                response.raise_for_status()
                saved_count += 1
            except requests.exceptions.RequestException as e:
                error_count += 1
                error_msg = str(e)
                if hasattr(e, 'response') and e.response:
                    try:
                        error_msg = e.response.json().get('error', str(e))
                    except:
                        pass # Keep original error
                print(f"Error saving price for product {price_data['product_id']}: {error_msg}")
            
            progress_msg.setText(f"Saving... {saved_count+error_count}/{len(prices_to_save)}")
            QApplication.processEvents()

        progress_msg.close()

        summary_message = f"Successfully saved {saved_count} price changes.\n"
        if error_count > 0:
            summary_message += f"{error_count} operations failed. Check terminal for details."
            QMessageBox.warning(self, "Save Complete (with errors)", summary_message)
        else:
             QMessageBox.information(self, "Success", summary_message)

        # Reload data to reflect changes
        self.load_data()