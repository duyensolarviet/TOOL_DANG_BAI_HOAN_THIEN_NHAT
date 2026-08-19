import customtkinter as ctk

class CrossPlatformCommentUI:
    def __init__(self, parent_frame, initial_data=None):
        if initial_data is None:
            initial_data = {}
            
        self.frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.frame.pack(fill="x", pady=2)
        
        # Tiêu đề và các ô tích
        top_box = ctk.CTkFrame(self.frame, fg_color="transparent")
        top_box.pack(fill="x", padx=5)
        
        ctk.CTkLabel(top_box, text="Comment dưới Bài viết vừa đăng {Đa nền tảng}:").pack(side="left", padx=(0, 10))
        
        self.cb_vars = {}
        platforms = [("FB", "fb"), ("Tiktok", "tiktok"), ("Zalo video", "zalo_video"), 
                     ("Youtube", "youtube"), ("Instagram", "instagram"), ("Threads", "threads")]
                     
        for text, key in platforms:
            var = ctk.StringVar(value=initial_data.get(f"cmt_{key}", "0"))
            cb = ctk.CTkCheckBox(top_box, text=text, variable=var, onvalue="1", offvalue="0", width=60)
            cb.pack(side="left", padx=5)
            self.cb_vars[key] = var
            
        # Thêm 2 tùy chọn FB ở file riêng biệt
        try:
            from .comment_fb_options_ui import FBCommentOptionsUI
            self.fb_options_ui = FBCommentOptionsUI(self.frame, initial_data)
        except Exception:
            self.fb_options_ui = None
            
        # Ô nhập text bình luận
        self.comment_txt = ctk.CTkTextbox(self.frame, height=40)
        self.comment_txt.pack(fill="x", padx=5, pady=(2, 0))
        
        saved_text = initial_data.get("cmt_text", "")
        if saved_text:
            self.comment_txt.insert("1.0", saved_text)
            
    def get_data(self):
        data = {}
        for key, var in self.cb_vars.items():
            data[f"cmt_{key}"] = var.get()
            
        if hasattr(self, 'fb_options_ui') and self.fb_options_ui:
            data.update(self.fb_options_ui.get_data())
            
        data["cmt_text"] = self.comment_txt.get("1.0", "end-1c").strip()
        return data
