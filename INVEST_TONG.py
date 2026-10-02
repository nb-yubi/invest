# File: INVEST_TONG.py
# -*- coding: utf-8 -*-
"""Menu 05.Tra Tìm Theo Tổng — tổng hợp theo mã CP:
   Số CP còn lại, Giá mua TB, Phí MUA (từ bảng chi phí), Giá Online (vnstock),
   Lãi/Lỗ (Giá Online), % Hiệu Quả (Giá Online)."""
import datetime as dt
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from flask import Blueprint, request, redirect, url_for, session, render_template

from INVEST_COMMON import doc_giao_dich, MENU_ITEMS
from db_connection import supabase


def doc_phi_mua():
    """Đọc PHIGD, PHIMG từ bảng CHIPHI (1 dòng đầu tiên).
    Trả về (phigd, phimg); bảng rỗng/lỗi -> (0, 0)."""
    bang = "CHIPHI"
    try:
        res = supabase.table(bang).select("*").limit(1).execute()
        if res.data:
            row = res.data[0]
            phigd = float(row.get("PHIGD") or 0)
            phimg = float(row.get("PHIMG") or 0)
            return phigd, phimg
    except Exception as e:
        print(f"[CHIPHI-ERROR] {bang}", repr(e))
    return 0.0, 0.0

bp = Blueprint("tong", __name__)

# Cache giá trong ngày: key = (mã, ngày) -> dict kết quả, để không gọi
# vnstock lại nhiều lần cho cùng một mã trong cùng một phiên làm việc.
_CACHE_GIA = {}


def _lay_gia_1_ma(ma, hom_nay, bat_dau, ket_thuc):
    """Lấy giá 1 mã từ vnstock. Trả về dict hoặc None nếu lỗi."""
    try:
        from vnstock import Quote
        df = Quote(symbol=ma, source="VCI").history(start=bat_dau, end=ket_thuc)
        if df is None or df.empty:
            return None
        df = df.sort_values("time")
        # chỉ lấy các phiên <= hôm nay
        df = df[df["time"].dt.date <= hom_nay] if hasattr(df["time"], "dt") else df
        if df.empty:
            return None
        cuoi = df.iloc[-1]
        truoc = df.iloc[-2] if len(df) >= 2 else None
        ngay_c = pd.to_datetime(cuoi["time"]).date()
        return {
            # nếu phiên cuối chính là hôm nay -> đó là "Giá Hôm Nay",
            # phiên liền trước là "Giá Hôm Qua" (nếu hôm nay nghỉ thì
            # phiên cuối chính là giá trước ngày nghỉ, dùng làm Hôm Nay,
            # còn Hôm Qua là phiên trước nữa)
            "hom_nay": (ngay_c, float(cuoi["close"])),
            "hom_qua": ((pd.to_datetime(truoc["time"]).date(), float(truoc["close"]))
                        if truoc is not None else ("", None)),
        }
    except Exception as e:
        print("[VNSTOCK-ERROR]", ma, repr(e))
        return None


def lay_gia_vnstock(ma_list, hom_nay=None):
    """Lấy giá đóng cửa từ vnstock cho danh sách mã.
    Trả về (dict ma -> {'hom_qua': (ngay, gia), 'hom_nay': (ngay, gia)}).
    Kết quả được cache trong ngày và gọi song song để trang không bị chậm."""
    if hom_nay is None:
        hom_nay = dt.date.today()
    # Lấy đủ 15 ngày lịch để bao qua cả tuần nghỉ/lễ
    bat_dau = (hom_nay - dt.timedelta(days=15)).strftime("%Y-%m-%d")
    ket_thuc = hom_nay.strftime("%Y-%m-%d")

    # 1) Lấy từ cache những mã đã có, 2) gọi song song phần còn lại
    ket_qua, can_lay = {}, []
    for ma in ma_list:
        if (ma, hom_nay) in _CACHE_GIA:
            ket_qua[ma] = _CACHE_GIA[(ma, hom_nay)]
        else:
            can_lay.append(ma)

    if can_lay:
        if len(can_lay) == 1:
            kq = [_lay_gia_1_ma(can_lay[0], hom_nay, bat_dau, ket_thuc)]
        else:
            with ThreadPoolExecutor(max_workers=min(8, len(can_lay))) as pool:
                kq = list(pool.map(lambda m: _lay_gia_1_ma(m, hom_nay, bat_dau, ket_thuc),
                                   can_lay))
        for ma, info in zip(can_lay, kq):
            if info:
                _CACHE_GIA[(ma, hom_nay)] = info
                ket_qua[ma] = info
    return ket_qua


def _fmt_gia(v):
    """Giá vnstock đơn vị nghìn đồng -> hiển thị VND (×1000, số nguyên, ngăn cách nghìn bằng '.').
    VD: 33.25 -> 33.250"""
    if v is None:
        return ""
    return f"{v * 1000:,.0f}".replace(",", ".")


