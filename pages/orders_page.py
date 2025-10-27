# pages/orders_page.py
# (UPDATED: Replaced filter bar with popup dialog buttons)
# (UPDATED: Added search bar and correct sorting for date/numeric columns)
# (UPDATED: Fixed compressed column widths)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QPushButton, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QSpacerItem, QSizePolicy, QLineEdit
)
from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QIcon
from datetime import datetime # Import datetime

# --- NEW: Import custom widgets ---
from .custom_widgets import NumericTableWidgetItem, DateTimeTableWidgetItem

class OrdersPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)

        # --- 1. Header ---
        self.header = QLabel("Manage Orders")
        self.header.setObjectName("Header")
        self.layout.addWidget(self.header)

        # --- 2. Filter and Controls Layout (REBUILT) ---
        controls_layout = QHBoxLayout()

        # NEW: Filter Status Label
        self.filter_label = QLabel("Filter: All Time")
        self.filter_label.setStyleSheet("font-weight: bold; color: #555;")
        controls_layout.addWidget(self.filter_label)
        controls_layout.addStretch(1) # Add stretch

        # --- NEW: Search Bar ---
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by Order ID, Client, or Challan ID...")
        self.search_bar.setObjectName("SearchBar") # Add object name for styling
        self.search_bar.setMinimumWidth(300)
        self.search_bar.textChanged.connect(self.filter_table)
        controls_layout.addWidget(self.search_bar)
        
        # Spacer
        controls_layout.addSpacing(20)

        # NEW: Filter Popup Button
        self.filter_button = QPushButton()
        self.filter_button.setIcon(QIcon(self.main_window.ICON_FUNNEL))
        self.filter_button.setIconSize(QSize(18, 18))
        self.filter_button.setToolTip("Apply Filter")
        self.filter_button.setCursor(Qt.CursorShape.PointingHandCursor)
        # Set new object name for styling
        self.filter_button.setObjectName("FilterButton")
        controls_layout.addWidget(self.filter_button)

        # Reset Button (unchanged, but moved)
        self.reset_button = QPushButton()
        self.reset_button.setIcon(QIcon(self.main_window.ICON_RESET))
        self.reset_button.setIconSize(QSize(18, 18))
        self.reset_button.setToolTip("Reset Filter")
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.setObjectName("FilterButton") # Use same style
        controls_layout.addWidget(self.reset_button)

        # Spacer
        controls_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # --- Export Buttons ---
        self.export_csv_button = QPushButton()
        self.export_csv_button.setIcon(QIcon(self.main_window.ICON_CSV))
        self.export_csv_button.setIconSize(QSize(24, 24))
        self.export_csv_button.setToolTip("Export to CSV")
        self.export_csv_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_csv_button.setFixedSize(QSize(40, 40))
        controls_layout.addWidget(self.export_csv_button)

        self.export_excel_button = QPushButton()
        self.export_excel_button.setIcon(QIcon(self.main_window.ICON_EXCEL))
        self.export_excel_button.setIconSize(QSize(24, 24))
        self.export_excel_button.setToolTip("Export to Excel")
        self.export_excel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_excel_button.setFixedSize(QSize(40, 40))
        controls_layout.addWidget(self.export_excel_button)

        self.layout.addLayout(controls_layout)

        # --- 3. Table ---
        self.table = QTableWidget()
        self.main_window.setup_table_style(self.table)
        self.layout.addWidget(self.table, 1)

        # --- 4. Pagination Controls ---
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_button = QPushButton("Next")
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)

        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.next_button)

        self.layout.addLayout(pagination_layout)

    def filter_table(self, text):
        """Hides rows that do not match the search text."""
        search_text = text.lower()
        for row in range(self.table.rowCount()):
            # Check columns 0 (Order ID), 1 (Client), and 5 (Challan ID)
            id_item = self.table.item(row, 0)
            client_item = self.table.item(row, 1)
            challan_item = self.table.item(row, 5)

            id_text = id_item.text().lower() if id_item else ""
            client_text = client_item.text().lower() if client_item else ""
            challan_text = challan_item.text().lower() if challan_item else ""

            # Show row if any column matches
            if (search_text in id_text or 
                search_text in client_text or 
                search_text in challan_text):
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def populate_table(self, orders_data):
        # Disable sorting while populating
        self.table.setSortingEnabled(False)
        
        self.table.clearContents()
        self.table.setRowCount(len(orders_data))

        headers = ["Order ID", "Client", "Order Date", "Total", "Status", "Challan ID", "Actions"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for row, order in enumerate(orders_data):
            order_id = order.get('order_id')
            order_date_iso = order.get('order_date') # Get ISO string
            total_amount = order.get('total_amount', 0)
            
            # --- UPDATED: Use custom widgets for sorting ---
            self.table.setItem(row, 0, NumericTableWidgetItem(order_id))
            self.table.setItem(row, 1, QTableWidgetItem(order.get('client_name')))
            self.table.setItem(row, 2, DateTimeTableWidgetItem(order_date_iso))
            self.table.setItem(row, 3, NumericTableWidgetItem(total_amount, is_currency=True))
            
            self.table.setItem(row, 4, QTableWidgetItem(order.get('status')))
            self.table.setItem(row, 5, QTableWidgetItem(str(order.get('associated_challan_id', 'N/A'))))

            # --- Actions ---
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)

            view_btn = QPushButton(QIcon(self.main_window.ICON_VIEW), "")
            view_btn.setToolTip("View Order Details")
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(lambda _, oid=order_id: self.main_window.view_order_details(oid))

            challan_btn = QPushButton(QIcon(self.main_window.ICON_CHALLANS), "")
            challan_btn.setToolTip("Create Challan")
            challan_btn.setCursor(Qt.CursorShape.PointingHandCursor)

            if order.get('associated_challan_id'):
                challan_btn.setDisabled(True)
                challan_btn.setToolTip("Challan already created")
            else:
                challan_btn.clicked.connect(lambda _, oid=order_id: self.main_window.create_challan_for_order(oid))

            delete_btn = QPushButton(QIcon(self.main_window.ICON_DELETE), "")
            delete_btn.setToolTip("Delete Order")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda _, oid=order_id: self.main_window.delete_order_by_id(oid))

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(challan_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 6, actions_widget)

        # --- UPDATED: Set explicit column resize modes ---
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Order ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Client
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Order Date
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Total
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Challan ID
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Actions
        
        # Re-enable sorting
        self.table.setSortingEnabled(True)
        # Set initial sort column (e.g., Order Date, Descending)
        self.table.sortByColumn(2, Qt.SortOrder.DescendingOrder)