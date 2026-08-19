import customtkinter as ctk
import threading
from tkinter import messagebox, filedialog
from datetime import datetime, timedelta
from tiktok_crawler import TikTokCrawler
from tiktok_crawler_from_video import TikTokVideoStartCrawler
from ai_helper import GeminiHelper, GroqHelper
import json
import os

AI_CONFIG_FILE = "ai_config.json"

def open_tiktok_ai_window(app, default_target_acc_id=None, auto_start=False):
    # 1. Quản lý cửa sổ đơn lẻ cho từng tài khoản (Chỉ mở tối đa 1 tab/cửa sổ cho mỗi nick)
    if not hasattr(app, 'active_tiktok_ai_windows'):
        app.active_tiktok_ai_windows = {}

    acc_key = (default_target_acc_id or "default").strip()
    
    if acc_key in app.active_tiktok_ai_windows:
        existing_win = app.active_tiktok_ai_windows[acc_key]
        try:
            if existing_win.winfo_exists():
                existing_win.deiconify()
                existing_win.lift()
                existing_win.focus()
                return existing_win
        except Exception:
            pass

    window = ctk.CTkToplevel(app)
    app.active_tiktok_ai_windows[acc_key] = window
    
    title_acc = f" - Tài Khoản: {default_target_acc_id}" if default_target_acc_id else ""
    window.title(f"Quét TikTok & Lên Lịch AI{title_acc}")
    window.geometry("600x670")
    window.lift()
    window.focus()
    
    # Set Window Icon
    try:
        from ui_actions.icon_helper import apply_app_icon
        apply_app_icon(window)
    except: pass
        
    # --- Tiêu đề ---
    ctk.CTkLabel(window, text="TÍCH HỢP AI TỰ ĐỘNG CRAWL & LÊN LỊCH", font=ctk.CTkFont(size=16, weight="bold"), text_color="#38bdf8").pack(pady=10)
    
    # Load AI Config từ file
    ai_config = {}
    if os.path.exists(AI_CONFIG_FILE):
        try:
            with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                ai_config = json.load(f)
        except Exception as e:
            print("Lỗi đọc AI Config:", e)

    acc_configs = ai_config.get("accounts", {})
    acc_cfg = acc_configs.get(default_target_acc_id, {}) if default_target_acc_id else {}

    # 0. Provider
    prov_frame = ctk.CTkFrame(window, fg_color="transparent")
    prov_frame.pack(fill="x", padx=10, pady=3)
    ctk.CTkLabel(prov_frame, text="Nhà cung cấp AI:").pack(side="left", padx=5)
    
    saved_provider = acc_cfg.get("ai_provider") or ai_config.get("ai_provider", "Gemini")
    provider_combo = ctk.CTkComboBox(prov_frame, values=["Gemini", "Groq"], width=200)
    provider_combo.pack(side="left", padx=5)
    provider_combo.set(saved_provider)

    # 1. API Key
    api_frame = ctk.CTkFrame(window, fg_color="transparent")
    api_frame.pack(fill="x", padx=10, pady=3)
    api_lbl = ctk.CTkLabel(api_frame, text="Gemini API Key:" if saved_provider == "Gemini" else "Groq API Key:")
    api_lbl.pack(side="left", padx=5)
    
    saved_gemini_key = ai_config.get("gemini_api_key", "")
    saved_groq_key = ai_config.get("groq_api_key", "")
    
    api_entry = ctk.CTkEntry(api_frame, width=300, show="*", placeholder_text="Nhập API Key")
    api_entry.pack(side="left", padx=5)
    if saved_provider == "Gemini" and saved_gemini_key:
        api_entry.insert(0, saved_gemini_key)
    elif saved_provider == "Groq" and saved_groq_key:
        api_entry.insert(0, saved_groq_key)
    
    # 2. Target Account
    acc_frame = ctk.CTkFrame(window, fg_color="transparent")
    acc_frame.pack(fill="x", padx=10, pady=3)
    ctk.CTkLabel(acc_frame, text="Chọn tài khoản để đăng:").pack(side="left", padx=5)
    
    account_ids = [acc['id_entry'].get() for acc in app.account_frames if acc['id_entry'].get().strip()]
    if not account_ids:
        account_ids = ["Chưa có tài khoản nào"]
        
    acc_combo = ctk.CTkComboBox(acc_frame, values=account_ids, width=200)
    acc_combo.pack(side="left", padx=5)
    if default_target_acc_id and default_target_acc_id in account_ids:
        acc_combo.set(default_target_acc_id)
    
    # 3. TikTok URL & Mode
    url_frame = ctk.CTkFrame(window, fg_color="transparent")
    url_frame.pack(fill="x", padx=10, pady=3)
    
    saved_crawl_mode = acc_cfg.get("tiktok_crawl_mode") or ai_config.get("tiktok_crawl_mode", "channel")
    crawl_mode_var = ctk.StringVar(value=saved_crawl_mode)
    
    # Hàng 1: Link Kênh TikTok
    channel_sub_frame = ctk.CTkFrame(url_frame, fg_color="transparent")
    channel_sub_frame.pack(fill="x", pady=2)
    
    cb_mode_channel = ctk.CTkCheckBox(channel_sub_frame, text="Link Kênh TikTok:", font=ctk.CTkFont(size=12, weight="bold"))
    cb_mode_channel.pack(side="left", padx=5)
    
    saved_url = acc_cfg.get("tiktok_url") or ai_config.get("tiktok_url", "")
    url_entry = ctk.CTkEntry(channel_sub_frame, width=370, placeholder_text="https://www.tiktok.com/@username")
    url_entry.pack(side="left", padx=5)
    if saved_url: url_entry.insert(0, saved_url)
    
    # Hàng 2: Link kênh bắt đầu tải từ video này
    video_sub_frame = ctk.CTkFrame(url_frame, fg_color="transparent")
    video_sub_frame.pack(fill="x", pady=2)
    
    cb_mode_from_video = ctk.CTkCheckBox(video_sub_frame, text="Link kênh bắt đầu tải từ video này:", font=ctk.CTkFont(size=12, weight="bold"))
    cb_mode_from_video.pack(side="left", padx=5)
    
    saved_start_video = acc_cfg.get("tiktok_start_video_url") or ai_config.get("tiktok_start_video_url", "")
    start_video_entry = ctk.CTkEntry(video_sub_frame, width=285, placeholder_text="https://www.tiktok.com/@username/video/...")
    start_video_entry.pack(side="left", padx=5)
    if saved_start_video: start_video_entry.insert(0, saved_start_video)
    
    # Initial state of mode checkboxes
    if saved_crawl_mode == "from_video":
        cb_mode_from_video.select()
        cb_mode_channel.deselect()
        start_video_entry.configure(state="normal")
        url_entry.configure(state="disabled")
    else:
        cb_mode_channel.select()
        cb_mode_from_video.deselect()
        url_entry.configure(state="normal")
        start_video_entry.configure(state="disabled")
    
    # 4. Max Videos & Interval
    config_frame = ctk.CTkFrame(window, fg_color="transparent")
    config_frame.pack(fill="x", padx=10, pady=3)
    
    saved_max = acc_cfg.get("tiktok_max_videos") or ai_config.get("tiktok_max_videos", "5")
    ctk.CTkLabel(config_frame, text="Số lượng:").pack(side="left", padx=2)
    max_vid_entry = ctk.CTkEntry(config_frame, width=30)
    max_vid_entry.insert(0, str(saved_max))
    max_vid_entry.pack(side="left", padx=2)
    
    saved_dl_all = acc_cfg.get("tiktok_download_all", ai_config.get("tiktok_download_all", False))
    download_all_var = ctk.BooleanVar(value=bool(saved_dl_all))
    
    dl_all_cb = ctk.CTkCheckBox(config_frame, text="Tải tất cả", variable=download_all_var, font=ctk.CTkFont(size=12))
    dl_all_cb.pack(side="left", padx=(10, 5))
    if saved_dl_all:
        max_vid_entry.configure(state="disabled")
    
    saved_interval = acc_cfg.get("tiktok_interval") or ai_config.get("tiktok_interval", "4")
    ctk.CTkLabel(config_frame, text="Giãn cách(Giờ):").pack(side="left", padx=5)
    interval_entry = ctk.CTkEntry(config_frame, width=30)
    interval_entry.insert(0, str(saved_interval))
    interval_entry.pack(side="left", padx=2)
    
    saved_dl_dir = acc_cfg.get("tiktok_dl_dir") or ai_config.get("tiktok_dl_dir", "")
    ctk.CTkLabel(config_frame, text="Thư mục lưu:").pack(side="left", padx=5)
    dl_dir_entry = ctk.CTkEntry(config_frame, width=150, placeholder_text="Mặc định: tiktok_downloads")
    dl_dir_entry.pack(side="left", padx=2)
    if saved_dl_dir: dl_dir_entry.insert(0, saved_dl_dir)
    
    def choose_dir():
        d = filedialog.askdirectory(title="Chọn thư mục lưu video")
        if d:
            dl_dir_entry.delete(0, 'end')
            dl_dir_entry.insert(0, d)
            auto_save_all_settings()
            
    btn_choose_dir = ctk.CTkButton(config_frame, text="Chọn...", width=50, command=choose_dir)
    btn_choose_dir.pack(side="left", padx=2)
    
    # 4.5. Chế độ tải (History Mode)
    history_mode_frame = ctk.CTkFrame(window, fg_color="transparent")
    history_mode_frame.pack(fill="x", padx=10, pady=3)
    ctk.CTkLabel(history_mode_frame, text="Chế độ tải:").pack(side="left", padx=5)
    
    saved_history_mode = acc_cfg.get("history_mode") or ai_config.get("history_mode", "continue")
    history_var = ctk.StringVar(value=saved_history_mode)
        
    rb_continue = ctk.CTkRadioButton(history_mode_frame, text="Tiếp tục", variable=history_var, value="continue")
    rb_continue.pack(side="left", padx=10)
    
    rb_reset = ctk.CTkRadioButton(history_mode_frame, text="Tải lại từ đầu", variable=history_var, value="reset")
    rb_reset.pack(side="left", padx=10)
    
    # 5. Lịch bắt đầu (Bám sát giờ thực tế hiện tại, màu chữ vàng nổi bật)
    start_time_frame = ctk.CTkFrame(window, fg_color="transparent")
    start_time_frame.pack(fill="x", padx=10, pady=3)
    ctk.CTkLabel(start_time_frame, text="Bắt đầu đăng từ (Ngày/Tháng/Năm Giờ:Phút):", font=ctk.CTkFont(weight="bold", size=13)).pack(side="left", padx=5)
    
    now = datetime.now()
    yellow_color = "#facc15" # Màu vàng sáng nổi bật
    bold_yellow_font = ctk.CTkFont(weight="bold", size=13)

    sd = ctk.CTkEntry(start_time_frame, width=32, text_color=yellow_color, font=bold_yellow_font, justify="center")
    sd.insert(0, str(now.day))
    sd.pack(side="left", padx=2)
    ctk.CTkLabel(start_time_frame, text="/", font=bold_yellow_font, text_color=yellow_color).pack(side="left")
    
    sm = ctk.CTkEntry(start_time_frame, width=32, text_color=yellow_color, font=bold_yellow_font, justify="center")
    sm.insert(0, str(now.month))
    sm.pack(side="left", padx=2)
    ctk.CTkLabel(start_time_frame, text="/", font=bold_yellow_font, text_color=yellow_color).pack(side="left")
    
    sy = ctk.CTkEntry(start_time_frame, width=48, text_color=yellow_color, font=bold_yellow_font, justify="center")
    sy.insert(0, str(now.year))
    sy.pack(side="left", padx=2)
    
    sh = ctk.CTkEntry(start_time_frame, width=32, text_color=yellow_color, font=bold_yellow_font, justify="center")
    sh.insert(0, str(now.hour))
    sh.pack(side="left", padx=(10, 2))
    ctk.CTkLabel(start_time_frame, text=":", font=bold_yellow_font, text_color=yellow_color).pack(side="left")
    
    smin = ctk.CTkEntry(start_time_frame, width=32, text_color=yellow_color, font=bold_yellow_font, justify="center")
    smin.insert(0, str(now.minute))
    smin.pack(side="left", padx=2)
    
    # 6. Prompt Customization
    saved_use_ai = acc_cfg.get("use_ai") if "use_ai" in acc_cfg else ai_config.get("use_ai", True)
    use_ai_var = ctk.BooleanVar(value=bool(saved_use_ai))
    
    cb_use_ai = ctk.CTkCheckBox(window, text="Sử dụng AI để viết lại nội dung & tiêu đề (Bỏ chọn nếu muốn Re-up nguyên gốc)", variable=use_ai_var, font=ctk.CTkFont(weight="bold"))
    cb_use_ai.pack(padx=10, pady=(6, 2), anchor="w")
    
    prompt_frame = ctk.CTkFrame(window, fg_color="transparent")
    prompt_frame.pack(fill="x", padx=10, pady=2)
    ctk.CTkLabel(prompt_frame, text="Yêu cầu AI viết lại nội dung (Prompt):").pack(anchor="w", padx=5)
    
    saved_prompt = acc_cfg.get("gemini_prompt") or ai_config.get("gemini_prompt", "Hãy viết lại nội dung sau đây sao cho hấp dẫn, tự nhiên, giữ nguyên ý chính và chèn thêm các hashtag liên quan:")
    prompt_entry = ctk.CTkTextbox(prompt_frame, width=550, height=55)
    prompt_entry.pack(padx=5, pady=2)
    prompt_entry.insert("1.0", saved_prompt)
    
    if not saved_use_ai:
        prompt_entry.configure(state="disabled")

    # Log box
    log_box = ctk.CTkTextbox(window, width=550, height=130, state="disabled")
    log_box.pack(padx=10, pady=6)
    
    def ui_log(msg):
        def append():
            log_box.configure(state="normal")
            time_str = datetime.now().strftime("%H:%M:%S")
            log_box.insert("end", f"[{time_str}] {msg}\n")
            log_box.see("end")
            log_box.configure(state="disabled")
        window.after(0, append)

    # --- AUTO SAVE FUNCTION (Defined after all UI elements exist) ---
    def auto_save_all_settings(*_):
        try:
            target_acc_id = acc_combo.get().strip()
            prov = provider_combo.get()
            api_k = api_entry.get().strip()
            c_mode = crawl_mode_var.get()
            u_val = url_entry.get().strip()
            sv_val = start_video_entry.get().strip()
            m_val = max_vid_entry.get().strip()
            dl_all = download_all_var.get()
            int_val = interval_entry.get().strip()
            dl_d = dl_dir_entry.get().strip()
            h_mode = history_var.get()
            u_ai = use_ai_var.get()
            p_val = prompt_entry.get("1.0", "end").strip()
            
            s_time = {
                "d": sd.get().strip(),
                "m": sm.get().strip(),
                "y": sy.get().strip(),
                "h": sh.get().strip(),
                "min": smin.get().strip()
            }

            full_cfg = {}
            if os.path.exists(AI_CONFIG_FILE):
                try:
                    with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                        full_cfg = json.load(f)
                except: pass

            if "accounts" not in full_cfg:
                full_cfg["accounts"] = {}

            acc_data = {
                "ai_provider": prov,
                "use_ai": u_ai,
                "history_mode": h_mode,
                "gemini_prompt": p_val,
                "tiktok_crawl_mode": c_mode,
                "tiktok_url": u_val,
                "tiktok_start_video_url": sv_val,
                "tiktok_max_videos": m_val,
                "tiktok_download_all": dl_all,
                "tiktok_interval": int_val,
                "tiktok_dl_dir": dl_d,
                "start_time": s_time
            }

            if target_acc_id and target_acc_id != "Chưa có tài khoản nào":
                full_cfg["accounts"][target_acc_id] = acc_data

            # Cập nhật global defaults
            full_cfg["use_ai"] = u_ai
            full_cfg["ai_provider"] = prov
            full_cfg["history_mode"] = h_mode
            if prov == "Gemini" and api_k:
                full_cfg["gemini_api_key"] = api_k
            elif prov == "Groq" and api_k:
                full_cfg["groq_api_key"] = api_k
            full_cfg["gemini_prompt"] = p_val
            full_cfg["tiktok_crawl_mode"] = c_mode
            full_cfg["tiktok_url"] = u_val
            full_cfg["tiktok_start_video_url"] = sv_val
            full_cfg["tiktok_max_videos"] = m_val
            full_cfg["tiktok_download_all"] = dl_all
            full_cfg["tiktok_interval"] = int_val
            full_cfg["tiktok_dl_dir"] = dl_d
            full_cfg["start_time"] = s_time

            with open(AI_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(full_cfg, f, indent=4)
        except Exception as ex:
            print("Lỗi auto_save_all_settings:", ex)

    # --- WIRE UP EVENT HANDLERS ---
    def on_provider_change_event(*_):
        prov = provider_combo.get()
        if prov == "Gemini":
            api_lbl.configure(text="Gemini API Key:")
            api_entry.delete(0, "end")
            if saved_gemini_key: api_entry.insert(0, saved_gemini_key)
        else:
            api_lbl.configure(text="Groq API Key:")
            api_entry.delete(0, "end")
            if saved_groq_key: api_entry.insert(0, saved_groq_key)
        auto_save_all_settings()

    provider_combo.configure(command=on_provider_change_event)

    def on_mode_channel_toggle():
        crawl_mode_var.set("channel")
        cb_mode_channel.select()
        cb_mode_from_video.deselect()
        url_entry.configure(state="normal")
        start_video_entry.configure(state="disabled")
        auto_save_all_settings()
        
    def on_mode_from_video_toggle():
        crawl_mode_var.set("from_video")
        cb_mode_from_video.select()
        cb_mode_channel.deselect()
        start_video_entry.configure(state="normal")
        url_entry.configure(state="disabled")
        auto_save_all_settings()

    cb_mode_channel.configure(command=on_mode_channel_toggle)
    cb_mode_from_video.configure(command=on_mode_from_video_toggle)

    def on_download_all_changed():
        if download_all_var.get():
            max_vid_entry.configure(state="disabled")
        else:
            max_vid_entry.configure(state="normal")
        auto_save_all_settings()

    dl_all_cb.configure(command=on_download_all_changed)

    rb_continue.configure(command=auto_save_all_settings)
    rb_reset.configure(command=auto_save_all_settings)

    def on_use_ai_changed():
        if use_ai_var.get():
            prompt_entry.configure(state="normal")
        else:
            prompt_entry.configure(state="disabled")
        auto_save_all_settings()

    cb_use_ai.configure(command=on_use_ai_changed)

    # Hàm load cài đặt của 1 tài khoản cụ thể vào UI
    def load_account_settings_to_ui(acc_id):
        full_cfg = {}
        if os.path.exists(AI_CONFIG_FILE):
            try:
                with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    full_cfg = json.load(f)
            except: pass
        
        c = full_cfg.get("accounts", {}).get(acc_id, {})
        if not c:
            c = full_cfg

        # Provider
        p = c.get("ai_provider", "Gemini")
        provider_combo.set(p)
        if p == "Gemini":
            api_lbl.configure(text="Gemini API Key:")
            api_entry.delete(0, "end")
            if full_cfg.get("gemini_api_key"): api_entry.insert(0, full_cfg.get("gemini_api_key"))
        else:
            api_lbl.configure(text="Groq API Key:")
            api_entry.delete(0, "end")
            if full_cfg.get("groq_api_key"): api_entry.insert(0, full_cfg.get("groq_api_key"))

        # Crawl mode & URLs
        cm = c.get("tiktok_crawl_mode", "channel")
        crawl_mode_var.set(cm)
        url_entry.delete(0, "end")
        if c.get("tiktok_url"): url_entry.insert(0, c.get("tiktok_url"))
        
        start_video_entry.delete(0, "end")
        if c.get("tiktok_start_video_url"): start_video_entry.insert(0, c.get("tiktok_start_video_url"))

        if cm == "from_video":
            cb_mode_from_video.select()
            cb_mode_channel.deselect()
            start_video_entry.configure(state="normal")
            url_entry.configure(state="disabled")
        else:
            cb_mode_channel.select()
            cb_mode_from_video.deselect()
            url_entry.configure(state="normal")
            start_video_entry.configure(state="disabled")

        # Max videos & download all
        max_vid_entry.delete(0, "end")
        max_vid_entry.insert(0, str(c.get("tiktok_max_videos", "5")))
        
        is_dl_all = c.get("tiktok_download_all", False)
        download_all_var.set(bool(is_dl_all))
        if is_dl_all:
            max_vid_entry.configure(state="disabled")
        else:
            max_vid_entry.configure(state="normal")

        # Interval & Dir
        interval_entry.delete(0, "end")
        interval_entry.insert(0, str(c.get("tiktok_interval", "4")))

        dl_dir_entry.delete(0, "end")
        if c.get("tiktok_dl_dir"): dl_dir_entry.insert(0, c.get("tiktok_dl_dir"))

        # History mode
        hm = c.get("history_mode", "continue")
        history_var.set(hm)

        # Start time (Bám sát giờ thực tế hiện tại)
        current_now = datetime.now()
        sd.delete(0, "end"); sd.insert(0, str(current_now.day))
        sm.delete(0, "end"); sm.insert(0, str(current_now.month))
        sy.delete(0, "end"); sy.insert(0, str(current_now.year))
        sh.delete(0, "end"); sh.insert(0, str(current_now.hour))
        smin.delete(0, "end"); smin.insert(0, str(current_now.minute))

        # Use AI & prompt
        ua = c.get("use_ai", True)
        use_ai_var.set(bool(ua))
        prompt_entry.configure(state="normal")
        prompt_entry.delete("1.0", "end")
        prompt_entry.insert("1.0", c.get("gemini_prompt", "Hãy viết lại nội dung sau đây sao cho hấp dẫn, tự nhiên, giữ nguyên ý chính và chèn thêm các hashtag liên quan:"))
        if not ua:
            prompt_entry.configure(state="disabled")

    def on_account_change_event(selected_id):
        load_account_settings_to_ui(selected_id)
        auto_save_all_settings()

    acc_combo.configure(command=on_account_change_event)

    # Gắn sự kiện auto-save khi người dùng nhập bất cứ trường nào
    for entry in [api_entry, url_entry, start_video_entry, max_vid_entry, interval_entry, dl_dir_entry, sd, sm, sy, sh, smin]:
        entry.bind("<KeyRelease>", auto_save_all_settings)
        entry.bind("<FocusOut>", auto_save_all_settings)
        
    prompt_entry.bind("<KeyRelease>", auto_save_all_settings)
    prompt_entry.bind("<FocusOut>", auto_save_all_settings)

    # Lưu khi đóng cửa sổ và dọn dẹp bộ nhớ quản lý
    def on_window_close():
        auto_save_all_settings()
        if hasattr(app, 'active_tiktok_ai_windows') and acc_key in app.active_tiktok_ai_windows:
            del app.active_tiktok_ai_windows[acc_key]
        window.destroy()
        
    window.protocol("WM_DELETE_WINDOW", on_window_close)
    
    # 7. Start Process
    def start_process():
        # Lưu lại trước khi bắt đầu
        auto_save_all_settings()
        
        use_ai = use_ai_var.get()
        api_key = api_entry.get().strip()
        crawl_mode = crawl_mode_var.get()
        url = url_entry.get().strip()
        start_video_url = start_video_entry.get().strip()
        target_acc_id = acc_combo.get()
        prompt = prompt_entry.get("1.0", "end").strip() if use_ai else ""
        interval_hrs = float(interval_entry.get().strip() or 0.05)
        dl_dir = dl_dir_entry.get().strip()
        reset_history = (history_var.get() == "reset")
        
        try:
            if download_all_var.get():
                max_vids = 99999
            else:
                max_vids = int(max_vid_entry.get().strip())
                
            interval_hrs = float(interval_entry.get().strip())
            
            d = int(sd.get().strip())
            m = int(sm.get().strip())
            y = int(sy.get().strip())
            h = int(sh.get().strip())
            mn = int(smin.get().strip())
            start_dt = datetime(y, m, d, h, mn, 0)
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập đúng định dạng số cho cấu hình ngày giờ và số lượng!")
            return
            
        if crawl_mode == "channel" and not url:
            messagebox.showerror("Lỗi", "Vui lòng điền Link Kênh TikTok!")
            return
            
        if crawl_mode == "from_video" and not start_video_url:
            messagebox.showerror("Lỗi", "Vui lòng điền 'Link kênh bắt đầu tải từ video này'!")
            return
            
        if not target_acc_id or target_acc_id == "Chưa có tài khoản nào":
            messagebox.showerror("Lỗi", "Vui lòng chọn Tài khoản đích để đăng!")
            return
            
        if use_ai and not api_key:
            messagebox.showerror("Lỗi", "Bạn đang chọn dùng AI nhưng chưa nhập API Key!")
            return
            
        # Tìm frame của account target
        target_acc_dict = next((acc for acc in app.account_frames if acc['id_entry'].get() == target_acc_id), None)
        if not target_acc_dict:
            messagebox.showerror("Lỗi", "Không tìm thấy tài khoản đích trên giao diện!")
            return
            
        btn_start.configure(state="disabled", text="ĐANG XỬ LÝ...")
        
        # Lấy dữ liệu Bài Đăng Mẫu làm khuôn mẫu (template)
        all_data = app.get_accounts_data()
        acc_data = next((item for item in all_data if item["id"] == target_acc_id), None)
        base_post_data = {}
        if acc_data and acc_data.get('posts') and len(acc_data['posts']) > 0:
            sample_post = next((p for p in acc_data['posts'] if str(p.get('is_sample', '0')) == '1'), acc_data['posts'][0])
            base_post_data = sample_post.copy()
        
        def worker():
            try:
                ui_log("Bắt đầu tiến trình Crawl & AI...")
                
                # 1. Initialize AI & state
                if provider_combo.get() == "Groq":
                    ui_log("Đang khởi tạo Groq AI...")
                    ai = GroqHelper(api_key=api_key)
                else:
                    ui_log("Đang khởi tạo Gemini AI...")
                    ai = GeminiHelper(api_key=api_key)
                
                current_schedule = [start_dt] # Dùng list để pass by reference
                video_count = [0]
                from ui_actions.add_post import add_post_block
                
                def on_video_downloaded(v_data):
                    v_path = v_data['video_path']
                    o_desc = v_data['description']
                    video_count[0] += 1
                    idx = video_count[0]
                    
                    if not use_ai:
                        ui_log(f"-> Chế độ Re-up nguyên gốc (Bỏ qua AI). Lấy 100% nội dung gốc!")
                        new_desc = o_desc
                    else:
                        ui_log(f"Đang dùng AI viết lại caption cho video {idx}...")
                        try:
                            new_desc = ai.rewrite_content(o_desc, prompt)
                            ui_log(f"-> Viết caption thành công!")
                        except Exception as e:
                            ui_log(f"-> Lỗi AI: {e}. Sử dụng caption gốc.")
                            new_desc = o_desc
                    
                    # Calculate schedule strings
                    dt = current_schedule[0]
                    d_str, m_str, y_str = str(dt.day), str(dt.month), str(dt.year)
                    h_str, min_str = str(dt.hour), str(dt.minute)
                    
                    def add_block_to_ui(path=v_path, desc=new_desc,
                                        sd=d_str, sm=m_str, sy=y_str, sh=h_str, smin=min_str):
                        pre_data = base_post_data.copy()
                        
                        # Giữ nguyên 100% cấu hình Tiêu đề AI & Prompt từ Bài Đăng Mẫu
                        is_yt_ai = base_post_data.get('is_yt_ai_title', '0')
                        is_yt_manual = base_post_data.get('is_yt_manual_title', '1')
                        yt_ai_prompt_val = base_post_data.get('yt_ai_prompt', '')
                        yt_title_val = base_post_data.get('yt_title', '')
                        
                        # Chỉ dán nội dung AI/video vào ô "Nội dung bài đăng" (description)
                        # Tất cả các ô text khác (Threads, FB, YT cmt, Newsfeed cmt, Nhóm, Hashtag...) giữ nguyên 100% từ Bài Khuôn Mẫu
                        pre_data.update({
                            'is_sample': '0',
                            'is_post_video': '1',
                            'video_path': path,
                            'description': desc,
                            'yt_title': yt_title_val,
                            'is_yt_manual_title': str(is_yt_manual),
                            'is_yt_ai_title': str(is_yt_ai),
                            'yt_ai_prompt': yt_ai_prompt_val,
                            'is_schedule': '1',
                            'sch_d': sd,
                            'sch_m': sm,
                            'sch_y': sy,
                            'sch_h': sh,
                            'sch_min': smin
                        })
                        add_post_block(app, target_acc_dict, pre_data, is_sample=False)
                        
                    window.after(0, add_block_to_ui)
                    
                    ui_log(f"Đã tạo bài đăng lúc {dt.strftime('%H:%M %d/%m/%Y')} cho video {idx}")
                    current_schedule[0] += timedelta(hours=interval_hrs)
                
                # 2. Crawl
                if crawl_mode == "from_video":
                    crawler = TikTokVideoStartCrawler(log_callback=ui_log, download_dir=dl_dir)
                    videos = crawler.crawl_from_start_video(start_video_url, max_vids, profile_id=target_acc_id, on_video_downloaded=on_video_downloaded, reset_history=reset_history)
                else:
                    crawler = TikTokCrawler(log_callback=ui_log, download_dir=dl_dir)
                    videos = crawler.crawl_profile(url, max_vids, profile_id=target_acc_id, on_video_downloaded=on_video_downloaded, reset_history=reset_history)
                
                if not videos or video_count[0] == 0:
                    ui_log("Không tải được video nào. Dừng tiến trình.")
                    window.after(0, lambda: btn_start.configure(state="normal", text="Bắt Đầu Quét & Lên Lịch"))
                    return
                    
                ui_log("===== HOÀN TẤT TOÀN BỘ TIẾN TRÌNH! =====")
                
            except Exception as e:
                ui_log(f"Lỗi không xác định: {e}")
            finally:
                window.after(0, lambda: btn_start.configure(state="normal", text="Bắt Đầu Quét & Lên Lịch"))
                
        threading.Thread(target=worker, daemon=True).start()
        
    btn_start = ctk.CTkButton(window, text="Bắt Đầu Quét & Lên Lịch", font=ctk.CTkFont(weight="bold"), fg_color="green", hover_color="darkgreen", height=40, command=start_process)
    btn_start.pack(pady=10)
    
    if auto_start:
        window.after(800, start_process)
