# -*- coding: utf-8 -*-
"""
Ứng dụng INVEST — chạy trên WEBSITE (Flask)
 Sau khi đăng nhập: màn hình chính, click icon 3 gạch (☰) hiện menu:
   01.Ghi Nhận MUA / 02.Ghi Nhận BÁN / 03.Ghi Nhận CỔ TỨC / 04.Tra Tìm Dữ Liệu Giao Dịch

Code tách theo từng loại menu (Blueprint):
   INVEST_MUA.py    -> /form/MUA
   INVEST_BAN.py    -> /form/BAN
   INVEST_COTUC.py  -> /form/CỔ TỨC
   INVEST_TRA.py    -> /tra
   INVEST_COMMON.py -> helpers dùng chung (đọc/ghi giao dịch, validate, render form)

Chạy:  python invest_web.py   ->  mở http://127.0.0.1:5000 trên trình duyệt
"""
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

from db_connection import supabase
from INVEST_COMMON import (BANG_GIAODICH, MENU_ITEMS, kiem_tra_dang_nhap,
                           doc_giao_dich, validate_row, doc_madot)
from INVEST_MUA import bp as mua_bp
from INVEST_BAN import bp as ban_bp
from INVEST_COTUC import bp as cotuc_bp
from INVEST_TRA import bp as tra_bp
from INVEST_DOTGD import bp as dotgd_bp
from INVEST_TONG import bp as tong_bp
from INVEST_CHITIET import bp as chitiet_bp

ERR_LOGIN = "Tài khoản hay mật mã không đúng, xin kiểm tra lại, cám ơn!"

app = Flask(__name__)
app.secret_key = "invest-secret-key-2026"
app.config["TEMPLATES_AUTO_RELOAD"] = True   # nạp lại template khi sửa file, không cần restart


@app.after_request
def khong_cache(response):
    """Chặn trình duyệt cache HTML — luôn tải phiên bản trang mới nhất."""
    if response.mimetype == "text/html":
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response

# Đăng ký các màn hình theo từng loại menu
app.register_blueprint(mua_bp)
app.register_blueprint(ban_bp)
app.register_blueprint(cotuc_bp)
app.register_blueprint(tra_bp)
app.register_blueprint(dotgd_bp)
app.register_blueprint(tong_bp)
app.register_blueprint(chitiet_bp)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        taikhoan = request.form.get("taikhoan", "")
        matma = request.form.get("matma", "")
        if kiem_tra_dang_nhap(taikhoan, matma):
            session["user"] = taikhoan.strip()
            return redirect(url_for("index"))
        flash(ERR_LOGIN, "error")
        return render_template("login.html", error=ERR_LOGIN)
    return render_template("login.html")


@app.route("/index")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", user=session["user"], menu=MENU_ITEMS)


# (route /form/<loai> đã tách sang INVEST_MUA.py / INVEST_BAN.py / INVEST_COTUC.py)


@app.route("/api/madot")
def api_madot():
    """Lấy MADOT đang mở (NGAYKT rỗng/NULL) của 1 mã CP từ bảng DOTGD."""
    if "user" not in session:
        return jsonify({"ok": False, "error": "Chưa đăng nhập!"}), 401
    ma = request.args.get("ma", "").strip().upper()
    return jsonify({"ok": True, "ma": ma, "madot": doc_madot(ma)})


@app.route("/api/luu", methods=["POST"])
def api_luu():
    """Thêm mới 1 giao dịch vào bảng GIAODICH."""
    if "user" not in session:
        return jsonify({"ok": False, "error": "Chưa đăng nhập!"}), 401
    data = request.get_json(silent=True) or {}
    row, err = validate_row(data)
    if err:
        return jsonify({"ok": False, "error": err})
    row["IDGD"] = str(uuid.uuid4())          # Khóa chính của bảng
    try:
        supabase.table(BANG_GIAODICH).insert(row).execute()
    except Exception as e:
        print("[LUU-ERROR]", repr(e))
        return jsonify({"ok": False, "error": f"Không lưu được giao dịch: {e}"})
    return jsonify({"ok": True, "message":
                    f"Đã ghi nhận {row['LOAIGD']}: {row['MACP']} — {row['THANHTIEN']:,.0f} VND"})


@app.route("/api/sua", methods=["POST"])
def api_sua():
    if "user" not in session:
        return jsonify({"ok": False, "error": "Chưa đăng nhập!"}), 401
    data = request.get_json(silent=True) or {}
    idgd = str(data.get("id", "")).strip()
    if not idgd:
        return jsonify({"ok": False, "error": "Dòng không hợp lệ!"})
    row, err = validate_row(data)
    if err:
        return jsonify({"ok": False, "error": err})
    try:
        res = supabase.table(BANG_GIAODICH).update(row).eq("IDGD", idgd).execute()
    except Exception as e:
        print("[SUA-ERROR]", repr(e))
        return jsonify({"ok": False, "error": f"Không cập nhật được giao dịch: {e}"})
    if not res.data:
        return jsonify({"ok": False, "error": "Không tìm thấy dòng cần sửa!"})
    return jsonify({"ok": True, "message":
                    f"Đã cập nhật: {row['MACP']} — {row['THANHTIEN']:,.0f} VND"})


@app.route("/api/xoa", methods=["POST"])
def api_xoa():
    if "user" not in session:
        return jsonify({"ok": False, "error": "Chưa đăng nhập!"}), 401
    data = request.get_json(silent=True) or {}
    idgd = str(data.get("id", "")).strip()
    if not idgd:
        return jsonify({"ok": False, "error": "Dòng không hợp lệ!"})
    try:
        res = supabase.table(BANG_GIAODICH).delete().eq("IDGD", idgd).execute()
    except Exception as e:
        print("[XOA-ERROR]", repr(e))
        return jsonify({"ok": False, "error": f"Không xóa được giao dịch: {e}"})
    if not res.data:
        return jsonify({"ok": False, "error": "Không tìm thấy dòng cần xóa!"})
    return jsonify({"ok": True, "message": f"Đã xóa giao dịch: {res.data[0].get('MACP', '')}"})


# (route /tra đã tách sang INVEST_TRA.py)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    print("Open browser: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
