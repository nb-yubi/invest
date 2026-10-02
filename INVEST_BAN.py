# File: INVEST_BAN.py
# -*- coding: utf-8 -*-
"""Menu 02.Ghi Nhận BÁN — màn hình ghi nhận giao dịch BÁN."""
from flask import Blueprint

from INVEST_COMMON import form_giao_dich

bp = Blueprint("ban", __name__)


@bp.route("/form/BAN")
def form_ban():
    return form_giao_dich("BAN")