@bp.route("/tong")
def tong():
    if "user" not in session:
        return redirect(url_for("login"))
    ma = request.args.get("ma", "").strip().upper()
    sl = request.args.get("sl", "ALL").strip().upper() or "ALL"
    df = doc_giao_dich()
    if df.empty:
        return render_template("tong.html", rows=[], cols=[], ma=ma, sl=sl, menu=MENU_ITEMS)

    loai = df["LOAIGD"].astype(str).str.upper()
    mua = df["KHOILUONG"] * (loai == "MUA")
    ban = df["KHOILUONG"] * (loai == "BÁN")

    g = pd.DataFrame({
        "MACP": df["MACP"].astype(str).str.upper(),
        "KL_MUA": mua, "KL_BAN": ban,
        "GIAMUA": df["GIA"], "LOAI": loai,
    })
    g["GIA_MUA"] = g["GIAMUA"] * g["KL_MUA"]

    tong_theo_ma = g.groupby("MACP").agg(
        KL_MUA=("KL_MUA", "sum"),
        KL_BAN=("KL_BAN", "sum"),
        T_GIA_MUA=("GIA_MUA", "sum"),
    ).reset_index()

    tong_theo_ma["CON_LAI"] = tong_theo_ma["KL_MUA"] - tong_theo_ma["KL_BAN"]
    tong_theo_ma["GIA_TB"] = 0.0
    mask = tong_theo_ma["KL_MUA"] > 0
    tong_theo_ma.loc[mask, "GIA_TB"] = (
        tong_theo_ma.loc[mask, "T_GIA_MUA"] / tong_theo_ma.loc[mask, "KL_MUA"])

    # Lọc theo mã CP / số CP còn lại
    if ma:
        tong_theo_ma = tong_theo_ma[tong_theo_ma["MACP"] == ma]
    if sl == "GT0":
        tong_theo_ma = tong_theo_ma[tong_theo_ma["CON_LAI"] > 0]
    elif sl == "EQ0":
        tong_theo_ma = tong_theo_ma[tong_theo_ma["CON_LAI"] == 0]

    tong_theo_ma = tong_theo_ma.sort_values("MACP")

    # Giá từ vnstock
    gia = lay_gia_vnstock(list(tong_theo_ma["MACP"]))

    # Phí MUA = Giá MUA T.Bình × (PHIGD + PHIMG), lấy từ bảng chi phí
    phigd, phimg = doc_phi_mua()
    ty_le_phi = phigd + phimg

    rows = []
    for _, r in tong_theo_ma.iterrows():
        m = r["MACP"]
        info = gia.get(m)
        if info:
            nq, gq = info["hom_qua"]
            nn, gn = info["hom_nay"]
        else:
            nq, gq, nn, gn = "", None, "", None
        chenh = ((gn - gq) / gq * 100) if (gq not in (None, 0) and gn is not None) else None
        # Phí MUA trên mỗi CP
        phi_mua = r["GIA_TB"] * ty_le_phi
        # Giá vốn gồm phí = Giá MUA T.Bình + Phí MUA
        giaVon = r["GIA_TB"] + phi_mua
        # Giá online (VND) từ vnstock
        gia_online = gn * 1000 if gn is not None else None
        # Lãi/Lỗ (Giá Online) = (SL × Giá Online) − (SL × (Giá MUA T.Bình + Phí MUA))
        if gia_online is not None:
            lai_lo = r["CON_LAI"] * gia_online - r["CON_LAI"] * giaVon
        else:
            lai_lo = None
        # % Chênh Lệch Giá = ((Giá Online - Giá MUA T.Bình (Gồm Thuế)) / Giá MUA T.Bình (Gồm Thuế)) * 100
        chenh_pct = ((gia_online - giaVon) / giaVon * 100) if (giaVon and gia_online is not None) else None
        # % Hiệu Quả (Giá Online) = (Giá Online − Giá vốn gồm phí) / Giá vốn gồm phí
        hieu_qua = ((gia_online - giaVon) / giaVon * 100) if (giaVon and gia_online is not None) else None
        rows.append([
            m,
            f"{int(r['CON_LAI']):,}".replace(",", "."),
            f"{lai_lo:+,.0f}".replace(",", ".") if lai_lo is not None else "",
            f"{r['GIA_TB']:,.0f}".replace(",", "."),
            f"{phi_mua:,.0f}".replace(",", "."),
            _fmt_gia(gq),
            _fmt_gia(gn),
            f"{giaVon:,.0f}".replace(",", "."),
            f"{gia_online - giaVon:+,.0f}".replace(",", ".") if gia_online is not None else "",
            f"{chenh_pct:+.1f}%" if chenh_pct is not None else "",
            f"{hieu_qua:+.2f}%" if hieu_qua is not None else "",
        ])

    cols = [
        ("Mã CP", ""),
        ("Số CP C.Lại", ""),
        ("Tổng Lãi/Lỗ",
         "Tổng Lãi/Lỗ Cho Số CP C.Lại = (Số CP C.Lại * Giá Online) - "
         "(Số CP C.Lại * Giá MUA T.Bình (Gồm Thuế))"),
        ("Giá MUA T.Bình<br>(Chưa Thuế)", ""),
        ("Phí MUA", ""),
        ("Giá Tham Chiếu", "Lấy giá VNStock"),
        ("Giá Online", "Lấy giá VNStock"),
        ("Giá MUA T.Bình<br>(Gồm Thuế)", ""),
        ("Chênh Lệch<br>Giá",
         "Chênh Lệch Giữa Giá Online Trừ Giá MUA T.Bình (Gồm Thuế)"),
        ("% Chênh Lệch<br>Giá", 
          "Chênh Lệch Giá = ((Giá Online - Giá MUA T.Bình (Gồm Thuế))/Giá MUA T.Bình (Gồm Thuế)) *100% "),
        ("Hiệu Suất<br>Danh Mục", "Hiệu Suất Danh Mục= (Tổng Lãi/Lỗ / (Số CP C.Lại*Giá MUA T.Bình (Gồm Thuế)) *100% "),
    ]
    return render_template("tong.html", rows=rows, cols=cols, ma=ma, sl=sl, menu=MENU_ITEMS)
