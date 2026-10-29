"""Fetch pinned Apache ECharts distribution and its license for offline use."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
VERSION="5.6.0"
def main():
    directory=ROOT/"web/vendor"
    directory.mkdir(parents=True,exist_ok=True)
    files={"echarts.min.js":"dist/echarts.min.js","ECHARTS-LICENSE.txt":"LICENSE","ECHARTS-NOTICE.txt":"NOTICE"}
    manifest=[]
    for local,remote in files.items():
        url=f"https://raw.githubusercontent.com/apache/echarts/{VERSION}/{remote}"
        with urllib.request.urlopen(url,timeout=60) as response:
            body=response.read()
        if not body:raise RuntimeError("Empty asset: "+url)
        (directory/local).write_bytes(body)
        manifest.append({"file":local,"url":url,"sha256":hashlib.sha256(body).hexdigest(),"version":VERSION})
        print(local,len(body))
    (directory/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
if __name__=="__main__":main()
