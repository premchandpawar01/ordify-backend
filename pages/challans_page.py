# pages/challans_page.py
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

class ChallansPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)

        # --- 1. Header ---
        self.header = QLabel("Manage Challans")
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
        self.search_bar.setPlaceholderText("Search by Challan ID, Order ID, or Client...")
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
        self.filter_button.setObjectName("FilterButton") # Style the button
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
            # Check columns 0 (Challan ID), 1 (Order ID), and 2 (Client)
            challan_id_item = self.table.item(row, 0)
            order_id_item = self.table.item(row, 1)
            client_item = self.table.item(row, 2)

            challan_id_text = challan_id_item.text().lower() if challan_id_item else ""
            order_id_text = order_id_item.text().lower() if order_id_item else ""
            client_text = client_item.text().lower() if client_item else ""

            # Show row if any column matches
            if (search_text in challan_id_text or 
                search_text in order_id_text or 
                search_text in client_text):
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def populate_table(self, challans_data):
        # Disable sorting while populating
        self.table.setSortingEnabled(False)
        
        self.table.clearContents()
        self.table.setRowCount(len(challans_data))

        headers = ["Challan ID", "Order ID", "Client", "Challan Date", "Total", "Status", "Actions"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for row, challan in enumerate(challans_data):
            challan_id = challan.get('challan_id')
            order_id = challan.get('order_id') # Can be None
            challan_date_iso = challan.get('challan_date')
            total_amount = challan.get('total_amount', 0)
            
            # --- UPDATED: Use custom widgets for sorting ---
            self.table.setItem(row, 0, NumericTableWidgetItem(challan_id))
            
            # Handle potential None for Order ID
            if order_id:
                self.table.setItem(row, 1, NumericTableWidgetItem(order_id))
            else:
                self.table.setItem(row, 1, QTableWidgetItem("N/A"))
                
            self.table.setItem(row, 2, QTableWidgetItem(challan.get('client_name')))
            self.table.setItem(row, 3, DateTimeTableWidgetItem(challan_date_iso))
            self.table.setItem(row, 4, NumericTableWidgetItem(total_amount, is_currency=True))
            
            self.table.setItem(row, 5, QTableWidgetItem(challan.get('status')))

            # --- Actions ---
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)

            pdf_btn = QPushButton(QIcon(self.main_window.ICON_PDF), "")
            pdf_btn.setToolTip("Download Challan PDF")
            pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pdf_btn.clicked.connect(lambda _, cid=challan_id: self.main_window.download_challan_pdf(cid))

            reset_btn = QPushButton(QIcon(self.main_window.ICON_RESET), "")
            reset_btn.setToolTip("Reset Billing Status (Remove from Bill)")
            reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            reset_btn.clicked.connect(lambda _, cid=challan_id: self.main_window.reset_challan_billing(cid))

            delete_btn = QPushButton(QIcon(self.main_window.ICON_DELETE), "")
            delete_btn.setToolTip("Delete Challan")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda _, cid=challan_id: self.main_window.delete_challan_by_id(cid))

            # Disable reset button if challan is not linked to a bill (using monthly_bill_id now)
            if challan.get('monthly_bill_id') is None:
                 reset_btn.setDisabled(True)
                 reset_btn.setToolTip("Challan is not part of a bill")

            actions_layout.addWidget(pdf_btn)
            actions_layout.addWidget(reset_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 6, actions_widget)

        # --- UPDATED: Set explicit column resize modes ---
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Challan ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Order ID
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Client
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Challan Date
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Total
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Status
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Actions
        
        # Re-enable sorting
        self.table.setSortingEnabled(True)
        # Set initial sort column (e.g., Challan Date, Descending)
        self.table.sortByColumn(3, Qt.SortOrder.DescendingOrder)