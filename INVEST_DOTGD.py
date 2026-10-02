# File: INVEST_DOTGD.py
# -*- coding: utf-8 -*-
"""Menu 07.Thiết Lập Mã Đợt — quản lý bảng DOTGD (MADOT, MACP, NGAYBD, NGAYKT)."""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session

from db_connection import supabase
from INVEST_COMMON import BANG_DOTGD, MENU_ITEMS

bp = Blueprint("dotgd", __name__)

COT = ["IDDOT", "MADOT", "MACP", "NGAYBD", "NGAYKT"]


def doc_dotgd():
    """Đọc toàn bộ bảng DOTGD, sắp xếp theo Mã Đợt rồi Mã CP."""
    try:
        res = supabase.table(BANG_DOTGD).select(",".join(COT)).execute()
        df = res.data or []
    except Exception as e:
        print("[DOTGD-ERROR]", repr(e))
        df = []
    df.sort(key=lambda r: (str(r.get("MADOT") or ""), str(r.get("MACP") or "")))
    return df


def _ngay(v):
    """YYYY/MM/DD hoặc YYYY-MM-DD -> YYYY-MM-DD; rỗng -> None (đợt còn mở)."""
    v = (v or "").strip().replace("-", "/")
    if not v:
        return None
    import datetime as dt
    try:
        return dt.datetime.strptime(v, "%Y/%m/%d").strftime("%Y-%m-%d")
    except ValueError:
        return ""


@bp.route("/dotgd")
def dotgd():
    if "user" not in session:
        return redirect(url_for("login"))
    ma = request.args.get("ma", "").strip().upper()
    rows = doc_dotgd()
    if ma:
        rows = [r for r in rows if str(r.get("MACP") or "").upper() == ma]
    return render_template("dotgd.html", rows=rows, ma=ma,
                           hom_nay=__import__("datetime").date.today().strftime("%Y/%m/%d"),
                           menu_items=MENU_ITEMS)


@bp.route("/api/dotgd/luu", methods=["POST"])
def luu():
    if "user" not in session:
        return jsonify({"ok": False, "error": "Chưa đăng nhập!"}), 401
    data = request.get_json(silent=True) or {}
    madot = str(data.get("madot", "")).strip().upper()
    macp = str(data.get("ma", "")).strip().upper()
    ngaybd = _ngay(data.get("ngaybd"))
    ngaykt = _ngay(data.get("ngaykt"))
    if not madot:
        return jsonify({"ok": False, "error": "Vui lòng nhập Mã Đợt!"})
    if not macp:
        return jsonify({"ok": False, "error": "Vui lòng nhập Mã CP!"})
    if ngaybd == "" or ngaykt == "":
        return jsonify({"ok": False, "error": "Ngày phải theo định dạng YYYY/MM/DD!"})
    row = {"MADOT": madot, "MACP": macp, "NGAYBD": ngaybd, "NGAYKT": ngaykt}
    try:
        iddot = str(data.get("id") or "").strip()
        if iddot:
            supabase.table(BANG_DOTGD).update(row).eq("IDDOT", iddot).execute()
        else:
            supabase.table(BANG_DOTGD).insert(row).execute()
        return jsonify({"ok": True})
    except Exception as e:
        print("[DOTGD-LUU-ERROR]", repr(e))
        return jsonify({"ok": False, "error": "Không lưu được đợt, xin thử lại!"})


@bp.route("/api/dotgd/xoa", methods=["POST"])
def xoa():
    if "user" not in session:
        return jsonify({"ok": False, "error": "Chưa đăng nhập!"}), 401
    data = request.get_json(silent=True) or {}
    iddot = str(data.get("id") or "").strip()
    if not iddot:
        return jsonify({"ok": False, "error": "Thiếu mã dòng cần xóa!"})
    try:
        supabase.table(BANG_DOTGD).delete().eq("IDDOT", iddot).execute()
        return jsonify({"ok": True})
    except Exception as e:
        print("[DOTGD-XOA-ERROR]", repr(e))
        return jsonify({"ok": False, "error": "Không xóa được đợt, xin thử lại!"})
