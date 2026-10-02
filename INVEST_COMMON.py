# File: INVEST_COMMON.py
# -*- coding: utf-8 -*-
"""Phần dùng chung cho các loại menu: helpers đọc/ghi giao dịch, render form."""
import datetime as dt
import pandas as pd

from db_connection import supabase

BANG_GIAODICH = "GIAODICH"   # Bảng giao dịch trên Supabase
BANG_TAIKHOAN = "TAIKHOAN"   # Bảng tài khoản trên Supabase
BANG_CHIPHI = "CHIPHI"       # Bảng cấu hình phí giao dịch (PHIGD, PHIMG)
BANG_DOTGD = "DOTGD"         # Bảng đợt giao dịch (MADOT, MACP, NGAYBD, NGAYKT)

MENU_ITEMS = [
    ("01.Ghi Nhận MUA", "/form/MUA"),
    ("02.Ghi Nhận BÁN", "/form/BAN"),
    ("03.Ghi Nhận CỔ TỨC", "/form/CỔ TỨC"),
    ("04.Tra Tìm Dữ Liệu Giao Dịch", "/tra"),
    ("07.Thiết Lập Mã Đợt", "/dotgd"),
    ("05.Tra Tìm Theo Tổng", "/tong"),
    ("06.Tra Tìm Chi Tiết", "/chitiet"),
]


def kiem_tra_dang_nhap(taikhoan: str, matma: str) -> bool:
    """Kiểm tra tài khoản/mật mã trên bảng TAIKHOAN (Supabase)."""
    if not taikhoan or not matma:
        return False
    try:
        res = supabase.table(BANG_TAIKHOAN).select("*") \
            .eq("TAIKHOAN", taikhoan.strip()).eq("MATMA", matma).execute()
        return bool(res.data)
    except Exception as e:
        print("[LOGIN-ERROR]", repr(e))
        return False


