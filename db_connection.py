# File: db_connection.py
# Module kết nối tập trung đến Supabase (PostgreSQL trên Supabase)
# Các file khác chỉ cần: from db_connection import supabase, get_supabase

import os
from supabase import create_client, Client

# --- CẤU HÌNH KẾT NỐI ---
# Ưu tiên đọc từ biến môi trường (an toàn hơn); nếu không có thì dùng giá trị mặc định bên dưới.
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://yizfbtbsfhkuxitjlomn.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_8FOmhSxm_DsVxQxbVhafWg_vq-8DmWd")

_client: Client | None = None


def get_supabase() -> Client:
    """Trả về client Supabase (tạo 1 lần duy nhất, tái sử dụng cho toàn app)."""
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# Dùng trực tiếp nếu muốn (khuyến nghị: get_supabase())
supabase: Client = get_supabase()


# --- CÁC HÀM DÙNG CHUNG ---
def fetch_all(table: str, columns: str = "*") -> list[dict]:
    """Đọc toàn bộ dữ liệu từ một bảng."""
    try:
        res = supabase.table(table).select(columns).execute()
        return res.data or []
    except Exception as e:
        print(f"Lỗi khi đọc bảng '{table}':", e)
        return []


def insert_row(table: str, data: dict) -> list[dict] | None:
    """Thêm 1 dòng vào bảng."""
    try:
        res = supabase.table(table).insert(data).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi thêm dữ liệu vào '{table}':", e)
        return None


def update_row(table: str, match_column: str, match_value, data: dict) -> list[dict] | None:
    """Cập nhật các dòng thỏa điều kiện match_column = match_value."""
    try:
        res = (
            supabase.table(table)
            .update(data)
            .eq(match_column, match_value)
            .execute()
        )
        return res.data
    except Exception as e:
        print(f"Lỗi khi cập nhật '{table}':", e)
        return None


def delete_row(table: str, match_column: str, match_value) -> list[dict] | None:
    """Xóa các dòng thỏa điều kiện match_column = match_value."""
    try:
        res = supabase.table(table).delete().eq(match_column, match_value).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi xóa dữ liệu trong '{table}':", e)
        return None


# --- KIỂM TRA KẾT NỐI KHI CHẠY TRỰC TIẾP FILE NÀY ---
if __name__ == "__main__":
    print("Đang kiểm tra kết nối đến Supabase...")
    data = fetch_all("TAIKHOAN")
    if data:
        print(f"Kết nối OK! Bảng TAIKHOAN có {len(data)} dòng:")
        for row in data:
            print(row)
    else:
        print("Không có dữ liệu hoặc có lỗi kết nối (xem thông báo ở trên).")
