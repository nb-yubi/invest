from supabase import create_client, Client

# Thông tin kết nối dự án của bạn
url: str = "https://yizfbtbsfhkuxitjlomn.supabase.co"
# Sử dụng Publishable key bắt đầu bằng sb_publishable_... đã lấy ở phần API Keys
key: str = "sb_publishable_8FOmhSxm_DsVxQxbVhafWg_vq-8DmWd"

supabase: Client = create_client(url, key)

# --- PHẦN 1: ĐỌC DỮ LIỆU TỪ BẢNG TAIKHOAN ---
try:
    print("Đang tải dữ liệu từ bảng TAIKHOAN...")
    response = supabase.table("TAIKHOAN").select("*").execute()

    # In ra danh sách dữ liệu hiện có
    print("Dữ liệu hiện tại trong bảng:", response.data)

except Exception as e:
    print("Lỗi khi đọc dữ liệu:", e)


# --- PHẦN 2: THÊM DỮ LIỆU MỚI (Ví dụ nếu bạn muốn code tự động thêm dòng) ---
# Uncomment (bỏ dấu #) đoạn dưới đây nếu bạn muốn thử thêm dữ liệu mới từ Python:
"""
try:
    # Điền tên cột và giá trị tương ứng thực tế trong bảng của bạn
    data_moi = {"ten_cot_1": "Gia_tri_1", "ten_cot_2": 100}

    res_insert = supabase.table("TAIKHOAN").insert(data_moi).execute()
    print("Thêm dữ liệu thành công:", res_insert.data)
except Exception as e:
    print("Lỗi khi thêm dữ liệu:", e)
"""    