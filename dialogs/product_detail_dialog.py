# dialogs/product_detail_dialog.py
# UPDATED: Wrapped details in a styled QFrame for better looks.
# UPDATED: Added objectNames to key labels for styling.

import requests
import threading
from PyQt6.QtWidgets import (
    QVBoxLayout, QFormLayout, QLabel, QProgressBar, QDialogButtonBox, QFrame # Added QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap

# Import the new BaseDialog
from .base_dialog import BaseDialog

class ProductDetailDialog(BaseDialog):
    """
    A dialog to display product details, inheriting from BaseDialog.
    The image is downloaded in a separate thread.
    """
    # Signal to update image when download is complete
    image_downloaded = pyqtSignal(QPixmap)

    def __init__(self, product_data, parent=None):
        self.product_data = product_data
        title = f"Details for {product_data.get('name', 'N/A')}"
        
        # Call BaseDialog's init
        super().__init__(title, parent)
        
        self.setMinimumSize(450, 500)

        # --- Image Area ---
        self.image_label = QLabel("Downloading image...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(250)
        self.image_label.setStyleSheet("background-color: #EEE; border: 1px solid #CCC; border-radius: 5px;")
        self.image_label.setScaledContents(True) 
        self.image_label.setWordWrap(True) # For error messages
        
        # Add to content_layout from BaseDialog
        self.content_layout.addWidget(self.image_label)
        
        # --- Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.content_layout.addWidget(self.progress_bar)

        # --- Details Area ---
        # NEW: Wrap form layout in a frame
        details_frame = QFrame()
        details_frame.setObjectName("DetailFormFrame")
        form_layout = QFormLayout(details_frame) # Set layout on the frame
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(15, 15, 15, 15) # Add padding
        
        # Use object names for styling
        
        # Key Label 1
        key1 = QLabel("Product ID:")
        key1.setObjectName("DetailKey")
        # Value Label 1
        id_val = QLabel(str(product_data.get('product_id')))
        id_val.setObjectName("DetailValue")
        form_layout.addRow(key1, id_val)

        # Key Label 2
        key2 = QLabel("Name:")
        key2.setObjectName("DetailKey")
        # Value Label 2
        name_val = QLabel(product_data.get('name'))
        name_val.setObjectName("DetailValue")
        form_layout.addRow(key2, name_val)

        # Key Label 3
        key3 = QLabel("Price:")
        key3.setObjectName("DetailKey")
        # Value Label 3
        price_val = QLabel(f"₹{product_data.get('price', 0.0):.2f}")
        price_val.setObjectName("DetailValue")
        form_layout.addRow(key3, price_val)

        # Key Label 4
        key4 = QLabel("Stock:")
        key4.setObjectName("DetailKey")
        # Value Label 4
        stock_val = QLabel(f"{product_data.get('stock_quantity')} (Threshold: {product_data.get('low_stock_threshold')})")
        stock_val.setObjectName("DetailValue")
        form_layout.addRow(key4, stock_val)
        
        desc_text = product_data.get('description')
        if not desc_text:
            desc_text = "N/A" # Fill in empty description
            
        # Key Label 5
        key5 = QLabel("Description:")
        key5.setObjectName("DetailKey")
        key5.setAlignment(Qt.AlignmentFlag.AlignTop) # Align key to top
        # Value Label 5
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setObjectName("DetailValue")
        form_layout.addRow(key5, desc_label)
        
        # Add to content_layout from BaseDialog
        self.content_layout.addWidget(details_frame) # Add the frame, not the layout
        self.content_layout.addStretch() # Pushes content up

        # --- Configure Button Box ---
        # Use the button_box from BaseDialog
        self.button_box.clear() # Remove default OK/Cancel
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Close)
        # 'Close' button automatically connects to self.reject

        # --- Connect signal and start download ---
        self.image_downloaded.connect(self.set_image)
        self.start_image_download()

    def start_image_download(self):
        image_url = self.product_data.get('image_url')
        if not image_url:
            self.image_label.setText("No image provided")
            self.progress_bar.hide()
            return
        
        # Run the download in a separate thread to avoid freezing the UI
        threading.Thread(target=self.download_image, args=(image_url,), daemon=True).start()

    def download_image(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            
            # Emit the signal with the downloaded pixmap
            self.image_downloaded.emit(pixmap)
        except Exception as e:
            print(f"!!! Image Download Error: {e}")
            # Emit an empty pixmap on failure
            self.image_downloaded.emit(QPixmap())

    def set_image(self, pixmap):
        self.progress_bar.hide() # Hide progress bar
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Failed to load image")