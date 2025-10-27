# dialogs/product_dialog.py
# UPDATED: Inherits from BaseDialog for a professional look.

import sys
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QFormLayout, QLineEdit,
    QDoubleSpinBox, QSpinBox, QTextEdit, QMessageBox,
    QPushButton, QLabel, QFileDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt

# NEW: Import BaseDialog
from .base_dialog import BaseDialog

# UPDATED: Inherit from BaseDialog
class ProductDialog(BaseDialog):
    def __init__(self, parent, product_data=None):
        self.parent = parent # This is the main AdminDashboard window
        self.product_data = product_data
        self.image_file_path = None # Store the path to the new image file

        # UPDATED: Set title for BaseDialog
        title = "Edit Product" if product_data else "Add New Product"
        super().__init__(title, parent)
        
        self.setMinimumWidth(450)

        # --- Create Widgets ---
        self.name_input = QLineEdit()
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.0, 999999.99)
        self.price_input.setPrefix("₹")

        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 999999)

        self.threshold_input = QSpinBox()
        self.threshold_input.setRange(0, 999999)

        self.desc_input = QTextEdit()
        self.desc_input.setFixedHeight(100)

        # --- Image Upload Widgets ---
        self.image_browse_btn = QPushButton("Browse...")
        self.image_browse_btn.clicked.connect(self.open_file_dialog)
        self.image_path_label = QLabel("No file selected.")
        self.image_path_label.setStyleSheet("font-style: italic; color: #555;")

        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_browse_btn)
        image_layout.addWidget(self.image_path_label, 1) # Give label extra space

        # --- Layout (No main layout needed) ---
        self.form_layout = QFormLayout()
        self.form_layout.addRow("Name:", self.name_input)
        self.form_layout.addRow("Price:", self.price_input)
        self.form_layout.addRow("Stock Quantity:", self.stock_input)
        self.form_layout.addRow("Low Stock Threshold:", self.threshold_input)
        self.form_layout.addRow("Description:", self.desc_input)
        self.form_layout.addRow("Image:", image_layout)

        # UPDATED: Add the form layout to the BaseDialog's content area
        self.content_layout.addLayout(self.form_layout)

        # UPDATED: Connect the existing button_box from BaseDialog
        # BaseDialog defaults to Ok | Cancel, which is what we want.
        # We just need to connect 'accepted' (OK) to our submit function.
        self.button_box.accepted.disconnect() # Disconnect default self.accept
        self.button_box.accepted.connect(self.submit_data)
        self.button_box.rejected.connect(self.reject)

        # --- Populate data if editing ---
        if self.product_data:
            # self.setWindowTitle("Edit Product") # No longer needed
            self.name_input.setText(self.product_data.get('name', ''))
            self.price_input.setValue(self.product_data.get('price', 0.0))
            self.stock_input.setValue(self.product_data.get('stock_quantity', 0))
            self.threshold_input.setValue(self.product_data.get('low_stock_threshold', 10))
            self.desc_input.setPlainText(self.product_data.get('description', ''))
            
            img_url = self.product_data.get('image_url')
            if img_url:
                filename = img_url.split('/')[-1]
                if "placeholder" not in filename:
                    self.image_path_label.setText(filename)
                    self.image_path_label.setStyleSheet("font-style: normal; color: #333;")


    def open_file_dialog(self):
        """Opens a file dialog to select an image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Product Image",
            "", # Start directory
            "Image Files (*.png *.jpg *.jpeg *.gif)"
        )
        if file_path:
            self.image_file_path = file_path
            self.image_path_label.setText(os.path.basename(file_path))
            self.image_path_label.setStyleSheet("font-style: normal; color: #333;")

    def submit_data(self):
        """
        Submits product data (including image) to the API
        using multipart/form-data.
        """
        url = f"{self.parent.API_BASE_URL}/products"
        
        # 1. Prepare the text data
        data = {
            'name': self.name_input.text(),
            'price': self.price_input.value(),
            'stock_quantity': self.stock_input.value(),
            'low_stock_threshold': self.threshold_input.value(),
            'description': self.desc_input.toPlainText()
        }

        # 2. Prepare the file (if one was selected)
        files = {}
        file_handle = None
        if self.image_file_path:
            try:
                file_handle = open(self.image_file_path, 'rb')
                files['image_file'] = (
                    os.path.basename(self.image_file_path),
                    file_handle
                )
            except Exception as e:
                QMessageBox.warning(self, "File Error", f"Could not read image file: {e}")
                if file_handle:
                    file_handle.close()
                return

        try:
            if self.product_data: 
                # --- This is an UPDATE (PUT) ---
                endpoint = f"{url}/{self.product_data['product_id']}"
                
                if not self.image_file_path and self.product_data.get('image_url'):
                    filename = self.product_data['image_url'].split('/')[-1]
                    data['image_url'] = filename

                response = requests.put(endpoint, data=data, files=files, timeout=10)
            
            else: 
                # --- This is a CREATE (POST) ---
                response = requests.post(url, data=data, files=files, timeout=10)
            
            response.raise_for_status() # Raise HTTPError for bad responses
            self.accept() # Close the dialog successfully

        except requests.exceptions.RequestException as e:
            try:
                error = e.response.json().get('error', str(e))
            except:
                error = str(e)
            QMessageBox.critical(self, "API Error", f"Failed to save product: {error}")
        
        finally:
            if file_handle:
                file_handle.close()