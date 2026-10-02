# File: INVEST_COTUC.py
# -*- coding: utf-8 -*-
"""Menu 03.Ghi Nhận CỔ TỨC — màn hình ghi nhận giao dịch CỔ TỨC."""
from flask import Blueprint

from INVEST_COMMON import form_giao_dich

bp = Blueprint("cotuc", __name__)


@bp.route("/form/CỔ TỨC")
def form_cotuc():
    return form_giao_dich("CỔ TỨC")
