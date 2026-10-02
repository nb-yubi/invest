-- ==== Script thiết lập bảng GIAODICH (Supabase) ====
-- Chạy trong Supabase SQL Editor

-- 1) Tạo bảng nếu chưa có
create table if not exists public."GIAODICH" (
  "IDGD"      text primary key,
  "LOAIGD"    varchar(20),
  "MACP"      varchar(10),
  "NGAYGD"    varchar(10),
  "KHOILUONG" numeric(14,2),
  "GIA"       numeric(14,2),
  "PHI_THUE"  numeric(14,2),
  "THANHTIEN" numeric(18,2)
);

-- 2) Tắt RLS (cách đơn giản) HOẶC dùng chính sách cho phép toàn bộ
-- Cách A: tắt RLS
alter table public."GIAODICH" disable row level security;

-- Cách B: nếu muốn giữ RLS, dùng policy
-- alter table public."GIAODICH" enable row level security;
-- create policy "allow all" on public."GIAODICH"
--   for all using (true) with check (true);
