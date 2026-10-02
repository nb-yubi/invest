# File: INVEST_CHITIET.py
# -*- coding: utf-8 -*-
"""Menu 06.Tra Tìm Chi Tiết — bảng tổng hợp chi tiết theo từng mã CP:
   Tổng tiền MUA, Tổng tiền BÁN (2 cách), Lãi/Lỗ, Số tiền còn lại,
   Tỷ suất sinh lời, các chỉ tiêu giao dịch MUA / BÁN / CỔ TỨC."""
import pandas as pd
from flask import Blueprint, request, redirect, url_for, session, render_template, make_response

from INVEST_COMMON import doc_giao_dich, MENU_ITEMS
from INVEST_TONG import lay_gia_vnstock

bp = Blueprint("chitiet", __name__)


def _n(v, dec=0):
    """Định dạng số: dấu phân cách nghìn bằng dấu chấm. dec = số chữ số lẻ."""
    return f"{v:,.{dec}f}".replace(",", ".")


def _ns(v, dec=0):
    """Định dạng số có dấu: dương có dấu '+', âm có dấu '-', 0 thì không dấu.
    Dùng dấu để template tô màu: '+' = lãi (xanh lá), '-' = lỗ (đỏ).
    dec = số chữ số thập phân (mặc định 0)."""
    s = f"{abs(v):,.{dec}f}".replace(",", ".")
    return ("+" if v > 0 else "-" if v < 0 else "") + s


