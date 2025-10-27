# pages/products_page.py
# (Updated with icon-based "Add New" button and objectName for styling)
# (UPDATED: Added numeric sorting for ID, Price, and Stock)
# (UPDATED: Fixed compressed column widths)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QPushButton, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

# --- NEW: Import custom widgets ---
from .custom_widgets import NumericTableWidgetItem

class ProductsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)

        # --- 1. Header ---
        header_layout = QHBoxLayout()
        self.header = QLabel("Manage Products")
        self.header.setObjectName("Header")
        header_layout.addWidget(self.header)
        
        header_layout.addStretch() # Add stretch

        # --- 2. Controls Layout (New) ---

        # --- Search Bar ---
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by product name...")
        self.search_bar.setObjectName("SearchBar") # Add object name for styling
        self.search_bar.setMinimumWidth(300)
        self.search_bar.textChanged.connect(self.filter_table)
        header_layout.addWidget(self.search_bar)
        
        # Spacer
        header_layout.addSpacing(20)


        # --- Add New Product Button (UPDATED to icon) ---
        self.add_product_btn = QPushButton()
        self.add_product_btn.setIcon(QIcon(self.main_window.ICON_ADD)) # Use new icon
        self.add_product_btn.setIconSize(QSize(24, 24))
        self.add_product_btn.setToolTip("Add New Product")
        self.add_product_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_product_btn.setFixedSize(QSize(40, 40)) # Match other buttons
        self.add_product_btn.setObjectName("AddButton") # Add object name for styling
        self.add_product_btn.clicked.connect(self.main_window.open_product_dialog)
        header_layout.addWidget(self.add_product_btn)

        # Export Buttons
        self.export_csv_button = QPushButton()
        self.export_csv_button.setIcon(QIcon(self.main_window.ICON_CSV))
        self.export_csv_button.setIconSize(QSize(24, 24))
        self.export_csv_button.setToolTip("Export to CSV")
        self.export_csv_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_csv_button.setFixedSize(QSize(40, 40))
        header_layout.addWidget(self.export_csv_button)

        self.export_excel_button = QPushButton()
        self.export_excel_button.setIcon(QIcon(self.main_window.ICON_EXCEL))
        self.export_excel_button.setIconSize(QSize(24, 24))
        self.export_excel_button.setToolTip("Export to Excel")
        self.export_excel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_excel_button.setFixedSize(QSize(40, 40))
        header_layout.addWidget(self.export_excel_button)

        self.layout.addLayout(header_layout)
        # --- End New Controls ---

        # --- 3. Table ---
        self.table = QTableWidget()
        self.main_window.setup_table_style(self.table)
        self.layout.addWidget(self.table, 1) # Add stretch factor

    def filter_table(self, text):
        """Hides rows that do not match the search text."""
        search_text = text.lower()
        for row in range(self.table.rowCount()):
            # Column 1 is the Product Name
            item = self.table.item(row, 1)
            if item:
                item_text = item.text().lower()
                # Hide row if text doesn't match
                self.table.setRowHidden(row, search_text not in item_text)
            else:
                # Hide rows that somehow have no name item
                self.table.setRowHidden(row, True)

    def populate_table(self, products_data):
        # Disable sorting while populating
        self.table.setSortingEnabled(False)
        
        self.table.clearContents()
        self.table.setRowCount(len(products_data))

        headers = ["Product ID", "Name", "Price", "Stock", "Actions"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for row, product in enumerate(products_data):
            product_id = product.get('product_id')
            
            # --- UPDATED: Use NumericTableWidget for sorting ---
            self.table.setItem(row, 0, NumericTableWidgetItem(product_id))
            self.table.setItem(row, 1, QTableWidgetItem(product.get('name')))
            self.table.setItem(row, 2, NumericTableWidgetItem(product.get('price', 0), is_currency=True))
            self.table.setItem(row, 3, NumericTableWidgetItem(product.get('stock_quantity')))

            # --- Actions ---
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)

            view_btn = QPushButton(QIcon(self.main_window.ICON_VIEW), "")
            view_btn.setToolTip("View Product Details")
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(lambda _, pid=product_id: self.main_window.view_product_details_by_id(pid))

            edit_btn = QPushButton(QIcon(self.main_window.ICON_EDIT), "")
            edit_btn.setToolTip("Edit Product")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda _, pid=product_id: self.main_window.edit_product_by_id(pid))

            delete_btn = QPushButton(QIcon(self.main_window.ICON_DELETE), "")
            delete_btn.setToolTip("Delete Product")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda _, pid=product_id: self.main_window.delete_product_by_id(pid))

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 4, actions_widget)

        # --- UPDATED: Set explicit column resize modes ---
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Product ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Price
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Stock
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Actions
        
        # Re-enable sorting
        self.table.setSortingEnabled(True)
        # Set initial sort column (e.g., Product ID, Ascending)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)