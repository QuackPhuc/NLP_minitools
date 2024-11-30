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
from language_helper import ( 
    percentage_chinese, percentage_vietnamese, is_uppercase,
    percentage_similarity, clean_sentence, is_number
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
        self.num_columns = 2  # Default number of columns

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
            self.checkbox.setChecked(True) # Lười ấn nút

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
            self.checkbox.setChecked(True)

    def load_json_data(self):
        """Load OCR data from a JSON file and populate the table."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json)")
        if not file_name:
            return

        try:
            with open(file_name, "r", encoding="utf-8") as file:
                self.ocr_data = json.load(file)
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
            label_data = [
                item for item in self.ocr_data 
                if str(item["label_index"]) == str(self.current_label_index)
            ]
            if not label_data:
                QMessageBox.warning(self, "No Data", f"No data found for label index {self.current_label_index}.")
                return

            # Initialize data structures
            full_table = [[], [], [], [], [], []]  # Page, Box, Han, Phien am, Dich nghia, Dich tho
            current_state = "Han"
            title, tmp_title = "", ""
            titleDN, titleDT = "", ""
            # Iterate through label data and collect relevant text
            for entry in label_data:
                results = entry.get("result", {})
                lines = results.get("lines", [])
                for line in lines:
                    text = line.get("text", "").strip()
                    if not text:
                        continue

                    page_index = entry.get("page_index", "")
                    bounding_polygon = line.get("boundingPolygon", "")

                    # Convert bounding_polygon (list) to a string
                    bounding_polygon_str = json.dumps(bounding_polygon) if isinstance(bounding_polygon, list) else str(bounding_polygon)

                    if percentage_chinese(text) > 60:  # If text is predominantly Chinese
                        if current_state != "Han" and text.strip().strip("\n") == "":
                            continue
                        full_table[0].append(page_index)  # Page
                        full_table[1].append(bounding_polygon_str)  # Box
                        full_table[2].append(text)  # Han
                    elif percentage_vietnamese(text) > 70:  # If text contains Vietnamese
                        is_pass = False
                        for state in ["Phien am", "Dich nghia", "Dich tho"]:
                            if percentage_similarity(text, state) > 70 and current_state != state and len(full_table[2]) > 0:
                                current_state = state
                                is_pass = True
                                break
                        
                        meadian_len = 7
                        if current_state != "Han" and len(full_table[2]) > 0:
                            meadian_len = median([len(i.strip().strip("\n").strip("，。o，,。,,.,;")) for i in full_table[2]])

                        if is_pass:
                            continue
                        elif current_state != "Han" and len(text.split(" "))  / meadian_len > 2:
                            continue
                        elif current_state == "Han" and is_uppercase(text) and tmp_title == "":
                            tmp_title = text
                        elif current_state == "Phien am":
                            if len(full_table[3]) - len(full_table[2]) < 0:
                                if title == "" and is_uppercase(text):
                                    title = text
                                else:
                                    if clean_sentence(text) == "":
                                        pass
                                    else:
                                        full_table[3].append(clean_sentence(text))
                        elif current_state == "Dich nghia":
                            if len(full_table[4]) - len(full_table[2]) < 0:
                                if len(full_table[4]) > 0 and len(full_table[4][-1]) / len(text) > 2:
                                    full_table[4][-1] += " " + clean_sentence(text)
                                else:
                                    if titleDN == "" and is_uppercase(text):
                                        titleDN = clean_sentence(text)
                                    full_table[4].append(clean_sentence(text))
                        elif current_state == "Dich tho":
                            if len(full_table[5]) - len(full_table[2]) < 0:
                                if len(full_table[5]) > 0 and len(full_table[5][-1]) / len(text) > 2:
                                    full_table[5][-1] += " " + clean_sentence(text)
                                else:
                                    if titleDT == "" and is_uppercase(text):
                                        titleDT = clean_sentence(text)
                                    full_table[5].append(clean_sentence(text))

            if title != "":
                full_table[3] = [title] + full_table[3]
                if titleDN == "" and len(full_table[4]) > 0:
                    full_table[4] = [title] + full_table[4]
                if titleDT == "" and len(full_table[5]) > 0:
                    full_table[5] = [title] + full_table[5]
            elif tmp_title != "":
                full_table[3] = [tmp_title] + full_table[3]
                if titleDN == "" and len(full_table[4]) > 0:
                    full_table[4] = [tmp_title] + full_table[4]
                if titleDT == "" and len(full_table[5]) > 0:
                    full_table[5] = [tmp_title] + full_table[5]

            # Ensure consistent column lengths
            max_length = max(len(col) for col in full_table)
            for col in full_table:
                while len(col) < max_length:
                    col.append("")

            # Populate the table with data
            self.ocr_table.setRowCount(max_length)
            self.ocr_table.setColumnCount(6)
            self.ocr_table.setHorizontalHeaderLabels(["Page", "Box", "Han", "Phien am", "Dich nghia", "Dich tho"])

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
        current_data["data"] = [[], [], [], [], [], []]

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
                header = ",".join(["ID"] + ["Page", "Box", "Han", "Phien am", "Dich nghia", "Dich tho"])
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
        """Save OCR data to a JSON file based on the current table."""
        try:
            output_file, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json)")
            if not output_file:
                return

            label_name = "LabelName"  # You can customize this or take input from the user
            label_index = self.current_label_index
            result = []

            # Build the result array
            for row in range(self.ocr_table.rowCount()):
                row_data = {}
                for col in range(self.ocr_table.columnCount()):
                    header = self.ocr_table.horizontalHeaderItem(col).text()
                    cell = self.ocr_table.item(row, col)
                    row_data[header] = cell.text() if cell else ""
                row_data["line_index"] = row + 1  # Add line_index
                result.append(row_data)

            # Create the final JSON structure
            output_data = {
                "label_name": label_name,
                "label_index": label_index,
                "result": result
            }

            with open(output_file, "w", encoding="utf-8") as file:
                json.dump([output_data], file, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "Success", "Data saved successfully!")
        except Exception as e:
            error_file = output_file.replace(".json", "_error.json")
            with open(error_file, "w", encoding="utf-8") as file:
                json.dump({"error": str(e)}, file, indent=4)
            QMessageBox.critical(self, "Error", f"Failed to save JSON: {e}. Saved error log to {error_file}.")

    def show_context_menu(self, pos):
        """Show context menu for table with options to add/delete rows/columns and rename column."""
        menu = QMenu(self)

        # Copy selected
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_selected)
        menu.addAction(copy_action)

        # Paste clipboard
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.paste_selected)
        menu.addAction(paste_action)

        # Add row
        add_row_action = QAction("Add Row", self)
        add_row_action.triggered.connect(self.add_row)
        menu.addAction(add_row_action)

        # Delete row
        del_row_action = QAction("Delete Row", self)
        del_row_action.triggered.connect(self.delete_row)
        menu.addAction(del_row_action)

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


    def delete_column(self):
        """Delete the currently selected column."""
        current_column = self.ocr_table.currentColumn()
        if current_column >= 0:
            self.ocr_table.removeColumn(current_column)


    def rename_column(self):
        """Rename the currently selected column."""
        current_column = self.ocr_table.currentColumn()
        if current_column >= 0:
            current_name = self.ocr_table.horizontalHeaderItem(current_column).text()
            new_name, ok = QInputDialog.getText(self, "Rename Column", "Enter new column name:", text=current_name)
            if ok and new_name.strip():
                self.ocr_table.setHorizontalHeaderItem(current_column, QTableWidgetItem(new_name))


    def copy_cell(self):
        """Copy the selected cell to the clipboard."""
        selected_items = self.ocr_table.selectedItems()
        if selected_items:
            clipboard = QApplication.clipboard()
            clipboard.setText(selected_items[0].text())


    def paste_cell(self):
        """Paste the clipboard content into the selected cell."""
        selected_items = self.ocr_table.selectedItems()
        if selected_items:
            clipboard = QApplication.clipboard()
            selected_items[0].setText(clipboard.text())


    def keyPressEvent(self, event):
        """Override keyPressEvent to handle copy-paste shortcuts."""
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                self.copy_cell()
            elif event.key() == Qt.Key_V:
                self.paste_cell()
        super().keyPressEvent(event)



if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
