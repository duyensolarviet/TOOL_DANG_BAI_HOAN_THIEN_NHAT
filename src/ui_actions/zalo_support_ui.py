import webbrowser
import customtkinter as ctk

ZALO_GROUP_LINK = "https://zalo.me/g/mmgznzbleun8cirr19ld"

def open_zalo_support():
    """
    Mở trực tiếp link Nhóm Zalo Hỗ Trợ trên trình duyệt
    """
    try:
        webbrowser.open(ZALO_GROUP_LINK)
    except Exception as e:
        print("Lỗi mở link Zalo:", e)

def create_zalo_support_button(parent):
    """
    Tạo nút / link chữ in đậm nổi bật dẫn tới Nhóm Zalo Hỗ Trợ
    """
    btn = ctk.CTkButton(
        parent,
        text="💬 Nhóm Zalo Hỗ Trợ",
        command=open_zalo_support,
        font=ctk.CTkFont(size=14, weight="bold"),
        fg_color="#0284c7",
        hover_color="#0369a1",
        text_color="#ffffff",
        height=36,
        corner_radius=8,
        cursor="hand2"
    )
    return btn
