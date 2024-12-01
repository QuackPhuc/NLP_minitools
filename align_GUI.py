# main.py (Updated with full requested functionalities)
import os
import json
from statistics import median
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QGridLayout, QCheckBox,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QSpinBox, QHeaderView, QSplitter,
    QMenu, QAction, QScrollArea, QWidget, QMessageBox, QHBoxLayout, QInputDialog
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from simple_filter import (
    only_text, simple, only_phien_am, simple_chinese
)

GUI_HEIGHT = 800
GUI_WIDTH = 1200

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image and OCR Viewer")
        self.setGeometry(100, 100, GUI_WIDTH, GUI_HEIGHT)

        # Initialize variables
        self.images = {}  # {"label_index": [list of file paths]}
        self.current_label_index = None
        self.ocr_data = []
        self.edited_data = {}
        self.column_names = []
        self.num_columns = 2  # Default number of image columns

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Buttons for loading data
        self.load_folder_button = QPushButton("Load Folder")
        self.load_folder_button.clicked.connect(self.load_images_from_folder)
        self.load_json_button = QPushButton("Load JSON")
        self.load_json_button.clicked.connect(self.load_json_data)

        splitter = QSplitter(Qt.Vertical)

        # Image Viewer
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_container = QWidget()
        self.image_grid_layout = QGridLayout(self.image_container)
        self.image_scroll.setWidget(self.image_container)
        splitter.addWidget(self.image_scroll)

        # Column adjustment control
        controls_layout = QHBoxLayout()
        self.column_spinbox = QSpinBox()
        self.column_spinbox.setMinimum(1)
        self.column_spinbox.setValue(self.num_columns)
        self.column_spinbox.valueChanged.connect(self.display_current_label_images)
        controls_layout.addWidget(QLabel("Columns:"))
        controls_layout.addWidget(self.column_spinbox)


        # Navigation Buttons
        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Previous Label")
        self.back_button.clicked.connect(self.show_previous_label)
        self.next_button = QPushButton("Next Label")
        self.next_button.clicked.connect(self.show_next_label)


        # OCR Data Table
        self.ocr_table = QTableWidget()
        self.ocr_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ocr_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ocr_table.customContextMenuRequested.connect(self.show_context_menu)
        self.ocr_table.setSelectionBehavior(self.ocr_table.SelectItems)
        self.ocr_table.setSelectionMode(self.ocr_table.ExtendedSelection)
        self.ocr_table.setHorizontalHeaderLabels(["Text"])
        splitter.addWidget(self.ocr_table)

        splitter.setSizes([int(GUI_HEIGHT * 2/3), int(GUI_HEIGHT/3)])
        layout.addWidget(splitter)

        # Save Button
        self.save_button = QPushButton("Save CSV")
        self.save_button.clicked.connect(self.save_csv_data)
        layout.addWidget(self.save_button)

        self.checkbox = QCheckBox("Save this file")
        controls_layout.addWidget(self.checkbox)
        controls_layout.addWidget(self.back_button)
        controls_layout.addWidget(self.next_button)
        layout.addLayout(controls_layout)
        layout.addWidget(self.load_folder_button)
        layout.addWidget(self.load_json_button)
        

    def load_images_from_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.images.clear()
        for file_name in sorted(os.listdir(folder)):
            parts = file_name.split('_')
            if len(parts) >= 3:
                label = parts[1]
                page = parts[2].split('.')[0]
                try:
                    label_index = int(label)
                    file_path = os.path.join(folder, file_name)
                    if label_index not in self.images:
                        self.images[label_index] = []
                    self.images[label_index].append((int(page), file_path))
                except ValueError:
                    continue

        # Sort pages within each label index
        for key in self.images:
            self.images[key].sort()  # Sort by page index
            self.images[key] = [item[1] for item in self.images[key]]

        self.current_label_index = min(self.images.keys(), default=None)
        self.display_current_label_images()

    def display_current_label_images(self):
        """Update the image grid layout based on the current label index and number of columns."""
        if self.current_label_index is None:
            self.image_grid_layout.setRowMinimumHeight(0, 0)
            return

        # Clear existing grid layout
        while self.image_grid_layout.count():
            child = self.image_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Calculate image size based on number of columns
        num_columns = self.column_spinbox.value()
        screen = QApplication.primaryScreen()
        screen_width = screen.size().width()
        image_width = screen_width // num_columns - 20

        images = self.images.get(self.current_label_index, [])
        if not images:
            return

        # Add images to the grid
        for idx, image_path in enumerate(images):
            row, col = divmod(idx, num_columns)
            pixmap = QPixmap(image_path).scaled(image_width, image_width, Qt.KeepAspectRatio)
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            self.image_grid_layout.addWidget(image_label, row, col)

        self.image_container.adjustSize()

    def show_next_label(self):
        if not self.images:
            return
        
        keys = sorted(self.images.keys())
        current_index = keys.index(self.current_label_index)

        self.update_edited_data()

        if current_index + 1 < len(keys):
            self.current_label_index = keys[current_index + 1]
            self.display_current_label_images()
        if f"{self.current_label_index}" in self.edited_data:
            self.show_edited_data()
            self.checkbox.setChecked(self.edited_data[f"{self.current_label_index}"]["is_save"])
        else:
            self.populate_table()
            self.checkbox.setChecked(False)

    def show_previous_label(self):
        if not self.images:
            return

        keys = sorted(self.images.keys())
        current_index = keys.index(self.current_label_index)

        self.update_edited_data()

        if current_index - 1 >= 0:
            self.current_label_index = keys[current_index - 1]
            self.display_current_label_images()
        
        if f"{self.current_label_index}" in self.edited_data:
            self.show_edited_data()
            self.checkbox.setChecked(self.edited_data[f"{self.current_label_index}"]["is_save"])
        else:
            self.populate_table()
            self.checkbox.setChecked(False)

    def load_json_data(self):
        """Load OCR data from a JSON file and populate the table."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json)")
        if not file_name:
            return
        
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                self.ocr_data.append(json.load(file))
                self.populate_table()
        except (json.JSONDecodeError, KeyError) as e:
            QMessageBox.critical(self, "Error", f"Failed to load JSON: {e}")
            self.ocr_data = []

    def show_edited_data(self):
        """Show the edited data in the table."""
        if not self.edited_data:
            return

        self.ocr_table.clear()
        self.ocr_table.setRowCount(len(self.edited_data[f"{self.current_label_index}"]["data"][0]))
        self.ocr_table.setColumnCount(len(self.edited_data[f"{self.current_label_index}"]["data"]))

        for col_idx, column_data in enumerate(self.edited_data[f"{self.current_label_index}"]["data"]):
            for row_idx, value in enumerate(column_data):
                item = QTableWidgetItem(str(value))
                self.ocr_table.setItem(row_idx, col_idx, item)

    def populate_table(self):
        """Populate the table with OCR data based on the current label index."""
        try:
            # Clear the table before populating
            self.ocr_table.clear()

            # Ensure label index exists
            if self.current_label_index is None:
                QMessageBox.warning(self, "No Label Index", "No label index is selected.")
                return

            # Find data matching the current label index
            label_datas = []
            for data in self.ocr_data:
                label_datas.append([
                    item for item in data if str(item["label_index"]) == str(self.current_label_index)
                ])

            if not label_datas:
                QMessageBox.warning(self, "No Data", f"No data found for label index {self.current_label_index}.")
                return
            
            full_table = []

            # Iterate through label data and collect relevant text
            for col, data in enumerate(label_datas): # Tự thay đổi và tùy chỉnh cho phù hợp ngữ liệu
                #full_table.extend(only_text(data))
                if col == 0:
                    full_table.extend(simple_chinese(data))
                elif col == 1:
                    if len(full_table[0]) > 0:
                        med = median([len(text) for text in full_table[2]])
                        leng = len(full_table[2])
                    else:
                        med = float("inf")
                        leng = float("inf")
                    full_table.extend(only_phien_am(data, med=med, leng=leng))

            # Ensure consistent column lengths
            max_length = max(len(col) for col in full_table)
            for col in full_table:
                while len(col) < max_length:
                    col.append("")

            # Populate the table with data
            self.ocr_table.setRowCount(max_length)
            self.ocr_table.setColumnCount(len(full_table))

            if len(self.column_names) == 0:
                self.column_names = [f"Label {i + 1}" for i in range(len(full_table))]
            elif len(self.column_names) > len(full_table):
                self.column_names = self.column_names[:len(full_table)]
            elif len(self.column_names) < len(full_table):
                self.column_names.extend([f"Label {i + 1}" for i in range(len(self.column_names), len(full_table))])
            
            self.ocr_table.setHorizontalHeaderLabels(self.column_names)

            for col_idx, column_data in enumerate(full_table):
                for row_idx, value in enumerate(column_data):
                    # Ensure value is a string
                    item = QTableWidgetItem(str(value))
                    self.ocr_table.setItem(row_idx, col_idx, item)

        except Exception as e:
            print(str(e))
            QMessageBox.critical(self, "Error", f"An error occurred while populating the table: {str(e)}")

    def update_edited_data(self):
        current_data = {}
        current_data["is_save"] = self.checkbox.isChecked()
        current_data["data"] = [[] for _ in range(self.ocr_table.columnCount())]

        for row in range(self.ocr_table.rowCount()):
            for col in range(self.ocr_table.columnCount()):
                item = self.ocr_table.item(row, col)
                if item:
                    current_data["data"][col].append(item.text())
                else:
                    current_data["data"][col].append("")
        
        self.edited_data[f"{self.current_label_index}"] = current_data

    def save_csv_data(self):
        """Save OCR data to a CSV file based on the current table."""
        try:
            output_file, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "", "CSV Files (*.csv)")
            if not output_file:
                return
            
            self.update_edited_data()

            with open(output_file, "w", encoding="utf-8-sig") as file:
                # Write header
                header = ",".join(["index"] + self.column_names)
                file.write(header + "\n")

                # Write data
                for label_index, data in self.edited_data.items():
                    if not data["is_save"]:
                        continue

                    for row in range(len(data[f"data"][0])):
                        row_data = [row + 1] + [data["data"][col][row] for col in range(len(data["data"]))]
                        row_data = [str(item).replace(",", "") for item in row_data]
                        file.write(",".join(row_data) + "\n")

            QMessageBox.information(self, "Success", "Data saved successfully!")
        except Exception as e:
            print(str(e))
            error_file = output_file.replace(".csv", "_error.csv")
            with open(error_file, "w", encoding="utf-8") as file:
                file.write(str(e))
            QMessageBox.critical(self, "Error", f"Failed to save CSV: {e}. Saved error log to {error_file}.")


    def save_json_data(self):
        pass

    def show_context_menu(self, pos):
        """Show context menu for table with options to add/delete rows/columns and rename column."""
        menu = QMenu(self)

        # Add row
        add_row_action = QAction("Add Row", self)
        add_row_action.triggered.connect(self.add_row)
        menu.addAction(add_row_action)

        # Delete row
        del_row_action = QAction("Delete Row", self)
        del_row_action.triggered.connect(self.delete_row)
        menu.addAction(del_row_action)

        # Copy selected
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_selected)
        menu.addAction(copy_action)

        # Paste clipboard
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.paste_selected)
        menu.addAction(paste_action)

        # Add column
        add_column_action = QAction("Add Column", self)
        add_column_action.triggered.connect(self.add_column)
        menu.addAction(add_column_action)

        # Delete column
        del_column_action = QAction("Delete Column", self)
        del_column_action.triggered.connect(self.delete_column)
        menu.addAction(del_column_action)

        # Rename column
        rename_column_action = QAction("Rename Column", self)
        rename_column_action.triggered.connect(self.rename_column)
        menu.addAction(rename_column_action)

        menu.exec_(self.ocr_table.mapToGlobal(pos))
    
    def copy_selected(self):
        """Copy the selected cells' content to the clipboard."""
        selected_ranges = self.ocr_table.selectedRanges()
        if not selected_ranges:
            return

        rows = []
        for selection in selected_ranges:
            for row in range(selection.topRow(), selection.bottomRow() + 1):
                row_data = []
                for col in range(selection.leftColumn(), selection.rightColumn() + 1):
                    item = self.ocr_table.item(row, col)
                    row_data.append(item.text() if item else "")
                rows.append("\t".join(row_data))
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(rows))

    def paste_selected(self):
        """Paste the clipboard content into the selected cells."""
        clipboard = QApplication.clipboard()
        data = clipboard.text().strip()
        if not data:
            return

        rows = data.split("\n")
        current_row = self.ocr_table.currentRow()
        current_col = self.ocr_table.currentColumn()

        for r_offset, row_data in enumerate(rows):
            columns = row_data.split("\t")
            for c_offset, text in enumerate(columns):
                target_row = current_row + r_offset
                target_col = current_col + c_offset
                if target_row < self.ocr_table.rowCount() and target_col < self.ocr_table.columnCount():
                    item = self.ocr_table.item(target_row, target_col)
                    if not item:
                        item = QTableWidgetItem()
                        self.ocr_table.setItem(target_row, target_col, item)
                    item.setText(text)

    def keyPressEvent(self, event):
        """Override keyPressEvent to handle copy-paste shortcuts."""
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                self.copy_selected()
            elif event.key() == Qt.Key_V:
                self.paste_selected()
        super().keyPressEvent(event)
    
    def add_row(self):
        """Add a new empty row to the table."""
        self.ocr_table.insertRow(self.ocr_table.rowCount())
        

    def delete_row(self):
        """Delete the selected row from the table."""
        selected_rows = set(index.row() for index in self.ocr_table.selectedIndexes())
        for row in sorted(selected_rows, reverse=True):
            self.ocr_table.removeRow(row)
        

    def add_column(self):
        """Add a new column to the table."""
        current_column_count = self.ocr_table.columnCount()
        self.ocr_table.insertColumn(current_column_count)
        self.ocr_table.setHorizontalHeaderItem(current_column_count, QTableWidgetItem(f"Column {current_column_count + 1}"))
        self.column_names.append(f"Column {current_column_count + 1}")


    def delete_column(self):
        """Delete the currently selected column."""
        # Hiện thông báo xác nhận xóa cột
        reply = QMessageBox.question(self, 'Delete Column', 'Do you want to delete the current column?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        current_column = self.ocr_table.currentColumn()
        if current_column >= 0:
            self.ocr_table.removeColumn(current_column)
            self.column_names.pop(current_column)

    def rename_column(self):
        """Rename the currently selected column."""
        current_column = self.ocr_table.currentColumn()
        if current_column >= 0:
            current_name = self.column_names[current_column]
            new_name, ok = QInputDialog.getText(self, "Rename Column", "Enter new column name:", text=current_name)
            if ok and new_name.strip():
                self.ocr_table.setHorizontalHeaderItem(current_column, QTableWidgetItem(new_name))
                self.column_names[current_column] = new_name


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
