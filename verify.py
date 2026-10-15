"""Одинаковые реальные проверки на Windows и Linux."""
import html,json,os,platform,subprocess,sys,tempfile
from pathlib import Path
from analyzer import analyze
root=Path(__file__).parent
folder=root/"sample";folder.mkdir(exist_ok=True)
(folder/"вложенная папка").mkdir(exist_ok=True)
for name,data in {"a.txt":b"hello","B.TXT":b"abc",
    "вложенная папка/code.py":b"print(1)\n","README":b"demo"}.items():
    (folder/name).write_bytes(data)
result=analyze(folder,folder/"report.txt")
assert result["count"]==4 and result["bytes"]==21, result
assert result["extensions"]=={".txt":2,".py":1,"(без расширения)":1}
again=analyze(folder,folder/"report.txt")
assert again["bytes"]==21 and again["count"]==4
checks=["Кириллица и вложенный каталог: OK","4 файла, 21 байт, 0.000021 МБ: OK",
        "Расширения .TXT/.txt объединены: OK","Сам отчёт исключён: OK"]
with tempfile.TemporaryDirectory() as tmp:
    assert analyze(tmp,Path(tmp)/"report.txt")["count"]==0
    checks.append("Пустой каталог: OK")
try: analyze(folder/"несуществующий")
except FileNotFoundError: checks.append("Несуществующий путь: OK")
else: raise AssertionError("Expected FileNotFoundError")
env=os.environ.copy();env["PYTHONIOENCODING"]="utf-8"
run=subprocess.run([sys.executable,"analyzer.py","sample","--output","sample/report.txt"],cwd=root,
    capture_output=True,text=True,encoding="utf-8",env=env,check=True)
report=(folder/"report.txt").read_text(encoding="utf-8")
evidence=root/"evidence";evidence.mkdir(exist_ok=True)
meta={"os":platform.system(),"platform":platform.platform(),"python":platform.python_version(),
      "checks":checks,"count":result["count"],"bytes":result["bytes"],"stdout":run.stdout,"report":report}
(evidence/"result.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
(evidence/"report.txt").write_text(report,encoding="utf-8")
text=f"ОС: {meta['platform']}\nPython: {meta['python']}\n\npython analyzer.py sample --output sample/report.txt\n{run.stdout}\n{report}\n"+"\n".join(checks)
(evidence/"run.txt").write_text(text,encoding="utf-8")
print(text)
if "--screenshot" in sys.argv:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        page=browser.new_page(viewport={"width":1280,"height":1100})
        page.set_content('<html lang="ru"><meta charset="utf-8"><body style="margin:32px;font:19px Arial;background:#f4f6f8;color:#17212b"><h2>Фактический вывод запуска — '+html.escape(platform.system())+'</h2><pre style="white-space:pre-wrap;font:18px monospace;background:white;padding:24px;border:1px solid #ccd2d8">'+html.escape(text)+'</pre></body></html>')
        page.screenshot(path=str(evidence/"screenshot.png"),full_page=True)
        browser.close()
