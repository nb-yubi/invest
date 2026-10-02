# File: _render_test.py
# Kiểm tra layout chitiet.html bằng Jinja với dữ liệu mẫu, sau đó đo độ rộng cột bằng trình duyệt headless
import sys
sys.stdout.reconfigure(encoding="utf-8")
from jinja2 import Environment, FileSystemLoader

rows = [["TCB", "1.000.100", "0", "0", "0", "100", "1.000.000", "3.315.000",
         "-231.5%", "-231.5%", "100", "10.000,00", "1.000.100", "0", "0,00", "0", "0", "0"]]
menu = [("06.Tra Tìm Chi Tiết", "/chitiet")]

env = Environment(loader=FileSystemLoader("templates"), autoescape=True)
html = env.get_template("chitiet.html").render(rows=rows, ma="", sl="ALL", menu=menu)
open("_render_test.html", "w", encoding="utf-8").write(html)
print("OK — đã render:", len(html), "ký tự")
