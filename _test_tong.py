# File: _test_tong.py — test render trang /tong với dữ liệu giả (không ảnh hưởng DB)
import re
import pandas as pd
from flask import Flask, session

import INVEST_TONG as t
import INVEST_COMMON as c

# Dữ liệu giả
c.doc_giao_dich = lambda: pd.DataFrame({
    "IDGD": [1], "LOAIGD": ["MUA"], "MACP": ["TCB"],
    "NGAYGD": ["2026-09-29"], "KHOILUONG": [1000], "GIA": [24000.0],
    "PHIGD": [15.0], "THANHTIEN": [240015.0]})
t.doc_giao_dich = c.doc_giao_dich
t.lay_gia_vnstock = lambda lst, hom_nay=None: {
    "TCB": {"hom_qua": ("2026-09-29", 24.5), "hom_nay": ("2026-09-30", 25.2)}}
t.doc_phi_mua = lambda: (0.0015, 0.0005)  # PHIGD + PHIMG

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "t"

with app.test_request_context("/tong"):
    session["user"] = "x"
    html = t.tong()
print("TH:", re.findall(r"<th>(.*?)</th>", html))
print("TD:", re.findall(r'<td class="([^"]*)">([^<]*)</td>', html))