@bp.route("/chitiet")
def chitiet():
    if "user" not in session:
        return redirect(url_for("login"))
    ma = request.args.get("ma", "").strip().upper()
    # Điều kiện số cổ phiếu còn lại: ALL / GT0 / EQ0
    sl = request.args.get("sl", "ALL").strip().upper() or "ALL"

    df = doc_giao_dich()
    if df.empty:
        return render_template("chitiet.html", rows=[], ma=ma, sl=sl, menu=MENU_ITEMS)

    loai = df["LOAIGD"].astype(str).str.upper()
    k_mua = df["KHOILUONG"] * (loai == "MUA")
    k_ban = df["KHOILUONG"] * (loai == "BÁN")
    k_ct = df["KHOILUONG"] * (loai == "CỔ TỨC")

    g = pd.DataFrame({
        "MACP": df["MACP"].astype(str).str.upper(),
        "KL_MUA": k_mua, "KL_BAN": k_ban, "KL_CT": k_ct,
        "GIA_MUA": df["GIA"] * k_mua,          # KL*GIA (chỉ dòng MUA)
        "GIA_BAN": df["GIA"] * k_ban,
        "PHI_MUA": df["PHIGD"] * (loai == "MUA"),
        "PHI_BAN": df["PHIGD"] * (loai == "BÁN"),
        "TIEN_CT": df["THANHTIEN"] * (loai == "CỔ TỨC"),
    })

    t = g.groupby("MACP").agg(
        KL_MUA=("KL_MUA", "sum"), KL_BAN=("KL_BAN", "sum"), KL_CT=("KL_CT", "sum"),
        T_GIA_MUA=("GIA_MUA", "sum"), T_GIA_BAN=("GIA_BAN", "sum"),
        PHI_MUA=("PHI_MUA", "sum"), PHI_BAN=("PHI_BAN", "sum"),
        TIEN_CT=("TIEN_CT", "sum"),
    ).reset_index()

    t["CON_LAI"] = t["KL_MUA"] - t["KL_BAN"]
    t["GIA_MUA_TB"] = 0.0
    t["GIA_BAN_TB"] = 0.0
    m1 = t["KL_MUA"] > 0
    t.loc[m1, "GIA_MUA_TB"] = t.loc[m1, "T_GIA_MUA"] / t.loc[m1, "KL_MUA"]
    m2 = t["KL_BAN"] > 0
    t.loc[m2, "GIA_BAN_TB"] = t.loc[m2, "T_GIA_BAN"] / t.loc[m2, "KL_BAN"]

    # Lọc theo mã CP / số CP còn lại
    if ma:
        t = t[t["MACP"] == ma]
    if sl == "GT0":
        t = t[t["CON_LAI"] > 0]
    elif sl == "EQ0":
        t = t[t["CON_LAI"] == 0]
    t = t.sort_values("MACP")

    # Giá online (giá hôm nay) từ vnstock — dùng cho Cân Hòa Vốn / Thực Tế
    gia = lay_gia_vnstock(list(t["MACP"]))

    rows = []
    for _, r in t.iterrows():
        m = r["MACP"]
        kl_mua, kl_ban, kl_ct = r["KL_MUA"], r["KL_BAN"], r["KL_CT"]
        gia_mua_tb, gia_ban_tb = r["GIA_MUA_TB"], r["GIA_BAN_TB"]
        phi_mua, phi_ban, tien_ct = r["PHI_MUA"], r["PHI_BAN"], r["TIEN_CT"]
        con_lai = r["CON_LAI"]

        # Tổng Tiền MUA = (Tổng SL MUA * Giá Mua T.Bình + Thuế/Phí) — số dương
        tien_mua = kl_mua * gia_mua_tb + phi_mua

        # Tổng tiền BÁN theo giá MUA = (Tổng SL BÁN * Giá Mua T.Bình)
        #                             - (Thuế/Phí MUA * Tổng SL BÁN / Tổng SL MUA) — số dương
        ty_le_ban = (kl_ban / kl_mua) if kl_mua else 0.0
        tt_ban_gm = kl_ban * gia_mua_tb - phi_mua * ty_le_ban

        # Tổng tiền BÁN theo giá BÁN + C.TỨC = (SL BÁN * Giá Bán T.Bình) - Thuế/Phí + T.Tiền C.Tức
        tt_ban_gb = kl_ban * gia_ban_tb - phi_ban + tien_ct

        # Lãi/Lỗ = (Tổng Tiền BÁN theo giá BÁN + C.TỨC) - Tổng Tiền BÁN theo giá MUA
        lai_lo = tt_ban_gb - tt_ban_gm

        # Giá online (giá hôm nay) — chưa có thì lấy giá mua trung bình
        info = gia.get(m)
        gia_online = info["hom_nay"][1] * 1000 if info and info["hom_nay"][1] is not None else None
        so_tien_con_lai = con_lai * gia_mua_tb
        can_hoa_von = con_lai * gia_online if gia_online else None

        # Tỷ suất sinh lời (dùng _ns để có dấu + / - cho tô màu)
        ts_da_ban = (lai_lo / tt_ban_gm * 100) if (tt_ban_gm and tt_ban_gm != 0) else None
        
        # Giá gốc so sánh = Giá Mua T.Bình + Tổng Thu/Phí MUA (tính trên 1 CP)
        phi_mua_1cp = (phi_mua / kl_mua) if kl_mua else 0.0
        gia_goc = gia_mua_tb + phi_mua_1cp

        # Cột Giá Online: đỏ nếu thấp hơn giá gốc, xanh lá nếu cao hơn, đen nếu bằng
        if gia_online:
            go_cls = "go-thap" if gia_online < gia_goc else ("go-cao" if gia_online > gia_goc else "go-bang")
            go_str = _n(gia_online)
        else:
            go_cls = ""
            go_str = ""

        # Tính toán % Lãi/Lỗ Tạm Tính (Giá Online)
        # Công thức: (Giá Online - (Giá Mua T.Bình + Thuế/Phí MUA/CP)) / (Giá Mua T.Bình + Thuế/Phí MUA/CP) * 100
        if gia_online and gia_goc > 0:
            ts_tam_tinh = ((gia_online - gia_goc) / gia_goc) * 100
        else:
            ts_tam_tinh = None

        rows.append(([
            m,
            _n(tien_mua),                                   # Tổng Tiền MUA
            _n(tt_ban_gm),                                   # Tổng Tiền BÁN - Theo Giá MUA
            _n(tt_ban_gb),                                   # Tổng Tiền BÁN - Theo Giá BÁN + C.TỨC
            _ns(lai_lo),                                      # Lãi/Lỗ (luôn có dấu + / -)
            _n(con_lai),                                     # Số CP Còn Lại
            _n(so_tien_con_lai),                             # Cân Hòa Vốn
            go_str,                                          # Giá Online
            _n(can_hoa_von) if can_hoa_von is not None else "",   # Thực Tế
            f"{_ns(ts_da_ban, 1)}%" if ts_da_ban is not None else "",      # % Lãi/Lỗ Đã Bán
            f"{_ns(ts_tam_tinh, 1)}%" if ts_tam_tinh is not None else "",  # % Lãi/Lỗ Tạm Tính
            _n(kl_mua),                                      # Tổng SL MUA
            _n(gia_mua_tb),                                  # Giá MUA T.Bình (VND, lấy từ DB)
            _n(kl_mua * gia_mua_tb + phi_mua),              # Tổng Thu/Phí (MUA)
            _n(kl_ban),                                      # Tổng SL BÁN
            _n(gia_ban_tb),                                  # Giá BÁN T.Bình (VND, lấy từ DB)
            _n(kl_ban * gia_ban_tb - phi_ban),               # Tổng Thu/Phí (BÁN)
            _n(kl_ct),                                       # SL Cổ Tức
            _n(tien_ct),                                     # T.Tiền C.Tức
        ], go_cls))

    resp = make_response(render_template("chitiet.html", rows=rows, ma=ma, sl=sl, menu=MENU_ITEMS))
    # Chặn cache trình duyệt để luôn nhận bản template mới nhất
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp
