import customtkinter as ctk

def add_delete_posted_checkbox(header_frame, app):
    app.is_auto_delete_posted_var = ctk.StringVar(value="0")
    cb_delete = ctk.CTkCheckBox(
        header_frame, 
        text="Xóa bài đã đăng & lên lịch", 
        variable=app.is_auto_delete_posted_var, 
        onvalue="1", 
        offvalue="0",
        text_color="#e74c3c", 
        font=ctk.CTkFont(weight="bold")
    )
    cb_delete.pack(side="right", padx=2)

def check_and_delete_posted(app, account, post_dict):
    """
    Được gọi từ bot_manager sau khi một bài đăng đã xử lý xong.
    Nếu checkbox đang bật, nó sẽ tự động xóa bài đăng đó khỏi giao diện và dữ liệu ngay lập tức.
    """
    try:
        # Tuyệt đối không xóa Bài Đăng Mẫu
        if str(post_dict.get('is_sample', '0')) == '1' or post_dict.get('is_sample') is True:
            return

        if hasattr(app, 'is_auto_delete_posted_var') and app.is_auto_delete_posted_var.get() == "1":
            # 1. Xóa khỏi JSON/dữ liệu
            if post_dict in account.get('posts', []):
                account['posts'].remove(post_dict)
            
            # 2. Xóa khỏi giao diện
            post_frame = post_dict.get('post_frame')
            if post_frame:
                # Phải chạy destroy trên main thread của Tkinter
                app.after(0, post_frame.destroy)
            
            # 3. Lưu lại
            if hasattr(app, 'save_data'):
                app.after(100, app.save_data)
            
            # 4. Ghi log
            if hasattr(app, 'write_log'):
                app.after(0, lambda: app.write_log(f"[{account.get('id', '')}] Đã tự động XÓA cấu hình bài đăng (do tính năng dọn dẹp tự động)."))
                
    except Exception as e:
        print(f"Lỗi khi tự động xóa bài: {e}")
