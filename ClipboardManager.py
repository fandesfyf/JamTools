import sys
import json
import base64
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QScrollBar, QScroller, QAbstractItemView, QPushButton, QHBoxLayout, 
                             QLabel, QMenu, QInputDialog, QMessageBox)
from PyQt5.QtGui import QClipboard, QCursor, QFont, QFontMetrics,QPixmap,QImage
from PyQt5.QtCore import Qt, QTimer, QSize,QByteArray, QBuffer
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QDesktopWidget
from PyQt5.QtCore import pyqtSignal

from pynput import mouse, keyboard
import io
class CustomListWidget(QListWidget):
    itemActivated = pyqtSignal(QListWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current_item = self.currentItem()
            if current_item:
                self.itemActivated.emit(current_item)
        else:
            super().keyPressEvent(event)
class CustomInputDialog(QDialog):
    def __init__(self, parent=None, title="", text=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(240, 248, 255, 220);
                border: 1px solid #4682B4;
                border-radius: 10px;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #87CEFA;
                border-radius: 5px;
                padding: 5px;
                color: black;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(240, 248, 255, 0);
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #4682B4;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QPushButton {
                background-color: #4682B4;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5c9fd6;
            }
        """)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit(self)
        self.text_edit.setText(text)
        self.text_edit.setMinimumSize(300, 200)
        layout.addWidget(self.text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.adjust_size(text)

    def adjust_size(self, text):
        font = self.text_edit.font()
        fm = QFontMetrics(font)
        
        max_width = 600  # 设置最大宽度
        text_width = fm.width(max(text.split('\n'), key=len)) + 30  # 30 for padding and scrollbar
        
        width = min(max_width, max(300, text_width))  # 确保宽度不小于300
        
        screen = QApplication.primaryScreen().geometry()
        max_height = int(screen.height() * 0.8)  # 设置最大高度为屏幕高度的80%
        
        self.text_edit.setMinimumWidth(width)
        self.resize(width + 20, min(max_height, max(200, len(text.split('\n')) * fm.lineSpacing() + 100)))

    def get_text(self):
        return self.text_edit.toPlainText()
    
class ClipboardItemWidget(QWidget):
    def __init__(self, content, is_image=False, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.windows_width = 300
        self.windows_height = 90
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 15, 5)
        layout.setSpacing(10)
        
        if is_image:
            self.label = QLabel()
            pixmap = QPixmap()
            pixmap.loadFromData(content)
            scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled_pixmap)
        else:
            self.label = QLabel()
            self.label.setStyleSheet("background: transparent; color: black;")
            font = QFont()
            font.setPointSize(10)
            self.label.setFont(font)
            
            fm = QFontMetrics(font)
            line_height = fm.lineSpacing()
            available_height = self.windows_height - 5*2
            max_lines = available_height // line_height
            
            lines = content.split('\n')
            if len(lines) > max_lines:
                display_text = '\n'.join(lines[:max_lines-1]) + '\n...'
            else:
                display_text = '\n'.join(lines)
            
            max_width = self.windows_width - 60
            wrapped_text = []
            for line in display_text.split('\n'):
                if fm.width(line) > max_width:
                    wrapped_line = []
                    current_line = ""
                    for word in line.split():
                        if fm.width(current_line + " " + word) <= max_width:
                            current_line += " " + word if current_line else word
                        else:
                            wrapped_line.append(current_line)
                            current_line = word
                    wrapped_line.append(current_line)
                    wrapped_text.extend(wrapped_line)
                else:
                    wrapped_text.append(line)
            
            if len(wrapped_text) > max_lines:
                wrapped_text = wrapped_text[:max_lines-1] + ['...']
            
            self.label.setText('\n'.join(wrapped_text))
        
        layout.addWidget(self.label, stretch=1)
        
        self.option_button = QPushButton("⋮")
        self.option_button.setFixedSize(24, 24)
        self.option_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4682B4;
                border: none;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #5c9fd6;
            }
        """)
        layout.addWidget(self.option_button, alignment=Qt.AlignVCenter)

    def sizeHint(self):
        return QSize(self.windows_width, self.windows_height)

