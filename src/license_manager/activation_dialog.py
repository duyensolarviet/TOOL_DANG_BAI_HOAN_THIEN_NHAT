import os
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import pyperclip

from .hwid import get_device_hwid, get_device_info
from .license_checker import LicenseChecker
from .storage_backend import load_license_config

class ActivationViewMixin:
    def init_activation_data(self, parent=None, on_success_callback=None):
        self.parent_window = parent
        self.on_success_callback = on_success_callback
        self.checker = LicenseChecker()
        self.config = load_license_config()
        self.hwid = get_device_hwid()
        self.device_info = get_device_info()
        self.is_success = False

        self.title("Kích Hoạt Bản Quyền - Vũ Duyên Tools")
        self.geometry("630x590")
        self.resizable(False, False)

        try:
            from ui_actions.icon_helper import apply_app_icon
            apply_app_icon(self)
        except Exception:
            pass

        self.center_window()
        self.lift()
        self.focus_force()

        # Handle window close immediately without blocking popups
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_ui()

    def center_window(self):
        self.update_idletasks()
        width = 630
        height = 590
        x = max(0, (self.winfo_screenwidth() // 2) - (width // 2))
        y = max(0, (self.winfo_screenheight() // 2) - (height // 2))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def on_close(self):
        """Handle clicking X button - close immediately and cleanly"""
        self.destroy()
        if not self.is_success:
            if not self.parent_window:
                # Standalone startup: exit process cleanly
                os._exit(0)
            else:
                try:
                    self.parent_window.deiconify()
                except Exception:
                    pass
        else:
            if self.parent_window:
                try:
                    self.parent_window.deiconify()
                except Exception:
                    pass

    def setup_ui(self):
        # Header Banner
        header_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        header_frame.pack(fill="x", padx=14, pady=(8, 3))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="🔐 XÁC THỰC BẢN QUYỀN THIẾT BỊ",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#38bdf8"
        )
        title_lbl.pack(pady=(6, 1))

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="VU DUYEN AUTO ALL IN ONE - HỆ THỐNG TỰ ĐỘNG HÓA ĐA NỀN TẢNG",
            font=ctk.CTkFont(size=10),
            text_color="#94a3b8"
        )
        sub_lbl.pack(pady=(0, 6))

        # HWID Card
        hwid_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        hwid_frame.pack(fill="x", padx=14, pady=3)

        hwid_title = ctk.CTkLabel(
            hwid_frame,
            text="💻 MÃ THIẾT BỊ CỦA BẠN (HWID KHÓA MÁY DUY NHẤT):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#e2e8f0"
        )
        hwid_title.pack(anchor="w", padx=12, pady=(6, 2))

        hwid_box = ctk.CTkFrame(hwid_frame, fg_color="#0f172a", corner_radius=6)
        hwid_box.pack(fill="x", padx=12, pady=(0, 4))

        self.hwid_entry = ctk.CTkEntry(
            hwid_box,
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#38bdf8",
            fg_color="transparent",
            border_width=0,
            justify="center",
            height=30
        )
        self.hwid_entry.insert(0, self.hwid)
        self.hwid_entry.configure(state="readonly")
        self.hwid_entry.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=3)

        copy_btn = ctk.CTkButton(
            hwid_box,
            text="📋 Sao Chép",
            width=85,
            height=28,
            fg_color="#0284c7",
            hover_color="#0369a1",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.copy_hwid
        )
        copy_btn.pack(side="right", padx=4, pady=3)

        hwid_note = ctk.CTkLabel(
            hwid_frame,
            text="ℹ Gửi mã thiết bị này cho Admin khi mua key hoặc cần hỗ trợ cấp phép bản quyền.",
            font=ctk.CTkFont(size=10, slant="italic"),
            text_color="#64748b"
        )
        hwid_note.pack(anchor="w", padx=12, pady=(0, 5))

        # Key Input Card
        key_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        key_frame.pack(fill="x", padx=14, pady=3)

        key_title = ctk.CTkLabel(
            key_frame,
            text="🔑 NHẬP MÃ BẢN QUYỀN (LICENSE KEY):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#e2e8f0"
        )
        key_title.pack(anchor="w", padx=12, pady=(6, 2))

        self.key_entry = ctk.CTkEntry(
            key_frame,
            placeholder_text="Nhập mã key (Ví dụ: VD-1M-XXXXXX hoặc VD-1Y-XXXXXX)...",
            font=ctk.CTkFont(family="Consolas", size=12),
            height=34,
            fg_color="#0f172a",
            border_color="#334155",
            border_width=1
        )
        self.key_entry.pack(fill="x", padx=12, pady=(0, 4))
        self.key_entry.bind("<Return>", lambda e: self.start_activation())

        self.status_lbl = ctk.CTkLabel(
            key_frame,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#f87171",
            wraplength=580
        )
        self.status_lbl.pack(padx=12, pady=(0, 2))

        self.activate_btn = ctk.CTkButton(
            key_frame,
            text="🚀 KÍCH HOẠT BẢN QUYỀN & MỞ TOOL",
            height=36,
            fg_color="#16a34a",
            hover_color="#15803d",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.start_activation
        )
        self.activate_btn.pack(fill="x", padx=12, pady=(0, 8))

        # Packages & Support Frame
        support_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        support_frame.pack(fill="x", padx=14, pady=3)

        pkg_title = ctk.CTkLabel(
            support_frame,
            text="📦 CÁC GÓI BẢN QUYỀN HỖ TRỢ:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#e2e8f0"
        )
        pkg_title.pack(anchor="w", padx=12, pady=(5, 2))

        pkg_info_grid = ctk.CTkFrame(support_frame, fg_color="transparent")
        pkg_info_grid.pack(fill="x", padx=12, pady=(0, 4))

        packages = [
            ("🔹 Gói 1 Tháng", "30 Ngày"),
            ("🔹 Gói 3 Tháng", "90 Ngày"),
            ("🔹 Gói 6 Tháng", "180 Ngày"),
            ("👑 Gói 1 Năm", "365 Ngày"),
            ("💎 Gói Vĩnh Viễn", "Trọn Đời"),
            ("📞 Hỗ Trợ 24/7", "Admin Zalo")
        ]

        for i, (p_name, p_desc) in enumerate(packages):
            col = i % 3
            row = i // 3
            box = ctk.CTkFrame(pkg_info_grid, fg_color="#0f172a", corner_radius=5)
            box.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            pkg_info_grid.columnconfigure(col, weight=1)

            lbl1 = ctk.CTkLabel(box, text=p_name, font=ctk.CTkFont(size=10, weight="bold"), text_color="#38bdf8")
            lbl1.pack(anchor="w", padx=5, pady=(2, 0))
            lbl2 = ctk.CTkLabel(box, text=p_desc, font=ctk.CTkFont(size=9), text_color="#94a3b8")
            lbl2.pack(anchor="w", padx=5, pady=(0, 2))

        # Contact & Buy Key Buttons (Zalo Group)
        btn_box = ctk.CTkFrame(support_frame, fg_color="transparent")
        btn_box.pack(fill="x", padx=12, pady=(4, 8))

        zalo_link = self.config.get("zalo_support", "https://zalo.me/g/mmgznzbleun8cirr19ld")

        zalo_btn = ctk.CTkButton(
            btn_box,
            text="💬 THAM GIA NHÓM ZALO ĐỂ MUA KEY & HỖ TRỢ",
            height=36,
            fg_color="#0284c7",
            hover_color="#0369a1",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: webbrowser.open(zalo_link)
        )
        zalo_btn.pack(fill="x", expand=True)

    def copy_hwid(self):
        try:
            pyperclip.copy(self.hwid)
            self.status_lbl.configure(
                text="✔ Đã sao chép mã thiết bị (HWID) vào bộ nhớ tạm!",
                text_color="#4ade80"
            )
        except Exception:
            self.status_lbl.configure(
                text=f"Mã máy của bạn: {self.hwid}",
                text_color="#38bdf8"
            )

    def start_activation(self):
        key = self.key_entry.get().strip()
        if not key:
            self.status_lbl.configure(
                text="⚠ Vui lòng nhập mã Key bản quyền!",
                text_color="#f87171"
            )
            return

        self.activate_btn.configure(state="disabled", text="⏳ ĐANG KIỂM TRA MÃ KEY...")
        self.status_lbl.configure(
            text="Đang kết nối máy chủ xác thực bản quyền...",
            text_color="#38bdf8"
        )

        def verify_thread():
            is_valid, msg, key_data = self.checker.activate_key(key)
            self.after(0, lambda: self.on_activation_finished(is_valid, msg, key_data))

        threading.Thread(target=verify_thread, daemon=True).start()

    def on_activation_finished(self, is_valid: bool, msg: str, key_data: dict):
        self.activate_btn.configure(state="normal", text="🚀 KÍCH HOẠT BẢN QUYỀN & MỞ TOOL")
        if is_valid:
            self.is_success = True
            self.status_lbl.configure(text=f"✔ {msg}", text_color="#4ade80")
            messagebox.showinfo("Thành Công", f"Kích hoạt bản quyền thành công!\n{msg}", parent=self)
            cb = self.on_success_callback
            self.destroy()
            if cb:
                cb(key_data)
        else:
            self.status_lbl.configure(text=f"❌ {msg}", text_color="#f87171")
            messagebox.showerror("Lỗi Kích Hoạt", msg, parent=self)

class StandaloneActivationWindow(ctk.CTk, ActivationViewMixin):
    def __init__(self, on_success_callback=None):
        super().__init__()
        self.init_activation_data(parent=None, on_success_callback=on_success_callback)

class ActivationDialog(ctk.CTkToplevel, ActivationViewMixin):
    def __init__(self, parent=None, on_success_callback=None):
        super().__init__(parent)
        self.init_activation_data(parent=parent, on_success_callback=on_success_callback)

def show_activation_dialog(parent=None, on_success_callback=None):
    """
    Opens activation dialog:
    - If parent is None: runs standalone CTk root window.
    - If parent is provided: opens modal CTkToplevel dialog.
    """
    if parent is None:
        dlg = StandaloneActivationWindow(on_success_callback=on_success_callback)
        dlg.mainloop()
        return dlg
    else:
        dlg = ActivationDialog(parent=parent, on_success_callback=on_success_callback)
        dlg.grab_set()
        dlg.focus_force()
        return dlg

def check_and_prompt_license(on_success, parent=None):
    """
    Checks if active license is already present.
    If valid -> immediately calls on_success(license_data).
    If not valid -> displays ActivationDialog.
    """
    checker = LicenseChecker()
    is_valid, msg, data = checker.check_current_license()
    if is_valid and data:
        on_success(data)
    else:
        show_activation_dialog(parent=parent, on_success_callback=on_success)

if __name__ == "__main__":
    def on_ok(data):
        print(f"License Activated successfully: {data}")
    show_activation_dialog(on_success_callback=on_ok)
