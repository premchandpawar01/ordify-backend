# pages/clients_page.py
# (Updated with icon-based "Add New" button and objectName for styling)
# (UPDATED: Added search bar and numeric sorting)
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

class ClientsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)

        # --- 1. Header & Controls Layout ---
        header_layout = QHBoxLayout()
        self.header = QLabel("Manage Clients")
        self.header.setObjectName("Header")
        header_layout.addWidget(self.header)
        header_layout.addStretch(1) # Add stretch to push controls right

        # --- NEW: Search Bar ---
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by Client ID, Name, or Username...")
        self.search_bar.setObjectName("SearchBar") # Add object name for styling
        self.search_bar.setMinimumWidth(300)
        self.search_bar.textChanged.connect(self.filter_table)
        header_layout.addWidget(self.search_bar)
        
        # Spacer
        header_layout.addSpacing(20)

        # --- Add New Client Button (UPDATED to icon) ---
        self.add_client_btn = QPushButton()
        self.add_client_btn.setIcon(QIcon(self.main_window.ICON_ADD)) # Use new icon
        self.add_client_btn.setIconSize(QSize(24, 24))
        self.add_client_btn.setToolTip("Add New Client")
        self.add_client_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_client_btn.setFixedSize(QSize(40, 40)) # Match other buttons
        self.add_client_btn.setObjectName("AddButton") # Add object name for styling
        self.add_client_btn.clicked.connect(self.main_window.open_client_dialog)
        header_layout.addWidget(self.add_client_btn)

        # --- Export Buttons ---
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

        # --- 2. Table ---
        self.table = QTableWidget()
        self.main_window.setup_table_style(self.table)
        self.layout.addWidget(self.table, 1) # Add stretch factor

    def filter_table(self, text):
        """Hides rows that do not match the search text."""
        search_text = text.lower()
        for row in range(self.table.rowCount()):
            # Check columns 0 (ID), 1 (Name), and 2 (Username)
            id_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            user_item = self.table.item(row, 2)

            # Get text, default to empty string if item is None
            id_text = id_item.text().lower() if id_item else ""
            name_text = name_item.text().lower() if name_item else ""
            user_text = user_item.text().lower() if user_item else ""

            # Show row if any column matches
            if (search_text in id_text or 
                search_text in name_text or 
                search_text in user_text):
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def populate_table(self, clients_data):
        # Disable sorting while populating
        self.table.setSortingEnabled(False)
        
        self.table.clearContents()
        self.table.setRowCount(len(clients_data))

        headers = ["Client ID", "Company Name", "Username", "Actions"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for row, client in enumerate(clients_data):
            client_id = client.get('client_id')
            
            # --- UPDATED: Use NumericTableWidgetItem for sorting ---
            self.table.setItem(row, 0, NumericTableWidgetItem(client_id))
            
            self.table.setItem(row, 1, QTableWidgetItem(client.get('company_name')))
            self.table.setItem(row, 2, QTableWidgetItem(client.get('username')))

            # --- Actions ---
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)

            edit_btn = QPushButton(QIcon(self.main_window.ICON_EDIT), "")
            edit_btn.setToolTip("Edit Client Details")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda _, cid=client_id: self.main_window.edit_client_by_id(cid))

            pricing_btn = QPushButton(QIcon(self.main_window.ICON_PRICING), "")
            pricing_btn.setToolTip("Manage Client-Specific Pricing")
            pricing_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pricing_btn.clicked.connect(lambda _, cid=client_id: self.main_window.open_client_pricing_window(cid))

            delete_btn = QPushButton(QIcon(self.main_window.ICON_DELETE), "")
            delete_btn.setToolTip("Delete Client")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda _, cid=client_id: self.main_window.delete_client_by_id(cid))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(pricing_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 3, actions_widget)

        # --- UPDATED: Set explicit column resize modes ---
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Client ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Company Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Username
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Actions
        
        # Re-enable sorting
        self.table.setSortingEnabled(True)
        # Set initial sort column (e.g., Client ID, Ascending)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)