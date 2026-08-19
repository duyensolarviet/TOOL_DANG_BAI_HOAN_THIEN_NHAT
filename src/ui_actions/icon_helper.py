import os

def apply_app_icon(window):
    """
    Đặt icon chuẩn VU DUYEN TOOLS cho cửa sổ (hỗ trợ cả CTk và CTkToplevel,
    tự động lặp lại với window.after để đảm bảo ghi đè 100% icon mặc định của CustomTkinter).
    """
    try:
        possible_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "icon.ico")),
            os.path.abspath(os.path.join(os.getcwd(), "assets", "icon.ico")),
            os.path.abspath("assets/icon.ico"),
            os.path.abspath("src/assets/icon.ico")
        ]
        icon_path = None
        for p in possible_paths:
            if os.path.exists(p):
                icon_path = p
                break
                
        if icon_path:
            def _do_set():
                try:
                    window.iconbitmap(icon_path)
                except:
                    pass
            _do_set()
            window.after(100, _do_set)
            window.after(300, _do_set)
            window.after(700, _do_set)
    except:
        pass
