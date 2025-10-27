# pages/dashboard_page.py
# Defines the UI for the Dashboard tab

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QFrame, QPushButton, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QIcon # Import QIcon

class DashboardPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Dashboard Overview", objectName="Header"))
        header_layout.addStretch()
        
        # UPDATED: Use an icon for refresh button
        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon(self.main_window.ICON_RESET)) # Use Reset icon
        refresh_btn.setToolTip("Refresh Dashboard")
        refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        refresh_btn.clicked.connect(self.main_window.refresh_dashboard_data)
        refresh_btn.setObjectName("FilterButton") # Style like a filter button
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)

        metrics_frame = QFrame(objectName="CardFrame")
        metrics_layout = QGridLayout(metrics_frame)

        self.metric_new_orders_label = QLabel("--", objectName="MetricNumber", alignment=Qt.AlignmentFlag.AlignCenter)
        self.metric_pending_challans_label = QLabel("--", objectName="MetricNumber", alignment=Qt.AlignmentFlag.AlignCenter)
        self.metric_unbilled_challans_label = QLabel("--", objectName="MetricNumber", alignment=Qt.AlignmentFlag.AlignCenter)
        self.metric_overdue_bills_label = QLabel("--", objectName="MetricNumber", alignment=Qt.AlignmentFlag.AlignCenter)

        metrics_layout.addWidget(self.metric_new_orders_label, 0, 0)
        metrics_layout.addWidget(QLabel("New Orders Today", alignment=Qt.AlignmentFlag.AlignCenter), 1, 0)
        metrics_layout.addWidget(self.metric_pending_challans_label, 0, 1)
        metrics_layout.addWidget(QLabel("Pending Challans", alignment=Qt.AlignmentFlag.AlignCenter), 1, 1)
        metrics_layout.addWidget(self.metric_unbilled_challans_label, 0, 2)
        metrics_layout.addWidget(QLabel("Unbilled Challans", alignment=Qt.AlignmentFlag.AlignCenter), 1, 2)
        metrics_layout.addWidget(self.metric_overdue_bills_label, 0, 3)
        metrics_layout.addWidget(QLabel("Overdue Bills", alignment=Qt.AlignmentFlag.AlignCenter), 1, 3)
        layout.addWidget(metrics_frame)

        alerts_frame = QFrame(objectName="CardFrame")
        self.alerts_layout = QVBoxLayout(alerts_frame)
        self.alerts_layout.addWidget(QLabel("🔥 Low Stock Alerts"))
        self.alerts_content_widget = QWidget()
        self.alerts_content_layout = QVBoxLayout(self.alerts_content_widget)
        self.alerts_layout.addWidget(self.alerts_content_widget)
        self.alerts_layout.addStretch()

        layout.addWidget(alerts_frame)
        layout.addStretch()

    def update_metrics(self, summary_data):
        self.metric_new_orders_label.setText(str(summary_data.get('new_orders_today', '--')))
        self.metric_pending_challans_label.setText(str(summary_data.get('pending_challans', '--')))
        self.metric_unbilled_challans_label.setText(str(summary_data.get('unbilled_challans', '--')))
        overdue_count = summary_data.get('overdue_bills', 0)
        self.metric_overdue_bills_label.setText(str(overdue_count))
        if overdue_count > 0:
            self.metric_overdue_bills_label.setStyleSheet("color: #C53030;")
        else:
            self.metric_overdue_bills_label.setStyleSheet("color: #38A169;")

    def update_low_stock_alerts(self, low_stock_data, clear_layout_func):
        clear_layout_func(self.alerts_content_layout) # Clear old alerts
        if low_stock_data:
            for item in low_stock_data:
                alert_text = f"❗ {item['name']} - Remaining: {item['stock_quantity']} (Threshold: {item['low_stock_threshold']})"
                self.alerts_content_layout.addWidget(QLabel(alert_text, styleSheet="color: #C53030;"))
        elif low_stock_data is not None:
            self.alerts_content_layout.addWidget(QLabel("No low stock items. Everything looks good!", styleSheet="color: #38A169;"))
        else:
            self.alerts_content_layout.addWidget(QLabel("Failed to load low stock data.", styleSheet="color: #C53030;"))
        self.alerts_content_layout.addStretch()
