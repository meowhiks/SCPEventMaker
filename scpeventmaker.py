import sys
import os
import random
import json
import ast
from PyQt5 import QtWidgets, QtGui, QtCore
import time

"""

███████╗██╗   ██╗███████╗███╗   ██╗████████╗███╗   ███╗ █████╗ ██╗  ██╗███████╗██████╗ 
██╔════╝██║   ██║██╔════╝████╗  ██║╚══██╔══╝████╗ ████║██╔══██╗██║ ██╔╝██╔════╝██╔══██╗
█████╗  ██║   ██║█████╗  ██╔██╗ ██║   ██║   ██╔████╔██║███████║█████╔╝ █████╗  ██████╔╝
██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║   ██║   ██║╚██╔╝██║██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗
███████╗ ╚████╔╝ ███████╗██║ ╚████║   ██║   ██║ ╚═╝ ██║██║  ██║██║  ██╗███████╗██║  ██║
╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝1.0

by meowhiks
"""

def evaluate_code_snippets(command, variables=None):
    if variables is None:
        variables = {}

    def replace_variables(text):
        segments = []
        last_end = 0
        while True:
            start_idx = text.find('<var=')
            if start_idx == -1:
                segments.append(text[last_end:])
                break
            end_idx = text.find('>', start_idx)
            if end_idx == -1:
                segments.append(text[last_end:])
                break
            segments.append(text[last_end:start_idx])
            var_name = text[start_idx + 5:end_idx]
            var_value = variables.get(var_name, f'<var={var_name}>')
            segments.append(str(var_value))
            text = text[end_idx + 1:]
        return ''.join(segments)


    command = replace_variables(command)

  
    def process_random_functions(text):
        processed_text = ''
        i = 0
        while i < len(text):
            if text[i:i+8] == '%random(':
                end_idx = text.find(')%', i)
                if end_idx != -1:
                    snippet = text[i+8:end_idx]
                    try:
                        args = ast.literal_eval('(' + snippet + ')')
                        if isinstance(args, tuple):
                            if all(isinstance(arg, int) for arg in args) and len(args) == 2:
                                rand_value = str(random.randint(args[0], args[1]))
                            else:
                                rand_value = str(random.choice(args))
                        else:
                            rand_value = str(args)
                        processed_text += rand_value
                        i = end_idx + 2
                        continue
                    except Exception as e:
                        processed_text += text[i:end_idx+2]
                        i = end_idx + 2
                        continue
                else:
                    processed_text += text[i]
                    i += 1
            else:
                processed_text += text[i]
                i += 1
        return processed_text


    command = process_random_functions(command)

    return command


def parse_command_text(command_text):
    segments = []
    last_end = 0
    current_color = None
    while True:
        start_idx = command_text.find('<color=', last_end)
        if start_idx == -1:
            segments.append((command_text[last_end:], current_color))
            break
        end_idx = command_text.find('>', start_idx)
        if end_idx == -1:
            segments.append((command_text[last_end:], current_color))
            break
        if start_idx > last_end:
            segments.append((command_text[last_end:start_idx], current_color))
        current_color = command_text[start_idx + 7:end_idx]
        last_end = end_idx + 1
    return segments


class Command:
    def __init__(self, original_command, sequence=None, exclude_from_random=False):
        self.original = original_command
        self.sequence = sequence or []
        self.exclude_from_random = exclude_from_random 

    def to_dict(self):
        return {
            'original': self.original,
            'sequence': self.sequence,
            'exclude_from_random': self.exclude_from_random  
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            original_command=data['original'],
            sequence=data.get('sequence', []),
            exclude_from_random=data.get('exclude_from_random', False) 
        )


class Preset:
    def __init__(self, name, is_random=False):
        self.name = name
        self.is_random = is_random  
        self.commands = []

    def to_dict(self):
        return {
            'name': self.name,
            'is_random': self.is_random,  
            'commands': [cmd.to_dict() for cmd in self.commands]
        }

    @classmethod
    def from_dict(cls, data):
        preset = cls(data['name'], data.get('is_random', False))  
        preset.commands = [Command.from_dict(cmd_data) for cmd_data in data['commands']]
        return preset


class PresetApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon('scrpt.png')) 
        self.presets = []
        self.variables = {}
        self.selected_preset_index = None
        self.selected_command = None
        self.selected_command_index = None
        self.default_sequence = ['~', 'Ctrl+V', 'Enter']
        self.miniapp_visible = True
        self.mini_drag_position = None 
        self.init_ui()
        self.load_presets()
        self.load_variables()

    def init_ui(self):
      
        self.setWindowTitle("meowhiks")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)


        self.setStyleSheet("""
        QMainWindow {
            background-color: #1E1E1E;
        }
        QLabel {
            color: #FFFFFF;
            background-color: transparent;
            font-size: 16px;
        }
        QPushButton {
            color: #FFFFFF;
            background-color: #2D2D30;
            border: 1px solid #3E3E42;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: #3E3E42;
        }
        QPushButton:pressed {
            background-color: #2D2D30;
        }
        QLineEdit {
            color: #FFFFFF;
            background-color: #2D2D30;
            border: 1px solid #3E3E42;
            padding: 6px;
            border-radius: 4px;
            font-size: 16px;
        }
        QListWidget {
            color: #FFFFFF;
            background-color: #2D2D30;
            border: 1px solid #3E3E42;
            border-radius: 4px;
            font-size: 16px;
        }
        QListWidget::item:selected {
            background-color: #3E3E42;
        }
        QListWidget::item:hover {
            background-color: #45454A;
        }
        QScrollArea {
            border: none;
            background-color: #1E1E1E;
        }
        QScrollBar:vertical, QScrollBar:horizontal {
            background: #2D2D30;
            width: 12px;
            height: 12px;
            margin: 0px;
            border: 1px solid #3E3E42;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background: #3E3E42;
            min-height: 20px;
            min-width: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            height: 0px;
            width: 0px;
            subcontrol-origin: margin;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        QCheckBox {
            color: #FFFFFF;
            background-color: transparent;
            font-size: 16px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        QCheckBox::indicator:unchecked {
            image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAAI0lEQVQoU2NkwAT/gYGB4T8GNJCYgWBANgKDE5YMyAkAYpYBAHnbBxjGSE+jAAAAAElFTkSuQmCC);
        }
        QCheckBox::indicator:checked {
            image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAAO0lEQVQoU2NkwA78x4GBgUGBiYFALwEyDLEIGhGgQiZBEliLGDAIEqQZA0EwDAgNYZAAMUBAQZ6oGYDAAAAABJRU5ErkJggg==);
        }
        QMenu {
            color: #FFFFFF;
            background-color: #2D2D30;
            border: 1px solid #3E3E42;
            font-size: 16px;
        }
        QMenu::item:selected {
            background-color: #3E3E42;
        }
        """)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_layout.setSpacing(10)
        self.main_layout.addLayout(self.header_layout)

        self.title_label = QtWidgets.QLabel("🎮 SCP:SL Создатель ивентов")
        self.title_label.setFont(QtGui.QFont("Segoe UI", 28, QtGui.QFont.Bold))
        self.header_layout.addWidget(self.title_label)

        self.header_layout.addStretch()

        self.add_preset_button = QtWidgets.QPushButton("➕ Добавить пресет")
        self.add_preset_button.clicked.connect(self.add_preset_window)
        self.add_preset_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.header_layout.addWidget(self.add_preset_button)

        self.import_preset_button = QtWidgets.QPushButton("📁 Импортировать пресет")
        self.import_preset_button.clicked.connect(self.import_preset_window)
        self.import_preset_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.header_layout.addWidget(self.import_preset_button)

        self.settings_button = QtWidgets.QPushButton("⚙ Настройки")
        self.settings_button.clicked.connect(self.open_settings_window)
        self.settings_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.header_layout.addWidget(self.settings_button)

        self.content_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.main_layout.addWidget(self.content_splitter)

        self.presets_frame = QtWidgets.QFrame()
        self.presets_layout = QtWidgets.QVBoxLayout(self.presets_frame)
        self.presets_layout.setContentsMargins(10, 10, 10, 10)
        self.presets_layout.setSpacing(10)

        self.presets_label = QtWidgets.QLabel("📁 Пресеты")
        self.presets_label.setFont(QtGui.QFont("Segoe UI", 22, QtGui.QFont.Bold))
        self.presets_layout.addWidget(self.presets_label)

        self.preset_listbox = QtWidgets.QListWidget()
        self.preset_listbox.itemSelectionChanged.connect(self.on_preset_select)
        self.preset_listbox.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.preset_listbox.customContextMenuRequested.connect(self.on_preset_right_click)
        self.presets_layout.addWidget(self.preset_listbox)

        self.presets_layout.addStretch()

        self.content_splitter.addWidget(self.presets_frame)
        self.content_splitter.setStretchFactor(0, 1)

        self.commands_frame = QtWidgets.QFrame()
        self.commands_layout = QtWidgets.QVBoxLayout(self.commands_frame)
        self.commands_layout.setContentsMargins(10, 10, 10, 10)
        self.commands_layout.setSpacing(10)

        self.preset_header_layout = QtWidgets.QHBoxLayout()
        self.preset_header_layout.setSpacing(10)
        self.commands_layout.addLayout(self.preset_header_layout)

        self.preset_name_label = QtWidgets.QLabel("")
        self.preset_name_label.setFont(QtGui.QFont("Segoe UI", 22, QtGui.QFont.Bold))
        self.preset_header_layout.addWidget(self.preset_name_label)

        self.preset_header_layout.addStretch()

        self.edit_default_sequence_button = QtWidgets.QPushButton("🔄 Изменить последовательность")
        self.edit_default_sequence_button.clicked.connect(self.edit_default_sequence)
        self.edit_default_sequence_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.preset_header_layout.addWidget(self.edit_default_sequence_button)

        self.add_command_layout = QtWidgets.QHBoxLayout()
        self.add_command_layout.setSpacing(10)
        self.commands_layout.addLayout(self.add_command_layout)

        self.new_command_entry = QtWidgets.QLineEdit()
        self.new_command_entry.setPlaceholderText("Введите новую команду...")
        self.new_command_entry.returnPressed.connect(self.add_command)
        self.add_command_layout.addWidget(self.new_command_entry)

        self.add_command_button = QtWidgets.QPushButton("➕")
        self.add_command_button.clicked.connect(self.add_command)
        self.add_command_button.setFixedWidth(40)
        self.add_command_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.add_command_layout.addWidget(self.add_command_button)

        self.commands_scroll_area = QtWidgets.QScrollArea()
        self.commands_scroll_area.setWidgetResizable(True)
        self.commands_scroll_area.setStyleSheet("""
        QScrollArea {
            border: none;
            background-color: #1E1E1E;
        }
        """)
        self.commands_layout.addWidget(self.commands_scroll_area)

        self.commands_container = QtWidgets.QWidget()
        self.commands_container.setStyleSheet("background-color: #1E1E1E;")
        self.commands_scroll_area.setWidget(self.commands_container)
        self.commands_container_layout = QtWidgets.QVBoxLayout(self.commands_container)
        self.commands_container_layout.setSpacing(0)
        self.commands_container_layout.setContentsMargins(0, 0, 0, 0)

        self.content_splitter.addWidget(self.commands_frame)
        self.content_splitter.setStretchFactor(1, 2)

        self.create_mini_widget()

    def create_mini_widget(self):
        self.mini_widget = QtWidgets.QWidget()
        self.mini_widget.setWindowTitle("MiniApp")
        self.mini_widget.setGeometry(100, 100, 300, 500)
        self.mini_widget.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.mini_widget.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.mini_widget.setWindowOpacity(0.9)
        self.mini_widget.setWindowIcon(QtGui.QIcon('scrpt.png')) 

        screen_geometry = QtWidgets.QApplication.desktop().screenGeometry()
        x = screen_geometry.width() - self.mini_widget.width() - 20
        y = 20
        self.mini_widget.move(x, y)

        self.mini_layout = QtWidgets.QGridLayout(self.mini_widget)
        self.mini_layout.setContentsMargins(0, 0, 0, 0)
        self.mini_widget.setStyleSheet("""
        QScrollBar:vertical, QScrollBar:horizontal {
            background: #2D2D30;
            width: 12px;
            height: 12px;
            margin: 0px;
            border: 1px solid #3E3E42;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background: #3E3E42;
            min-height: 20px;
            min-width: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            height: 0px;
            width: 0px;
            subcontrol-origin: margin;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        """)
        self.mini_background_frame = QtWidgets.QFrame()
        self.mini_background_frame.setStyleSheet("""
        QFrame {
            background-color: rgba(30, 30, 30, 230);
            border-radius: 10px;
        }
        """)
        self.mini_layout.addWidget(self.mini_background_frame, 0, 0)

        self.mini_background_layout = QtWidgets.QVBoxLayout(self.mini_background_frame)
        self.mini_background_layout.setContentsMargins(10, 10, 10, 10)
        self.mini_background_layout.setSpacing(10)

        self.mini_title_layout = QtWidgets.QHBoxLayout()
        self.mini_title_label = QtWidgets.QLabel("📋 Команды")
        self.mini_title_label.setFont(QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold))
        self.mini_title_label.setStyleSheet("color: #FFFFFF;")
        self.mini_title_layout.addWidget(self.mini_title_label)
        self.mini_title_layout.addStretch()

        self.mini_close_button = QtWidgets.QPushButton("✖")
        self.mini_close_button.setFixedSize(24, 24)
        self.mini_close_button.setStyleSheet("""
        QPushButton {
            background-color: transparent;
            color: #FFFFFF;
            border: none;
        }
        QPushButton:hover {
            color: #FF0000;
        }
        """)
        self.mini_close_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.mini_close_button.clicked.connect(self.toggle_miniapp)
        self.mini_title_layout.addWidget(self.mini_close_button)

        self.mini_background_layout.addLayout(self.mini_title_layout)

        self.mini_scroll_area = QtWidgets.QScrollArea()
        self.mini_scroll_area.setWidgetResizable(True)
        self.mini_scroll_area.setStyleSheet("""
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        """)
        self.mini_background_layout.addWidget(self.mini_scroll_area)

        self.mini_container = QtWidgets.QWidget()
        self.mini_container.setStyleSheet("background-color: transparent;")
        self.mini_scroll_area.setWidget(self.mini_container)
        self.mini_container_layout = QtWidgets.QVBoxLayout(self.mini_container)
        self.mini_container_layout.setSpacing(10)
        self.mini_container_layout.setContentsMargins(0, 0, 0, 0)

        self.size_grip = QtWidgets.QSizeGrip(self.mini_widget)
        self.mini_layout.addWidget(self.size_grip, 0, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)


        self.mini_widget.mousePressEvent = self.mini_mouse_press_event
        self.mini_widget.mouseMoveEvent = self.mini_mouse_move_event

        self.mini_widget.show()
        self.update_mini_widget_commands()

    def mini_mouse_press_event(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.mini_drag_position = event.globalPos() - self.mini_widget.frameGeometry().topLeft()
            event.accept()

    def mini_mouse_move_event(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self.mini_drag_position is not None:
            self.mini_widget.move(event.globalPos() - self.mini_drag_position)
            event.accept()

    def update_mini_widget_commands(self):
        while self.mini_container_layout.count():
            item = self.mini_container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for preset in self.presets:
            if not preset.commands:
                continue
            preset_header_layout = QtWidgets.QHBoxLayout()
            preset_label = QtWidgets.QLabel(preset.name)
            preset_label.setFont(QtGui.QFont("Segoe UI", 14, QtGui.QFont.Bold))
            preset_label.setStyleSheet("color: #FFFFFF;")
            if preset.is_random:
                preset_label.setText(f"{preset.name} (Рандом)")
                random_button = QtWidgets.QPushButton("🎲")
                random_button.setFixedSize(24, 24)
                random_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #FFFFFF;
                    border: none;
                }
                QPushButton:hover {
                    color: #00FF00;
                }
                """)
                random_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                random_button.clicked.connect(lambda checked, p=preset: self.show_roulette(p))
                preset_header_layout.addWidget(preset_label)
                preset_header_layout.addStretch()
                preset_header_layout.addWidget(random_button)
            else:
                preset_header_layout.addWidget(preset_label)
            self.mini_container_layout.addLayout(preset_header_layout)

            for index, command in enumerate(preset.commands):
                frame = QtWidgets.QFrame()
                frame_layout = QtWidgets.QHBoxLayout(frame)
                frame_layout.setContentsMargins(5, 5, 5, 5)
                frame_layout.setSpacing(5)

                segments = parse_command_text(command.original)

                text_label = QtWidgets.QLabel()
                text = ""
                for segment_text, color in segments:
                    if color:
                        segment_text = f'<span style="color:{color};">{segment_text}</span>'
                    else:
                        segment_text = f'<span style="color:#FFFFFF;">{segment_text}</span>'
                    text += segment_text

                if command.exclude_from_random:
                    text = f"🚫 {text}"

                text_label.setText(text)
                text_label.setFont(QtGui.QFont("Segoe UI", 12))
                text_label.setTextFormat(QtCore.Qt.RichText)
                text_label.setStyleSheet("color: #FFFFFF;")
                frame_layout.addWidget(text_label)

                text_label.mouseDoubleClickEvent = lambda event, cmd=command.original, preset=preset: self.copy_command_from_mini(cmd, preset)

                frame.setStyleSheet("""
                QFrame {
                    background-color: #2D2D30;
                    border-radius: 4px;
                }
                """)

                self.mini_container_layout.addWidget(frame)

        self.mini_container_layout.addStretch()

    def copy_command_from_mini(self, cmd_text, preset):
        if preset.is_random:
            commands = [cmd for cmd in preset.commands if not cmd.exclude_from_random]
            if not commands:
                QtWidgets.QMessageBox.warning(self, "Внимание", "Нет команд для выбора в рандоме.")
                return
            command = random.choice(commands)
            processed_command = evaluate_code_snippets(command.original, self.variables)
        else:
            processed_command = evaluate_code_snippets(cmd_text, self.variables)
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(processed_command)

    def show_roulette(self, preset):
        commands = [cmd for cmd in preset.commands if not cmd.exclude_from_random]
        if not commands:
            QtWidgets.QMessageBox.warning(self, "Внимание", "Нет команд для выбора в рандоме.")
            return

        roulette_window = QtWidgets.QDialog(self)
        roulette_window.setWindowTitle("Рулетка")
        roulette_window.setGeometry(100, 100, 1000, 700)
        roulette_window.setModal(True)
        roulette_window.setWindowIcon(QtGui.QIcon('scrpt.png'))
        roulette_window.setStyleSheet("""
        QDialog {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        QLabel {
            color: #FFFFFF;
            font-size: 24px;
        }
        """)
        roulette_layout = QtWidgets.QVBoxLayout(roulette_window)

        roulette_label = QtWidgets.QLabel("")
        roulette_label.setAlignment(QtCore.Qt.AlignCenter)
        roulette_label.setFont(QtGui.QFont("Segoe UI", 24, QtGui.QFont.Bold))
        roulette_layout.addWidget(roulette_label)

        def spin_roulette():
            self.roulette_timer = QtCore.QTimer()
            self.spin_count = 0
            max_spins = 30

            def update_label():
                self.spin_count += 1
                command = random.choice(commands)
                processed_command = evaluate_code_snippets(command.original, self.variables)
                roulette_label.setText(processed_command)
                if self.spin_count >= max_spins:
                    self.roulette_timer.stop()
                    clipboard = QtWidgets.QApplication.clipboard()
                    clipboard.setText(processed_command)
                    time.sleep(0.5)
                    roulette_window.accept()

            self.roulette_timer.timeout.connect(update_label)
            self.roulette_timer.start(100)

        spin_roulette()
        roulette_window.exec_()

    def copy_to_clipboard(self, text):
        processed_text = evaluate_code_snippets(text, self.variables)
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(processed_text)

    def open_settings_window(self):
        settings_window = QtWidgets.QDialog(self)
        settings_window.setWindowTitle("Настройки")
        settings_window.setGeometry(100, 100, 400, 500)
        settings_window.setWindowIcon(QtGui.QIcon('scrpt.png'))
        settings_window.setStyleSheet("""
        QDialog {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        QLabel, QPushButton, QLineEdit, QCheckBox, QListWidget {
            background-color: transparent;
            color: #FFFFFF;
            font-size: 16px;
        }
        QLineEdit {
            background-color: #2D2D30;
            border: 1px solid #3E3E42;
            padding: 6px;
            border-radius: 4px;
        }
        QListWidget {
            background-color: #2D2D30;
            border: 1px solid #3E3E42;
            border-radius: 4px;
        }
        QListWidget::item:selected {
            background-color: #3E3E42;
        }
        QListWidget::item:hover {
            background-color: #45454A;
        }
        QPushButton {
            color: #FFFFFF;
            background-color: #2D2D30;
            border: 1px solid #3E3E42;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #3E3E42;
        }
        QPushButton:pressed {
            background-color: #2D2D30;
        }
        QCheckBox {
            color: #FFFFFF;
            background-color: transparent;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        QCheckBox::indicator:unchecked {
            image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAAI0lEQVQoU2NkwAT/gYGB4T8GNJCYgWBANgKDE5YMyAkAYpYBAHnbBxjGSE+jAAAAAElFTkSuQmCC);
        }
        QCheckBox::indicator:checked {
            image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAAO0lEQVQoU2NkwA78x4GBgUGBiYFALwEyDLEIGhGgQiZBEliLGDAIEqQZA0EwDAgNYZAAMUBAQZ6oGYDAAAAABJRU5ErkJggg==);
        }
        """)
        settings_layout = QtWidgets.QVBoxLayout(settings_window)

        miniapp_layout = QtWidgets.QHBoxLayout()
        miniapp_label = QtWidgets.QLabel("Показывать Miniapp:")
        miniapp_checkbox = QtWidgets.QCheckBox()
        miniapp_checkbox.setChecked(self.miniapp_visible)
        miniapp_checkbox.stateChanged.connect(self.toggle_miniapp_checkbox)
        miniapp_layout.addWidget(miniapp_label)
        miniapp_layout.addWidget(miniapp_checkbox)
        settings_layout.addLayout(miniapp_layout)

        discord_button = QtWidgets.QPushButton("🌐 Перейти в Discord-сервер")
        discord_button.clicked.connect(self.open_discord_link)
        discord_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        settings_layout.addWidget(discord_button)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        settings_layout.addWidget(separator)

        variables_label = QtWidgets.QLabel("Переменные:")
        variables_label.setFont(QtGui.QFont("Segoe UI", 18, QtGui.QFont.Bold))
        settings_layout.addWidget(variables_label)

        variables_list = QtWidgets.QListWidget()
        self.variables_list_widget = variables_list
        self.update_variables_list()
        settings_layout.addWidget(variables_list)

        variables_buttons_layout = QtWidgets.QHBoxLayout()
        add_var_button = QtWidgets.QPushButton("➕ Добавить переменную")
        add_var_button.clicked.connect(lambda: self.add_variable_window(settings_window))
        add_var_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        del_var_button = QtWidgets.QPushButton("➖ Удалить переменную")
        del_var_button.clicked.connect(self.delete_variable)
        del_var_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        variables_buttons_layout.addWidget(add_var_button)
        variables_buttons_layout.addWidget(del_var_button)
        settings_layout.addLayout(variables_buttons_layout)

        variables_list.itemDoubleClicked.connect(self.edit_variable)

        separator2 = QtWidgets.QFrame()
        separator2.setFrameShape(QtWidgets.QFrame.HLine)
        separator2.setFrameShadow(QtWidgets.QFrame.Sunken)
        settings_layout.addWidget(separator2)

        footer_layout = QtWidgets.QHBoxLayout()
        author_button = QtWidgets.QPushButton("Автор: meowhiks")
        author_button.clicked.connect(self.open_author_link)
        author_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        version_button = QtWidgets.QPushButton("Версия: 1.1137 Beta")
        version_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        footer_layout.addWidget(author_button)
        footer_layout.addWidget(version_button)
        settings_layout.addLayout(footer_layout)

        close_button = QtWidgets.QPushButton("Закрыть")
        close_button.clicked.connect(settings_window.close)
        close_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        settings_layout.addWidget(close_button)

        settings_window.exec_()

    def open_discord_link(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://discord.gg/NCVT4CyUgu"))

    def open_author_link(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://t.me/serverforkittens"))
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://t.me/meowka_a_ui"))

    def update_variables_list(self):
        self.variables_list_widget.clear()
        for var_name, var_value in self.variables.items():
            self.variables_list_widget.addItem(f"{var_name} = {var_value}")

    def add_variable_window(self, parent_window):
        var_window = QtWidgets.QDialog(parent_window)
        var_window.setWindowTitle("Добавить переменную")
        var_window.setGeometry(100, 100, 300, 200)
        var_window.setWindowIcon(QtGui.QIcon('scrpt.png'))
        var_window.setStyleSheet(parent_window.styleSheet())
        var_layout = QtWidgets.QVBoxLayout(var_window)

        var_name_label = QtWidgets.QLabel("Имя переменной:")
        var_layout.addWidget(var_name_label)
        var_name_entry = QtWidgets.QLineEdit()
        var_layout.addWidget(var_name_entry)

        var_value_label = QtWidgets.QLabel("Значение переменной:")
        var_layout.addWidget(var_value_label)
        var_value_entry = QtWidgets.QLineEdit()
        var_layout.addWidget(var_value_entry)

        save_button = QtWidgets.QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.save_variable(var_name_entry.text(), var_value_entry.text(), var_window))
        save_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        var_layout.addWidget(save_button)

        var_window.exec_()

    def save_variable(self, name, value, window):
        if name and value:
            self.variables[name] = value
            self.update_variables_list()
            self.save_variables()
            window.close()
        else:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Пожалуйста, введите имя и значение переменной.")

    def delete_variable(self):
        selected_items = self.variables_list_widget.selectedItems()
        if selected_items:
            var_text = selected_items[0].text()
            var_name = var_text.split('=')[0].strip()
            del self.variables[var_name]
            self.update_variables_list()
            self.save_variables()
        else:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Пожалуйста, выберите переменную для удаления.")

    def edit_variable(self, item):
        var_text = item.text()
        var_name = var_text.split('=')[0].strip()
        var_value = self.variables[var_name]

        var_window = QtWidgets.QDialog(self)
        var_window.setWindowTitle("Редактировать переменную")
        var_window.setGeometry(100, 100, 300, 200)
        var_window.setWindowIcon(QtGui.QIcon('scrpt.png'))
        var_window.setStyleSheet(self.styleSheet())
        var_layout = QtWidgets.QVBoxLayout(var_window)

        var_name_label = QtWidgets.QLabel("Имя переменной:")
        var_layout.addWidget(var_name_label)
        var_name_entry = QtWidgets.QLineEdit()
        var_name_entry.setText(var_name)
        var_name_entry.setDisabled(True)
        var_layout.addWidget(var_name_entry)

        var_value_label = QtWidgets.QLabel("Значение переменной:")
        var_layout.addWidget(var_value_label)
        var_value_entry = QtWidgets.QLineEdit()
        var_value_entry.setText(var_value)
        var_layout.addWidget(var_value_entry)

        save_button = QtWidgets.QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.save_variable(var_name, var_value_entry.text(), var_window))
        save_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        var_layout.addWidget(save_button)

        var_window.exec_()

    def toggle_miniapp_checkbox(self, state):
        self.miniapp_visible = bool(state)
        if self.miniapp_visible:
            self.mini_widget.show()
        else:
            self.mini_widget.hide()

    def toggle_miniapp(self):
        self.miniapp_visible = not self.miniapp_visible
        if self.miniapp_visible:
            self.mini_widget.show()
        else:
            self.mini_widget.hide()

    def add_preset_window(self):
        preset_window = QtWidgets.QDialog(self)
        preset_window.setWindowTitle("Добавить новый пресет")
        preset_window.setGeometry(100, 100, 300, 150)
        preset_window.setWindowIcon(QtGui.QIcon('scrpt.png'))
        preset_window.setStyleSheet(self.styleSheet())
        preset_layout = QtWidgets.QVBoxLayout(preset_window)

        name_label = QtWidgets.QLabel("Название пресета:")
        preset_layout.addWidget(name_label)
        name_entry = QtWidgets.QLineEdit()
        preset_layout.addWidget(name_entry)

        add_button = QtWidgets.QPushButton("Добавить пресет")
        add_button.clicked.connect(lambda: self.add_preset(name_entry.text(), preset_window))
        add_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        preset_layout.addWidget(add_button)

        preset_window.exec_()

    def add_preset(self, name, window):
        if name:
            preset = Preset(name)
            self.presets.append(preset)
            self.update_preset_list()
            self.save_presets()
            self.update_mini_widget_commands()
            window.close()
        else:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Пожалуйста, введите название пресета.")

    def import_preset_window(self):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Импортировать пресет", "", "Text Files (*.txt)", options=options)
        if filename:
            preset_name, ok = QtWidgets.QInputDialog.getText(self, "Импортировать пресет", "Введите название нового пресета:")
            if ok and preset_name:
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    new_commands = [line.strip() for line in lines if line.strip()]
                    if new_commands:
                        new_preset = Preset(preset_name)
                        new_preset.commands = [Command(cmd) for cmd in new_commands]
                        self.presets.append(new_preset)
                        self.update_preset_list()
                        self.save_presets()
                        self.update_mini_widget_commands()
                        QtWidgets.QMessageBox.information(self, "Импорт завершен", f"Пресет '{preset_name}' успешно импортирован.")
                    else:
                        QtWidgets.QMessageBox.warning(self, "Внимание", "Файл не содержит команд для импорта.")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать пресет: {str(e)}")
            else:
                QtWidgets.QMessageBox.warning(self, "Внимание", "Импорт пресета отменен.")

    def update_preset_list(self):
        self.preset_listbox.clear()
        for preset in self.presets:
            item_text = preset.name
            if preset.is_random:
                item_text += " (Рандом)"
            self.preset_listbox.addItem(item_text)

    def on_preset_select(self):
        selected_items = self.preset_listbox.selectedItems()
        if selected_items:
            self.selected_preset_index = self.preset_listbox.row(selected_items[0])
            self.show_preset_commands()

    def on_preset_right_click(self, position):
        indexes = self.preset_listbox.selectedIndexes()
        if indexes:
            index = indexes[0].row()
            preset = self.presets[index]

            menu = QtWidgets.QMenu()
            delete_action = menu.addAction("Удалить пресет")
            if preset.is_random:
                toggle_random_action = menu.addAction("Убрать рандом")
            else:
                toggle_random_action = menu.addAction("Сделать рандомным")
            export_action = menu.addAction("Экспортировать пресет")
            import_action = menu.addAction("Импортировать в пресет")
            action = menu.exec_(self.preset_listbox.viewport().mapToGlobal(position))
            if action == delete_action:
                reply = QtWidgets.QMessageBox.question(self, 'Удалить пресет',
                    f"Вы действительно хотите удалить пресет '{preset.name}'?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.Yes:
                    del self.presets[index]
                    self.update_preset_list()
                    self.save_presets()
                    self.update_mini_widget_commands()
                    self.clear_commands_display()
            elif action == toggle_random_action:
                preset.is_random = not preset.is_random
                self.save_presets()
                self.update_preset_list()
                self.show_preset_commands()
                self.update_mini_widget_commands()
            elif action == export_action:
                self.export_preset(preset)
            elif action == import_action:
                self.import_preset_into_existing_preset(preset)
            else:
                pass

    def clear_commands_display(self):
        while self.commands_container_layout.count():
            item = self.commands_container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def show_preset_commands(self):
        self.clear_commands_display()
        preset = self.presets[self.selected_preset_index]
        self.preset_name_label.setText(preset.name)

        self.current_commands = preset.commands
        self.command_frames = []
        self.selected_command_index = None
        self.selected_command = None

        for index, command in enumerate(self.current_commands):
            self.display_command(command, index)

        self.commands_container_layout.addStretch()

    def display_command(self, command, index):
        frame = QtWidgets.QFrame()
        frame_layout = QtWidgets.QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(10)

        segments = parse_command_text(command.original)

        text_label = QtWidgets.QLabel()
        text = ""
        for segment_text, color in segments:
            if color:
                segment_text = f'<span style="color:{color};">{segment_text}</span>'
            else:
                segment_text = f'<span style="color:#FFFFFF;">{segment_text}</span>'
            text += segment_text

        if command.exclude_from_random:
            text = f"🚫 {text}"

        text_label.setText(text)
        text_label.setFont(QtGui.QFont("Segoe UI", 16))
        text_label.setTextFormat(QtCore.Qt.RichText)
        text_label.setStyleSheet("color: #FFFFFF;")
        frame_layout.addWidget(text_label)

        def on_enter():
            if self.selected_command_index == index:
                frame.setStyleSheet("""
                background-color: #262626;
                border-top: 1px solid orange;
                border-bottom: 1px solid orange;
                border-radius: 0px;
                """)
            else:
                frame.setStyleSheet("""
                background-color: #262626;
                border-radius: 0px;
                """)

        def on_leave():
            if self.selected_command_index == index:
                frame.setStyleSheet("""
                background-color: #262626;
                border-top: 1px solid orange;
                border-bottom: 1px solid orange;
                border-radius: 0px;
                """)
            else:
                frame.setStyleSheet("""
                background-color: #2D2D30;
                border: none;
                border-radius: 0px;
                """)

        frame.enterEvent = lambda event: on_enter()
        frame.leaveEvent = lambda event: on_leave()


        frame.mousePressEvent = lambda event: self.select_command(index)
        text_label.mousePressEvent = lambda event: self.select_command(index)

        frame.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        frame.customContextMenuRequested.connect(lambda pos: self.on_command_right_click(pos, index))


        frame.setStyleSheet("""
        background-color: #2D2D30;
        border: none;
        border-radius: 0px;
        """)

        self.commands_container_layout.addWidget(frame)
        self.command_frames.append((index, frame))

    def select_command(self, index):
        self.selected_command_index = index
        preset = self.presets[self.selected_preset_index]
        self.selected_command = preset.commands[index]

        for idx, frame in self.command_frames:
            if idx == index:
                frame.setStyleSheet("""
                background-color: #262626;
                border-top: 1px solid orange;
                border-bottom: 1px solid orange;
                border-radius: 0px;
                """)
            else:
                frame.setStyleSheet("""
                background-color: #2D2D30;
                border: none;
                border-radius: 0px;
                """)

    def on_command_right_click(self, position, index):
        preset = self.presets[self.selected_preset_index]
        command = preset.commands[index]

        menu = QtWidgets.QMenu()
        copy_action = menu.addAction("Копировать")
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")
        sequence_action = menu.addAction("Изменить последовательность")
        if command.exclude_from_random:
            toggle_exclude_action = menu.addAction("Включить в рандом")
        else:
            toggle_exclude_action = menu.addAction("Исключить из рандома")
        action = menu.exec_(QtGui.QCursor.pos())
        if action == copy_action:
            self.copy_command(index)
        elif action == edit_action:
            self.edit_command(index)
        elif action == delete_action:
            self.delete_command(index)
        elif action == sequence_action:
            self.edit_sequence_command(index)
        elif action == toggle_exclude_action:
            command.exclude_from_random = not command.exclude_from_random
            self.save_presets()
            self.show_preset_commands()
            self.update_mini_widget_commands()
    
    def add_command(self):
        if self.selected_preset_index is None:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Пожалуйста, выберите пресет для добавления команды.")
            return

        command_text = self.new_command_entry.text()
        if command_text:
            preset = self.presets[self.selected_preset_index]
            command = Command(command_text)
            preset.commands.append(command)
            self.show_preset_commands()
            self.new_command_entry.clear()
            self.update_mini_widget_commands()
            self.save_presets()
        else:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Пожалуйста, введите команду.")

    def copy_command(self, index):
        preset = self.presets[self.selected_preset_index]

        if preset.is_random:
            commands = [cmd for cmd in preset.commands if not cmd.exclude_from_random]
            if not commands:
                QtWidgets.QMessageBox.warning(self, "Внимание", "Нет команд для выбора в рандоме.")
                return
            command = random.choice(commands)
        else:
            command = preset.commands[index]

        processed_command = evaluate_code_snippets(command.original, self.variables)
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(processed_command)
        self.selected_command = command

    def edit_command(self, index):
        preset = self.presets[self.selected_preset_index]
        command = preset.commands[index]

        edit_window = QtWidgets.QDialog(self)
        edit_window.setWindowTitle("Редактировать команду")
        edit_window.setGeometry(100, 100, 500, 200)
        edit_window.setWindowIcon(QtGui.QIcon('scrpt.png'))
        edit_window.setStyleSheet(self.styleSheet())
        edit_layout = QtWidgets.QVBoxLayout(edit_window)

        command_label = QtWidgets.QLabel("Редактировать команду:")
        edit_layout.addWidget(command_label)
        command_entry = QtWidgets.QLineEdit()
        command_entry.setText(command.original)
        edit_layout.addWidget(command_entry)

        save_button = QtWidgets.QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.save_edited_command(command_entry.text(), command, edit_window))
        save_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        edit_layout.addWidget(save_button)

        edit_window.exec_()

    def save_edited_command(self, new_text, command, window):
        if new_text:
            command.original = new_text
            self.show_preset_commands()
            self.update_mini_widget_commands()
            self.save_presets()
            window.close()
        else:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Пожалуйста, введите команду.")

    def delete_command(self, index):
        preset = self.presets[self.selected_preset_index]
        del preset.commands[index]
        self.show_preset_commands()
        self.update_mini_widget_commands()
        self.save_presets()
        if self.selected_command_index == index:
            self.selected_command_index = None
            self.selected_command = None

    def edit_sequence_command(self, index):
        preset = self.presets[self.selected_preset_index]
        command = preset.commands[index]

        edit_window = QtWidgets.QDialog(self)
        edit_window.setWindowTitle("Редактировать последовательность")
        edit_window.setGeometry(100, 100, 500, 200)
        edit_window.setWindowIcon(QtGui.QIcon('scrpt.png'))
        edit_window.setStyleSheet(self.styleSheet())
        edit_layout = QtWidgets.QVBoxLayout(edit_window)

        sequence_label = QtWidgets.QLabel("Редактировать последовательность (разделенные запятыми):")
        edit_layout.addWidget(sequence_label)
        sequence_entry = QtWidgets.QLineEdit()
        sequence_entry.setText(', '.join(command.sequence or self.default_sequence))
        edit_layout.addWidget(sequence_entry)

        save_button = QtWidgets.QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.save_sequence(sequence_entry.text(), command, edit_window))
        save_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        edit_layout.addWidget(save_button)

        edit_window.exec_()

    def save_sequence(self, sequence_text, command, window):
        if sequence_text:
            new_sequence = [s.strip() for s in sequence_text.split(',')]
            command.sequence = new_sequence
            self.save_presets()
            window.close()
        else:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Пожалуйста, введите последовательность.")

    def edit_default_sequence(self):
        edit_window = QtWidgets.QDialog(self)
        edit_window.setWindowTitle("Редактировать последовательность по умолчанию")
        edit_window.setGeometry(100, 100, 500, 200)
        edit_window.setWindowIcon(QtGui.QIcon('scrpt.png'))
        edit_window.setStyleSheet(self.styleSheet())
        edit_layout = QtWidgets.QVBoxLayout(edit_window)

        sequence_label = QtWidgets.QLabel("Редактировать последовательность по умолчанию (разделенные запятыми):")
        edit_layout.addWidget(sequence_label)
        sequence_entry = QtWidgets.QLineEdit()
        sequence_entry.setText(', '.join(self.default_sequence))
        edit_layout.addWidget(sequence_entry)

        save_button = QtWidgets.QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.save_default_sequence(sequence_entry.text(), edit_window))
        save_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        edit_layout.addWidget(save_button)

        edit_window.exec_()

    def save_default_sequence(self, sequence_text, window):
        if sequence_text:
            self.default_sequence = [s.strip() for s in sequence_text.split(',')]
            window.close()
        else:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Пожалуйста, введите последовательность.")

    def save_presets(self):
        data = [preset.to_dict() for preset in self.presets]
        with open('presets.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self.update_mini_widget_commands() 

    def load_presets(self):
        if os.path.exists('presets.json'):
            with open('presets.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.presets = [Preset.from_dict(preset_data) for preset_data in data]
            self.update_preset_list()
            self.update_mini_widget_commands()

    def export_preset(self, preset):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить пресет", preset.name + ".txt", "Text Files (*.txt)", options=options)
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for command in preset.commands:
                        f.write(command.original + '\n')
                QtWidgets.QMessageBox.information(self, "Экспорт завершен", f"Пресет '{preset.name}' успешно экспортирован.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать пресет: {str(e)}")

    def import_preset_into_existing_preset(self, preset):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Импортировать в пресет", "", "Text Files (*.txt)", options=options)
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                new_commands = [line.strip() for line in lines if line.strip()]
                if new_commands:
                    reply = QtWidgets.QMessageBox.question(self, 'Импорт в пресет',
                        "Вы хотите заменить существующие команды или добавить новые?\nВыберите 'Да' для замены, 'Нет' для добавления.",
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                        QtWidgets.QMessageBox.No)
                    if reply == QtWidgets.QMessageBox.Yes:
                        preset.commands = [Command(cmd) for cmd in new_commands]
                    else:
                        preset.commands.extend([Command(cmd) for cmd in new_commands])
                    self.show_preset_commands()
                    self.save_presets()
                    self.update_mini_widget_commands()
                    QtWidgets.QMessageBox.information(self, "Импорт завершен", f"Команды успешно импортированы в пресет '{preset.name}'.")
                else:
                    QtWidgets.QMessageBox.warning(self, "Внимание", "Файл не содержит команд для импорта.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать команды: {str(e)}")

    def save_variables(self):
        with open('variables.json', 'w', encoding='utf-8') as f:
            json.dump(self.variables, f, ensure_ascii=False, indent=4)

    def load_variables(self):
        if os.path.exists('variables.json'):
            with open('variables.json', 'r', encoding='utf-8') as f:
                self.variables = json.load(f)

    def closeEvent(self, event):
        self.mini_widget.close()
        QtWidgets.QApplication.quit()
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    preset_app = PresetApp()
    preset_app.show()
    sys.exit(app.exec_())