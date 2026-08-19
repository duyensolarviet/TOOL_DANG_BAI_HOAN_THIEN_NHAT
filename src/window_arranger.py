import time
import threading
import json
import os
import ctypes

def get_config():
    try:
        if os.path.exists("global_config.json"):
            with open("global_config.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"split_cols": "2", "auto_arrange": "1"}

def set_config(val, auto_arrange=None):
    try:
        data = get_config()
        if val is not None:
            data["split_cols"] = str(val)
        if auto_arrange is not None:
            data["auto_arrange"] = str(auto_arrange)
        with open("global_config.json", "w", encoding="utf-8") as f:
            json.dump(data, f)
    except:
        pass

last_driver_count = 0

def auto_arrange_windows(num_cols):
    try:
        from facebook_bot import ACTIVE_DRIVERS
        drivers = list(ACTIVE_DRIVERS.values())
        num_windows = len(drivers)
        if num_windows == 0:
            return

        cols = int(num_cols)
        if cols <= 0:
            cols = 1
            
        rows = (num_windows + cols - 1) // cols
        
        # Lấy độ phân giải màn hình trên Windows (dùng Logical pixels để Selenium tự scale)
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        
        # Trừ đi khoảng trống của thanh Taskbar bên dưới
        taskbar_height = 40
        usable_height = screen_height - taskbar_height
        
        win_width = screen_width // cols
        win_height = usable_height // rows
        
        # Lấy tỷ lệ scale (DPI) của màn hình
        try:
            dpi = user32.GetDpiForSystem()
            scale = dpi / 96.0
        except:
            scale = 1.0
            
        # Viền tàng hình của Windows 10/11 (tính bằng physical pixels, thường là 7px)
        invisible_border = 7
        
        for idx, driver in enumerate(drivers):
            col = idx % cols
            row = idx // cols
            
            # Tính toán vị trí và kích thước mong muốn (physical pixels)
            vx = col * win_width
            vy = row * win_height
            
            # Bù trừ viền tàng hình để các cửa sổ khớp khít vào nhau
            x_phys = vx - invisible_border
            y_phys = vy
            w_phys = win_width + (invisible_border * 2)
            h_phys = win_height + invisible_border
            
            # Đổi sang Logical pixels vì Selenium điều khiển Chrome thông qua CSS pixels (logical)
            x = round(x_phys / scale)
            y = round(y_phys / scale)
            w = round(w_phys / scale)
            h = round(h_phys / scale)
            
            try:
                # Đặt vị trí và kích thước cửa sổ
                driver.set_window_position(x, y)
                driver.set_window_size(w, h)
            except:
                pass
    except Exception as e:
        print(f"Lỗi sắp xếp cửa sổ: {e}")

def start_auto_arranger():
    """
    Tiến trình chạy ngầm để theo dõi và sắp xếp cửa sổ mỗi khi có Chrome mới mở ra.
    """
    global last_driver_count
    def worker():
        global last_driver_count
        while True:
            try:
                from facebook_bot import ACTIVE_DRIVERS
                current_count = len(ACTIVE_DRIVERS)
                
                # Cứ khi nào số lượng trình duyệt mở ra thay đổi (thêm tab mới), nó sẽ tự động sắp xếp lại
                if current_count > 0 and current_count != last_driver_count:
                    # Chờ 3 giây để cửa sổ Chrome tải xong hẳn giao diện rồi mới kéo
                    time.sleep(3) 
                    config = get_config()
                    is_auto = config.get("auto_arrange", "1") == "1"
                    if is_auto:
                        cols_str = config.get("split_cols", "2")
                        if cols_str and cols_str.isdigit():
                            cols = int(cols_str)
                            if cols > 0:
                                auto_arrange_windows(cols)
                    last_driver_count = current_count
                elif current_count == 0:
                    last_driver_count = 0
            except:
                pass
            time.sleep(2)
    
    t = threading.Thread(target=worker, daemon=True)
    t.start()
