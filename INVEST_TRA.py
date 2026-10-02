# File: INVEST_TRA.py
# -*- coding: utf-8 -*-
"""Menu 04.Tra Tìm Dữ Liệu Giao Dịch — tra tìm toàn bộ giao dịch."""
import datetime as dt
from flask import Blueprint, request, redirect, url_for, session, render_template

from INVEST_COMMON import doc_giao_dich, MENU_ITEMS
import pandas as pd

bp = Blueprint("tra", __name__)


@bp.route("/tra")
def tra():
    if "user" not in session:
        return redirect(url_for("login"))
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
        if ma:
            df = df[df["MACP"].astype(str).str.upper() == ma]
        if madot:
            df = df[df["MADOT"].astype(str).str.upper() == madot]
        d_tu = _parse_date(tu)
        d_den = _parse_date(den)
        if d_tu:
            df = df[df["_NGAY"] >= d_tu]
        if d_den:
            df = df[df["_NGAY"] <= d_den]
    # Sắp xếp: ngày mới nhất nằm trên, cùng ngày xếp theo Mã CP (sắp trước khi cắt cột)
    df = df.sort_values(["_NGAY", "MACP"], ascending=[False, True])
    hien = df[["LOAIGD", "MACP", "NGAYGD", "KHOILUONG", "GIA", "PHIGD", "THANHTIEN"]].copy()
    hien = hien.rename(columns={"LOAIGD": "LOAI", "MACP": "MA", "NGAYGD": "NGAY",
                                "KHOILUONG": "KHOLUONG", "PHIGD": "PHI"})
    return render_template("tra.html", rows=hien.values.tolist(), cols=list(hien.columns),
                           ma=ma, madot=madot, tu=tu, den=den, menu=MENU_ITEMS)
