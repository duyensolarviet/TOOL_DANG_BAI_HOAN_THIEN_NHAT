import os
import shutil
import json
import tkinter.messagebox as messagebox

def clean_unused_profiles(app):
    """
    Xoá các thư mục Chrome profile trong thư mục 'profiles' 
    mà không tương ứng với bất kỳ tài khoản nào trong accounts.json.
    """
    try:
        profiles_dir = os.path.join(os.getcwd(), 'profiles')
        accounts_file = os.path.join(os.getcwd(), 'accounts.json')
        
        if not os.path.exists(profiles_dir):
            messagebox.showinfo("Thông báo", "Không tìm thấy thư mục profiles.")
            return

        # Đọc danh sách ID tài khoản đang có
        active_ids = set()
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r', encoding='utf-8') as f:
                try:
                    accounts = json.load(f)
                    for acc in accounts:
                        if 'id' in acc and acc['id']:
                            active_ids.add(str(acc['id']).strip())
                except json.JSONDecodeError:
                    pass
        
        # Quét các thư mục trong profiles
        deleted_count = 0
        freed_space = 0
        
        for item in os.listdir(profiles_dir):
            item_path = os.path.join(profiles_dir, item)
            
            # Nếu là thư mục và tên thư mục không nằm trong danh sách active_ids
            if os.path.isdir(item_path) and item not in active_ids:
                # Tính dung lượng trước khi xoá (tuỳ chọn)
                def get_size(start_path):
                    total_size = 0
                    for dirpath, dirnames, filenames in os.walk(start_path):
                        for f in filenames:
                            fp = os.path.join(dirpath, f)
                            if not os.path.islink(fp):
                                total_size += os.path.getsize(fp)
                    return total_size
                
                try:
                    folder_size = get_size(item_path)
                except:
                    folder_size = 0
                
                # Xoá thư mục
                try:
                    shutil.rmtree(item_path)
                    deleted_count += 1
                    freed_space += folder_size
                except Exception as e:
                    print(f"Không thể xoá {item_path}: {e}")
        
        if deleted_count > 0:
            mb = freed_space / (1024 * 1024)
            messagebox.showinfo(
                "Hoàn tất", 
                f"Đã dọn dẹp {deleted_count} profile rác không sử dụng.\nGiải phóng {mb:.2f} MB dung lượng ổ cứng."
            )
        else:
            messagebox.showinfo("Thông báo", "Không có profile rác nào cần dọn dẹp. Hệ thống đang sạch sẽ!")
            
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi dọn dẹp profile: {e}")
