from tkinter import messagebox

def save_data_and_notify(app):
    """
    Hàm xử lý khi người dùng bấm nút Lưu Lại.
    Lưu dữ liệu và hiển thị thông báo.
    """
    app.save_data()
    messagebox.showinfo("Thành công", "Đã lưu lại thông tin tài khoản!")
    app.write_log("Đã lưu trữ cài đặt tài khoản.")
