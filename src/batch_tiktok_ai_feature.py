import os
import json
import customtkinter as ctk
from tkinter import messagebox
from ui_actions.tiktok_ai_tab import open_tiktok_ai_window

AI_CONFIG_FILE = "ai_config.json"

def add_batch_tiktok_ai_checkbox(header_frame, app):
    """
    Thêm ô tích 'Quét và lên lịch hàng loạt' vào thanh công cụ của phần mềm.
    Tách riêng thành file độc lập để dễ dàng bảo trì và sửa chữa.
    """
    app.batch_tiktok_ai_var = ctk.StringVar(value="0")
    
    def on_batch_cb_clicked():
        if app.batch_tiktok_ai_var.get() == "1":
            open_batch_tiktok_ai_window(app)
        else:
            pass

    cb_batch = ctk.CTkCheckBox(
        header_frame,
        text="Quét và lên lịch hàng loạt",
        variable=app.batch_tiktok_ai_var,
        onvalue="1",
        offvalue="0",
        command=on_batch_cb_clicked,
        text_color="#c084fc", # Màu tím sáng nổi bật
        font=ctk.CTkFont(weight="bold", size=13)
    )
    cb_batch.pack(side="left", padx=(25, 10))


def open_batch_tiktok_ai_window(app):
    """
    Giao diện khởi chạy: Khi bấm 'Bắt Đầu', cửa sổ Quét TikTok & Lên Lịch AI 
    của từng tài khoản sẽ hiện lên đồng loạt và tự động bắt đầu quét theo cấu hình riêng của từng nick.
    (Chỉ cho phép mở DUY NHẤT 1 cửa sổ, tránh mở trùng lặp)
    """
    # Nếu cửa sổ đã tồn tại và đang mở thì chỉ cần đưa lên đầu, không tạo cửa sổ mới
    if hasattr(app, 'batch_tiktok_ai_window') and app.batch_tiktok_ai_window:
        try:
            if app.batch_tiktok_ai_window.winfo_exists():
                app.batch_tiktok_ai_window.deiconify()
                app.batch_tiktok_ai_window.lift()
                app.batch_tiktok_ai_window.focus()
                return app.batch_tiktok_ai_window
        except Exception:
            pass

    window = ctk.CTkToplevel(app)
    app.batch_tiktok_ai_window = window
    window.title("⚡ Quét & Lên Lịch TikTok AI Hàng Loạt")
    window.geometry("520x460")
    window.lift()
    window.focus()

    # Set Window Icon
    try:
        from ui_actions.icon_helper import apply_app_icon
        apply_app_icon(window)
    except: pass

    def on_close():
        if hasattr(app, 'batch_tiktok_ai_var'):
            app.batch_tiktok_ai_var.set("0")
        app.batch_tiktok_ai_window = None
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)

    # Tiêu đề
    ctk.CTkLabel(
        window, 
        text="⚡ QUÉT & LÊN LỊCH TIKTOK AI ĐỒNG LOẠT", 
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="#c084fc"
    ).pack(pady=(15, 5))

    ctk.CTkLabel(
        window,
        text="Mỗi tài khoản sẽ sử dụng cấu hình Quét TikTok & Lên Lịch riêng đã cài đặt.\nKhi bấm 'Bắt Đầu', tất cả cửa sổ của các nick được chọn sẽ hiện lên\nvà tự động bắt đầu quét & lên lịch song song.",
        font=ctk.CTkFont(size=12),
        text_color="#cccccc",
        justify="center"
    ).pack(padx=15, pady=(0, 10))

    # Load AI config để hiển thị link đã lưu của từng nick
    ai_config = {}
    if os.path.exists(AI_CONFIG_FILE):
        try:
            with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                ai_config = json.load(f)
        except:
            pass
    acc_configs = ai_config.get("accounts", {})

    # Danh sách tài khoản
    acc_box = ctk.CTkFrame(window)
    acc_box.pack(fill="both", expand=True, padx=20, pady=5)

    ctk.CTkLabel(acc_box, text="Danh sách tài khoản áp dụng:", font=ctk.CTkFont(weight="bold", size=13)).pack(anchor="w", padx=10, pady=(8, 4))

    acc_scroll = ctk.CTkScrollableFrame(acc_box, height=180)
    acc_scroll.pack(fill="both", expand=True, padx=10, pady=5)

    account_cb_vars = []
    
    if not app.account_frames:
        ctk.CTkLabel(acc_scroll, text="Chưa có tài khoản nào trên giao diện chính!", text_color="orange").pack(padx=10, pady=10)
    else:
        for idx, acc in enumerate(app.account_frames):
            acc_id = acc['id_entry'].get().strip() or f"Tài khoản #{idx+1}"
            cfg = acc_configs.get(acc_id, {})
            mode = cfg.get("tiktok_crawl_mode", "channel")
            link_info = cfg.get("tiktok_start_video_url") if mode == "from_video" else cfg.get("tiktok_url")
            
            if link_info:
                display_text = f"{acc_id}  ({link_info[:35]}...)" if len(link_info) > 35 else f"{acc_id}  ({link_info})"
            else:
                display_text = f"{acc_id}  (Chưa cài link TikTok)"

            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(acc_scroll, text=display_text, variable=var, font=ctk.CTkFont(size=12))
            cb.pack(anchor="w", padx=8, pady=3)
            account_cb_vars.append((acc_id, var))

    # Nút chọn tất cả
    btn_bar = ctk.CTkFrame(acc_box, fg_color="transparent")
    btn_bar.pack(fill="x", padx=10, pady=(2, 8))

    def select_all(state=True):
        for _, var in account_cb_vars:
            var.set(state)

    ctk.CTkButton(btn_bar, text="Chọn tất cả", width=85, height=24, command=lambda: select_all(True)).pack(side="left", padx=2)
    ctk.CTkButton(btn_bar, text="Bỏ chọn tất cả", width=85, height=24, command=lambda: select_all(False)).pack(side="left", padx=5)

    # Nút Bắt Đầu Đồng Loạt
    def start_batch_launch():
        selected = [acc_id for acc_id, var in account_cb_vars if var.get()]
        if not selected:
            messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất 1 tài khoản để chạy!")
            return

        # Đóng cửa sổ launcher
        on_close()

        # Mở đồng loạt các cửa sổ Quét TikTok AI của từng tài khoản và tự động kích hoạt
        for idx, acc_id in enumerate(selected):
            # Tạo độ trễ nhẹ giữa các cửa sổ để UI mở mượt mà
            delay_ms = idx * 250
            app.after(delay_ms, lambda a_id=acc_id: open_tiktok_ai_window(app, default_target_acc_id=a_id, auto_start=True))

    btn_start = ctk.CTkButton(
        window,
        text="▶ BẮT ĐẦU QUÉT & LÊN LỊCH ĐỒNG LOẠT",
        font=ctk.CTkFont(size=14, weight="bold"),
        fg_color="green",
        hover_color="darkgreen",
        height=45,
        command=start_batch_launch
    )
    btn_start.pack(padx=20, pady=(10, 15), fill="x")
