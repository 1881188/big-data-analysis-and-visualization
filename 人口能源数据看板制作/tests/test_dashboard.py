from pathlib import Path
import csv
import hashlib
import io
import json
import math
import sys
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dashboard_data import DashboardData, ENERGIES
from app import handler_type

class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/"data").rglob("*") if p.is_file()}
        cls.data=DashboardData()
    @classmethod
    def tearDownClass(cls):
        cls.data.close()
        for p,digest in cls.before.items():
            assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,str(p)+" source changed"

    def test_default_and_independent_csv_values(self):
        payload=self.data.payload()
        self.assertEqual(payload["state"],{"year":2025,"base":2011,"energy":"coal","mode":"amount"})
        with (ROOT/"data/processed/population_annual.csv").open(encoding="utf-8-sig",newline="") as f:
            expected={int(r["year"]):r for r in csv.DictReader(f)}
        self.assertEqual(len(payload["population"]),15)
        for row in payload["population"]:
            self.assertEqual(row["population_total"],int(expected[int(row["year"])]["population_total"]))
        self.assertEqual(payload["current_population"]["population_total"],140489)
        self.assertIsNone(payload["current_energy"]["living_energy_per_capita"])
        self.assertEqual(len(payload["selected_energy_series"]),15)

    def test_all_960_filter_combinations(self):
        count=0
        for year in range(2011,2026):
            for base in range(2011,year+1):
                for energy in ENERGIES:
                    for mode in ("amount","share"):
                        result=self.data.payload(year,base,energy,mode)
                        w=result["waterfall"]
                        self.assertTrue(math.isclose(w["start"]+sum(r["delta"] for r in w["changes"]),w["end"],abs_tol=1e-6))
                        self.assertEqual([int(r["year"]) for r in result["population"]],list(range(2011,2026)))
                        self.assertTrue(all(r["energy_key"]==energy for r in result["selected_energy_series"]))
                        count+=1
        self.assertEqual(count,960)

    def test_scope_isolation_and_rounding(self):
        coal=self.data.payload(2019,2011,"coal")
        gas=self.data.payload(2019,2011,"gas")
        self.assertEqual(coal["population"],gas["population"])
        self.assertEqual(coal["current_population"],gas["current_population"])
        self.assertNotEqual(coal["selected_energy_series"],gas["selected_energy_series"])
        self.assertAlmostEqual(coal["waterfall"]["changes"][-1]["delta"],485.584)
        same=self.data.payload(2019,2019)
        self.assertTrue(all(r["delta"]==0 for r in same["waterfall"]["changes"]))
        self.assertEqual(self.data.payload(2018)["current_population"]["age_sum_difference"],-1)

    def test_invalid_filters(self):
        cases=[{"year":2008},{"year":2026},{"base":2026},{"year":2012,"base":2013},
               {"energy":"coal' OR 1=1"},{"mode":"unknown"},{"year":True},{"year":2010.5}]
        for values in cases:
            with self.assertRaises(ValueError):self.data.payload(**values)

    def test_latest_years_preserve_missing_values(self):
        for year,population,total in [(2024,140828,596175),(2025,140489,617000)]:
            payload=self.data.payload(year,2011)
            self.assertEqual(payload["current_population"]["population_total"],population)
            self.assertEqual(payload["current_energy"]["energy_total"],total)
            self.assertIsNone(payload["current_energy"]["living_energy_per_capita"])
            self.assertEqual(payload["availability"]["living_energy_per_capita"],
                             {"missing_years":[2024,2025],"last_available_year":2023})
            self.assertEqual([r["living_energy_per_capita"] for r in payload["energy"]][-3:],[501,None,None])
            csv_rows=list(csv.DictReader(io.StringIO(self.data.export_csv(payload).decode("utf-8-sig"))))
            living=next(r for r in csv_rows if r["字段"]=="living_energy_per_capita")
            self.assertEqual(living["数值"],"")
            self.assertTrue(all(r["in_display_window"]==1 for r in payload["energy"]))

    def test_export_values_and_metadata(self):
        p=self.data.payload(2019,2011,"gas","share")
        current=self.data.export_csv(p)
        self.assertTrue(current.startswith(b"\xef\xbb\xbf"))
        rows=list(csv.DictReader(io.StringIO(current.decode("utf-8-sig"))))
        self.assertEqual({r["年份"] for r in rows},{"2019"})
        self.assertEqual({r["比较基期"] for r in rows},{"2011"})
        official=next(r for r in rows if r["字段"]=="energy_yoy_official_pct")
        self.assertEqual(official["数值"],"")
        share=next(r for r in rows if r["字段"]=="share_pct")
        self.assertEqual(share["计算方法"],"官方占比")
        all_rows=self.data.export_rows(p,"all")
        self.assertEqual({int(r["年份"]) for r in all_rows},set(range(2011,2026)))

    def test_http_routes_and_local_export(self):
        server=ThreadingHTTPServer(("127.0.0.1",0),handler_type(self.data))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url="http://127.0.0.1:"+str(server.server_port)
        try:
            with urllib.request.urlopen(url+"/api/data?year=2018&base=2011&energy=oil") as response:
                self.assertEqual(json.load(response)["state"]["year"],2018)
            for target in ("/api/data?year=2026","/api/data?year=2010&base=2020","/api/data?year=2010&year=2011"):
                with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(url+target)
                self.assertEqual(error.exception.code,400)
            for target in ("/%2e%2e/data/processed/population_annual.csv","/vendor/"):
                with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(url+target)
                self.assertEqual(error.exception.code,404)
            request=urllib.request.Request(url+"/api/save",data=json.dumps({"kind":"csv","year":2018,"base":2011,"energy":"oil","mode":"share"}).encode(),headers={"Content-Type":"application/json"},method="POST")
            with urllib.request.urlopen(request) as response:saved=json.load(response)["saved"]
            path=(ROOT/saved).resolve()
            self.assertTrue(path.is_relative_to((ROOT/"outputs/dashboard/exports").resolve()))
            self.assertTrue(path.is_file())
            bad=urllib.request.Request(url+"/api/save",data=b'{"kind":"png","image":"invalid"}',headers={"Content-Type":"application/json"},method="POST")
            with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(bad)
            self.assertEqual(error.exception.code,400)
        finally:server.shutdown();server.server_close();thread.join()

if __name__=="__main__":unittest.main(verbosity=2)
