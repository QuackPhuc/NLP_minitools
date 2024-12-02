# Hướng dẫn nhanh
- Dùng `pdf_to_png.py` để xuất ảnh ra thư mục. (cần có fitz nếu chưa có dùng `pip install fitz`)
- Chạy file `label_GUI.py`: (cần có Qt5: `pip install PyQt5`)
    + Load thư mục ảnh vừa xuất (ảnh có dạng [0-N].png)
    + Có thể thêm, sửa, xóa các nhãn, id nhãn,... bằng click chuột phải vào phần bảng.
    + Có thể chỉnh sửa số cột ảnh hiển thị bằng cách thay đổi ở góc trên bên phải GUI
    + Ảnh load lần lượt nên có thể dùng `Load more images` để tải thêm ảnh.
    + Click chuột trái vào ảnh để tăng nhãn lên 1 (vd: 1.png đang ở label1, click chuột trái lần nữa sẽ chuyển sang label2).
    + Click chuột phải để lùi nhãn (có thể xóa ảnh ra khỏi nhãn bằng cách này)
- Save ảnh lại, ảnh sẽ được save theo định dạng: `[Label name]_[Label index]_[page index].png`
    + `[Label name]`: tên các nhãn ví dụ như `Han`, `Viet`, `Phienam`,...(người dùng có thể tự sửa đổi qua GUI).
    + `[Label index]`: những bài thơ, ngữ liệu tương ứng sẽ có cùng `Label index`, ví dụ bài thơ chữ hán, phần phiên âm, dịch nghĩa, dịch thơ tương ứng sẽ có cùng `Label index`.
    + `[Page index]`: Là chỉ số trang của ảnh trong file `pdf`.
- Xem video demo: [`Demo_Label_GUI.mp4`](https://drive.google.com/file/d/1RVkRAdbpUjWg5-lp8JPzzyjMeuj3ggIs/view?usp=sharing)