def doc_giao_dich() -> pd.DataFrame:
    """Đọc toàn bộ giao dịch từ bảng GIAODICH (Supabase)."""
    cols = ["IDGD", "LOAIGD", "MACP", "NGAYGD", "MADOT", "KHOILUONG", "GIA", "PHIGD", "THANHTIEN"]
    try:
        res = supabase.table(BANG_GIAODICH).select(",".join(cols)).order("NGAYGD", desc=False).execute()
        df = pd.DataFrame(res.data or [], columns=cols)
    except Exception as e:
        print("[GIAODICH-ERROR]", repr(e))
        return pd.DataFrame(columns=cols)
    # Chuẩn hóa số & tính lại THANHTIEN = KL*GIA + Phí (GIAODICH.PHIGD)
    for c in ("KHOILUONG", "GIA", "PHIGD", "THANHTIEN"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["THANHTIEN"] = df["KHOILUONG"] * df["GIA"] + \
        df["KHOILUONG"] * df["PHIGD"] * df["LOAIGD"].astype(str).str.upper().map(
            lambda l: -1 if l == "BAN" else 1)
    return df


def doc_chiphi():
    """Đọc tỷ lệ phí/thuế từ bảng CHIPHI (Supabase). Trả về (PHIGD, PHIMG, THUETNCN)."""
    try:
        res = supabase.table(BANG_CHIPHI).select("PHIGD,PHIMG,THUETNCN").limit(1).execute()
        row = (res.data or [{}])[0]
        return (float(row.get("PHIGD") or 0), float(row.get("PHIMG") or 0),
                float(row.get("THUETNCN") or 0))
    except Exception as e:
        print("[CHIPHI-ERROR]", repr(e))
        return (0.0, 0.0, 0.0)


def doc_madot(macp: str) -> str:
    """Lấy MADOT đang mở của mã CP: dòng DOTGD có MACP khớp và NGAYKT rỗng/NULL.
    Không tìm thấy -> '' (rỗng)."""
    if not macp:
        return ""
    try:
        res = supabase.table(BANG_DOTGD).select("MADOT") \
            .eq("MACP", macp).or_("NGAYKT.is.null,NGAYKT.eq.").limit(1).execute()
        data = res.data or []
        return str(data[0].get("MADOT") or "") if data else ""
    except Exception as e:
        print("[DOTGD-ERROR]", repr(e))
        return ""


def validate_row(data):
    """Kiểm tra & chuẩn hóa 1 dòng giao dịch. Trả về (dict, None) hoặc (None, lỗi).
    Ngày nhập định dạng YYYY/MM/DD (cả YYYY-MM-DD cũng được chấp nhận).
    Kết quả khớp các cột của bảng GIAODICH trên Supabase."""
    ma = str(data.get("ma", "")).strip().upper()
    loai = str(data.get("loai", "")).strip().upper()
    ngay = str(data.get("ngay", "")).strip().replace("-", "/")

    def _so(v):
        """Đọc số linh hoạt: '25.330' -> 25330 (nghìn), '45.59' -> 45.59 (thập phân).
        Quy tắc: nhiều dấu '.' hoặc nhóm cuối đủ 3 chữ số -> nghìn; ',' luôn là thập phân."""
        s = str(v).strip().replace(" ", "")
        if not s:
            return 0.0
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            p = s.split(".")
            if len(p) > 2 or (len(p) == 2 and p[1].isdigit() and len(p[1]) == 3 and p[0] != ""):
                s = "".join(p)   # ngăn cách nghìn
        try:
            return float(s)
        except ValueError:
            return 0.0
    try:
        kl = int(_so(data.get("kholuong")))
        gia = _so(data.get("gia"))
        phi = _so(data.get("phi"))
    except (ValueError, TypeError):
        return None, "Khối lượng/Giá/Phí phải là số!"
    try:
        ngay_iso = dt.datetime.strptime(ngay, "%Y/%m/%d").strftime("%Y-%m-%d")
    except ValueError:
        return None, "Ngày phải theo định dạng YYYY/MM/DD!"
    if not ma:
        return None, "Vui lòng nhập mã CP!"
    # MADOT: từ bảng DOTGD (đợt còn mở NGAYKT rỗng/NULL) — áp dụng cho mọi loại GD
    madot = str(data.get("madot", "") or "").strip() or doc_madot(ma)
    if not madot:
        return None, f"Mã CP: {ma} chưa có mã đợt, xin thiết lập, cám ơn!"
    # Phí/Thuế tự tính theo loại GD (server luôn tính lại, không nhận từ user):
    #   MUA: Phí/CP     = Giá * (CHIPHI.PHIGD + CHIPHI.PHIMG)
    #   BÁN: Phí Thuế/CP = Giá * (CHIPHI.PHIGD + CHIPHI.THUETNCN)
    if loai == "MUA":
        phigd, phimg, _thue = doc_chiphi()
        phi = gia * (phigd + phimg)
    elif loai == "BAN":
        phigd, _phimg, thue = doc_chiphi()
        phi = gia * (phigd + thue)
    # Tổng Tiền: MUA = KL*Giá + Tổng Phí; BÁN = KL*Giá − Tổng Thuế Phí (đã trừ thuế)
    dau = 1 if loai != "BAN" else -1
    thanh_tien = kl * gia + dau * kl * phi
    return {"LOAIGD": str(data.get("loai", "")).strip(), "MACP": ma, "NGAYGD": ngay_iso,
            "MADOT": madot,
            "KHOILUONG": kl, "GIA": gia, "PHIGD": phi, "THANHTIEN": thanh_tien}, None


def form_giao_dich(loai: str):
    """Xử lý route /form/<loai>: tra tìm + lọc + sắp xếp + render form.html.
    Dùng chung cho MUA / BÁN / CỔ TỨC."""
    from flask import request, render_template, redirect, url_for, session

    if "user" not in session:
        return redirect(url_for("login"))
    # Điều kiện tra tìm: theo Mã, Mã Đợt và/hoặc Từ ngày - Đến ngày
    ma = request.args.get("ma", "").strip().upper()
    madot = request.args.get("madot", "").strip().upper()
    tu = request.args.get("tu", "").strip()   # YYYY/MM/DD (hoặc YYYY-MM-DD)
    den = request.args.get("den", "").strip()

    def _parse_date(v):
        v = v.strip().replace("-", "/")
        try:
            return dt.datetime.strptime(v, "%Y/%m/%d")
        except ValueError:
            return None

    df = doc_giao_dich()
    df["_NGAY"] = pd.to_datetime(df["NGAYGD"], errors="coerce")
    if not df.empty:
        df = df[df["LOAIGD"].astype(str).str.upper() == loai.upper()]
        if ma:
            df = df[df["MACP"].astype(str).str.upper() == ma]
        if madot:
            df = df[df["MADOT"].astype(str).str.upper() == madot]
        df = df.copy()
        d_tu = _parse_date(tu)
        d_den = _parse_date(den)
        if d_tu:
            df = df[df["_NGAY"] >= d_tu]
        if d_den:
            df = df[df["_NGAY"] <= d_den]
    # Sắp xếp: ngày mới nhất đứng đầu, cùng ngày thì theo mã CP (A→Z)
    df = df.sort_values(["_NGAY", "MACP"], ascending=[False, True])
    df = df.drop(columns=["_NGAY"])
    rows = []
    for _, r in df.iterrows():
        rows.append({"id": str(r["IDGD"]),
                     "ma": str(r["MACP"]),
                     "madot": str(r.get("MADOT") or ""),
                     "ngay": str(r["NGAYGD"])[:10].replace("-", "/"),
                     "kholuong": r["KHOILUONG"],
                     "gia": r["GIA"],
                     "phi": r["PHIGD"],
                     "thanhtien": r["THANHTIEN"]})
    # Menu 01.Ghi Nhận MUA / 02.Ghi Nhận BÁN: Phí tự tính từ bảng CHIPHI, không cho user nhập
    auto_phi = loai.upper() in ("MUA", "BAN")
    phigd, phimg, thue = doc_chiphi() if auto_phi else (0.0, 0.0, 0.0)
    loai_hien = "BÁN" if loai.upper() == "BAN" else loai
    return render_template("form.html", loai=loai, loai_hien=loai_hien, rows=rows,
                           ma=ma, madot=madot, tu=tu, den=den, auto_phi=auto_phi,
                           phigd=phigd, phimg=phimg, thue=thue,
                           hom_nay=dt.date.today().strftime("%Y/%m/%d"),
                           menu_items=MENU_ITEMS)
