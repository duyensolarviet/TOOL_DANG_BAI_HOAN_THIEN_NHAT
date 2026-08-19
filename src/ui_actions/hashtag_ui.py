import customtkinter as ctk

class HashtagUI:
    """
    Component UI độc lập để nhập hashtag/nội dung bổ sung.
    """
    def __init__(self, parent, initial_text=""):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.pack(side="left", padx=5)
        
        ctk.CTkLabel(self.frame, text="Thêm hashtag:").pack(side="left", padx=2)
        
        # Ô nhập dạng text
        self.textbox = ctk.CTkTextbox(self.frame, width=250, height=40)
        self.textbox.pack(side="left", padx=5)
        
        if initial_text:
            self.textbox.insert("1.0", initial_text)
            
    def get_text(self):
        return self.textbox.get("1.0", "end-1c").strip()
