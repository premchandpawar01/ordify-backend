# dialogs/base_dialog.py
# A new base class for all dialogs to give them a professional,
# consistent look with a branded header.
# UPDATED: Removed circular self-import

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QDialogButtonBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

# REMOVED: from .base_dialog import BaseDialog  <-- This line was removed

class BaseDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)

        # --- Main Layout ---
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main background frame
        self.bg_frame = QFrame(self)
        self.bg_frame.setObjectName("DialogBackground")
        self.bg_frame.setContentsMargins(0, 0, 0, 0)

        self.main_layout = QVBoxLayout(self.bg_frame)
        self.main_layout.setContentsMargins(1, 1, 1, 1) # 1px border for the header
        self.main_layout.setSpacing(0)

        # --- 1. Header Frame ---
        self.header_frame = QFrame()
        self.header_frame.setObjectName("DialogHeader")
        self.header_frame.setFixedHeight(40)
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(15, 0, 15, 0)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("DialogHeaderTitle")

        # Add icon to header (optional, but professional)
        if parent and hasattr(parent, 'windowIcon'): # Check if parent has windowIcon
            self.title_icon = QLabel()
            self.title_icon.setPixmap(parent.windowIcon().pixmap(QSize(18, 18)))
            header_layout.addWidget(self.title_icon)
            header_layout.addSpacing(10)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.main_layout.addWidget(self.header_frame)

        # --- 2. Content Frame ---
        self.content_frame = QFrame()
        self.content_frame.setObjectName("DialogContent")
        self.content_frame.setContentsMargins(20, 20, 20, 20)

        # This is where subclasses will add their widgets
        self.content_layout = QVBoxLayout(self.content_frame)

        self.main_layout.addWidget(self.content_frame, 1) # Add stretch

        # --- 3. Footer (Button Box) Frame ---
        self.footer_frame = QFrame()
        self.footer_frame.setObjectName("DialogFooter")
        self.footer_frame.setFixedHeight(60)
        footer_layout = QHBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(20, 0, 20, 0)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        footer_layout.addStretch()
        footer_layout.addWidget(self.button_box)

        self.main_layout.addWidget(self.footer_frame)

        # Set the main_layout as the layout for the dialog itself
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.bg_frame)
        self.layout().setContentsMargins(0, 0, 0, 0)

        # Make dialog draggable by the header
        self._mouse_press_pos = None
        self._mouse_move_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
             # Check if the press occurred within the header's geometry
             header_rect = self.header_frame.geometry()
             if header_rect.contains(event.pos()):
                self._mouse_press_pos = event.globalPosition().toPoint()
                self._mouse_move_pos = event.globalPosition().toPoint()
                event.accept() # Indicate event was handled
             else:
                event.ignore() # Let parent handle it
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self._mouse_press_pos is not None:
            delta = event.globalPosition().toPoint() - self._mouse_move_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._mouse_move_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._mouse_press_pos is not None:
            self._mouse_press_pos = None
            self._mouse_move_pos = None
            event.accept()
        else:
            event.ignore()