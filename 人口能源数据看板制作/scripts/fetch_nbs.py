"""Download public NBS annual responses; keep raw response bytes and provenance."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import time
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://data.stats.gov.cn/dg/website/"
CATALOGS = {
    "population_total": "6331ad868e8b4f55b8e9b6e765609ce1",
    "population_rates": "ffed4267bba24830beea5991d4c9bcfc",
    "population_age": "c7743eefda9d44b5ad2ab0b4f29ba969",
    "energy_total": "ea81a442991544f984906c2c264d13ca",
    "energy_elasticity": "3e856fff55934a2fae631912d5d1f64e",
    "energy_living_per_capita": "5b8c88b272d747af9c0403a300f1c1e4",
}
MANIFEST = []

def fetch(name, endpoint, params=None, payload=None):
    raw_dir = ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    url = BASE + endpoint
    if params:
        url += "?" + urllib.parse.urlencode(params)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": "PopulationEnergyResearch/1.0",
        "Content-Type": "application/json;charset=UTF-8",
        "Referer": BASE + "page.html",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                content = response.read()
            result = json.loads(content)
            if not result.get("success"):
                raise RuntimeError(str(result)[:500])
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 + attempt)
    target = raw_dir / (name + ".json")
    target.write_bytes(content)
    MANIFEST.append({
        "file": target.relative_to(ROOT).as_posix(),
        "url": url, "method": "GET" if body is None else "POST",
        "request_body": payload,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    })
    (raw_dir / "manifest.json").write_text(
        json.dumps(MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8")
    time.sleep(0.4)
    return result

def main():
    fetch("catalog_population", "publicrelease/web/external/new/queryIndexTreeAsync",
          {"code": "3", "pid": "040faf60f9b64535957e242e62a18a85"})
    fetch("catalog_energy", "publicrelease/web/external/new/queryIndexTreeAsync",
          {"code": "3", "pid": "2dc0c279011e4d2e9f24f7d42f1d4af4"})
    for name, cid in CATALOGS.items():
        metadata = fetch(name + "_indicators",
                         "publicrelease/web/external/new/queryIndicatorsByCid", {"cid": cid})
        indicators = metadata["data"]["list"]
        print(name, [(x["_id"], x["i_showname"]) for x in indicators], flush=True)
        payload = {
            "cid": cid, "rootId": "884c062607104a91967b22742537f44f",
            "indicatorIds": [x["_id"] for x in indicators],
            "daCatalogId": "", "das": [{"text": "全国", "value": "000000000000"}],
            "showType": 1, "dts": ["2008YY-2025YY"],
        }
        data = fetch(name + "_data", "publicrelease/web/external/stream/esData", payload=payload)
        print(name, "response sample:", str(data)[:1000], flush=True)

if __name__ == "__main__":
    main()
