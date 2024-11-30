import os
import sys
import json
import re
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImageReader
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QInputDialog,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QSpinBox,
    QCheckBox, QAbstractItemView, QMessageBox, QGridLayout, QSplitter, QStatusBar, QMenu, QProgressDialog
)


# Constants
IMAGES_PER_LOAD = 50
GUI_HEIGHT = 800
GUI_WIDTH = 1200
CONFIG_FILE = "config.json"


class ImageLoaderThread(QThread):
    images_loaded = pyqtSignal(list)

    def __init__(self, folder, start_index, count):
        super().__init__()
        self.folder = folder
        self.start_index = start_index
        self.count = count

    def run(self):
        valid_images = []
        files = os.listdir(self.folder)
        sorted_files = sorted(
            (f for f in files if f.split(".")[0].isdigit()),
            key=lambda x: int(x.split(".")[0])
        )

        for i in range(self.start_index, min(len(sorted_files), self.start_index + self.count)):
            file_path = os.path.join(self.folder, sorted_files[i])
            if QImageReader(file_path).canRead():
                valid_images.append(file_path)

        self.images_loaded.emit(valid_images)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Labeling Tool")
        self.setGeometry(100, 100, GUI_WIDTH, GUI_HEIGHT)

        self.image_folder = ""
        self.images = []
        self.loaded_image_count = 0
        self.columns = 3
        self.current_tick_row = 0
        self.label_names = []

        # Load configuration if exists
        self.config = self.load_config()

        # Main Layout
        main_layout = QVBoxLayout()

        # Top Layout
        top_layout = QHBoxLayout()
        self.btn_load_folder = QPushButton("Load Folder")
        self.btn_load_more = QPushButton("Load More Images")
        self.column_selector = QSpinBox()
        self.column_selector.setRange(1, 10)
        self.column_selector.setValue(self.config.get("columns", 3))
        self.column_selector.valueChanged.connect(self.update_columns)

        top_layout.addWidget(self.btn_load_folder)
        top_layout.addWidget(self.btn_load_more)
        top_layout.addWidget(QLabel("Columns:"))
        top_layout.addWidget(self.column_selector)
        main_layout.addLayout(top_layout)

        # Create splitter for images and label table
        splitter = QSplitter(Qt.Vertical)

        # Image Display Area
        self.image_area = QWidget()
        self.image_layout = QGridLayout()
        self.image_area.setLayout(self.image_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_area)
        splitter.addWidget(self.scroll_area)

        # Label Table Area
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)

        self.table = QTableWidget(self.config.get("rows", 1), self.config.get("labels", 1))
        self.table.setHorizontalHeaderLabels(
            [f"{self.config["label_names"][i]}" if self.config else f"Label {i + 1}" for i in range(self.config.get("labels", 1))]
        )
        self.table.setVerticalHeaderLabels(
            [str(i+1) for i in range(self.config.get("rows", 1))]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)

        # Add Tickboxes
        self.add_tickboxes()

        table_layout.addWidget(self.table)
        splitter.addWidget(table_widget)
        splitter.setSizes([int(GUI_HEIGHT * 2/3), int(GUI_HEIGHT/3)])

        main_layout.addWidget(splitter)

        # Save Button
        self.btn_save = QPushButton("Save Images")
        main_layout.addWidget(self.btn_save)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()

        # Central Widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Connections
        self.btn_load_folder.clicked.connect(self.load_folder)
        self.btn_load_more.clicked.connect(self.load_more_images)
        self.btn_save.clicked.connect(self.save_images)

        # Setup context menu
        self.setup_table_context_menu()

    def load_config(self):
        """Load configuration from a JSON file."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as file:
                return json.load(file)
        return {}

    def save_config(self):
        """Save configuration to a JSON file."""
        config = {
            "rows": self.table.rowCount(),
            "columns": self.columns,
            "labels": self.table.columnCount() - 1, # Exclude tick box column
            "label_names": [self.get_column_name(i) for i in range(1, self.table.columnCount())]
        }
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.image_folder = folder
            self.images = []
            self.loaded_image_count = 0
            self.image_layout.setRowMinimumHeight(0, 0)  # Clear previous grid
            self.load_more_images()

    def load_more_images(self):
        if not self.image_folder:
            QMessageBox.warning(self, "Error", "Please load a folder first!")
            return

        self.btn_load_more.setEnabled(False)
        self.thread = ImageLoaderThread(self.image_folder, self.loaded_image_count, IMAGES_PER_LOAD)
        self.thread.images_loaded.connect(self.display_images)
        self.thread.start()

    def display_images(self, image_paths):
        screen = QApplication.primaryScreen()
        screen_width = screen.size().width()
        image_width = screen_width // self.columns - 20

        for path in image_paths:
            pixmap = QPixmap(path)
            label = QLabel()
            label.setPixmap(pixmap.scaled(image_width, image_width, Qt.KeepAspectRatio))
            label.setAlignment(Qt.AlignCenter)
            label.setObjectName(path)  # Store image path in QLabel
            label.mousePressEvent = lambda event, path=path: self.image_clicked(event, path)

            row = self.loaded_image_count // self.columns
            col = self.loaded_image_count % self.columns
            self.image_layout.addWidget(label, row, col)

            self.loaded_image_count += 1

        self.update_status_bar()
        self.btn_load_more.setEnabled(True)

    def setup_table_context_menu(self):
        """Thiết lập menu chuột phải cho bảng."""
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)

    def show_table_context_menu(self, position):
        """Hiển thị menu chuột phải tại vị trí click."""
        menu = QMenu()

        add_row_action = menu.addAction("Add Label Index")
        add_col_action = menu.addAction("Add Label")
        delete_row_action = menu.addAction("Delete Label Index")
        delete_col_action = menu.addAction("Delete Label")
        clear_row_action = menu.addAction("Clear Row")
        edit_label_action = menu.addAction("Edit Label Name")

        action = menu.exec_(self.table.viewport().mapToGlobal(position))

        if action == add_row_action:
            self.add_table_row()
        elif action == add_col_action:
            self.add_table_column()
        elif action == delete_row_action:
            self.delete_table_row()
        elif action == delete_col_action:
            self.delete_table_column()
        elif action == clear_row_action:
            self.clear_table_row()
        elif action == edit_label_action:
            self.edit_label_name()

    
    def add_table_row(self):
        """Thêm một hàng mới vào bảng và gắn tick box vào cột đầu tiên."""
        current_row_count = self.table.rowCount()
        self.table.insertRow(current_row_count)
        self.table.setVerticalHeaderItem(current_row_count, QTableWidgetItem(str(current_row_count + 1)))

        # Thêm tick box vào cột đầu tiên
        tickbox = QCheckBox()
        tickbox.toggled.connect(lambda checked, idx=current_row_count: self.tickbox_toggled(checked, idx))
        self.table.setCellWidget(current_row_count, 0, tickbox)

        # Đảm bảo tick box mới hoạt động chính xác
        for i in range(self.table.rowCount()):
            tickbox = self.table.cellWidget(i, 0)
            if i == current_row_count:  # Bật tick box mới nếu đây là hàng đầu tiên
                tickbox.setChecked(True)
            elif tickbox:
                tickbox.setChecked(False)

        # Cập nhật thanh trạng thái
        self.update_status_bar()

    def add_table_column(self):
        """Thêm một cột mới vào bảng và gán tên nhãn tự động."""
        current_col_count = self.table.columnCount()
        self.table.insertColumn(current_col_count)
        self.table.setHorizontalHeaderItem(current_col_count, QTableWidgetItem(f"Label {current_col_count}"))

        # Đảm bảo các ô trong cột mới có thể chỉnh sửa nội dung
        for row in range(self.table.rowCount()):
            self.table.setItem(row, current_col_count, QTableWidgetItem(""))

        # Cập nhật thanh trạng thái
        self.update_status_bar()

    def delete_table_row(self):
        """Xóa hàng hiện tại và cập nhật index."""
        current_row = self.table.currentRow()
        if current_row != -1:
            self.table.removeRow(current_row)

            # Cập nhật lại index cho các hàng
            for i in range(self.table.rowCount()):
                self.table.setVerticalHeaderItem(i, QTableWidgetItem(str(i + 1)))

            QMessageBox.information(self, "Row Deleted", f"Row {current_row + 1} has been deleted.")
    
    def delete_table_column(self):
        """Xóa cột hiện tại."""
        current_col = self.table.currentColumn()
        if current_col > 0:  # Không cho phép xóa cột tick box
            self.table.removeColumn(current_col)
            QMessageBox.information(self, "Column Deleted", f"Column {current_col} has been deleted.")
        else:
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete the tick box column.")

    def clear_table_row(self):
        """Xóa toàn bộ nội dung trong một hàng (trừ tick box)."""
        current_row = self.table.currentRow()
        if current_row != -1:
            for col in range(1, self.table.columnCount()):  # Bỏ qua cột tick box
                self.table.setItem(current_row, col, QTableWidgetItem(""))
            QMessageBox.information(self, "Row Cleared", f"All content in row {current_row + 1} has been cleared.")

    def edit_label_name(self):
        """Cho phép sửa tên nhãn (header của cột)."""
        current_col = self.table.currentColumn()
        if current_col > 0:  # Không cho phép sửa tên tick box
            new_name, ok = QInputDialog.getText(self, "Edit Label Name", "Enter new label name:")
            if ok and new_name.strip():
                self.table.setHorizontalHeaderItem(current_col, QTableWidgetItem(new_name))
                QMessageBox.information(self, "Label Edited", f"Label name has been updated to '{new_name}'.")
        else:
            QMessageBox.warning(self, "Cannot Edit", "Cannot edit the tick box column.")

    def get_column_name(self, col_index):
        """Lấy tên của cột tại chỉ số `col_index`."""
        header_item = self.table.horizontalHeaderItem(col_index)
        if header_item:
            return header_item.text()  # Trả về tên cột
        return ""
    
    def get_valid_column_names(self, col_index):
        """Trả về tên cột hợp lệ, thích hợp để đặt tên cho file"""
        name = self.get_column_name(col_index)

        # Các ký tự bị cấm
        invalid_chars = r'[\/:*?"<>|]'  # Windows-specific
        reserved_names = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
                        "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2",
                        "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}

        # Xóa các ký tự không hợp lệ
        sanitized = re.sub(invalid_chars, "", name).strip()
        if name != sanitized:
            print("Removed unvalid character")

        # Nếu tên bị rỗng hoặc nằm trong danh sách tên cấm
        if not sanitized or sanitized.upper() in reserved_names:
            return f"Label{col_index}"  # Giá trị mặc định

        # Đảm bảo không bắt đầu bằng dấu chấm hoặc khoảng trắng
        if sanitized[0] in {".", " "}:
            sanitized = f"Label{col_index}{sanitized}"

        return sanitized

    def add_tickboxes(self):
        """Add tickboxes to the table's first column."""
        self.table.insertColumn(0)
        self.table.setHorizontalHeaderItem(0, QTableWidgetItem("Select"))
        for i in range(self.table.rowCount()):
            tickbox = QCheckBox()
            tickbox.toggled.connect(lambda checked, idx=i: self.tickbox_toggled(checked, idx))
            self.table.setCellWidget(i, 0, tickbox)
            if i == 0:  # First tickbox selected by default
                tickbox.setChecked(True)

    def tickbox_toggled(self, checked, idx):
        if checked:
            for i in range(self.table.rowCount()):
                if i != idx:
                    tickbox = self.table.cellWidget(i, 0)
                    if tickbox:
                        tickbox.setChecked(False)
            self.current_tick_row = idx

    def update_columns(self, value):
        self.columns = value
        self.refresh_images()

    def refresh_images(self):
        for i in reversed(range(self.image_layout.count())):
            widget = self.image_layout.itemAt(i).widget()
            self.image_layout.removeWidget(widget)
            widget.deleteLater()

        self.loaded_image_count = 0
        self.load_more_images()

    def save_images(self):
        save_folder = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        if not save_folder:
            return

        total_items = 0
        for row in range(self.table.rowCount()):
            for col in range(1, self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    total_items += len(item.text().split(","))

        progress_dialog = QProgressDialog("Saving images...", "Cancel", 0, total_items, self)
        progress_dialog.setWindowTitle("Saving Images")
        progress_dialog.setWindowModality(Qt.ApplicationModal)
        progress_dialog.setValue(0)

        current_progress = 0

        for row in range(self.table.rowCount()):
            for col in range(1, self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    indices = item.text().split(",")
                    for index in indices:
                        index = index.strip()
                        try:
                            img_path = os.path.join(self.image_folder, f"{index}.png")
                            label_name = self.get_valid_column_names(col)
                            save_path = os.path.join(save_folder, f"{label_name}_{row + 1}_{index}.png")
                            QPixmap(img_path).save(save_path)
                        except Exception as e:
                            print(f"Error saving image {index}: {e}")
                        current_progress += 1
                        progress_dialog.setValue(current_progress)

                        if progress_dialog.wasCanceled():
                            QMessageBox.warning(self, "Operation Cancelled", "Saving images was cancelled!")
                            return

        progress_dialog.close()
        QMessageBox.information(self, "Save Complete", "All images have been saved successfully!")


    def update_status_bar(self):
        total_images = self.loaded_image_count
        labeled_images = sum(
            len(item.text().split(",")) if item and item.text() else 0
            for row in range(self.table.rowCount())
            for item in [self.table.item(row, col) for col in range(1, self.table.columnCount())]
        )
        self.status_bar.showMessage(f"Total Images: {total_images}, Labeled Images: {labeled_images}")

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

    def image_clicked(self, event, image_path):
        """Xử lý sự kiện click chuột trái/phải trên ảnh."""
        index = os.path.basename(image_path).split(".")[0]
        if not index.isdigit():
            return

        index = int(index)
        row = self.current_tick_row

        if event.button() == Qt.LeftButton:
            for col in range(1, self.table.columnCount()):
                item = self.table.item(row, col)
                if item and (str(index) in item.text().split(", ")):
                    next_col = col + 1

                    # Chuyển giá trị sang ô tiếp theo nếu tồn tại
                    if next_col < self.table.columnCount():
                        # Xóa giá trị tại ô cũ
                        updated_text = ", ".join([x for x in item.text().split(", ") if x != str(index)])
                        item.setText(updated_text)

                        next_item = self.table.item(row, next_col) or QTableWidgetItem()
                        new_text = next_item.text() + f", {index}" if next_item.text() else f"{index}"
                        next_item.setText(new_text)
                        self.table.setItem(row, next_col, next_item)
                    return

            # Thêm vào cột đầu tiên nếu không tìm thấy
            first_item = self.table.item(row, 1) or QTableWidgetItem()
            first_text = first_item.text() + f", {index}" if first_item.text() else f"{index}"
            first_item.setText(first_text)
            self.table.setItem(row, 1, first_item)

        elif event.button() == Qt.RightButton:
            for col in range(1, self.table.columnCount()):
                item = self.table.item(row, col)
                if item and (str(index) in item.text().split(", ")):
                    # Xóa giá trị tại ô hiện tại
                    updated_text = ", ".join([x for x in item.text().split(", ") if x != str(index)])
                    item.setText(updated_text)

                    # Nếu không phải cột đầu tiên, chuyển về cột trước đó
                    if col > 1:
                        prev_item = self.table.item(row, col - 1) or QTableWidgetItem()
                        prev_text = prev_item.text() + f", {index}" if prev_item.text() else f"{index}"
                        prev_item.setText(prev_text)
                        self.table.setItem(row, col - 1, prev_item)
                    return



def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
