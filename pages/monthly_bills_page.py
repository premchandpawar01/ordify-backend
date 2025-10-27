# pages/monthly_bills_page.py
# UPDATED: Changed object name of generate_bill_button
# UPDATED: Set maxVisibleItems on bill_month_combo
# UPDATED: Added missing QTableWidgetItem import
# UPDATED: Corrected key name to 'billing_month' to match API alias
# UPDATED: Corrected key name to 'payment_date' to match DB schema
# UPDATED: Used QGridLayout for bill generator widget alignment
# UPDATED: Applied explicit Fixed resize mode and width for Bill ID column

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QLabel, QFrame, QComboBox, QSpinBox, QPushButton,
    QLineEdit, QTableWidgetItem, QHeaderView, QGridLayout # Added QGridLayout & QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon, QColor

class MonthlyBillsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # --- Main Layout ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Use main content frame padding

        # --- Header ---
        header_label = QLabel("Manage Monthly Bills", objectName="Header")
        layout.addWidget(header_label)

        # --- Bill Generator Widget ---
        bill_generator_frame = self.create_bill_generator_widget()
        layout.addWidget(bill_generator_frame)

        # --- Filter/Search Bar ---
        filter_search_layout = QHBoxLayout()

        # Filter: Label
        self.filter_label = QLabel("Filter: All Time")
        self.filter_label.setObjectName("FilterLabel")
        filter_search_layout.addWidget(self.filter_label)

        # Filter: Button
        self.filter_button = QPushButton(QIcon(self.main_window.ICON_FUNNEL), "")
        self.filter_button.setObjectName("FilterButton")
        self.filter_button.setToolTip("Select Date Filter")
        filter_search_layout.addWidget(self.filter_button)

        # Reset: Button
        self.reset_button = QPushButton(QIcon(self.main_window.ICON_RESET), "")
        self.reset_button.setObjectName("FilterButton")
        self.reset_button.setToolTip("Reset Filter")
        filter_search_layout.addWidget(self.reset_button)

        filter_search_layout.addStretch(1) # Spacer

        # Search: Bar
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setPlaceholderText("Search by Bill ID or Client...")
        self.search_bar.textChanged.connect(self.filter_table)
        filter_search_layout.addWidget(self.search_bar)

        # Export: CSV
        self.export_csv_button = QPushButton(QIcon(self.main_window.ICON_CSV), "")
        self.export_csv_button.setToolTip("Export to CSV")
        self.export_csv_button.setIconSize(QIcon(self.main_window.ICON_CSV).pixmap(18, 18).size())
        filter_search_layout.addWidget(self.export_csv_button)

        # Export: Excel
        self.export_excel_button = QPushButton(QIcon(self.main_window.ICON_EXCEL), "")
        self.export_excel_button.setToolTip("Export to Excel")
        self.export_excel_button.setIconSize(QIcon(self.main_window.ICON_EXCEL).pixmap(18, 18).size())
        filter_search_layout.addWidget(self.export_excel_button)

        layout.addLayout(filter_search_layout)

        # --- Table ---
        self.table = QTableWidget()
        self.main_window.setup_table_style(self.table)
        layout.addWidget(self.table, 1)

        # --- Pagination ---
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.page_label = QLabel("Page 1 of 1")
        self.next_button = QPushButton("Next")

        pagination_layout.addStretch()
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addStretch()

        layout.addLayout(pagination_layout)

    def create_bill_generator_widget(self):
        """Creates the 'Generate Bill' widget using a QGridLayout for better alignment."""
        frame = QFrame(objectName="CardFrame")
        grid_layout = QGridLayout(frame)
        grid_layout.setContentsMargins(15, 10, 15, 10)
        grid_layout.setSpacing(10)

        # Row 0: Labels
        grid_layout.addWidget(QLabel("Select Client:"), 0, 0)
        grid_layout.addWidget(QLabel("Billing Period (MM-YYYY):"), 0, 1, 1, 2, Qt.AlignmentFlag.AlignRight)

        # Row 1: Input Widgets
        self.bill_client_combo = QComboBox()
        self.bill_client_combo.setMinimumWidth(250)
        self.bill_client_combo.currentIndexChanged.connect(self.run_bill_check)
        grid_layout.addWidget(self.bill_client_combo, 1, 0)

        self.bill_month_combo = QComboBox()
        months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
        self.bill_month_combo.addItems(months)
        self.bill_month_combo.setMaxVisibleItems(12)
        grid_layout.addWidget(self.bill_month_combo, 1, 1)

        self.bill_year_combo = QSpinBox()
        self.bill_year_combo.setRange(2020, 2099)
        current_year = QDate.currentDate().year()
        self.bill_year_combo.setValue(current_year)
        grid_layout.addWidget(self.bill_year_combo, 1, 2)

        current_month_index = QDate.currentDate().month() - 1
        self.bill_month_combo.setCurrentIndex(current_month_index)

        self.bill_month_combo.currentIndexChanged.connect(self.run_bill_check)
        self.bill_year_combo.valueChanged.connect(self.run_bill_check)

        self.generate_bill_button = QPushButton(QIcon(self.main_window.ICON_ADD), "")
        self.generate_bill_button.setToolTip("Generate New Bill")
        self.generate_bill_button.setObjectName("GenerateBillButton")
        self.generate_bill_button.clicked.connect(self.main_window.generate_monthly_bill)
        grid_layout.addWidget(self.generate_bill_button, 1, 3)

        self.bill_status_label = QLabel("Select a client to check status.")
        self.bill_status_label.setObjectName("StatusLabel")
        grid_layout.addWidget(self.bill_status_label, 1, 4)

        grid_layout.setColumnStretch(4, 1)

        return frame

    def update_client_dropdown(self, clients):
        """Populates the client dropdown with a list of clients."""
        self.bill_client_combo.blockSignals(True)
        self.bill_client_combo.clear()
        self.bill_client_combo.addItem("Select a Client", None)
        for client in sorted(clients, key=lambda x: x['company_name']):
            self.bill_client_combo.addItem(client['company_name'], client['client_id'])
        self.bill_client_combo.blockSignals(False)
        self.run_bill_check() # Run check after populating

    def run_bill_check(self):
        """Checks the API if a bill already exists for the selected client/period."""
        client_id = self.bill_client_combo.currentData()
        if not client_id:
            self.bill_status_label.setText("Select a client to check status.")
            self.generate_bill_button.setEnabled(False)
            return

        month = self.bill_month_combo.currentText()
        year = self.bill_year_combo.value()
        billing_month = f"{year}-{month}"

        try:
            data = self.main_window.fetch_generic_details(
                "/monthly-bills/check-status",
                params={"client_id": client_id, "billing_month": billing_month}
            )
            if data:
                self.bill_status_label.setText(data.get("message", "Status unknown."))
                self.generate_bill_button.setEnabled(data.get("can_generate", False))
                if data.get("status") == "Billed" or "exists" in data.get("message", ""):
                    self.bill_status_label.setStyleSheet("color: #D32F2F;") # Red
                elif data.get("status") == "Ready":
                    self.bill_status_label.setStyleSheet("color: #388E3C;") # Green
                else:
                    self.bill_status_label.setStyleSheet("color: #FFA000;") # Orange/Yellow
        except Exception as e:
            print(f"Error checking bill status: {e}")
            self.bill_status_label.setText("Error checking status.")
            self.bill_status_label.setStyleSheet("color: #D32F2F;") # Red
            self.generate_bill_button.setEnabled(False)

    def populate_table(self, data):
        """Populates the table with monthly bill data."""
        self.table.setRowCount(len(data))

        headers = [
            "Bill ID", "Client", "Billing Month", "Total",
            "Status", "Due Date", "Paid Date", "Actions"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        color_paid = QColor("#388E3C")
        color_unpaid = QColor("#FFA000")
        color_overdue = QColor("#D32F2F")

        for row, item in enumerate(data):
            bill_id = item.get('bill_id')

            self.table.setItem(row, 0, QTableWidgetItem(str(bill_id)))
            self.table.setItem(row, 1, QTableWidgetItem(item.get('client_name')))
            self.table.setItem(row, 2, QTableWidgetItem(item.get('billing_month')))

            total_str = f"₹{item.get('total_amount', 0.0):.2f}"
            total_item = QTableWidgetItem(total_str)
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, total_item)

            status = item.get('status', 'N/A')
            status_item = QTableWidgetItem(status)

            if status == 'Paid': status_item.setForeground(color_paid)
            elif status == 'Unpaid': status_item.setForeground(color_unpaid)
            elif status == 'Overdue': status_item.setForeground(color_overdue)

            self.table.setItem(row, 4, status_item)
            self.table.setItem(row, 5, QTableWidgetItem(item.get('due_date', 'N/A')))
            self.table.setItem(row, 6, QTableWidgetItem(item.get('payment_date', 'N/A')))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            actions_layout.setSpacing(5)

            pdf_btn = self.create_table_button(self.main_window.ICON_PDF, "Download PDF")
            pdf_btn.clicked.connect(lambda _, bid=bill_id: self.main_window.download_monthly_bill_pdf(bid))
            actions_layout.addWidget(pdf_btn)

            paid_btn = self.create_table_button(self.main_window.ICON_PAID, "Mark as Paid")
            paid_btn.clicked.connect(lambda _, bid=bill_id: self.main_window.open_mark_as_paid_dialog(bid))
            if status == 'Paid' or status == 'Cancelled':
                paid_btn.setEnabled(False)
                paid_btn.setToolTip("Bill is already paid or cancelled.")
            actions_layout.addWidget(paid_btn)

            delete_btn = self.create_table_button(self.main_window.ICON_DELETE, "Delete Bill")
            delete_btn.clicked.connect(lambda _, bid=bill_id: self.main_window.delete_monthly_bill_by_id(bid))
            actions_layout.addWidget(delete_btn)

            actions_layout.addStretch()
            self.table.setCellWidget(row, 7, actions_widget)

        # --- Column Width Adjustments ---
        header = self.table.horizontalHeader()

        # Set Bill ID (index 0) to Fixed mode and specific width
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 10) # Adjust 70px as needed

        # Set Client (index 1) to Stretch
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setMinimumSectionSize(150) # Minimum width when stretching

        # Set fixed widths for other columns
        self.table.setColumnWidth(2, 110) # Billing Month
        self.table.setColumnWidth(3, 120) # Total
        self.table.setColumnWidth(4, 90)  # Status
        self.table.setColumnWidth(5, 110) # Due Date
        self.table.setColumnWidth(6, 110) # Paid Date

        # Set Actions (index 7) to resize based on content
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False) # Turn off stretch for last section

    def filter_table(self, text):
        """Hides rows that don't match the search text."""
        text = text.lower()
        for row in range(self.table.rowCount()):
            bill_id_item = self.table.item(row, 0)
            client_name_item = self.table.item(row, 1)

            bill_id_match = bill_id_item and text in bill_id_item.text().lower()
            client_name_match = client_name_item and text in client_name_item.text().lower()

            self.table.setRowHidden(row, not (bill_id_match or client_name_match))

    def create_table_button(self, icon_path, tooltip):
        """Helper to create a consistent icon button for the table."""
        button = QPushButton(QIcon(icon_path), "")
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button