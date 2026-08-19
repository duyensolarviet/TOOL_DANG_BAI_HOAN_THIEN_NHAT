import os
import shutil

def add_delete_media_checkbox(ui_frame, ctk, var_dict, key):
    """
    Thêm ô checkbox 'Xoá ảnh/video khi đã đăng xong' vào giao diện.
    Sẽ lưu biến vào var_dict[key].
    """
    delete_var = ctk.StringVar(value="0")
    checkbox = ctk.CTkCheckBox(
        ui_frame, 
        text="Xoá video khi đăng bài xong", 
        variable=delete_var,
        onvalue="1",
        offvalue="0"
    )
    # Dùng place(relx=0.5) để đưa ô checkbox vào chính giữa khung (header) một cách tuyệt đối
    checkbox.place(relx=0.5, rely=0.5, anchor="center")
    var_dict[key] = delete_var

def delete_media_if_requested(media_path, is_requested, log_callback=None):
    """
    Xóa riêng lẻ file media nếu người dùng có tích chọn.
    Chỉ xóa chính xác file đã được tải lên chứ không xóa toàn bộ thư mục.
    """
    if is_requested != "1" or not media_path:
        return

    try:
        paths = [p.strip() for p in media_path.split('\n') if p.strip()]
        for p in paths:
            abs_path = os.path.abspath(p)
            if os.path.exists(abs_path):
                os.remove(abs_path)
                if log_callback:
                    log_callback(f"[Hệ thống] Đã xóa file sau khi đăng: {abs_path}")
    except Exception as e:
        if log_callback:
            log_callback(f"[Hệ thống] Lỗi khi xóa file {media_path}: {e}")
