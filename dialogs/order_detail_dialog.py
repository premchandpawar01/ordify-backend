# dialogs/order_detail_dialog.py
# NEW FILE: Displays order details, inheriting from BaseDialog.

from PyQt6.QtWidgets import (
    QFormLayout, QLabel, QDialogButtonBox, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt

# Import the BaseDialog
from .base_dialog import BaseDialog

class OrderDetailDialog(BaseDialog):
    """
    A dialog to display order details, inheriting from BaseDialog.
    """
    def __init__(self, order_data, parent=None):
        self.order_data = order_data
        title = f"Details for Order #{order_data.get('order_id', 'N/A')}"

        # Call BaseDialog's init
        super().__init__(title, parent)

        self.setMinimumWidth(400)

        # --- Details Area ---
        details_frame = QFrame()
        details_frame.setObjectName("DetailFormFrame") # Reuse style
        form_layout = QFormLayout(details_frame)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(15, 15, 15, 15)

        # Order ID
        key1 = QLabel("Order ID:")
        key1.setObjectName("DetailKey")
        val1 = QLabel(str(order_data.get('order_id', 'N/A')))
        val1.setObjectName("DetailValue")
        form_layout.addRow(key1, val1)

        # Client
        key2 = QLabel("Client:")
        key2.setObjectName("DetailKey")
        val2 = QLabel(order_data.get('client_name', 'N/A'))
        val2.setObjectName("DetailValue")
        form_layout.addRow(key2, val2)

        # Status
        key3 = QLabel("Status:")
        key3.setObjectName("DetailKey")
        val3 = QLabel(order_data.get('status', 'N/A'))
        val3.setObjectName("DetailValue")
        # Optional: Add color based on status if needed later
        form_layout.addRow(key3, val3)

        # Total Amount
        key4 = QLabel("Total:")
        key4.setObjectName("DetailKey")
        total_val = order_data.get('total_amount', 0.0)
        # Ensure total_val is float before formatting
        try:
             total_float = float(total_val)
        except (ValueError, TypeError):
             total_float = 0.0
        val4 = QLabel(f"₹{total_float:.2f}")
        val4.setObjectName("DetailValue")
        form_layout.addRow(key4, val4)

        # Add the details frame to the main content
        self.content_layout.addWidget(details_frame)

        # --- Items List ---
        items_header = QLabel("Items:")
        items_header.setObjectName("DetailKey") # Reuse style for header
        items_header.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        self.content_layout.addWidget(items_header)

        items_text = ""
        items_list = order_data.get('items', [])
        if items_list:
            for item in items_list:
                try:
                    price_float = float(item.get('price_per_unit', 0.0))
                except (ValueError, TypeError):
                    price_float = 0.0
                items_text += f"• {item.get('quantity', 0)} x {item.get('product_name', 'N/A')} @ ₹{price_float:.2f}\n"
        else:
            items_text = "No items found for this order."

        # Use a read-only QTextEdit for potentially long item lists
        items_display = QTextEdit()
        items_display.setReadOnly(True)
        items_display.setPlainText(items_text)
        items_display.setObjectName("DetailValue") # Reuse style
        items_display.setFixedHeight(100) # Limit height, will scroll if needed
        items_display.setStyleSheet("background-color: #FFFFFF; border: 1px solid #DCDCDC; border-radius: 4px; padding: 5px;") # Card-like style
        self.content_layout.addWidget(items_display)

        self.content_layout.addStretch() # Pushes content up

        # --- Configure Button Box ---
        self.button_box.clear() # Remove default OK/Cancel
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Close)
        # 'Close' button automatically connects to self.reject