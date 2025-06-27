import sys
import json
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QScrollArea,
    QMessageBox, QFileDialog, QColorDialog, QDialog, QDialogButtonBox, QFormLayout,
    QComboBox, QTabWidget, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, QMimeData, QSize
from PyQt6.QtGui import QDrag, QColor, QBrush, QFont
from PyQt6.QtGui import QIcon


class Teacher:
    def __init__(self, name, subject, color):
        self.name = name
        self.subject = subject
        self.color = color


class TeacherEditDialog(QDialog):
    def __init__(self, teacher, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit or Delete Teacher")
        self.teacher = teacher
        self.selected_color = teacher.color
        layout = QFormLayout(self)

        self.name_input = QLineEdit(teacher.name)
        self.subject_input = QLineEdit(teacher.subject)
        self.color_btn = QPushButton()
        self.update_color_btn()
        self.color_btn.clicked.connect(self.pick_color)

        layout.addRow("Name:", self.name_input)
        layout.addRow("Subject:", self.subject_input)
        layout.addRow("Subject Color:", self.color_btn)

        buttons = QDialogButtonBox()
        self.modify_btn = buttons.addButton("Modify", QDialogButtonBox.ButtonRole.AcceptRole)
        self.delete_btn = buttons.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.modify_btn.clicked.connect(self.modify_clicked)
        self.delete_btn.clicked.connect(self.delete_clicked)
        layout.addWidget(buttons)

        self.action = None

    def update_color_btn(self):
        c = self.selected_color.name()
        self.color_btn.setStyleSheet(f"background-color: {c}; color: white; font-weight: 600; padding: 6px; border-radius: 4px;")

    def pick_color(self):
        color = QColorDialog.getColor(initial=self.selected_color, parent=self)
        if color.isValid():
            self.selected_color = color
            self.update_color_btn()

    def modify_clicked(self):
        if not self.name_input.text().strip() or not self.subject_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Please enter both name and subject.")
            return
        self.action = "modify"
        self.accept()

    def delete_clicked(self):
        confirm = QMessageBox.question(self, "Confirm Delete", f"Delete teacher '{self.teacher.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.action = "delete"
            self.accept()


class TeacherList(QListWidget):
    def __init__(self, teachers, parent):
        super().__init__()
        self.setDragEnabled(True)
        self.teachers = teachers
        self.parent = parent
        self.itemDoubleClicked.connect(self.edit_teacher_dialog)
        self.setStyleSheet("""
            QListWidget {
                background-color: #2e2e2e;
                border-radius: 8px;
                color: white;
                font-size: 14px;
            }
            QListWidget::item:selected {
                background-color: #5a9bd8;
                color: white;
            }
        """)


    def startDrag(self, dropActions):
        item = self.currentItem()
        if item:
            key = item.data(Qt.ItemDataRole.UserRole)
            if key:
                mime_data = QMimeData()
                mime_data.setText(key)
                drag = QDrag(self)
                drag.setMimeData(mime_data)
                drag.exec()

    def add_teacher(self, teacher):
        key = f"{teacher.name}|{teacher.subject}"
        self.teachers[key] = teacher
        item = QListWidgetItem(f"{teacher.name} ({teacher.subject})")
        item.setForeground(QBrush(Qt.GlobalColor.white))
        item.setBackground(QBrush(teacher.color))
        item.setData(Qt.ItemDataRole.UserRole, key)
        self.addItem(item)

    def update_teacher_item(self, old_key, new_teacher):
        if old_key != f"{new_teacher.name}|{new_teacher.subject}":
            self.teachers.pop(old_key, None)
            new_key = f"{new_teacher.name}|{new_teacher.subject}"
            self.teachers[new_key] = new_teacher
            for i in range(self.count()):
                item = self.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == old_key:
                    item.setText(f"{new_teacher.name} ({new_teacher.subject})")
                    item.setBackground(QBrush(new_teacher.color))
                    item.setForeground(QBrush(Qt.GlobalColor.white))
                    item.setData(Qt.ItemDataRole.UserRole, new_key)
                    # Fix style shape by resetting stylesheet or item flags if needed:
                    item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                    break


    def edit_teacher_dialog(self, item):
        old_key = item.data(Qt.ItemDataRole.UserRole)
        if not old_key or old_key not in self.teachers:
            return
        teacher = self.teachers[old_key]
        dialog = TeacherEditDialog(teacher, self)
        if dialog.exec():
            if dialog.action == "modify":
                new_name = dialog.name_input.text().strip().title()
                new_subject = dialog.subject_input.text().strip().title()
                new_color = dialog.selected_color
                new_teacher = Teacher(new_name, new_subject, new_color)
                self.update_teacher_item(old_key, new_teacher)
                for grade_tab in self.parent.all_tables.values():
                    for class_table in grade_tab["tables"].values():
                        for row in range(class_table.rowCount()):
                            for col in range(class_table.columnCount()):
                                cell = class_table.item(row, col)
                                if cell.data(Qt.ItemDataRole.UserRole) == old_key:
                                    cell.setText(new_name)
                                    cell.setBackground(QBrush(new_color))
                                    cell.setForeground(QBrush(Qt.GlobalColor.white))
                                    cell.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                                    cell.setData(Qt.ItemDataRole.UserRole, f"{new_name}|{new_subject}")
                                    
            elif dialog.action == "delete":
                del self.teachers[old_key]
                self.takeItem(self.row(item))
                for grade_tab in self.parent.all_tables.values():
                    for class_table in grade_tab["tables"].values():
                        for row in range(class_table.rowCount()):
                            for col in range(class_table.columnCount()):
                                cell = class_table.item(row, col)
                                if cell.data(Qt.ItemDataRole.UserRole) == old_key:
                                    cell.setText("")
                                    cell.setBackground(QBrush(Qt.GlobalColor.transparent))
                                    cell.setForeground(QBrush(Qt.GlobalColor.black))
                                    cell.setFont(QFont())
                                    cell.setData(Qt.ItemDataRole.UserRole, None)


class TimetableCell(QTableWidgetItem):
    def __init__(self):
        super().__init__("")
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

class TimetableTable(QTableWidget):
    def __init__(self, class_name, all_tables_ref, teachers):
        super().__init__(8, 5)
        self.class_name = class_name
        self.all_tables_ref = all_tables_ref
        self.teachers = teachers
        self.setAcceptDrops(True)
        self.setHorizontalHeaderLabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
        self.setVerticalHeaderLabels([f'P{i+1}' for i in range(8)])
        self.init_table()
        self.setMinimumSize(QSize(480, 320))
        self.cellDoubleClicked.connect(self.cell_double_clicked)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1f1f1f;
                gridline-color: #444;
                font-family: "Segoe UI";
                font-size: 12pt;
                color: white;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: white;
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #5a9bd8;
                color: white;
            }
        """)

    def init_table(self):
        for r in range(8):
            for c in range(5):
                cell = TimetableCell()
                cell.setData(Qt.ItemDataRole.UserRole, None)
                self.setItem(r, c, cell)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        key = event.mimeData().text()
        if not key or '|' not in key:
            return
        name, subject = key.split("|", 1)
        idx = self.indexAt(event.position().toPoint())
        if idx.row() == -1 or idx.column() == -1:
            return

        # Check conflicts in all tables in all grades
        for grade_info in self.all_tables_ref.values():
            for tab in grade_info["tables"].values():
                cell = tab.item(idx.row(), idx.column())
                if cell.text():
                    existing_key = cell.data(Qt.ItemDataRole.UserRole)
                    if existing_key:
                        existing_name, _ = existing_key.split("|", 1)
                        if existing_name == name:
                            QMessageBox.warning(self, "Conflict", f"Teacher {name} is already assigned at this time slot in another class.")
                            return

        cell = self.item(idx.row(), idx.column())
        teacher = self.teachers.get(key)
        cell.setText(name if teacher else "")
        if teacher:
            cell.setBackground(QBrush(teacher.color))
            cell.setForeground(QBrush(Qt.GlobalColor.white))
            cell.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        else:
            cell.setBackground(QBrush(Qt.GlobalColor.transparent))
            cell.setForeground(QBrush(Qt.GlobalColor.black))
            cell.setFont(QFont())
        cell.setData(Qt.ItemDataRole.UserRole, key)
        event.acceptProposedAction()

    def cell_double_clicked(self, row, col):
        cell = self.item(row, col)
        if cell.text():
            cell.setText("")
            cell.setBackground(QBrush(Qt.GlobalColor.transparent))
            cell.setForeground(QBrush(Qt.GlobalColor.black))
            cell.setFont(QFont())
            cell.setData(Qt.ItemDataRole.UserRole, None)

    def get_data(self):
        return [[self.item(r, c).data(Qt.ItemDataRole.UserRole) or "" for c in range(5)] for r in range(8)]

    def set_data(self, data):
        for r in range(8):
            for c in range(5):
                key = data[r][c]
                cell = self.item(r, c)
                if key:
                    name, subject = key.split("|", 1)
                    teacher = self.teachers.get(key)
                    if teacher:
                        cell.setText(name)
                        cell.setBackground(QBrush(teacher.color))
                        cell.setForeground(QBrush(Qt.GlobalColor.white))
                        cell.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                        cell.setData(Qt.ItemDataRole.UserRole, key)
                    else:
                        cell.setText("")
                        cell.setData(Qt.ItemDataRole.UserRole, None)
                else:
                    cell.setText("")
                    cell.setData(Qt.ItemDataRole.UserRole, None)


def normalize_class_name(name):
    name = name.strip().upper()
    match = re.match(r"(\d+)\s*[-\s]?\s*([A-Z])", name)
    if match:
        return f"{int(match.group(1))}-{match.group(2)}"
    else:
        return name.replace(" ", "-").upper()

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import QComboBox


from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QTextEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt


class AbsentTeacherDialog(QDialog):
    def __init__(self, teachers, all_tables, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Absent Teacher Analysis")
        self.setStyleSheet("color: white; background-color: #2c3e50; font-family: 'Segoe UI';")
        self.setFixedSize(650, 470)

        self.teachers = teachers
        self.all_tables = all_tables

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        label_style = "font-size: 10pt; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;"

        # Row layout: Teacher name and Day selector
        input_row = QHBoxLayout()
        input_row.setSpacing(15)

        name_label = QLabel("Teacher:")
        name_label.setFixedWidth(50) 
        name_label.setStyleSheet(label_style)
        input_row.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setFixedSize(230, 30)
        input_row.addWidget(self.name_input)

        day_label = QLabel("Day:")
        day_label.setFixedWidth(30)
        day_label.setStyleSheet(label_style)
        input_row.addWidget(day_label)

        self.day_combo = QComboBox()
        self.day_combo.addItems(["Any", "Mon", "Tue", "Wed", "Thu", "Fri"])
        self.day_combo.setFixedSize(120, 30)
        input_row.addWidget(self.day_combo)

        layout.addLayout(input_row)

        # Result box
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setFixedSize(600, 260)
        self.result_box.setStyleSheet("""
            background-color: #34495e;
            border-radius: 6px;
            font-size: 10pt;
            padding: 8px;
        """)
        layout.addWidget(self.result_box)

        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.addStretch()

        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.setFixedSize(120, 36)
        self.analyze_btn.setStyleSheet(self._button_style("#2980b9", "#1c5980", "#145374"))
        self.analyze_btn.clicked.connect(self.analyze_absent_teacher)
        btn_layout.addWidget(self.analyze_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedSize(120, 36)
        self.clear_btn.setStyleSheet(self._button_style("#e67e22", "#d35400", "#b34700"))
        self.clear_btn.clicked.connect(self.clear_data)
        btn_layout.addWidget(self.clear_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedSize(120, 36)
        self.close_btn.setStyleSheet(self._button_style("#c0392b", "#e74c3c", "#922b21"))
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _button_style(self, base, hover, press):
        return f"""
            QPushButton {{
                font-size: 10pt;
                font-weight: bold;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                padding: 6px 18px;
                background-color: {base};
                color: white;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {press};
            }}
        """

    def analyze_absent_teacher(self):
        name_input = self.name_input.text().strip().title()
        selected_day = self.day_combo.currentText()

        if not name_input:
            QMessageBox.warning(self, "Input Error", "Please enter the absent teacher's name.")
            return

        matched_key = None
        subject = None

        for key, teacher in self.teachers.items():
            if teacher.name == name_input:
                matched_key = key
                subject = teacher.subject
                break

        if not matched_key:
            QMessageBox.warning(self, "Not Found", f"No teacher named '{name_input}' found.")
            return

        result_lines = []
        day_map = ["Mon", "Tue", "Wed", "Thu", "Fri"]

        for grade, data in self.all_tables.items():
            for class_name, table in data["tables"].items():
                for r in range(8):
                    for c in range(5):
                        if selected_day != "Any" and day_map[c] != selected_day:
                            continue
                        cell = table.item(r, c)
                        if cell and cell.data(Qt.ItemDataRole.UserRole) == matched_key:
                            result_lines.append(f"📌 {class_name} - {day_map[c]} P{r+1}:")

                            replacements = []
                            for alt_key, alt_teacher in self.teachers.items():
                                if alt_key == matched_key or alt_teacher.subject != subject:
                                    continue
                                busy = False
                                for g in self.all_tables.values():
                                    for t in g["tables"].values():
                                        other_cell = t.item(r, c)
                                        if other_cell and other_cell.data(Qt.ItemDataRole.UserRole) == alt_key:
                                            busy = True
                                            break
                                    if busy:
                                        break
                                if not busy:
                                    replacements.append(alt_teacher.name)

                            if replacements:
                                result_lines.append("   🔁 Replacements: " + ", ".join(replacements))
                            else:
                                result_lines.append("   ⚠️ No replacements available.")

        if not result_lines:
            self.result_box.setText("✅ No assigned periods found for this teacher on selected day.")
        else:
            self.result_box.setText("\n".join(result_lines))

    def clear_data(self):
        self.name_input.clear()
        self.day_combo.setCurrentIndex(0)
        self.result_box.clear()

    




class FilterDialog(QDialog):
    def __init__(self, teachers, all_tables, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter Teachers")
        self.setFixedSize(420, 580)
        self.setStyleSheet("color: white; background-color: #2c3e50; font-family: 'Segoe UI';")

        self.teachers = teachers
        self.all_tables = all_tables

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(12)

        label_style = """
            font-size: 10pt;
            font-weight: bold;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        """

        # Subject
        subject_label = QLabel("Subject:")
        subject_label.setStyleSheet(label_style)
        form_layout.addWidget(subject_label, 0, 0)

        self.subject_combo = QComboBox()
        self.subject_combo.addItem("Any")
        subjects = sorted(set(t.subject for t in self.teachers.values()))
        self.subject_combo.addItems(subjects)
        self.subject_combo.setFixedSize(170, 30)
        self.subject_combo.setStyleSheet(self._combo_style())
        form_layout.addWidget(self.subject_combo, 0, 1)

        # Day
        day_label = QLabel("Day:")
        day_label.setStyleSheet(label_style)
        form_layout.addWidget(day_label, 1, 0)

        self.day_combo = QComboBox()
        self.day_combo.addItems(["Any", "Mon", "Tue", "Wed", "Thu", "Fri"])
        self.day_combo.setFixedSize(170, 30)
        self.day_combo.setStyleSheet(self._combo_style())
        form_layout.addWidget(self.day_combo, 1, 1)

        # Period
        period_label = QLabel("Period:")
        period_label.setStyleSheet(label_style)
        form_layout.addWidget(period_label, 2, 0)

        self.period_combo = QComboBox()
        self.period_combo.addItems(["Any"] + [f"P{i}" for i in range(1, 9)])
        self.period_combo.setFixedSize(170, 30)
        self.period_combo.setStyleSheet(self._combo_style())
        form_layout.addWidget(self.period_combo, 2, 1)

        layout.addLayout(form_layout)

        # Result box (larger)
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setFixedHeight(240)
        self.result_box.setStyleSheet("""
            background-color: #34495e;
            border-radius: 6px;
            font-size: 10pt;
            padding: 6px;
        """)
        layout.addWidget(self.result_box)

        # Buttons layout
        # Buttons layout (Centered)
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setFixedSize(100, 32)
        self.filter_btn.setStyleSheet(self._button_style("#2980b9", "#1c5980", "#145374"))
        self.filter_btn.clicked.connect(self.filter_teachers)
        btn_layout.addWidget(self.filter_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedSize(100, 32)
        self.clear_btn.setStyleSheet(self._button_style("#e67e22", "#d35400", "#b34700"))
        self.clear_btn.clicked.connect(self.clear_filters)
        btn_layout.addWidget(self.clear_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedSize(100, 32)
        self.close_btn.setStyleSheet(self._button_style("#c0392b", "#e74c3c", "#922b21"))
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)


    def _combo_style(self):
        return """
            QComboBox {
                font-size: 10pt;
                padding: 4px 6px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #34495e;
                color: white;
            }
            QComboBox:hover {
                border-color: #2980b9;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
        """

    def _button_style(self, bg_color, hover_color, pressed_color):
        return f"""
            QPushButton {{
                font-size: 10pt;
                font-weight: bold;
                padding: 6px 16px;
                background-color: {bg_color};
                color: white;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """

    def filter_teachers(self):
        subject = self.subject_combo.currentText()
        day = self.day_combo.currentText()
        period = self.period_combo.currentText()

        day_to_col = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4}
        cols = range(5) if day == "Any" else [day_to_col.get(day, -1)]
        if -1 in cols:
            QMessageBox.warning(self, "Error", "Invalid day selected.")
            return

        if period == "Any":
            rows = range(8)
        else:
            try:
                rows = [int(period[1:]) - 1]
            except Exception:
                QMessageBox.warning(self, "Error", "Invalid period selected.")
                return

        busy_keys = set()
        for grade_data in self.all_tables.values():
            for table in grade_data["tables"].values():
                for row in rows:
                    for col in cols:
                        cell = table.item(row, col)
                        if cell:
                            key = cell.data(Qt.ItemDataRole.UserRole)
                            if key:
                                busy_keys.add(key)

        filtered_teachers = []
        for key, teacher in self.teachers.items():
            if subject != "Any" and teacher.subject != subject:
                continue
            if key in busy_keys:
                continue
            filtered_teachers.append(f"{teacher.name} ({teacher.subject})")

        if not filtered_teachers:
            self.result_box.setText("No available teachers found for selected filters.")
        else:
            self.result_box.setText("\n".join(filtered_teachers))

    def clear_filters(self):
        self.subject_combo.setCurrentIndex(0)
        self.day_combo.setCurrentIndex(0)
        self.period_combo.setCurrentIndex(0)
        self.result_box.clear()









class ScrollableGradeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.grid_layout)

    def add_class_widget(self, widget):
        count = self.grid_layout.count()
        row = count // 2
        col = count % 2
        self.grid_layout.addWidget(widget, row, col)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartSched(v1.5)")
        self.setWindowIcon(QIcon("C:/Users/kusal/Desktop/icon.png"))
        self.resize(1400, 820)
        self.setStyleSheet("background-color: #222222; color: white; font-family: 'Segoe UI';")

        self.teachers = {}
        self.teacher_list = TeacherList(self.teachers, self)
        self.all_tables = {}

        self.subject_color = QColor("#3498db")

        self.teacher_name_input = QLineEdit()
        self.teacher_name_input.setPlaceholderText("Teacher Name")
        self.teacher_name_input.setFixedHeight(40)
        self.teacher_name_input.setMaximumWidth(400)

        self.teacher_subject_input = QLineEdit()
        self.teacher_subject_input.setPlaceholderText("Subject")
        self.teacher_subject_input.setFixedHeight(40)
        self.teacher_subject_input.setMaximumWidth(400)

        self.color_btn = QPushButton("Pick Subject Color")
        self.color_btn.setFixedSize(310, 30)   # fixed size permanently set
        self.color_btn.setStyleSheet("""
        QPushButton {
            background-color: #2980b9;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: bold;
            font-size: 9pt;
            padding: 8px 16px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #1c5980;
        }
        """)

        self.color_btn.clicked.connect(self.pick_color)
        self.color_btn.setMaximumWidth(180)

        self.add_teacher_btn = QPushButton("Add Teacher")
        self.add_teacher_btn.setFixedWidth(260)
        self.add_teacher_btn.setStyleSheet("""
        QPushButton {
            background-color: #2980b9;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: bold;
            font-size: 9pt;
            padding: 8px;
            border-radius: 5px;
            min-width: 265px;
        }
        QPushButton:hover {
            background-color: #1c5980;
        }
        """)

        self.add_teacher_btn.clicked.connect(self.add_teacher)
        self.add_teacher_btn.setMaximumWidth(310)

        self.class_input = QLineEdit()
        self.class_input.setPlaceholderText("e.g., 6-A")
        self.class_input.setFixedHeight(40)
        self.class_input.setMaximumWidth(310)

        self.add_class_btn = QPushButton("Add Class")
        self.add_class_btn.setFixedWidth(310)
        self.add_class_btn.setStyleSheet("""
        QPushButton {
            background-color: #2980b9;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: bold;
            font-size: 9pt;
            padding: 8px 16px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #1c5980;
        }
        """)

        self.add_class_btn.clicked.connect(self.add_class)
        self.add_class_btn.setMaximumWidth(180)

        self.delete_class_combo = QComboBox()
        self.delete_class_combo.setFixedSize(140, 33)  # width=150, height=30
        
        self.delete_class_btn = QPushButton("Delete Class")
        self.delete_class_btn.setFixedWidth(155)

        self.delete_class_btn.setStyleSheet("""
        QPushButton {
            background-color: #e74c3c;
            color: white;
            border-radius: 6px;
            padding: 8px 10px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: bold;
            font-size: 9pt;

        }
        QPushButton:hover {
            background-color: #c0392b;
        }
        QPushButton:pressed {
            background-color: #922b21;
        }
    """)

        self.delete_class_btn.clicked.connect(self.delete_class)
        self.delete_class_btn.setMaximumWidth(100)

        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setMovable(True)
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                background: #333333;
                color: white;
                padding: 10px 15px;
                border-radius: 8px 8px 0 0;
                margin-right: 5px;
            }
            QTabBar::tab:selected {
                background: #5a9bd8;
                color: white;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #444444;
                border-top: none;
                background: #1f1f1f;
                border-radius: 0 8px 8px 8px;
            }
        """)

        # Wrap teacher inputs in a fixed width box
        left_inputs_box = QWidget()
        left_inputs_layout = QVBoxLayout(left_inputs_box)
        left_inputs_layout.setContentsMargins(0, 0, 0, 0)
        left_inputs_layout.setSpacing(8)
        label = QLabel("Teacher Name:")
        label.setStyleSheet("font-size: 10pt; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;")
        left_inputs_layout.addWidget(label)
        left_inputs_layout.addWidget(self.teacher_name_input)
        subject_label = QLabel("Subject:")
        subject_label.setStyleSheet("font-size: 10pt; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;")
        left_inputs_layout.addWidget(subject_label)
        left_inputs_layout.addWidget(self.teacher_subject_input)
        left_inputs_layout.addWidget(self.color_btn)
        left_inputs_layout.addWidget(self.add_teacher_btn)

        # Teacher list box with fixed width
        # Teacher list box with fixed width and filter button
        teacher_list_box = QWidget()
        teacher_list_layout = QVBoxLayout(teacher_list_box)
        teacher_list_layout.setContentsMargins(0, 0, 0, 0)

        teachers_label = QLabel("Teacher List: (Double-click to Edit):")
        teachers_label.setStyleSheet("font-size: 10pt; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;")
        teacher_list_layout.addWidget(teachers_label)

        teacher_list_layout.addWidget(self.teacher_list)

        filter_btn_container = QWidget()
        filter_btn_layout = QHBoxLayout(filter_btn_container)
        filter_btn_layout.setContentsMargins(0, 0, 0, 0)
        filter_btn_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.absent_btn = QPushButton("Absent Teacher Analysis")
        self.absent_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
             QPushButton:pressed {
                background-color: #b34700;
            }                         

        """)
        self.absent_btn.clicked.connect(self.show_absent_teacher_dialog)
        filter_btn_layout.addWidget(self.absent_btn)

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setFixedWidth(150)
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1e8449;
            }
        """)
        self.filter_btn.clicked.connect(self.show_filter_dialog)
        filter_btn_layout.addWidget(self.filter_btn)


        teacher_list_layout.addWidget(filter_btn_container)


        


        # Class controls box fixed width
        class_controls_box = QWidget()
        class_controls_layout = QVBoxLayout(class_controls_box)
        class_controls_layout.setContentsMargins(0, 0, 0, 0)
        class_controls_layout.setSpacing(8)
        add_class_label = QLabel("Add Class:")
        add_class_label.setStyleSheet("font-size: 10pt; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;")
        class_controls_layout.addWidget(add_class_label)
        class_controls_layout.addWidget(self.class_input)
        class_controls_layout.addWidget(self.add_class_btn)
        class_controls_layout.addSpacing(10)
        delete_class_label = QLabel("Delete Class:")
        delete_class_label.setStyleSheet("font-size: 10pt; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;")
        class_controls_layout.addWidget(delete_class_label)
        delete_layout = QHBoxLayout()
        delete_layout.setSpacing(5)
        delete_layout.addWidget(self.delete_class_combo)
        delete_layout.addWidget(self.delete_class_btn)
        class_controls_layout.addLayout(delete_layout)

        # Save / Load buttons box with max width
        save_load_box = QWidget()
        save_load_layout = QHBoxLayout(save_load_box)
        save_load_layout.setContentsMargins(0, 0, 0, 0)
        save_load_layout.setSpacing(50)
        save_btn = QPushButton("Save")
        load_btn = QPushButton("Load")
        save_btn.clicked.connect(self.save_data)
        load_btn.clicked.connect(self.load_data)
        for btn in (save_btn, load_btn):
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2980b9;
                    border-radius: 5px;
                    padding: 8px;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    font-weight: bold;
                    font-size: 9pt;
                    color: white;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #1c5980;
                }
            """)
        save_load_layout.addWidget(save_btn)
        save_load_layout.addWidget(load_btn)
        save_load_box.setMaximumWidth(310)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)
        left_layout.addSpacing(20)  # You can increase the number for more space
        left_layout.addWidget(left_inputs_box)
        left_layout.addWidget(teacher_list_box)
        left_layout.addWidget(class_controls_box)
        left_layout.addWidget(save_load_box)
        left_layout.addStretch()

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.tab_widget)

        from PyQt6.QtGui import QPixmap

        # Create header widget
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(15)

        # Icon label
        icon_label = QLabel()
        pixmap = QPixmap("C:/Users/kusal/Desktop/icon.png")  # put your icon path here
        icon_label.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # App name label
        app_name_label = QLabel("SmartSched")
        app_name_label.setStyleSheet("font-size: 24pt; font-weight: bold; color: white;")
        app_name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        header_layout.addWidget(icon_label)
        header_layout.addWidget(app_name_label)
        header_layout.addStretch()

        # Set header height
        header_widget.setFixedHeight(70)  # or whatever height you want

        # Create a content layout for your existing widgets
        content_layout = QHBoxLayout()
        content_layout.addLayout(left_layout, 0)
        content_layout.addLayout(right_layout, 1)

        # Create main vertical layout to stack header and content
        main_layout = QVBoxLayout()
        main_layout.addWidget(header_widget)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

        self.update_delete_class_combo()

    def pick_color(self):
        color = QColorDialog.getColor(initial=self.subject_color, parent=self)
        if color.isValid():
            self.subject_color = color
            # Keep the button styled with its original blue color
        self.color_btn.setStyleSheet("""
            background-color: #2980b9;
            color: white;
            border-radius: 5px;
            padding: 8px;
            font-weight: 600;
        """)

    def add_teacher(self):
        name = self.teacher_name_input.text().strip().title()
        subject = self.teacher_subject_input.text().strip().title()
        if not name or not subject:
            QMessageBox.warning(self, "Input Error", "Please enter both teacher name and subject.")
            return
        key = f"{name}|{subject}"
        if key in self.teachers:
            QMessageBox.warning(self, "Duplicate Teacher", f"Teacher {name} ({subject}) already exists.")
            return
        teacher = Teacher(name, subject, self.subject_color)
        self.teacher_list.add_teacher(teacher)
        self.teacher_name_input.clear()
        self.teacher_subject_input.clear()

    def add_class(self):
        class_name = normalize_class_name(self.class_input.text())
        if not class_name:
            QMessageBox.warning(self, "Input Error", "Please enter a valid class name (e.g., 6-A).")
            return
        grade_number = int(re.match(r"(\d+)", class_name).group(1))
        grade_key = str(grade_number)

        if grade_key not in self.all_tables:
            container = QWidget()
            container.setLayout(QVBoxLayout())
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            layout_widget = ScrollableGradeWidget()
            scroll_area.setWidget(layout_widget)
            container.layout().addWidget(scroll_area)
            self.tab_widget.addTab(container, grade_key)
            self.all_tables[grade_key] = {
                "tables": {},
                "container": container,
                "scroll_area": scroll_area,
                "layout_widget": layout_widget
            }

        if class_name in self.all_tables[grade_key]["tables"]:
            QMessageBox.warning(self, "Duplicate Class", f"Class {class_name} already exists.")
            return

        table_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        label = QLabel(class_name)
        label.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 4px; color: white;")
        layout.addWidget(label)

        timetable = TimetableTable(class_name, self.all_tables, self.teachers)
        layout.addWidget(timetable)
        table_widget.setLayout(layout)

        self.all_tables[grade_key]["tables"][class_name] = timetable
        self.all_tables[grade_key]["layout_widget"].add_class_widget(table_widget)
        self.update_delete_class_combo()
        self.class_input.clear()

    def delete_class(self):
        class_name = self.delete_class_combo.currentText()
        if not class_name:
            return
        grade_number = int(re.match(r"(\d+)", class_name).group(1))
        grade_key = str(grade_number)

        if grade_key not in self.all_tables or class_name not in self.all_tables[grade_key]["tables"]:
            QMessageBox.warning(self, "Delete Error", "Class not found.")
            return
        timetable = self.all_tables[grade_key]["tables"].pop(class_name)
        parent_widget = timetable.parentWidget()
        if parent_widget:
            self.all_tables[grade_key]["layout_widget"].grid_layout.removeWidget(parent_widget)
            parent_widget.deleteLater()

        if not self.all_tables[grade_key]["tables"]:
            idx = self.tab_widget.indexOf(self.all_tables[grade_key]["container"])
            if idx >= 0:
                self.tab_widget.removeTab(idx)
            del self.all_tables[grade_key]

        self.update_delete_class_combo()

    def update_delete_class_combo(self):
        self.delete_class_combo.clear()
        all_classes = []
        for grade_data in self.all_tables.values():
            all_classes.extend(grade_data["tables"].keys())
        all_classes.sort()
        self.delete_class_combo.addItems(all_classes)

    def save_data(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Timetable Data", "", "JSON Files (*.json)")
        if not filename:
            return
        data = {
            "teachers": {},
            "timetables": {}
        }
        for key, teacher in self.teachers.items():
            data["teachers"][key] = {
                "name": teacher.name,
                "subject": teacher.subject,
                "color": teacher.color.name()
            }
        for grade, grade_data in self.all_tables.items():
            data["timetables"][grade] = {}
            for class_name, table in grade_data["tables"].items():
                data["timetables"][grade][class_name] = table.get_data()
        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(self, "Success", "Data saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def load_data(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Timetable Data", "", "JSON Files (*.json)")
        if not filename:
            return
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load file:\n{e}")
            return

        self.teachers.clear()
        self.teacher_list.clear()
        self.all_tables.clear()
        self.tab_widget.clear()

        for key, tdata in data.get("teachers", {}).items():
            color = QColor(tdata.get("color", "#3498db"))
            teacher = Teacher(tdata["name"], tdata["subject"], color)
            self.teachers[key] = teacher
            self.teacher_list.add_teacher(teacher)

        for grade, classes in data.get("timetables", {}).items():
            if grade not in self.all_tables:
                self.all_tables[grade] = {
                    "tables": {},
                    "container": QWidget(),
                    "scroll_area": QScrollArea(),
                    "layout_widget": ScrollableGradeWidget()
                }
                self.all_tables[grade]["container"].setLayout(QVBoxLayout())
                scroll_area = self.all_tables[grade]["scroll_area"]
                scroll_area.setWidgetResizable(True)
                scroll_area.setWidget(self.all_tables[grade]["layout_widget"])
                self.all_tables[grade]["container"].layout().addWidget(scroll_area)
                self.tab_widget.addTab(self.all_tables[grade]["container"], grade)

            for class_name, timetable_data in classes.items():
                table_widget = QWidget()
                layout = QVBoxLayout()
                layout.setContentsMargins(5, 5, 5, 5)
                label = QLabel(class_name)
                label.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 4px; color: white;")
                layout.addWidget(label)

                timetable = TimetableTable(class_name, self.all_tables, self.teachers)
                timetable.set_data(timetable_data)
                layout.addWidget(timetable)
                table_widget.setLayout(layout)

                self.all_tables[grade]["tables"][class_name] = timetable
                self.all_tables[grade]["layout_widget"].add_class_widget(table_widget)

        self.update_delete_class_combo()
        QMessageBox.information(self, "Success", "Data loaded successfully.")
    

    def show_filter_dialog(self):
        dialog = FilterDialog(self.teachers, self.all_tables, self)
        dialog.exec()
        # Removed analyze_absent_teacher() here, because now it's triggered by the dialog's Analyze button.


    def filter_teachers(self, subject, day, period):
        day_to_col = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4}

        # Calculate columns and rows to check:
        cols = range(5) if day == "Any" else [day_to_col.get(day, -1)]
        if -1 in cols:
            QMessageBox.warning(self, "Error", "Invalid day selected.")
            return

        if period == "Any":
            rows = range(8)
        else:
            try:
                rows = [int(period[1:]) - 1]
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid period selected.")
                return

        busy_keys = set()
        for grade_data in self.all_tables.values():
            for table in grade_data["tables"].values():
                for row in rows:
                    for col in cols:
                        cell = table.item(row, col)
                        if cell:
                            key = cell.data(Qt.ItemDataRole.UserRole)
                            if key:
                                busy_keys.add(key)

        # Filter teachers by subject and availability
        filtered_teachers = {}
        for k, t in self.teachers.items():
            if subject != "Any" and t.subject.lower() != subject.lower():
                continue
            if k in busy_keys:
                continue
            filtered_teachers[k] = t

        # Clear and repopulate teacher list with filtered teachers
        self.teacher_list.clear()
        for teacher in filtered_teachers.values():
            self.teacher_list.add_teacher(teacher)

    def reset_teacher_filter(self):
        self.teacher_list.clear()
        for teacher in self.teachers.values():
            self.teacher_list.add_teacher(teacher)

    def show_absent_teacher_dialog(self):
        dialog = AbsentTeacherDialog(self.teachers, self.all_tables, self)
        dialog.exec()

    def show_filter_dialog(self):
        dialog = FilterDialog(self.teachers, self.all_tables, self)
        dialog.exec()

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
