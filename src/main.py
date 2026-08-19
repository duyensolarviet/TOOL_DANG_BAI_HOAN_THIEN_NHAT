import customtkinter as ctk

from tkinter import messagebox
import threading
from bot_manager import BotManager
import json
import os
import datetime
from ui_actions.open_browser import open_manual_browser
from ui_actions.save_data import save_data_and_notify
from ui_actions.add_post import add_post_block, add_post_from_sample, extract_single_post_data
from cleaner import clean_chrome_cache
from license_manager.license_checker import LicenseChecker
from license_manager.activation_dialog import show_activation_dialog, check_and_prompt_license
from license_manager.hwid import get_device_hwid

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

DATA_FILE = "accounts.json"

class App(ctk.CTk):
    def __init__(self, license_data=None):
        super().__init__()
        ctk.set_widget_scaling(0.9)
        self.title("Tool auto All In One Main Vũ Duyên")
        self.geometry("1050x700")
        
        self.license_data = license_data
        if not self.license_data:
            checker = LicenseChecker()
            _, _, self.license_data = checker.check_current_license()
        
        # Set App Icon
        try:
            from ui_actions.icon_helper import apply_app_icon
            apply_app_icon(self)
        except: pass
        
        self.accounts = []
        self.account_frames = []
        
        self.last_saved_data = None
        
        self.load_data()
        self.setup_ui()
        
        # Bắt đầu vòng lặp auto-save & heartbeat online
        self.after(2000, self.auto_save_loop)
        self.after(5000, self.license_heartbeat_loop)
        
        try:
            from window_arranger import start_auto_arranger
            start_auto_arranger()
        except: pass
        
    def auto_save_loop(self):
        try:
            current_data = self.get_accounts_data()
            if self.last_saved_data != current_data:
                self.save_data_silent(current_data)
                self.last_saved_data = current_data
        except Exception:
            pass
        self.after(2000, self.auto_save_loop)

    def license_heartbeat_loop(self):
        def _ping():
            try:
                checker = LicenseChecker()
                is_valid, msg, _ = checker.check_current_license()
                if not is_valid:
                    self.after(0, lambda: self.handle_license_revoked(msg))
                else:
                    checker.update_heartbeat(self.license_data)
            except Exception:
                pass
        threading.Thread(target=_ping, daemon=True).start()
        self.after(5 * 1000, self.license_heartbeat_loop) # Check every 5 seconds for real-time instant kickout

    def handle_license_revoked(self, msg: str = ""):
        """Called when key is banned, deleted, or expired while tool is open"""
        reason = msg or "Bản quyền đã bị khóa hoặc hết hạn bởi Quản trị viên!"
        try:
            messagebox.showerror("Khóa Bản Quyền", f"❌ {reason}\n\nPhần mềm sẽ tự động dừng và thoát ngay bây giờ!", parent=self)
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
        os._exit(0)
        
    def setup_ui(self):
        # Header with Logo on Top-Left (Larger size)
        header_container = ctk.CTkFrame(self, fg_color="transparent")
        header_container.pack(fill="x", padx=15, pady=(8, 4))

        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.getcwd(), "assets", "logo.png")

        if os.path.exists(logo_path):
            try:
                from PIL import Image
                logo_pil = Image.open(logo_path)
                w, h = logo_pil.size
                target_h = 52
                target_w = int(w * (target_h / h))
                logo_img = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(target_w, target_h))
                logo_lbl = ctk.CTkLabel(header_container, image=logo_img, text="")
                logo_lbl.pack(side="left", padx=(0, 12))
            except Exception: pass

        title_box = ctk.CTkFrame(header_container, fg_color="transparent")
        title_box.pack(side="left", fill="y", expand=False)
        
        self.header_label = ctk.CTkLabel(title_box, text="VU DUYEN TOOLS - AUTO ALL IN ONE", font=ctk.CTkFont(size=20, weight="bold"), text_color="#38bdf8")
        self.header_label.pack(anchor="w")
        
        sub_title = ctk.CTkLabel(title_box, text="Hệ Thống Tự Động Hóa & Đăng Bài Đa Nền Tảng AI", font=ctk.CTkFont(size=12), text_color="#94a3b8")
        sub_title.pack(anchor="w")
        
        # Badge & Nút Thông Tin Bản Quyền / Dùng Thử
        try:
            badge_text = LicenseChecker.format_license_badge(self.license_data)
            is_trial = (self.license_data or {}).get("type") == "trial" or (self.license_data or {}).get("package") == "trial_auto"
            btn_fg = "#d97706" if is_trial else "#065f46"
            btn_hover = "#b45309" if is_trial else "#047857"
            
            self.license_btn = ctk.CTkButton(
                header_container,
                text=badge_text,
                fg_color=btn_fg,
                hover_color=btn_hover,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=self.show_license_info_popup
            )
            self.license_btn.pack(side="right", padx=5, pady=5)
        except Exception:
            pass
        
        # Nút liên kết Nhóm Zalo Hỗ Trợ (In đậm, nổi bật ở đầu trang)
        try:
            from ui_actions.zalo_support_ui import create_zalo_support_button
            zalo_btn = create_zalo_support_button(header_container)
            zalo_btn.pack(side="right", padx=5, pady=5)
        except Exception:
            pass
        
        # Bỏ config_frame vì các cài đặt giờ ở trong từng dòng tài khoản
        self.acc_header_frame = ctk.CTkFrame(self)
        self.acc_header_frame.pack(fill="x", padx=5, pady=1)
        
        ctk.CTkLabel(self.acc_header_frame, text="Danh sách tài khoản & Video", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)
        
        # --- UI CHIA CỬA SỔ ---
        try:
            from window_arranger import get_config, set_config
            config = get_config()
            self.split_cols_var = ctk.StringVar(value=config.get("split_cols", "2"))
            self.auto_arrange_var = ctk.StringVar(value=config.get("auto_arrange", "1"))
            
            lbl_split = ctk.CTkLabel(self.acc_header_frame, text="| Chia ô Chrome (Cột):")
            lbl_split.pack(side="left", padx=15)
            
            entry_split = ctk.CTkEntry(self.acc_header_frame, textvariable=self.split_cols_var, width=50)
            entry_split.pack(side="left", padx=2)
            
            chk_auto_arrange = ctk.CTkCheckBox(self.acc_header_frame, text="Sắp xếp Chrome", variable=self.auto_arrange_var, onvalue="1", offvalue="0")
            chk_auto_arrange.pack(side="left", padx=10)
            
            def save_split_config(*_):
                set_config(val=self.split_cols_var.get(), auto_arrange=self.auto_arrange_var.get())
                try:
                    from window_arranger import auto_arrange_windows
                    if self.auto_arrange_var.get() == "1":
                        cols_str = self.split_cols_var.get()
                        if cols_str and cols_str.isdigit() and int(cols_str) > 0:
                            auto_arrange_windows(int(cols_str))
                except Exception:
                    pass
            self.split_cols_var.trace_add("write", save_split_config)
            self.auto_arrange_var.trace_add("write", save_split_config)
        except Exception as e:
            print("Lỗi load window_arranger:", e)
        # ------------------------

        # Nút dọn dẹp profile rác
        def on_clean_profiles_click():
            try:
                from ui_actions.clean_profiles import clean_unused_profiles
                clean_unused_profiles(self)
            except Exception as ex:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Lỗi", f"Không thể tải chức năng: {ex}")

        self.clean_profile_btn = ctk.CTkButton(
            self.acc_header_frame, 
            text="Xoá Profile Rác", 
            fg_color="#c0392b", hover_color="#e74c3c", 
            command=on_clean_profiles_click
        )
        self.clean_profile_btn.pack(side="left", padx=5)

        self.add_acc_btn = ctk.CTkButton(self.acc_header_frame, text="Thêm Tài Khoản", command=self.add_account_row)
        self.add_acc_btn.pack(side="left", padx=10)
        
        try:
            from batch_tiktok_ai_feature import add_batch_tiktok_ai_checkbox
            add_batch_tiktok_ai_checkbox(self.acc_header_frame, self)
        except Exception as e:
            print("Lỗi load batch_tiktok_ai_feature:", e)
        
        try:
            from delete_posted_feature import add_delete_posted_checkbox
            add_delete_posted_checkbox(self.acc_header_frame, self)
        except Exception as e:
            print("Lỗi load delete_posted_feature:", e)
        
        self.acc_scroll_frame = ctk.CTkScrollableFrame(self, height=200)
        self.acc_scroll_frame.pack(fill="both", expand=True, padx=5, pady=1)
        
        if not self.accounts:
            self.add_account_row() 
        else:
            for acc in self.accounts:
                self.add_account_row(acc)
                
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.pack(fill="x", padx=5, pady=1)
        
        self.log_label = ctk.CTkLabel(self.log_frame, text="Nhật ký hoạt động (Log):", font=ctk.CTkFont(weight="bold"))
        self.log_label.pack(anchor="w", padx=2, pady=2)
        
        self.log_textbox = ctk.CTkTextbox(self.log_frame, height=100, state="disabled")
        self.log_textbox.pack(fill="x", padx=2, pady=1)
        
        self.footer_frame = ctk.CTkFrame(self)
        self.footer_frame.pack(fill="x", padx=5, pady=1)
        
        # Đóng tất cả chrome
        self.close_chrome_btn = ctk.CTkButton(self.footer_frame, text="Đóng Tất Cả Chrome", font=ctk.CTkFont(weight="bold"),
                                              command=self.close_all_chrome, fg_color="#b30000", hover_color="#800000", height=40)
        self.close_chrome_btn.pack(side="left", padx=5, pady=2)
        
        # Nút Dừng Tool
        self.stop_btn = ctk.CTkButton(self.footer_frame, text="🛑 DỪNG TOOL", font=ctk.CTkFont(weight="bold"),
                                      command=self.stop_bot, fg_color="red", hover_color="darkred", height=40, state="disabled")
        self.stop_btn.pack(side="right", padx=5, pady=2)
        
        # Nút Bắt đầu
        self.start_btn = ctk.CTkButton(self.footer_frame, text="▶ BẮT ĐẦU CHẠY ĐA LUỒNG", font=ctk.CTkFont(weight="bold"), 
                                       command=self.start_bot, fg_color="green", hover_color="darkgreen", height=40)
        self.start_btn.pack(side="right", padx=2, pady=2)
        
    def delete_account_row(self, frame):
        for acc in self.account_frames:
            if acc['frame'] == frame:
                self.account_frames.remove(acc)
                break
        frame.destroy()
        self.save_data_silent(self.get_accounts_data())

    def add_account_row(self, acc_data=None):
        frame = ctk.CTkFrame(self.acc_scroll_frame, border_width=1, border_color="#333333")
        frame.pack(fill="x", pady=1, padx=5)
        
        # Row 1: Credentials
        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", pady=1)
        
        id_entry = ctk.CTkEntry(row1, width=150, placeholder_text="ID")
        id_entry.pack(side="left", padx=5)
        
        pw_entry = ctk.CTkEntry(row1, width=150, placeholder_text="Password", show="*")
        pw_entry.pack(side="left", padx=5)
        
        twofa_entry = ctk.CTkEntry(row1, width=200, placeholder_text="2FA Secret Code")
        twofa_entry.pack(side="left", padx=5)
        
        def open_acc_ai():
            from ui_actions.tiktok_ai_tab import open_tiktok_ai_window
            current_id = id_entry.get().strip()
            open_tiktok_ai_window(self, default_target_acc_id=current_id)

        ai_btn = ctk.CTkButton(row1, text="👾 Quét TikTok & Lên Lịch AI", width=170, fg_color="#8e44ad", hover_color="#732d91",
                               command=open_acc_ai)
        ai_btn.pack(side="left", padx=10)
        
        del_btn = ctk.CTkButton(row1, text="Xoá", width=60, fg_color="red", hover_color="darkred",
                                command=lambda f=frame: self.delete_account_row(f))
        del_btn.pack(side="right", padx=5)
        
        save_btn = ctk.CTkButton(row1, text="Lưu Lại", width=70, fg_color="#2da44e", hover_color="#2c974b",
                                command=lambda: save_data_and_notify(self))
        save_btn.pack(side="right", padx=5)
        
        open_btn = ctk.CTkButton(row1, text="Mở Trình Duyệt", width=120, fg_color="#1f538d", hover_color="#14375e",
                                command=lambda f=frame: open_manual_browser(self, f))
        open_btn.pack(side="right", padx=5)
        
        posts_container = ctk.CTkFrame(frame, fg_color="transparent", height=0)
        posts_container.pack(fill="x", pady=2)
        
        acc_dict = {
            'frame': frame,
            'id_entry': id_entry,
            'pw_entry': pw_entry,
            'twofa_entry': twofa_entry,
            'posts_container': posts_container,
            'posts': []
        }
        self.account_frames.append(acc_dict)
        
        add_post_btn = ctk.CTkButton(frame, text="+ Thêm Bài Đăng", width=150, fg_color="#1f538d", command=lambda: add_post_from_sample(self, acc_dict))
        add_post_btn.pack(pady=5)
        
        if acc_data:
            id_entry.insert(0, acc_data.get('id', ''))
            pw_entry.insert(0, acc_data.get('password', ''))
            twofa_entry.insert(0, acc_data.get('two_fa', ''))
            if 'posts' in acc_data and len(acc_data['posts']) > 0:
                has_sample = any(str(p.get('is_sample', '0')) == '1' for p in acc_data['posts'])
                for idx, p_data in enumerate(acc_data['posts']):
                    if not has_sample and idx == 0:
                        p_data['is_sample'] = '1'
                    add_post_block(self, acc_dict, p_data)
            else:
                add_post_block(self, acc_dict, {'is_sample': '1'})
        else:
            add_post_block(self, acc_dict, {'is_sample': '1'})

    def get_accounts_data(self):
        data = []
        for acc in self.account_frames:
            uid = acc['id_entry'].get().strip()
            pw = acc['pw_entry'].get().strip()
            twofa = acc['twofa_entry'].get().strip()
            
            if not uid: continue
            
            account_data = {
                'id': uid,
                'password': pw,
                'two_fa': twofa,
                'posts': []
            }
            
            for post in acc['posts']:
                post_data = extract_single_post_data(post)
                if post_data:
                    account_data['posts'].append(post_data)
                
            # Grouping by ID across frames
            existing_account = next((item for item in data if item["id"] == uid), None)
            if existing_account:
                existing_account['posts'].extend(account_data['posts'])
            else:
                data.append(account_data)
                
        return data

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.accounts = json.load(f)
            except Exception as e:
                print(f"Lỗi load dữ liệu: {e}")
                
    def save_data(self):
        accounts = self.get_accounts_data()
        self.save_data_silent(accounts)
        self.last_saved_data = accounts
            
    def save_data_silent(self, accounts):
        try:
            # Loại bỏ các object không serialize được (như post_frame) trước khi lưu JSON
            clean_accounts = []
            for acc in accounts:
                clean_acc = acc.copy()
                clean_posts = []
                for p in acc.get('posts', []):
                    clean_p = p.copy()
                    if 'post_frame' in clean_p:
                        del clean_p['post_frame']
                    clean_posts.append(clean_p)
                clean_acc['posts'] = clean_posts
                clean_accounts.append(clean_acc)
                
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(clean_accounts, f, indent=4)
        except Exception as e:
            print(f"Lỗi lưu dữ liệu: {e}")
            
    def close_all_chrome(self):
        try:
            os.system("taskkill /F /IM chrome.exe /T >nul 2>&1")
            os.system("taskkill /F /IM chromedriver.exe /T >nul 2>&1")
            
            # Dọn dẹp cache cho tất cả tài khoản
            try:
                profiles_dir = os.path.join(os.getcwd(), 'profiles')
                if os.path.exists(profiles_dir):
                    for acc in os.listdir(profiles_dir):
                        if os.path.isdir(os.path.join(profiles_dir, acc)):
                            clean_chrome_cache(acc)
                self.write_log("Đã đóng Chrome và dọn dẹp bộ nhớ đệm (Cache) thành công.")
            except Exception as e:
                self.write_log(f"Đã đóng Chrome nhưng lỗi dọn cache: {e}")
                
        except Exception as e:
            self.write_log(f"Lỗi khi đóng Chrome: {e}")

    def stop_bot(self):
        if hasattr(self, 'manager') and self.manager:
            self.manager.stop()
            self.write_log("Đã gửi tín hiệu dừng Tool. Đang chờ các tiến trình hoàn tất hoặc hãy nhấn 'Đóng Tất Cả Chrome'.")
        self.start_btn.configure(state="normal", text="▶ BẮT ĐẦU CHẠY ĐA LUỒNG")
        self.stop_btn.configure(state="disabled")

    def write_log(self, message):
        def append():
            self.log_textbox.configure(state="normal")
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_textbox.insert("end", f"[{time_str}] {message}\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self.after(0, append)
            
    def start_bot(self):
        checker = LicenseChecker()
        is_valid, msg, _ = checker.check_current_license()
        if not is_valid:
            self.handle_license_revoked(msg)
            return

        self.save_data()
        
        accounts = self.get_accounts_data()
        
        if not accounts:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất 1 tài khoản!")
            return
            
        # Lọc ra những tài khoản có media (video/ảnh) hoặc nội dung mô tả
        valid_accounts = []
        for acc in accounts:
            vid_paths = [p.strip() for p in acc.get('video_path', '').split('\n') if p.strip()]
            img_paths = [p.strip() for p in acc.get('image_path', '').split('\n') if p.strip()]
            
            has_desc = bool(acc.get('description', ''))
            
            # Giờ tài khoản chỉ cần hợp lệ ID để chạy Zalo hoặc Facebook. Không bắt buộc phải có media (nếu chỉ đi tương tác)
            if acc.get('id'):
                valid_accounts.append(acc)
                
        if not valid_accounts:
            messagebox.showwarning("Cảnh báo", "Không có tài khoản nào được cấu hình đăng bài hợp lệ (Cần video/ảnh hoặc nội dung)!")
            return
        
        # Thông báo rõ từng tài khoản: lên lịch hay đăng ngay
        for acc in valid_accounts:
            uid = acc.get('id', '')
            if acc.get('is_schedule') == '1':
                d = acc.get('sch_d', '?')
                m = acc.get('sch_m', '?')
                y = acc.get('sch_y', '?')
                h = acc.get('sch_h', '?')
                mn = acc.get('sch_min', '?')
                self.write_log(f"[{uid}] [Schedule] Hẹn đăng vào: {d}/{m}/{y} lúc {h}:{mn} — Đang bắt đầu đếm ngược...")
            else:
                self.write_log(f"[{uid}] Sẽ đăng NGAY LẬP TỨC.")
            
        self.start_btn.configure(state="disabled", text="⏳ ĐANG CHỜ / ĐANG CHẠY...")
        self.stop_btn.configure(state="normal")
        self.write_log(f"==== BẮT ĐẦU CHẠY ĐA LUỒNG ({len(valid_accounts)} tài khoản) ====")
        
        self.manager = BotManager(valid_accounts, log_callback=self.write_log, app=self)
        
        def run_manager():
            self.manager.start_all()
            self.after(0, self.on_bot_finished)
            
        threading.Thread(target=run_manager, daemon=True).start()
        
    def on_bot_finished(self):
        self.start_btn.configure(state="normal", text="▶ BẮT ĐẦU CHẠY ĐA LUỒNG")
        self.stop_btn.configure(state="disabled")
        self.write_log("==== HOÀN THÀNH ====")
        
        try:
            if hasattr(self, 'is_auto_delete_posted_var') and self.is_auto_delete_posted_var.get() == "1":
                self.write_log("Đang tự động đóng Chrome do tính năng dọn dẹp được bật...")
                self.close_all_chrome()
        except Exception as e:
            self.write_log(f"Lỗi khi đóng Chrome cuối phiên: {e}")
            
        messagebox.showinfo("Hoàn thành", "Đã hoàn thành chạy tất cả tài khoản!")

    def show_license_info_popup(self):
        """Hiển thị thông tin chi tiết bản quyền và cho phép đổi key"""
        hwid = get_device_hwid()
        data = self.license_data or {}
        key = data.get("key", "Chưa có")
        pkg = data.get("duration_label") or data.get("package", "Bản quyền")
        exp = data.get("expires_at", "Chưa xác định")
        act = data.get("activated_at") or data.get("created_at", "Chưa xác định")
        
        info_text = (
            f"👑 BẢN QUYỀN PHẦN MỀM VU DUYEN TOOLS\n\n"
            f"🔑 Mã Key: {key}\n"
            f"📦 Gói dịch vụ: {pkg}\n"
            f"📅 Kích hoạt lúc: {act}\n"
            f"⏳ Hạn dùng đến: {exp}\n"
            f"💻 Mã thiết bị (HWID): {hwid}\n\n"
            f"Bạn có muốn đổi sang mã Key mới không?"
        )
        dialog_title = "Thông Tin Bản Quyền"

        if messagebox.askyesno(dialog_title, info_text, parent=self):
            self.withdraw()
            def on_re_activate(new_data):
                self.license_data = new_data
                if hasattr(self, 'license_btn'):
                    self.license_btn.configure(
                        text=LicenseChecker.format_license_badge(new_data),
                        fg_color="#065f46",
                        hover_color="#047857"
                    )
                self.deiconify()
                
            show_activation_dialog(parent=self, on_success_callback=on_re_activate)

if __name__ == "__main__":
    checker = LicenseChecker()
    is_valid, msg, lic_data = checker.check_current_license()
    
    if is_valid and lic_data:
        app = App(license_data=lic_data)
        app.mainloop()
    else:
        def on_activation_ok(new_lic_data):
            app = App(license_data=new_lic_data)
            app.mainloop()
            
        show_activation_dialog(on_success_callback=on_activation_ok)

