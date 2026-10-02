# _test_th.py — kiểm tra tooltip & thứ tự cột
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
src = open("_test_tong.py", encoding="utf-8").read()
src = src.replace('print("TH:", re.findall(r"<th>(.*?)</th>", html))', "")
src = src.replace('print("TD:", re.findall(r\'<td class="([^"]*)">([^<]*)</td>\', html))', "")
exec(src)
print("THFULL:", re.findall(r"<th[^>]*>(.*?)</th>", html))
print("TIPS  :", re.findall(r'<th title="([^"]*)"', html))
