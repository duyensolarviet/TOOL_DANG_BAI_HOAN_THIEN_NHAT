import threading
import time
from datetime import datetime
from facebook_bot import FacebookBot


def schedule_worker(target_time, run_posting_func, log_func, stop_event=None):
    """
    Hàm ngầm đếm ngược đến đúng giờ target_time mới gọi run_posting_func.
    - Khi còn > 10s: ngủ 5s rồi check lại, log mỗi 60s.
    - Khi còn <= 10s: ngủ 0.5s để căn chính xác.
    """
    log_func(f"[Schedule] Đã kích hoạt hẹn giờ! Bài sẽ đăng vào: {target_time.strftime('%d/%m/%Y %H:%M:%S')}")

    last_log_time = 0  # Theo dõi lần log gần nhất (để không log quá dày)

    while True:
        if stop_event and stop_event.is_set():
            log_func("[Schedule] Đã nhận tín hiệu DỪNG. Hủy lịch đăng bài.")
            return

        now = datetime.now()
        remaining_seconds = (target_time - now).total_seconds()

        # Đã đến hoặc qua thời gian hẹn -> BẮT ĐẦU CHẠY
        if remaining_seconds <= 0:
            log_func("[Schedule] ===== ĐÃ ĐẾN GIỜ HẸN! BẮT ĐẦU CHẠY TIẾN TRÌNH ĐĂNG BÀI =====")
            run_posting_func()
            break

        # Khi còn trên 10 giây: ngủ 5s, log mỗi 60s
        if remaining_seconds > 10:
            current_time = time.time()
            if current_time - last_log_time >= 60:
                mins = int(remaining_seconds // 60)
                secs = int(remaining_seconds % 60)
                if mins > 0:
                    log_func(f"[Schedule] Đang chờ đến {target_time.strftime('%H:%M %d/%m/%Y')} — Còn: {mins} phút {secs} giây...")
                else:
                    log_func(f"[Schedule] Đang chờ đến {target_time.strftime('%H:%M %d/%m/%Y')} — Còn: {secs} giây...")
                last_log_time = current_time
            time.sleep(5)
        else:
            # Dưới 10s: ngủ 0.5s để căn chính xác từng giây
            log_func(f"[Schedule] Sắp đến giờ! Đang đếm ngược {int(remaining_seconds)} giây...")
            time.sleep(0.5)


class BotManager:
    def __init__(self, accounts, log_callback=None, app=None):
        self.accounts = accounts
        self.log_callback = log_callback
        self.app = app
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def start_all(self):
        threads = []

        self.log(f"Bắt đầu chạy cho {len(self.accounts)} tài khoản có video/ảnh hợp lệ.")

        # Tạo luồng cho từng tài khoản
        for acc in self.accounts:
            # Khởi tạo bot và chạy trong thread
            thread = threading.Thread(
                target=self.run_bot,
                args=(acc,),
                daemon=True
            )
            threads.append(thread)
            thread.start()

        # Đợi tất cả các luồng hoàn thành
        for thread in threads:
            thread.join()

    def run_bot(self, account):
        if self.stop_event.is_set():
            return
            
        posts = list(account.get('posts', []))
        if not posts:
            # Fallback legacy
            posts = [account]
            
        for i, post_data in enumerate(posts):
            if self.stop_event.is_set():
                break
                
            is_sample = str(post_data.get('is_sample', '0')) == '1' or post_data.get('is_sample') is True
            merged_data = account.copy()
            merged_data.pop('posts', None)
            merged_data.update(post_data)
            
            is_post_video = merged_data.get('is_post_video', '1') == '1'
            is_post_image = merged_data.get('is_post_image', '0') == '1'
            video_path = merged_data.get('video_path', '') if is_post_video else ''
            image_path = merged_data.get('image_path', '') if is_post_image else ''
            desc_check = merged_data.get('description', '').strip()

            # Nếu là Bài Đăng Mẫu và không có video/ảnh/nội dung thì bỏ qua (chỉ làm khuôn mẫu)
            if is_sample and not video_path and not image_path and not desc_check:
                self.log(f"[{account['id']}] [Bài Đăng Mẫu] Bỏ qua vì chỉ đóng vai trò làm khuôn mẫu.")
                continue

            post_label = "BÀI ĐĂNG MẪU" if is_sample else f"BÀI ĐĂNG THỨ {i+1}/{len(posts)}"
            self.log(f"[{account['id']}] ===== XỬ LÝ {post_label} =====")
            
            is_schedule = merged_data.get('is_schedule') == '1'

            def do_post(data=merged_data, vp=video_path, ip=image_path, original_post_data=post_data):
                if self.stop_event.is_set():
                    self.log(f"[{data['id']}] Nhận tín hiệu dừng, hủy tiến trình chạy.")
                    return

                append_txt = data.get('append_text', '').strip()
                desc_val = data.get('description', '').strip()
                if append_txt:
                    data['description'] = desc_val + "\n" + append_txt if desc_val else append_txt

                data['is_schedule'] = '0'
                bot = FacebookBot(data, log_callback=self.log_callback, stop_event=self.stop_event)
                try:
                    bot.run(vp, ip)
                    # Sau khi đăng thành công toàn bộ quá trình bot, nếu user tích xóa file thì xóa đi
                    is_del = data.get('is_delete_media', '0')
                    if is_del == '1':
                        try:
                            from delete_media_feature import delete_media_if_requested
                            if vp:
                                delete_media_if_requested(vp, is_del, self.log)
                            if ip:
                                delete_media_if_requested(ip, is_del, self.log)
                        except Exception as e:
                            self.log(f"[{data['id']}] Lỗi khi load chức năng xóa video/ảnh: {e}")
                            
                    # --- GỌI TÍNH NĂNG TỰ ĐỘNG XÓA BÀI LIỀN ---
                    try:
                        from delete_posted_feature import check_and_delete_posted
                        # post_data là dữ liệu gốc lấy từ account['posts']
                        check_and_delete_posted(self.app, account, original_post_data)
                    except Exception as ex:
                        self.log(f"[{data['id']}] Lỗi tính năng xóa bài: {ex}")
                        
                except Exception as e:
                    self.log(f"Lỗi ở tài khoản {data['id']}: {e}")

            if is_schedule:
                # --- PARSE THỜI GIAN ---
                sch_d_raw = merged_data.get('sch_d', '').strip()
                sch_m_raw = merged_data.get('sch_m', '').strip()
                sch_y_raw = merged_data.get('sch_y', '').strip()
                sch_h_raw = merged_data.get('sch_h', '').strip()
                sch_min_raw = merged_data.get('sch_min', '').strip()

                if not all([sch_d_raw, sch_m_raw, sch_y_raw, sch_h_raw, sch_min_raw]):
                    self.log(
                        f"[{merged_data['id']}] [Schedule] CẢNH BÁO: Bật lên lịch nhưng chưa điền đủ "
                        f"Ngày/Tháng/Năm/Giờ/Phút! Sẽ đăng NGAY LẬP TỨC."
                    )
                    do_post()
                    continue

                try:
                    sch_d = int(sch_d_raw)
                    sch_m = int(sch_m_raw)
                    sch_y = int(sch_y_raw)
                    sch_h = int(sch_h_raw)
                    sch_min = int(sch_min_raw)

                    target_time = datetime(sch_y, sch_m, sch_d, sch_h, sch_min, 0)

                    if datetime.now() >= target_time:
                        self.log(
                            f"[{merged_data['id']}] [Schedule] Thời gian hẹn ({target_time.strftime('%d/%m/%Y %H:%M')}) "
                            f"đã qua! Sẽ đăng NGAY LẬP TỨC."
                        )
                        do_post()
                        continue

                    # Bắt buộc bind argument trong lambda
                    schedule_worker(
                        target_time, 
                        lambda d=merged_data, v=video_path, i=image_path: do_post(data=d, vp=v, ip=i), 
                        self.log, 
                        self.stop_event
                    )
                except ValueError:
                    self.log(f"[{merged_data['id']}] [Schedule] Ngày/giờ nhập không hợp lệ! Đăng ngay lập tức.")
                    do_post()
            else:
                do_post()
                
        # Dọn dẹp thủ công nếu driver còn kẹt (vì code cũ tự đóng, nhưng giờ ta gom nhóm)
        # Thực ra ta có thể xử lý việc đóng tại đây bằng cách gọi từ ACTIVE_DRIVERS
        try:
            from facebook_bot import ACTIVE_DRIVERS
            if account['id'] in ACTIVE_DRIVERS:
                ACTIVE_DRIVERS[account['id']].quit()
                del ACTIVE_DRIVERS[account['id']]
                
                # Sau khi đã đóng Chrome, tiến hành dọn rác
                import os, shutil
                profile_dir = os.path.join(os.getcwd(), 'profiles', str(account.get('id', '')))
                default_dir = os.path.join(profile_dir, 'Default')
                caches = [
                    os.path.join(default_dir, 'Cache'),
                    os.path.join(default_dir, 'Code Cache'),
                    os.path.join(default_dir, 'GPUCache'),
                    os.path.join(default_dir, 'Network Action Predictor')
                ]
                cleaned = 0
                for cache_path in caches:
                    if os.path.exists(cache_path):
                        try:
                            if os.path.isdir(cache_path):
                                shutil.rmtree(cache_path, ignore_errors=True)
                            else:
                                os.remove(cache_path)
                            cleaned += 1
                        except: pass
                if cleaned > 0:
                    self.log(f"[{account['id']}] Đã dọn dẹp xong Cache rác sau khi đóng trình duyệt.")
                    
                # KIỂM TRA VÀ XÓA FILE MP4 TẠM (DO YOUTUBEBOT TẠO RA) NẾU CÓ
                try:
                    for post_data in account.get('posts', [account]):
                        is_post_yt = str(post_data.get('is_post_yt', '0')) == '1'
                        if is_post_yt:
                            video_path = post_data.get('video_path', '').strip()
                            image_path = post_data.get('image_path', '').strip()
                            media_path = video_path if video_path else image_path
                            paths = [p.strip() for p in media_path.split('\n') if p.strip()]
                            if paths:
                                first_video = os.path.abspath(paths[0]).replace('\\', '/')
                                if not first_video.lower().endswith('.mp4'):
                                    mp4_tmp = os.path.splitext(first_video)[0] + ".mp4"
                                    if os.path.exists(mp4_tmp):
                                        for _ in range(5):
                                            try:
                                                import time
                                                time.sleep(2) # Đợi thêm chút để Chrome nhả hoàn toàn file lock
                                                os.remove(mp4_tmp)
                                                self.log(f"[{account['id']}] Đã xoá file MP4 tạm sau khi đóng trình duyệt.")
                                                break
                                            except Exception as e:
                                                self.log(f"[{account['id']}] Đang thử xoá lại MP4 tạm ({e})...")
                                    else:
                                        self.log(f"[{account['id']}] File MP4 tạm không tồn tại: {mp4_tmp}")
                                else:
                                    self.log(f"[{account['id']}] File gốc đã là MP4, không cần xoá bản sao: {first_video}")
                            else:
                                self.log(f"[{account['id']}] Không có media_path để kiểm tra xoá MP4.")
                        else:
                            self.log(f"[{account['id']}] Không chọn Đăng YouTube, bỏ qua dọn dẹp file MP4 tạm của YouTube.")
                except Exception as e:
                    self.log(f"[{account['id']}] Lỗi xoá file MP4 tạm: {e}")
                
        except: pass
