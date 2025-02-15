import hashlib
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
import os
import json
from cryptography.fernet import Fernet
import base64

class ModernEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom File Editor - TheZ")
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon("icon.png"))
        
        # Generate master key and multiple encryption layers
        master_seed = os.urandom(64)
        self.master_key = hashlib.sha512(master_seed).digest()
        self.encryption_layers = [Fernet(Fernet.generate_key()) for _ in range(200)]
        
        self.colors = {
            'bg': '#1a1b26',
            'text': '#a9b1d6',
            'accent': '#7aa2f7',
            'tab_bg': '#24283b',
            'selected_tab': '#2ac3de',
            'toolbar': '#1a1b26'
        }
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.colors['bg']};
                color: {self.colors['text']};
            }}
            QTabWidget {{
                background-color: {self.colors['tab_bg']};
                border: 1px solid {self.colors['accent']};
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background-color: {self.colors['tab_bg']};
                color: {self.colors['text']};
                padding: 10px 25px;
                border: none;
                border-radius: 4px;
                margin: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.colors['accent']};
                color: {self.colors['bg']};
            }}
            QToolBar {{
                background-color: {self.colors['toolbar']};
                border: none;
                spacing: 10px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {self.colors['accent']};
                color: {self.colors['bg']};
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['selected_tab']};
            }}
            QGroupBox {{
                color: {self.colors['text']};
                border: 1px solid {self.colors['accent']};
                border-radius: 5px;
                margin-top: 10px;
                padding: 15px;
            }}
            QLineEdit {{
                background-color: {self.colors['tab_bg']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['accent']};
                border-radius: 3px;
                padding: 5px;
            }}
            QCheckBox {{
                color: {self.colors['text']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.colors['accent']};
            }}
        """)

        self.current_file = None
        self.current_extension = ".txt"
        self.file_header = b''
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.editor_tab = QWidget()
        self.settings_tab = QWidget()
        
        self.tabs.addTab(self.editor_tab, "Editor")
        settings_index = self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.tabBar().setTabButton(settings_index, QTabBar.ButtonPosition.RightSide, None)
        
        self.tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.show_tab_context_menu)
        
        self.setup_editor()
        self.setup_settings()
        self.setup_toolbar()

    def setup_toolbar(self):
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        
        new_btn = QPushButton("New")
        save_btn = QPushButton("Save")
        load_btn = QPushButton("Load")
        
        new_btn.clicked.connect(self.new_file)
        save_btn.clicked.connect(self.save_file)
        load_btn.clicked.connect(self.load_file)
        
        self.toolbar.addWidget(new_btn)
        self.toolbar.addWidget(save_btn)
        self.toolbar.addWidget(load_btn)

    def setup_editor(self):
        layout = QVBoxLayout()
        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {self.colors['bg']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['accent']};
                border-radius: 5px;
                font-family: 'Consolas';
                font-size: 13px;
                padding: 5px;
            }}
        """)
        
        self.editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.show_editor_context_menu)
        
        layout.addWidget(self.editor)
        self.editor_tab.setLayout(layout)

    def setup_settings(self):
        layout = QVBoxLayout()
        
        ext_group = QGroupBox("File Extension Settings")
        ext_layout = QFormLayout()
        self.ext_input = QLineEdit()
        ext_layout.addRow("Custom Extension:", self.ext_input)
        
        self.protection_toggle = QCheckBox("Enable File Protection")
        ext_layout.addRow(self.protection_toggle)
        
        ext_group.setLayout(ext_layout)
        layout.addWidget(ext_group)
        
        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_btn)
        
        layout.addStretch()
        self.settings_tab.setLayout(layout)

    def show_tab_context_menu(self, position):
        tab_bar = self.tabs.tabBar()
        tab_index = tab_bar.tabAt(position)
        
        if tab_index == self.tabs.count() - 1:
            return
            
        context_menu = QMenu(self)
        rename_action = context_menu.addAction("Rename Tab")
        close_action = context_menu.addAction("Close Tab")
        new_file_action = context_menu.addAction("New File")
        
        action = context_menu.exec(self.tabs.mapToGlobal(position))
        
        if action == rename_action:
            self.rename_tab(tab_index)
        elif action == close_action:
            self.tabs.removeTab(tab_index)
        elif action == new_file_action:
            self.new_file()

    def show_editor_context_menu(self, position):
        context_menu = QMenu(self)
        
        select_all_action = context_menu.addAction("Select All")
        copy_action = context_menu.addAction("Copy")
        paste_action = context_menu.addAction("Paste")
        delete_action = context_menu.addAction("Delete")
        
        context_menu.addSeparator()
        
        rename_tab_action = context_menu.addAction("Rename Tab")
        close_tab_action = context_menu.addAction("Close Tab")
        new_file_action = context_menu.addAction("New File")
        
        action = context_menu.exec(self.editor.mapToGlobal(position))
        
        if action == select_all_action:
            self.editor.selectAll()
        elif action == copy_action:
            self.editor.copy()
        elif action == paste_action:
            self.editor.paste()
        elif action == delete_action:
            self.editor.textCursor().removeSelectedText()
        elif action == rename_tab_action:
            self.rename_current_tab()
        elif action == close_tab_action:
            self.close_current_tab()
        elif action == new_file_action:
            self.new_file()

    def rename_tab(self, index):
        new_name, ok = QInputDialog.getText(
            self,
            'Rename Tab',
            'Enter new tab name:',
            text=self.tabs.tabText(index)
        )
        if ok and new_name:
            self.tabs.setTabText(index, new_name)

    def rename_current_tab(self):
        current_index = self.tabs.currentIndex()
        if current_index != self.tabs.count() - 1:
            self.rename_tab(current_index)

    def close_current_tab(self):
        current_index = self.tabs.currentIndex()
        if current_index != self.tabs.count() - 1:
            self.tabs.removeTab(current_index)

    def save_settings(self):
        settings = {
            'extension': self.ext_input.text() or '.txt',
            'protection_enabled': self.protection_toggle.isChecked()
        }
        with open('editor_settings.json', 'w') as f:
            json.dump(settings, f)
        
        self.current_extension = settings['extension']
        self.file_header = b'PROTECTED_CUSTOM_EDITOR' if settings['protection_enabled'] else b''
        
        QMessageBox.information(self, "Success", "Settings saved successfully!")

    def load_settings(self):
        try:
            with open('editor_settings.json', 'r') as f:
                settings = json.load(f)
                self.ext_input.setText(settings.get('extension', '.txt'))
                self.current_extension = settings.get('extension', '.txt')
                self.protection_toggle.setChecked(settings.get('protection_enabled', False))
                self.file_header = b'PROTECTED_CUSTOM_EDITOR' if settings.get('protection_enabled', False) else b''
        except FileNotFoundError:
            pass

    def new_file(self):
        new_tab = QWidget()
        layout = QVBoxLayout()
        editor = QPlainTextEdit()
        editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {self.colors['bg']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['accent']};
                border-radius: 5px;
                font-family: 'Consolas';
                font-size: 13px;
                padding: 5px;
            }}
        """)
        editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        editor.customContextMenuRequested.connect(self.show_editor_context_menu)
        
        layout.addWidget(editor)
        new_tab.setLayout(layout)
        
        settings_index = self.tabs.count() - 1
        self.tabs.insertTab(settings_index, new_tab, f"New File {settings_index}")
        self.tabs.setCurrentIndex(settings_index)

    def save_file(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            f"Custom Files (*{self.current_extension});;All Files (*.*)"
        )
        
        if file_name:
            if not file_name.endswith(self.current_extension):
                file_name += self.current_extension
                
            # Save encryption keys
            key_file = file_name + '.key'
            key_data = {
                'master_key': base64.b64encode(self.master_key).decode(),
                'layer_keys': [base64.b64encode(layer.key).decode() for layer in self.encryption_layers]
            }
            with open(key_file, 'w') as kf:
                json.dump(key_data, kf)
                
            current_tab = self.tabs.currentWidget()
            editor = current_tab.layout().itemAt(0).widget()
            content = editor.toPlainText()
            
            with open(file_name, 'wb') as f:
                if self.protection_toggle.isChecked():
                    encrypted_data = content.encode()
                    for layer in self.encryption_layers:
                        encrypted_data = layer.encrypt(encrypted_data)
                    f.write(self.file_header + b'\n')
                    f.write(encrypted_data)
                else:
                    f.write(content.encode())
            
            self.current_file = file_name
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(file_name))
            QMessageBox.information(self, "Success", "File saved with maximum security!")

    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            f"Custom Files (*{self.current_extension});;All Files (*.*)"
        )
        
        if file_name:
            try:
                # Load encryption keys
                key_file = file_name + '.key'
                if os.path.exists(key_file):
                    with open(key_file, 'r') as kf:
                        key_data = json.load(kf)
                        self.master_key = base64.b64decode(key_data['master_key'])
                        self.encryption_layers = [Fernet(base64.b64decode(key)) for key in key_data['layer_keys']]
                
                with open(file_name, 'rb') as f:
                    content = f.read()
                    
                if content.startswith(b'PROTECTED_CUSTOM_EDITOR\n'):
                    encrypted_content = content[len(b'PROTECTED_CUSTOM_EDITOR\n'):]
                    decrypted_data = encrypted_content
                    for layer in reversed(self.encryption_layers):
                        decrypted_data = layer.decrypt(decrypted_data)
                    content = decrypted_data
                elif self.protection_toggle.isChecked():
                    QMessageBox.warning(self, "Error", "This file is not protected and cannot be opened with protection enabled!")
                    return
                
                self.new_file()
                current_tab = self.tabs.currentWidget()
                editor = current_tab.layout().itemAt(0).widget()
                editor.setPlainText(content.decode())
                
                self.current_file = file_name
                self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(file_name))
                
            except Exception as e:
                QMessageBox.warning(self, "Error", "This file cannot be opened with this editor!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernEditor()
    window.show()
    sys.exit(app.exec())
