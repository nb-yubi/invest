# File: INVEST_MUA.py
# -*- coding: utf-8 -*-
"""Menu 01.Ghi Nhận MUA — màn hình ghi nhận giao dịch MUA."""
from flask import Blueprint

from INVEST_COMMON import form_giao_dich

bp = Blueprint("mua", __name__)


@bp.route("/form/MUA")
def form_mua():
    return form_giao_dich("MUA")
