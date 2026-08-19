import customtkinter as ctk
from tkinter import filedialog
from ui_actions.hashtag_ui import HashtagUI

def add_post_block(app, acc_dict, acc_data=None, is_sample=None):
    if acc_data is None:
        acc_data = {}
    post_frame = ctk.CTkFrame(acc_dict['posts_container'], border_width=1, border_color="#555555")
    post_frame.pack(fill="x", pady=0, padx=5)
    
    post_dict = {}

    # --- HEADER FRAME ---
    header_frame = ctk.CTkFrame(post_frame, fg_color="#333333", height=30)
    header_frame.pack(fill="x", pady=0, padx=0)
    
    is_collapsed = [True]
    
    content_frame = ctk.CTkFrame(post_frame, fg_color="transparent")
    
    def toggle_collapse():
        if is_collapsed[0]:
            content_frame.pack(fill="x", pady=0, padx=2)
            toggle_btn.configure(text="-")
            is_collapsed[0] = False
        else:
            content_frame.pack_forget()
            toggle_btn.configure(text="+")
            is_collapsed[0] = True
            
    toggle_btn = ctk.CTkButton(header_frame, text="+", width=30, command=toggle_collapse, fg_color="#1f538d", font=ctk.CTkFont(weight="bold"))
    toggle_btn.pack(side="left", padx=5, pady=0)
    
    # Loại bỏ các bài đăng đã bị tự động xóa khỏi danh sách để lấy số chuẩn
    acc_dict['posts'] = [p for p in acc_dict['posts'] if p.get('post_frame') and p['post_frame'].winfo_exists()]
    
    # Kiểm tra xem đây có phải là bài đăng mẫu không
    if is_sample is True or str(acc_data.get('is_sample', '0')) == '1':
        is_sample_post = True
    elif is_sample is False:
        is_sample_post = False
    else:
        # Nếu chưa có bài nào trong danh sách thì bài đầu tiên là Bài Đăng Mẫu
        is_sample_post = (len(acc_dict['posts']) == 0)

    if is_sample_post:
        title_label = ctk.CTkLabel(header_frame, text="⭐ BÀI ĐĂNG MẪU", font=ctk.CTkFont(weight="bold", size=13), text_color="#f39c12")
        title_label.pack(side="left", padx=5)
        
        schedule_label = ctk.CTkLabel(header_frame, text="Lịch: Đăng ngay ", font=ctk.CTkFont(size=15, weight="bold", slant="italic"), text_color="#aaaaaa")
        schedule_label.pack(side="left", padx=20)
        
        # Checkbox Xóa video/ảnh sau khi đăng đặt ở header
        try:
            from delete_media_feature import add_delete_media_checkbox
            add_delete_media_checkbox(header_frame, ctk, post_dict, 'is_delete_media_var')
        except Exception as e:
            print("Lỗi load delete_media_feature:", e)
            post_dict['is_delete_media_var'] = ctk.StringVar(value="0")
        
        # Bài đăng mẫu KHÔNG THỂ XÓA
        badge_lbl = ctk.CTkLabel(header_frame, text="[KHUÔN MẪU - KHÔNG XOÁ]", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2ecc71")
        badge_lbl.pack(side="right", padx=8, pady=0)
    else:
        regular_posts = [p for p in acc_dict['posts'] if p.get('is_sample') != '1']
        post_index = len(regular_posts) + 1
        title_label = ctk.CTkLabel(header_frame, text=f"Bài Đăng {post_index}", font=ctk.CTkFont(weight="bold"))
        title_label.pack(side="left", padx=5)
        
        schedule_label = ctk.CTkLabel(header_frame, text="Lịch: Đăng ngay ", font=ctk.CTkFont(size=15, weight="bold", slant="italic"), text_color="#aaaaaa")
        schedule_label.pack(side="left", padx=20)
        
        # Checkbox Xóa video/ảnh sau khi đăng đặt ở header
        try:
            from delete_media_feature import add_delete_media_checkbox
            add_delete_media_checkbox(header_frame, ctk, post_dict, 'is_delete_media_var')
        except Exception as e:
            print("Lỗi load delete_media_feature:", e)
            post_dict['is_delete_media_var'] = ctk.StringVar(value="0")
            
        del_post_btn = ctk.CTkButton(header_frame, text="Xoá Bài", width=60, fg_color="red", command=lambda: delete_post_block(app, acc_dict, post_dict, post_frame))
        del_post_btn.pack(side="right", padx=5, pady=0)

    # Row 1.5: Master Toggle Facebook
    row1_5 = ctk.CTkFrame(content_frame, fg_color="transparent")
    row1_5.pack(fill="x", pady=0)
    
    is_post_facebook_var = ctk.StringVar(value="1")
    cb_post_facebook = ctk.CTkCheckBox(row1_5, text="Tự động hoá FACEBOOK", variable=is_post_facebook_var, onvalue="1", offvalue="0", font=("Arial", 12, "bold"))
    cb_post_facebook.pack(side="left", padx=5)

    # Row 2: CÃ¡ nhÃ¢n & Page
    row2 = ctk.CTkFrame(content_frame, fg_color="transparent")
    row2.pack(fill="x", pady=0)
    
    is_canhan_var = ctk.StringVar(value="1")
    is_page_var = ctk.StringVar(value="0")
    
    # We define the entry first so toggle_canhan can reference it
    canhan_name_entry = ctk.CTkEntry(row2, width=200, placeholder_text="Tên Trang Cá Nhân (chính xác)...")
    
    def toggle_canhan():
        if is_canhan_var.get() == "1":
            canhan_name_entry.configure(state="normal")
        else:
            canhan_name_entry.configure(state="disabled")
            
    cb_canhan = ctk.CTkCheckBox(row2, text="Đăng Tường Cá Nhân", variable=is_canhan_var, onvalue="1", offvalue="0", command=toggle_canhan)
    # Pack checkbox BEFORE the entry
    cb_canhan.pack(side="left", padx=5)
    canhan_name_entry.pack(side="left", padx=5)
    
    is_canhan_reels_var = ctk.StringVar(value="0")
    cb_canhan_reels = ctk.CTkCheckBox(row2, text="Reels fb trang cá nhân", variable=is_canhan_reels_var, onvalue="1", offvalue="0")
    cb_canhan_reels.pack(side="left", padx=5)
    
    def toggle_page():
        if is_page_var.get() == "1":
            pages_frame.pack(fill="x", pady=0, after=row2)
            add_page_btn.configure(state="normal")
        else:
            pages_frame.pack_forget()
            add_page_btn.configure(state="disabled")
            
    cb_page = ctk.CTkCheckBox(row2, text="Đăng Page", variable=is_page_var, onvalue="1", offvalue="0", command=toggle_page)
    cb_page.pack(side="left", padx=5)
    
    is_post_reel_var = ctk.StringVar(value="0")
    cb_post_reel = ctk.CTkCheckBox(row2, text="Đăng Page Reels", variable=is_post_reel_var, onvalue="1", offvalue="0")
    cb_post_reel.pack(side="left", padx=5)
    
    # Frame chứa danh sách page
    pages_frame = ctk.CTkFrame(content_frame, fg_color="transparent", height=0)
    
    page_entries = []
    
    def add_page_entry(page_name=""):
        p_row = ctk.CTkFrame(pages_frame, fg_color="transparent")
        p_row.pack(fill="x", pady=0)
        
        p_entry = ctk.CTkEntry(p_row, width=250, placeholder_text="Tên Page (chính xác)...")
        p_entry.pack(side="left", padx=5)
        if page_name:
            p_entry.insert(0, page_name)
            
        def del_page():
            p_row.destroy()
            if p_entry in page_entries:
                page_entries.remove(p_entry)
            
        del_btn = ctk.CTkButton(p_row, text="X", width=30, fg_color="red", command=del_page)
        del_btn.pack(side="left", padx=5)
        
        page_entries.append(p_entry)
        
    add_page_btn = ctk.CTkButton(row2, text="+ Thêm Tên Page", width=120, command=lambda: add_page_entry(""))
    add_page_btn.pack(side="left", padx=5)
    

    split_container = ctk.CTkFrame(content_frame, fg_color="transparent")
    split_container.pack(fill="x", pady=0)
    
    left_col = ctk.CTkFrame(split_container, fg_color="transparent")
    left_col.pack(side="left", anchor="n", fill="x", expand=True)
    
    right_col = ctk.CTkFrame(split_container, fg_color="transparent")
    right_col.pack(side="right", anchor="n", padx=5)
    
    # Row 3: Video and Multi-platform
    row3 = ctk.CTkFrame(left_col, fg_color="transparent")
    row3.pack(fill="x", pady=0)
    
    media_frame = ctk.CTkFrame(row3, fg_color="transparent")
    media_frame.pack(side="left")
    
    platform_frame = ctk.CTkFrame(right_col, fg_color="transparent")
    platform_frame.pack(side="top", anchor="n")
    
    is_post_video_var = ctk.StringVar(value="1")
    cb_post_video = ctk.CTkCheckBox(media_frame, text="Đăng Video:", variable=is_post_video_var, onvalue="1", offvalue="0")
    cb_post_video.pack(side="left", padx=5)
    
    vid_entry = ctk.CTkTextbox(media_frame, width=150, height=30)
    vid_entry.pack(side="left", padx=5)
    
    from tkinter import filedialog
    def pick_video(entry=vid_entry):
        filepaths = filedialog.askopenfilenames(filetypes=[("Video files", "*.mp4 *.mov *.avi *.MOV *.MP4 *.AVI")])
        if filepaths:
            entry.delete("1.0", "end")
            entry.insert("1.0", "\n".join(filepaths))
            
    vid_btn = ctk.CTkButton(media_frame, text="Chọn Video", width=80, command=pick_video)
    vid_btn.pack(side="left", padx=5)
    
    is_post_image_var = ctk.StringVar(value="0")
    cb_post_image = ctk.CTkCheckBox(media_frame, text="Đăng Ảnh:", variable=is_post_image_var, onvalue="1", offvalue="0")
    cb_post_image.pack(side="left", padx=5)
    img_entry = ctk.CTkTextbox(media_frame, width=150, height=30)
    img_entry.pack(side="left", padx=5)
    
    def pick_image(entry=img_entry):
        filepaths = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")])
        if filepaths:
            entry.delete("1.0", "end")
            entry.insert("1.0", "\n".join(filepaths))
            
    img_btn = ctk.CTkButton(media_frame, text="Chọn Ảnh", width=80, command=pick_image)
    img_btn.pack(side="left", padx=5)
    
    # Đa nền tảng (Right Side)
    ctk.CTkLabel(platform_frame, text="Đa nền tảng:", font=("Arial", 12, "bold")).pack(anchor="w", padx=5)
    
    is_post_zalo_var = ctk.StringVar(value="0")
    cb_post_zalo = ctk.CTkCheckBox(platform_frame, text="Đăng Zalo Video", variable=is_post_zalo_var, onvalue="1", offvalue="0")
    cb_post_zalo.pack(anchor="w", pady=0, padx=5)
    
    is_post_yt_var = ctk.StringVar(value="0")
    
    yt_row = ctk.CTkFrame(platform_frame, fg_color="transparent")
    yt_row.pack(anchor="w", fill="x", pady=0)
    
    cb_post_yt = ctk.CTkCheckBox(yt_row, text="Đăng YouTube", variable=is_post_yt_var, onvalue="1", offvalue="0")
    cb_post_yt.pack(side="left", padx=5)
    
    is_yt_shorts_var = ctk.StringVar(value="0")
    cb_yt_shorts = ctk.CTkCheckBox(yt_row, text="Shorts", variable=is_yt_shorts_var, onvalue="1", offvalue="0")
    cb_yt_shorts.pack(side="left", padx=5)
    
    yt_kids_combo = ctk.CTkComboBox(yt_row, values=["Không cho trẻ em", "Dành cho trẻ em"], width=130)
    yt_kids_combo.pack(side="left", padx=5)

    yt_title_row = ctk.CTkFrame(platform_frame, fg_color="transparent")
    yt_title_row.pack(anchor="w", fill="x", pady=0)

    is_yt_manual_title_var = ctk.StringVar(value="1")
    is_yt_ai_title_var = ctk.StringVar(value="0")

    def toggle_yt_title(choice):
        if choice == "manual":
            if is_yt_manual_title_var.get() == "1":
                is_yt_ai_title_var.set("0")
                yt_title_entry.configure(state="normal")
                yt_ai_prompt_entry.configure(state="disabled")
            else:
                is_yt_manual_title_var.set("1") # Bắt buộc phải có 1 cái được chọn
        elif choice == "ai":
            if is_yt_ai_title_var.get() == "1":
                is_yt_manual_title_var.set("0")
                yt_title_entry.configure(state="disabled")
                yt_ai_prompt_entry.configure(state="normal")
            else:
                is_yt_ai_title_var.set("1")

    cb_yt_manual_title = ctk.CTkCheckBox(yt_title_row, text="Tiêu đề { bắt buộc }:", variable=is_yt_manual_title_var, onvalue="1", offvalue="0", command=lambda: toggle_yt_title("manual"))
    cb_yt_manual_title.pack(side="left", padx=(10, 2))
    
    yt_title_entry = ctk.CTkEntry(yt_title_row, width=120)
    yt_title_entry.pack(side="left", padx=2)
    
    cb_yt_ai_title = ctk.CTkCheckBox(yt_title_row, text="Tiêu đề AI", variable=is_yt_ai_title_var, onvalue="1", offvalue="0", command=lambda: toggle_yt_title("ai"))
    cb_yt_ai_title.pack(side="left", padx=5)

    yt_ai_prompt_entry = ctk.CTkEntry(yt_title_row, width=200, placeholder_text="Prompt AI...")
    yt_ai_prompt_entry.pack(side="left", padx=2)
    yt_ai_prompt_entry.configure(state="disabled")
    
    yt_interact_row = ctk.CTkFrame(platform_frame, fg_color="transparent")
    yt_interact_row.pack(anchor="w", fill="x", pady=(2, 0))
    
    is_yt_interact_var = ctk.StringVar(value="0")
    cb_yt_interact = ctk.CTkCheckBox(yt_interact_row, text="Lướt bảng tin youtube", variable=is_yt_interact_var, onvalue="1", offvalue="0")
    cb_yt_interact.pack(side="left", padx=5)
    
    ctk.CTkLabel(yt_interact_row, text="Phút:").pack(side="left", padx=2)
    yt_interact_time = ctk.CTkEntry(yt_interact_row, width=40, placeholder_text="5")
    yt_interact_time.pack(side="left", padx=2)
    
    is_yt_like_var = ctk.StringVar(value="0")
    cb_yt_like = ctk.CTkCheckBox(yt_interact_row, text="Thích", variable=is_yt_like_var, onvalue="1", offvalue="0")
    cb_yt_like.pack(side="left", padx=5)
    
    yt_cmt_row = ctk.CTkFrame(platform_frame, fg_color="transparent")
    yt_cmt_row.pack(anchor="w", fill="x", pady=(2, 0))
    
    ctk.CTkLabel(yt_cmt_row, text="Bình luận bài Youtube:").pack(side="left", padx=(5, 2))
    yt_cmt_entry = ctk.CTkEntry(yt_cmt_row, width=280, placeholder_text="Nội dung bình luận youtube...")
    yt_cmt_entry.pack(side="left", padx=2)
    
    is_post_tiktok_var = ctk.StringVar(value="0")
    cb_post_tt = ctk.CTkCheckBox(platform_frame, text="Đăng TikTok Video", variable=is_post_tiktok_var, onvalue="1", offvalue="0")
    cb_post_tt.pack(anchor="w", pady=0, padx=5)
    
    # Instagram Row
    ig_row = ctk.CTkFrame(platform_frame, fg_color="transparent")
    ig_row.pack(anchor="w", fill="x", pady=(2, 0))
    
    is_post_ig_var = ctk.StringVar(value="0")
    cb_post_ig = ctk.CTkCheckBox(ig_row, text="Đăng Instagram", variable=is_post_ig_var, onvalue="1", offvalue="0")
    cb_post_ig.pack(side="left", padx=5)
    
    # Chia sẻ sang Threads (1 dòng riêng, font nhỏ)
    ig_threads_row = ctk.CTkFrame(platform_frame, fg_color="transparent")
    ig_threads_row.pack(anchor="w", fill="x", pady=(1, 0))
    
    is_ig_threads_var = ctk.StringVar(value="0")
    cb_ig_threads = ctk.CTkCheckBox(ig_threads_row, text="Chia sẻ lên Threads", font=("Arial", 11), variable=is_ig_threads_var, onvalue="1", offvalue="0")
    cb_ig_threads.pack(side="left", padx=(15, 5))
    
    threads_txt = ctk.CTkEntry(ig_threads_row, width=220, placeholder_text="Nội dung chia sẻ Threads...")
    threads_txt.pack(side="left", padx=2)
    
    # Chia sẻ sang Facebook (1 dòng riêng, font nhỏ)
    ig_fb_row = ctk.CTkFrame(platform_frame, fg_color="transparent")
    ig_fb_row.pack(anchor="w", fill="x", pady=(1, 0))
    
    is_ig_fb_var = ctk.StringVar(value="0")
    cb_ig_fb = ctk.CTkCheckBox(ig_fb_row, text="Chia sẻ lên Facebook", font=("Arial", 11), variable=is_ig_fb_var, onvalue="1", offvalue="0")
    cb_ig_fb.pack(side="left", padx=(15, 5))
    
    fb_txt = ctk.CTkEntry(ig_fb_row, width=220, placeholder_text="Nội dung chia sẻ Facebook...")
    fb_txt.pack(side="left", padx=2)
    
    threads_row = ctk.CTkFrame(platform_frame, fg_color="transparent")
    threads_row.pack(anchor="w", fill="x", pady=(2, 0))
    
    is_post_threads_var = ctk.StringVar(value="0")
    cb_post_threads = ctk.CTkCheckBox(threads_row, text="Đăng Threads", variable=is_post_threads_var, onvalue="1", offvalue="0")
    cb_post_threads.pack(side="left", padx=5)
    
    

    row3_1 = ctk.CTkFrame(left_col, fg_color="transparent")
    row3_1.pack(fill="x", pady=(5, 0))
    
    ctk.CTkLabel(row3_1, text="Nội dung bài đăng:").pack(side="left", padx=2)
    desc_entry = ctk.CTkTextbox(row3_1, width=250, height=40)
    desc_entry.pack(side="left", padx=5)
    
    append_ui = HashtagUI(row3_1, acc_data.get('append_text', ''))
    
    # Thêm block Comment dưới bài viết
    try:
        from ui_actions.comment_ui import CrossPlatformCommentUI
        comment_ui = CrossPlatformCommentUI(left_col, acc_data)
    except Exception as e:
        print(f"Error loading Comment UI: {e}")
        comment_ui = None
    
    # Row 3.5: Lên lịch (Schedule)
    row_schedule = ctk.CTkFrame(left_col, fg_color="transparent")
    row_schedule.pack(fill="x", pady=0)
    
    is_schedule_var = ctk.StringVar(value="0")
    
    def update_schedule_label(*_):
        if is_schedule_var.get() == "1":
            d = sch_d.get().strip() or "DD"
            m = sch_m.get().strip() or "MM"
            y = sch_y.get().strip() or "YYYY"
            h = sch_h.get().strip() or "HH"
            minute = sch_min.get().strip() or "mm"
            schedule_label.configure(text=f"Lịch: {d}/{m}/{y} {h}:{minute} ", text_color="#ffff00")
        else:
            schedule_label.configure(text="Lịch: Đăng ngay ", text_color="#aaaaaa")

    def toggle_schedule():
        state = "normal" if is_schedule_var.get() == "1" else "disabled"
        sch_d.configure(state=state)
        sch_m.configure(state=state)
        sch_y.configure(state=state)
        sch_h.configure(state=state)
        sch_min.configure(state=state)
        update_schedule_label()
            
    cb_schedule = ctk.CTkCheckBox(row_schedule, text="Lên lịch:", variable=is_schedule_var, onvalue="1", offvalue="0", command=toggle_schedule)
    cb_schedule.pack(side="left", padx=5)
    
    ctk.CTkLabel(row_schedule, text="Ngày:").pack(side="left", padx=(5, 1))
    sch_d = ctk.CTkEntry(row_schedule, width=40, placeholder_text="25", state="disabled")
    sch_d.pack(side="left", padx=1)
    sch_d.bind("<KeyRelease>", update_schedule_label)
    
    ctk.CTkLabel(row_schedule, text="Tháng:").pack(side="left", padx=(5, 1))
    sch_m = ctk.CTkEntry(row_schedule, width=40, placeholder_text="12", state="disabled")
    sch_m.pack(side="left", padx=1)
    sch_m.bind("<KeyRelease>", update_schedule_label)
    
    ctk.CTkLabel(row_schedule, text="Năm:").pack(side="left", padx=(5, 1))
    sch_y = ctk.CTkEntry(row_schedule, width=60, placeholder_text="2026", state="disabled")
    sch_y.pack(side="left", padx=1)
    sch_y.bind("<KeyRelease>", update_schedule_label)
    
    ctk.CTkLabel(row_schedule, text="Giờ:").pack(side="left", padx=(15, 1))
    sch_h = ctk.CTkEntry(row_schedule, width=40, placeholder_text="15", state="disabled")
    sch_h.pack(side="left", padx=1)
    sch_h.bind("<KeyRelease>", update_schedule_label)
    
    ctk.CTkLabel(row_schedule, text="Phút:").pack(side="left", padx=(5, 1))
    sch_min = ctk.CTkEntry(row_schedule, width=40, placeholder_text="30", state="disabled")
    sch_min.pack(side="left", padx=1)
    sch_min.bind("<KeyRelease>", update_schedule_label)
    
    # Row 4: Tương tác Newsfeed (Lướt & Cảm xúc)
    row4 = ctk.CTkFrame(left_col, fg_color="transparent")
    row4.pack(fill="x", pady=0)
    
    interact_nf_var = ctk.StringVar(value="0")
    cb_nf = ctk.CTkCheckBox(row4, text="Lướt Bảng Tin facebook", variable=interact_nf_var, onvalue="1", offvalue="0")
    cb_nf.pack(side="left", padx=5)
    
    ctk.CTkLabel(row4, text="Thời gian (s):").pack(side="left", padx=(10, 2))
    nf_time_entry = ctk.CTkEntry(row4, width=50, placeholder_text="60")
    nf_time_entry.pack(side="left", padx=2)
    
    ctk.CTkLabel(row4, text="Cảm xúc:").pack(side="left", padx=(10, 2))
    nf_like_var = ctk.StringVar(value="0")
    ctk.CTkCheckBox(row4, text="Like", variable=nf_like_var, onvalue="1", offvalue="0", width=50).pack(side="left", padx=2)
    
    nf_love_var = ctk.StringVar(value="0")
    ctk.CTkCheckBox(row4, text="Tim", variable=nf_love_var, onvalue="1", offvalue="0", width=50).pack(side="left", padx=2)
    
    nf_haha_var = ctk.StringVar(value="0")
    ctk.CTkCheckBox(row4, text="Haha", variable=nf_haha_var, onvalue="1", offvalue="0", width=60).pack(side="left", padx=2)
    
    nf_rand_var = ctk.StringVar(value="0")
    ctk.CTkCheckBox(row4, text="Ngẫu nhiên", variable=nf_rand_var, onvalue="1", offvalue="0", width=80).pack(side="left", padx=2)
    
    ctk.CTkLabel(row4, text="SL Cảm xúc:").pack(side="left", padx=(10, 2))
    nf_react_count_entry = ctk.CTkEntry(row4, width=50, placeholder_text="1")
    nf_react_count_entry.pack(side="left", padx=2)
    
    # Row 5: Bình luận Newsfeed
    row5 = ctk.CTkFrame(left_col, fg_color="transparent")
    row5.pack(fill="x", pady=(5, 2))
    
    nf_enable_cmt_var = ctk.StringVar(value="0")
    ctk.CTkCheckBox(row5, text="Bật Bình luận", variable=nf_enable_cmt_var, onvalue="1", offvalue="0").pack(side="left", padx=5)
    
    ctk.CTkLabel(row5, text="SL Comment:").pack(side="left", padx=(10, 2))
    nf_cmt_count_entry = ctk.CTkEntry(row5, width=50, placeholder_text="1")
    nf_cmt_count_entry.pack(side="left", padx=2)
    
    ctk.CTkLabel(row5, text="Nội dung (mỗi dòng 1 câu):").pack(side="left", padx=(10, 2))
    nf_cmt_entry = ctk.CTkTextbox(row5, width=250, height=40)
    nf_cmt_entry.pack(side="left", padx=2)
    
    # Row 6: Đăng nhóm (Group Posting)
    row6 = ctk.CTkFrame(left_col, fg_color="transparent")
    row6.pack(fill="x", pady=(5, 3))
    
    is_group_profile_var = ctk.StringVar(value="0")
    cb_grp_prof = ctk.CTkCheckBox(row6, text="Đăng nhóm bằng Cá nhân", variable=is_group_profile_var, onvalue="1", offvalue="0")
    cb_grp_prof.pack(side="left", padx=5)
    
    is_group_page_var = ctk.StringVar(value="0")
    cb_grp_page = ctk.CTkCheckBox(row6, text="Đăng nhóm bằng Page", variable=is_group_page_var, onvalue="1", offvalue="0")
    cb_grp_page.pack(side="left", padx=5)
    
    ctk.CTkLabel(row6, text="Danh sách Link Nhóm (1 link/dòng):").pack(side="left", padx=(10, 2))
    group_links_entry = ctk.CTkTextbox(row6, width=250, height=35)
    group_links_entry.pack(side="left", padx=2)
    
    if acc_data:
        is_post_facebook_var.set(acc_data.get('is_post_facebook', '1'))
        is_post_reel_var.set(acc_data.get('is_post_reel', '0'))
        is_post_video_var.set(acc_data.get('is_post_video', '1'))
        is_post_zalo_var.set(acc_data.get('is_post_zalo', '0'))
        is_post_tiktok_var.set(acc_data.get('is_post_tiktok', '0'))
        is_post_ig_var.set(acc_data.get('is_post_ig', '0'))
        is_post_threads_var.set(acc_data.get('is_post_threads', '0'))
        is_ig_threads_var.set(acc_data.get('is_ig_threads', '0'))
        threads_txt.insert(0, acc_data.get('ig_threads_txt', ''))
        is_ig_fb_var.set(acc_data.get('is_ig_fb', '0'))
        fb_txt.insert(0, acc_data.get('ig_fb_txt', ''))
        is_post_yt_var.set(acc_data.get('is_post_yt', '0'))
        is_yt_ai = str(acc_data.get('is_yt_ai_title', '0'))
        is_yt_manual = str(acc_data.get('is_yt_manual_title', '1'))
        is_yt_manual_title_var.set(is_yt_manual)
        is_yt_ai_title_var.set(is_yt_ai)
        
        yt_title_entry.configure(state="normal")
        yt_title_entry.delete(0, "end")
        yt_title_entry.insert(0, acc_data.get('yt_title', ''))
        
        yt_ai_prompt_entry.configure(state="normal")
        yt_ai_prompt_entry.delete(0, "end")
        yt_ai_prompt_entry.insert(0, acc_data.get('yt_ai_prompt', ''))
        
        if is_yt_ai == "1":
            toggle_yt_title("ai")
        else:
            toggle_yt_title("manual")
        is_yt_shorts_var.set(acc_data.get('is_yt_shorts', '0'))
        yt_kids_combo.set(acc_data.get('yt_kids_text', 'Không, không dành cho trẻ em'))
        
        is_yt_interact_var.set(acc_data.get('is_yt_interact', '0'))
        yt_interact_time.insert(0, acc_data.get('yt_interact_time', '5'))
        is_yt_like_var.set(acc_data.get('is_yt_like', '0'))
        yt_cmt_entry.insert(0, acc_data.get('yt_cmt', ''))
        is_post_image_var.set(acc_data.get('is_post_image', '0'))
        vid_entry.insert("1.0", acc_data.get('video_path', ''))
        img_entry.insert("1.0", acc_data.get('image_path', ''))
        desc_entry.insert("1.0", acc_data.get('description', ''))
        
        if 'is_delete_media_var' in post_dict:
            post_dict['is_delete_media_var'].set(acc_data.get('is_delete_media', '0'))
        
        interact_nf_var.set(acc_data.get('interact_nf', '0'))
        nf_time_entry.insert(0, acc_data.get('nf_time', '60'))
        nf_like_var.set(acc_data.get('nf_like', '0'))
        nf_love_var.set(acc_data.get('nf_love', '0'))
        nf_haha_var.set(acc_data.get('nf_haha', '0'))
        nf_rand_var.set(acc_data.get('nf_rand', '0'))
        nf_react_count_entry.insert(0, acc_data.get('nf_react_count', '1'))
        nf_enable_cmt_var.set(acc_data.get('nf_enable_cmt', '0'))
        nf_cmt_count_entry.insert(0, acc_data.get('nf_cmt_count', '1'))
        nf_cmt_entry.insert("1.0", acc_data.get('nf_cmts', ''))
        
        is_canhan = acc_data.get('is_canhan', '1')
        canhan_name = acc_data.get('canhan_name', acc_data.get('canhan_link', ''))
        canhan_name_entry.insert(0, canhan_name)
        
        is_canhan_reels_var.set(acc_data.get('is_canhan_reels', '0'))

        if is_canhan == '1':
            is_canhan_var.set('1')
            canhan_name_entry.configure(state="normal")
        else:
            is_canhan_var.set('0')
            canhan_name_entry.configure(state="disabled")
            
        is_page = acc_data.get('is_page', '0')
        if is_page == '1':
            is_page_var.set('1')
            pages_frame.pack(fill="x", pady=0, after=row2)
            add_page_btn.configure(state="normal")
        else:
            add_page_btn.configure(state="disabled")
            
        page_names = acc_data.get('page_names', acc_data.get('page_links', []))
        for p in page_names:
            if p:
                add_page_entry(p)
                
        is_schedule = acc_data.get('is_schedule', '0')
        is_schedule_var.set(is_schedule)
        if is_schedule == '1':
            sch_d.configure(state="normal")
            sch_m.configure(state="normal")
            sch_y.configure(state="normal")
            sch_h.configure(state="normal")
            sch_min.configure(state="normal")
        sch_d.insert(0, acc_data.get('sch_d', ''))
        sch_m.insert(0, acc_data.get('sch_m', ''))
        sch_y.insert(0, acc_data.get('sch_y', ''))
        sch_h.insert(0, acc_data.get('sch_h', ''))
        sch_min.insert(0, acc_data.get('sch_min', ''))
        
        is_group_profile_var.set(acc_data.get('is_group_profile', '0'))
        is_group_page_var.set(acc_data.get('is_group_page', '0'))
        group_links_entry.insert("1.0", acc_data.get('group_links', ''))
        
        update_schedule_label()
        
    else:
        canhan_name_entry.insert(0, '')
        nf_time_entry.insert(0, '60')
        nf_react_count_entry.insert(0, '1')
        nf_cmt_count_entry.insert(0, '1')
        
    post_dict.update({
        'is_post_facebook_var': is_post_facebook_var,
        'is_canhan_var': is_canhan_var,
        'is_canhan_reels_var': is_canhan_reels_var,
        'canhan_name_entry': canhan_name_entry,
        'is_page_var': is_page_var,
        'page_entries': page_entries,
        'is_post_reel_var': is_post_reel_var,
        'is_post_video_var': is_post_video_var,
        'is_post_zalo_var': is_post_zalo_var,
        'is_post_tiktok_var': is_post_tiktok_var,
        'is_post_ig_var': is_post_ig_var,
        'is_post_threads_var': is_post_threads_var,
        'is_ig_threads_var': is_ig_threads_var,
        'threads_txt': threads_txt,
        'is_ig_fb_var': is_ig_fb_var,
        'fb_txt': fb_txt,
        'is_post_yt_var': is_post_yt_var,
        'is_yt_manual_title_var': is_yt_manual_title_var,
        'is_yt_ai_title_var': is_yt_ai_title_var,
        'yt_title_entry': yt_title_entry,
        'yt_ai_prompt_entry': yt_ai_prompt_entry,
        'is_yt_shorts_var': is_yt_shorts_var,
        'yt_kids_combo': yt_kids_combo,
        'is_yt_interact_var': is_yt_interact_var,
        'yt_interact_time': yt_interact_time,
        'is_yt_like_var': is_yt_like_var,
        'yt_cmt_entry': yt_cmt_entry,
        'vid_entry': vid_entry,
        'is_post_image_var': is_post_image_var,
        'img_entry': img_entry,
        'desc_entry': desc_entry,
        'append_ui': append_ui,
        'comment_ui': comment_ui,
        'interact_nf_var': interact_nf_var,
        'nf_time_entry': nf_time_entry,
        'nf_like_var': nf_like_var,
        'nf_love_var': nf_love_var,
        'nf_haha_var': nf_haha_var,
        'nf_rand_var': nf_rand_var,
        'nf_react_count_entry': nf_react_count_entry,
        'nf_enable_cmt_var': nf_enable_cmt_var,
        'nf_cmt_count_entry': nf_cmt_count_entry,
        'nf_cmt_entry': nf_cmt_entry,
        'is_schedule_var': is_schedule_var,
        'sch_d': sch_d,
        'sch_m': sch_m,
        'sch_y': sch_y,
        'sch_h': sch_h,
        'sch_min': sch_min,
        'is_group_profile_var': is_group_profile_var,
        'is_group_page_var': is_group_page_var,
        'group_links_entry': group_links_entry,
        'is_sample': '1' if is_sample_post else '0',
        'title_label': title_label,
        'post_frame': post_frame
    })
    acc_dict['posts'].append(post_dict)

def delete_post_block(app, acc_dict, post_dict, post_frame):
    # Bài đăng mẫu tuyệt đối không thể xóa
    if post_dict.get('is_sample') == '1':
        return
    post_frame.destroy()
    if post_dict in acc_dict['posts']:
        acc_dict['posts'].remove(post_dict)
    
    # Đánh số lại các bài viết thông thường
    acc_dict['posts'] = [p for p in acc_dict['posts'] if p.get('post_frame') and p['post_frame'].winfo_exists()]
    regular_idx = 1
    for p in acc_dict['posts']:
        if p.get('is_sample') != '1':
            if 'title_label' in p and p['title_label'].winfo_exists():
                p['title_label'].configure(text=f"Bài Đăng {regular_idx}")
            regular_idx += 1

def extract_single_post_data(post):
    """
    Trích xuất toàn bộ dữ liệu cấu hình thực tế trên giao diện của 1 post_dict
    """
    post_frame = post.get('post_frame')
    if post_frame and not post_frame.winfo_exists():
        return {}
        
    is_post_facebook = post['is_post_facebook_var'].get() if 'is_post_facebook_var' in post else '1'
    is_canhan = post['is_canhan_var'].get() if 'is_canhan_var' in post else '1'
    is_canhan_reels = post['is_canhan_reels_var'].get() if 'is_canhan_reels_var' in post else '0'
    canhan_name_raw = post['canhan_name_entry'].get().strip() if 'canhan_name_entry' in post else ''
    PLACEHOLDER_CANHAN = "Tên Trang Cá Nhân (chính xác)..."
    canhan_name = "" if canhan_name_raw == PLACEHOLDER_CANHAN else canhan_name_raw
    is_page = post['is_page_var'].get() if 'is_page_var' in post else '0'
    
    PLACEHOLDER_PAGE = "Tên Page (chính xác)..."
    page_names = []
    if 'page_entries' in post:
        for p_e in post['page_entries']:
            if p_e.winfo_exists():
                val = p_e.get().strip()
                if val and val != PLACEHOLDER_PAGE:
                    page_names.append(val)
            
    is_post_reel = post['is_post_reel_var'].get() if 'is_post_reel_var' in post else '0'
    is_post_video = post['is_post_video_var'].get() if 'is_post_video_var' in post else '1'
    is_post_zalo = post['is_post_zalo_var'].get() if 'is_post_zalo_var' in post else '0'
    is_post_tiktok = post['is_post_tiktok_var'].get() if 'is_post_tiktok_var' in post else '0'
    is_post_ig = post['is_post_ig_var'].get() if 'is_post_ig_var' in post else '0'
    is_post_threads = post['is_post_threads_var'].get() if 'is_post_threads_var' in post else '0'
    is_ig_threads = post['is_ig_threads_var'].get() if 'is_ig_threads_var' in post else '0'
    ig_threads_txt = post['threads_txt'].get().strip() if 'threads_txt' in post else ''
    is_ig_fb = post['is_ig_fb_var'].get() if 'is_ig_fb_var' in post else '0'
    ig_fb_txt = post['fb_txt'].get().strip() if 'fb_txt' in post else ''
    is_post_yt = post['is_post_yt_var'].get() if 'is_post_yt_var' in post else '0'
    yt_title = post['yt_title_entry'].get().strip() if 'yt_title_entry' in post else ''
    is_yt_manual_title = post.get('is_yt_manual_title_var').get() if 'is_yt_manual_title_var' in post else "1"
    is_yt_ai_title = post.get('is_yt_ai_title_var').get() if 'is_yt_ai_title_var' in post else "0"
    yt_ai_prompt = post['yt_ai_prompt_entry'].get().strip() if 'yt_ai_prompt_entry' in post else ""
    is_yt_shorts = post['is_yt_shorts_var'].get() if 'is_yt_shorts_var' in post else '0'
    yt_kids_text = post['yt_kids_combo'].get() if 'yt_kids_combo' in post else 'Không cho trẻ em'
    yt_kids = "1" if "Có" in yt_kids_text else "0"
    is_yt_interact = post['is_yt_interact_var'].get() if 'is_yt_interact_var' in post else '0'
    yt_interact_time = post['yt_interact_time'].get().strip() if 'yt_interact_time' in post else '5'
    is_yt_like = post['is_yt_like_var'].get() if 'is_yt_like_var' in post else '0'
    yt_cmt = post['yt_cmt_entry'].get().strip() if 'yt_cmt_entry' in post else ''
    vid = post['vid_entry'].get("1.0", "end-1c").strip() if 'vid_entry' in post else ''
    is_post_image = post['is_post_image_var'].get() if 'is_post_image_var' in post else '0'
    img = post['img_entry'].get("1.0", "end-1c").strip() if 'img_entry' in post else ''
    desc = post['desc_entry'].get("1.0", "end-1c").strip() if 'desc_entry' in post else ''
    app_val = ""
    if 'append_ui' in post and post['append_ui']:
        app_val = post['append_ui'].get_text()
        
    comment_data = {}
    if 'comment_ui' in post and post['comment_ui']:
        comment_data = post['comment_ui'].get_data()
    
    interact_nf = post['interact_nf_var'].get() if 'interact_nf_var' in post else '0'
    nf_time = post['nf_time_entry'].get().strip() if 'nf_time_entry' in post else '60'
    nf_like = post['nf_like_var'].get() if 'nf_like_var' in post else '0'
    nf_love = post['nf_love_var'].get() if 'nf_love_var' in post else '0'
    nf_haha = post['nf_haha_var'].get() if 'nf_haha_var' in post else '0'
    nf_rand = post['nf_rand_var'].get() if 'nf_rand_var' in post else '0'
    nf_react_count = post['nf_react_count_entry'].get().strip() if 'nf_react_count_entry' in post else '1'
    nf_enable_cmt = post['nf_enable_cmt_var'].get() if 'nf_enable_cmt_var' in post else '0'
    nf_cmt_count = post['nf_cmt_count_entry'].get().strip() if 'nf_cmt_count_entry' in post else '1'
    nf_cmts = post['nf_cmt_entry'].get("1.0", "end-1c").strip() if 'nf_cmt_entry' in post else ''
    
    is_schedule = post['is_schedule_var'].get() if 'is_schedule_var' in post else '0'
    sch_d = post['sch_d'].get().strip() if 'sch_d' in post else ''
    sch_m = post['sch_m'].get().strip() if 'sch_m' in post else ''
    sch_y = post['sch_y'].get().strip() if 'sch_y' in post else ''
    sch_h = post['sch_h'].get().strip() if 'sch_h' in post else ''
    sch_min = post['sch_min'].get().strip() if 'sch_min' in post else ''
    
    is_group_profile = post['is_group_profile_var'].get() if 'is_group_profile_var' in post else '0'
    is_group_page = post['is_group_page_var'].get() if 'is_group_page_var' in post else '0'
    group_links = post['group_links_entry'].get("1.0", "end-1c").strip() if 'group_links_entry' in post else ''
    
    is_delete_media = post.get('is_delete_media_var').get() if 'is_delete_media_var' in post else '0'
    
    post_data = {
        'is_sample': post.get('is_sample', '0'),
        'is_post_facebook': is_post_facebook,
        'is_canhan': is_canhan,
        'is_canhan_reels': is_canhan_reels,
        'canhan_name': canhan_name,
        'is_page': is_page,
        'page_names': page_names,
        'is_post_reel': is_post_reel,
        'is_post_video': is_post_video,
        'is_post_zalo': is_post_zalo,
        'is_post_tiktok': is_post_tiktok,
        'is_post_ig': is_post_ig,
        'is_post_threads': is_post_threads,
        'is_ig_threads': is_ig_threads,
        'ig_threads_txt': ig_threads_txt,
        'is_ig_fb': is_ig_fb,
        'ig_fb_txt': ig_fb_txt,
        'is_post_yt': is_post_yt,
        'yt_title': yt_title,
        'is_yt_manual_title': is_yt_manual_title,
        'is_yt_ai_title': is_yt_ai_title,
        'yt_ai_prompt': yt_ai_prompt,
        'is_yt_shorts': is_yt_shorts,
        'yt_kids_text': yt_kids_text,
        'yt_kids': yt_kids,
        'is_yt_interact': is_yt_interact,
        'yt_interact_time': yt_interact_time,
        'is_yt_like': is_yt_like,
        'yt_cmt': yt_cmt,
        'video_path': vid,
        'is_post_image': is_post_image,
        'image_path': img,
        'description': desc,
        'append_text': app_val,
        'is_delete_media': is_delete_media,
        'interact_nf': interact_nf,
        'nf_time': nf_time,
        'nf_like': nf_like,
        'nf_love': nf_love,
        'nf_haha': nf_haha,
        'nf_rand': nf_rand,
        'nf_react_count': nf_react_count,
        'nf_enable_cmt': nf_enable_cmt,
        'nf_cmt_count': nf_cmt_count,
        'nf_cmts': nf_cmts,
        'is_schedule': is_schedule,
        'sch_d': sch_d,
        'sch_m': sch_m,
        'sch_y': sch_y,
        'sch_h': sch_h,
        'sch_min': sch_min,
        'is_group_profile': is_group_profile,
        'is_group_page': is_group_page,
        'group_links': group_links,
        'is_delete_media': is_delete_media,
        'post_frame': post.get('post_frame')
    }
    post_data.update(comment_data)
    return post_data

def add_post_from_sample(app, acc_dict):
    """
    Tạo bài đăng mới tự động sao chép 100% cấu hình từ Bài Đăng Mẫu (tim)
    """
    # Tìm bài đăng mẫu trong danh sách posts của acc_dict
    sample_post = next((p for p in acc_dict.get('posts', []) if str(p.get('is_sample', '0')) == '1'), None)
    template_data = {}
    if sample_post:
        template_data = extract_single_post_data(sample_post)
    elif acc_dict.get('posts') and len(acc_dict['posts']) > 0:
        template_data = extract_single_post_data(acc_dict['posts'][0])
        
    new_data = template_data.copy()
    new_data['is_sample'] = '0'
    new_data['video_path'] = ''
    new_data['image_path'] = ''
    new_data['is_schedule'] = '0'
    new_data.pop('post_frame', None)
    
    add_post_block(app, acc_dict, acc_data=new_data, is_sample=False)


