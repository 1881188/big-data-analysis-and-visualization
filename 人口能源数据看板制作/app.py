"""Local dashboard server. Run: python app.py; no pip dependencies."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, unquote
import argparse
import base64
import binascii
from datetime import datetime
import json
import threading
import webbrowser
from dashboard_data import DashboardData, ROOT, FIRST, LAST

WEB=ROOT/"web"

def handler_type(data):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,directory=str(WEB),**kwargs)
        def log_message(self,format,*args):
            pass
        def send_bytes(self,content,kind,status=200,filename=None):
            self.send_response(status)
            self.send_header("Content-Type",kind)
            self.send_header("Content-Length",str(len(content)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            if filename:self.send_header("Content-Disposition",'attachment; filename="'+filename+'"')
            self.end_headers()
            self.wfile.write(content)
        def do_GET(self):
            parsed=urlsplit(self.path)
            if parsed.path.startswith("/api/"):
                try:
                    params=parse_qs(parsed.query)
                    if any(len(v)!=1 for v in params.values()):raise ValueError("参数不能重复")
                    val=lambda key,default:params.get(key,[default])[0]
                    payload=data.payload(int(val("year",str(LAST))),int(val("base",str(FIRST))),val("energy","coal"),val("mode","amount"))
                    if parsed.path=="/api/data":
                        self.send_bytes(json.dumps(payload,ensure_ascii=False,allow_nan=False).encode(),"application/json; charset=utf-8")
                    elif parsed.path=="/api/export.csv":
                        self.send_bytes(data.export_csv(payload,val("scope","current")),"text/csv; charset=utf-8",filename="population-energy-"+val("year",str(LAST))+".csv")
                    elif parsed.path=="/api/export.json":
                        self.send_bytes(json.dumps(payload,ensure_ascii=False,indent=2).encode(),"application/json; charset=utf-8",filename="dashboard-state.json")
                    else:self.send_bytes(b'{"error":"not found"}',"application/json",404)
                except (ValueError,OverflowError) as error:
                    self.send_bytes(json.dumps({"error":str(error)},ensure_ascii=False).encode(),"application/json; charset=utf-8",400)
                return
            target=(WEB/unquote(parsed.path).lstrip("/")).resolve()
            if not target.is_relative_to(WEB.resolve()) or (target.is_dir() and target!=WEB.resolve()):
                self.send_error(404);return
            super().do_GET()
        def do_POST(self):
            if urlsplit(self.path).path!="/api/save":
                self.send_error(404);return
            expected=f"http://127.0.0.1:{self.server.server_port}"
            if self.headers.get("Origin",expected)!=expected:
                self.send_error(403);return
            try:
                size=int(self.headers.get("Content-Length","0"))
                if not 0<size<=8*1024*1024:raise ValueError("导出请求大小超出范围")
                body=json.loads(self.rfile.read(size))
                payload=data.payload(body.get("year",LAST),body.get("base",FIRST),body.get("energy","coal"),body.get("mode","amount"))
                kind=body.get("kind")
                if kind=="csv":
                    content=data.export_csv(payload,body.get("scope","current"))
                    label="data-"+body.get("scope","current")
                elif kind=="json":
                    content=json.dumps(payload,ensure_ascii=False,indent=2).encode()
                    label="state"
                elif kind=="png":
                    chart=body.get("chart")
                    if chart not in [f"{i:02}" for i in range(1,11)]:raise ValueError("未知图表编号")
                    encoded=body.get("image","")
                    if not encoded.startswith("data:image/png;base64,"):raise ValueError("图像格式必须为PNG")
                    content=base64.b64decode(encoded.split(",",1)[1],validate=True)
                    if not content.startswith(b"\x89PNG\r\n\x1a\n"):raise ValueError("无效PNG图像")
                    label="chart-"+chart
                else:raise ValueError("未知导出类型")
                directory=ROOT/"outputs/dashboard/exports"
                directory.mkdir(parents=True,exist_ok=True)
                state=payload["state"]
                filename=f'{label}-{state["year"]}-base{state["base"]}-{state["energy"]}-{datetime.now():%Y%m%d-%H%M%S-%f}.{kind}'
                target=directory/filename
                with target.open("xb") as handle:handle.write(content)
                self.send_bytes(json.dumps({"saved":target.relative_to(ROOT).as_posix()},ensure_ascii=False).encode(),"application/json; charset=utf-8")
            except (ValueError,TypeError,binascii.Error) as error:
                self.send_bytes(json.dumps({"error":str(error)},ensure_ascii=False).encode(),"application/json; charset=utf-8",400)
    return Handler

def main():
    parser=argparse.ArgumentParser(description="全国人口与能源交互分析看板")
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--no-browser",action="store_true")
    args=parser.parse_args()
    if not 0<=args.port<=65535:parser.error("端口范围为0—65535")
    data=DashboardData()
    try:
        server=ThreadingHTTPServer(("127.0.0.1",args.port),handler_type(data))
    except OSError as error:
        data.close();parser.exit(1,f"端口无法启动：{error}。可使用 --port 8766\n")
    url=f"http://127.0.0.1:{server.server_port}/"
    print("全国人口与能源交互分析看板",flush=True)
    print("Local: "+url,flush=True)
    print("在浏览器打开上方地址；按 Ctrl+C 关闭服务。",flush=True)
    if not args.no_browser:
        threading.Timer(0.5,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();data.close()

if __name__=="__main__":
    main()
