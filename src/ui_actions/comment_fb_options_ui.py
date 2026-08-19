import customtkinter as ctk

class FBCommentOptionsUI:
    def __init__(self, parent_frame, initial_data=None):
        if initial_data is None:
            initial_data = {}
            
        self.frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        # Pack ngay dưới thanh chọn nền tảng
        self.frame.pack(fill="x", padx=10, pady=(2, 2))
        
        # Ô 1: CMT cá nhân FB
        # Mặc định là 1 (có tích) hoặc theo dữ liệu đã lưu
        self.var_canhan = ctk.StringVar(value=initial_data.get("cmt_fb_canhan", "1"))
        cb_canhan = ctk.CTkCheckBox(self.frame, text="CMT cá nhân FB", variable=self.var_canhan, onvalue="1", offvalue="0")
        cb_canhan.pack(side="left", padx=(0, 20))
        
        # Ô 2: CMT page FB
        # Mặc định là 1 (có tích) hoặc theo dữ liệu đã lưu
        self.var_page = ctk.StringVar(value=initial_data.get("cmt_fb_page", "1"))
        cb_page = ctk.CTkCheckBox(self.frame, text="CMT page FB", variable=self.var_page, onvalue="1", offvalue="0")
        cb_page.pack(side="left", padx=0)
        
    def get_data(self):
        return {
            "cmt_fb_canhan": self.var_canhan.get(),
            "cmt_fb_page": self.var_page.get()
        }