class ClipboardManager(QWidget):
    def __init__(self, max_history=50, history_path=None):
        super().__init__()
        self.history_path = "clipboard_history.json" if history_path is None else history_path
        self.max_history = max_history
        self.initUI()
        self.clipboard = QApplication.clipboard()
        self.clipboard_history = []
        self.is_menu_visible = False
        self.load_history()
        self.clipboard.dataChanged.connect(self.on_clipboard_change)
        # self.clipboard.selectionChanged.connect(self.on_selection_change)

        self.keyboard_listener = keyboard.GlobalHotKeys({
            '<alt>+v': self.toggle_visibility
        })
        self.keyboard_listener.start()
        self.auto_hide = True

        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.list_widget = CustomListWidget(self)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list_widget.verticalScrollBar().setSingleStep(20)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: rgba(240, 248, 255, 220);
                border: 1px solid #4682B4;
                border-radius: 10px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 1px;
                border-bottom: 1px solid #87CEFA;
                color: black;
            }
            QListWidget::item:hover {
                background-color: rgba(135, 206, 250, 100);
            }
            QListWidget::item:selected {
                background-color: rgba(70, 130, 180, 150);
                color: black;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(240, 248, 255, 0);
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #4682B4;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                height: 0px;
            }
        """)
        self.list_widget.setVerticalScrollBar(QScrollBar())
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemActivated.connect(self.on_item_clicked)
        # QScroller.grabGesture(self.list_widget.viewport(), QScroller.LeftMouseButtonGesture)
        
        layout.addWidget(self.list_widget)
        
        self.setLayout(layout)
        self.resize(300, 400)
        self.setWindowTitle('Clipboard Manager')

    def on_clipboard_change(self):
        mime_data = self.clipboard.mimeData(mode=QClipboard.Clipboard)
        if mime_data.hasImage():
            image = mime_data.imageData()
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QBuffer.WriteOnly)
            image.save(buffer, "PNG")
            image_data = byte_array.data()
            self.add_to_history(image_data, is_image=True)
        elif mime_data.hasText():
            self.add_to_history(mime_data.text())

    def on_selection_change(self):
        pass
        # print("Selection changed")
        # self.add_to_history(self.clipboard.text(mode=QClipboard.Selection))

    def add_to_history(self, content, is_image=False):
        if content:
            for item in self.clipboard_history:
                if item['content'] == content:
                    self.clipboard_history.remove(item)
                    break
            self.clipboard_history.insert(0, {'content': content, 'is_image': is_image})
            if len(self.clipboard_history) > self.max_history:
                self.clipboard_history.pop()
            self.update_list_widget()
            self.save_history()

    def update_list_widget(self):
        self.list_widget.clear()
        for item in self.clipboard_history:
            list_item = QListWidgetItem(self.list_widget)
            item_widget = ClipboardItemWidget(item['content'], item['is_image'])
            item_widget.option_button.clicked.connect(lambda checked, i=item: self.show_options(i))
            list_item.setSizeHint(item_widget.sizeHint())
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, item_widget)



    def show_options(self, item):
        self.is_menu_visible = True
        menu = QMenu(self)
        edit_action = None
        if not item['is_image']:
            edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        delete_all_action = menu.addAction("全部删除")

        action = menu.exec_(QCursor.pos())
        
        if action == edit_action and edit_action is not None:
            self.edit_item(item)
        elif action == delete_action:
            self.delete_item(item)
        elif action == delete_all_action:
            self.delete_all_items()
        self.is_menu_visible = False

    def edit_item(self, item):
        dialog = CustomInputDialog(self, "编辑", item['content'])
        if dialog.exec_() == QDialog.Accepted:
            new_text = dialog.get_text()
            if new_text != item['content']:
                item['content'] = new_text
                self.update_list_widget()
                self.save_history()

    def delete_item(self, item):
        self.clipboard_history.remove(item)
        self.update_list_widget()
        self.save_history()

    def delete_all_items(self):
        reply = QMessageBox.question(self, '确认', '确定要删除所有历史记录吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.clipboard_history.clear()
            self.update_list_widget()
            self.save_history()
            
    def on_item_clicked(self, item):
        index = self.list_widget.row(item)
        clipboard_item = self.clipboard_history[index]
        
        if clipboard_item['is_image']:
            image_data = clipboard_item['content']
            image = QImage()
            image.loadFromData(image_data)
            self.clipboard.setImage(image)
        else:
            self.clipboard.setText(clipboard_item['content'])
        
        self.hide()
        QTimer.singleShot(50, self.simulate_paste)

    def simulate_paste(self):
        # 模拟粘贴操作
        controller = keyboard.Controller()
        controller.press(keyboard.Key.ctrl)
        controller.press(keyboard.Key.shift)
        controller.press('v')
        time.sleep(0.01)
        controller.release('v')
        controller.release(keyboard.Key.shift)
        controller.release(keyboard.Key.ctrl)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_near_cursor()

    def show_near_cursor(self):
        cursor_pos = QCursor.pos()
        desktop = QDesktopWidget()
        screen_number = desktop.screenNumber(cursor_pos)
        screen_geometry = desktop.screenGeometry(screen_number)

        x = cursor_pos.x()
        y = cursor_pos.y()

        # 确保窗口完全在屏幕内
        if x + self.width() > screen_geometry.right():
            x = screen_geometry.right() - self.width()
        if y + self.height() > screen_geometry.bottom():
            y = screen_geometry.bottom() - self.height()

        # 确保窗口不会超出屏幕左边和上边
        x = max(x, screen_geometry.left())
        y = max(y, screen_geometry.top())

        self.move(x, y)
        self.show()
        self.activateWindow()
        self.raise_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()

    def toggle_auto_hide(self):
        self.auto_hide = not self.auto_hide
        print(f"Auto-hide {'enabled' if self.auto_hide else 'disabled'}")

    def on_click(self, x, y, button, pressed):
        if pressed and self.isVisible() and self.auto_hide:
            if not self.is_menu_visible and not self.geometry().contains(x, y):
                self.hide()

    def save_history(self):
        serializable_history = []
        for item in self.clipboard_history:
            serializable_item = item.copy()
            if item['is_image']:
                serializable_item['content'] = base64.b64encode(item['content']).decode('utf-8')
            serializable_history.append(serializable_item)
        
        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_history, f, ensure_ascii=False, indent=2)

    def load_history(self):
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                serializable_history = json.load(f)
            
            self.clipboard_history = []
            for item in serializable_history:
                if item['is_image']:
                    item['content'] = base64.b64decode(item['content'])
                self.clipboard_history.append(item)
            
            self.update_list_widget()
        except FileNotFoundError:
            print("No history file found. Starting with empty history.")
        except json.JSONDecodeError:
            print("Error reading history file. Starting with empty history.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ClipboardManager()
    sys.exit(app.exec_())
