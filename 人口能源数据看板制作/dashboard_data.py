"""Read-only CSV loading, SQLite queries and dashboard calculations (standard library)."""
from pathlib import Path
import csv
import io
import json
import math
import sqlite3
import threading

ROOT = Path(__file__).resolve().parent
ENERGIES = {"coal":"煤炭","oil":"石油","gas":"天然气","primary_electricity_other":"一次电力及其他能源"}
FIRST, LAST = 2011, 2025

def read_csv(name):
    with (ROOT/"data/processed"/name).open(encoding="utf-8-sig",newline="") as handle:
        result = []
        for row in csv.DictReader(handle):
            item = {}
            for key,value in row.items():
                if value == "": item[key] = None
                elif value in ("True","False"): item[key] = int(value=="True")
                else:
                    try:
                        number = float(value)
                        item[key] = int(number) if number.is_integer() else number
                    except ValueError: item[key] = value
            result.append(item)
        return result

class DashboardData:
    def __init__(self):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(":memory:",check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        for table,filename in [("population","population_annual.csv"),("energy","energy_annual.csv"),("structure","energy_structure.csv")]:
            rows = read_csv(filename)
            columns = list(rows[0])
            definition = ",".join('"'+key+'" '+("TEXT" if any(isinstance(r[key],str) for r in rows) else "REAL") for key in columns)
            self.db.execute('CREATE TABLE '+table+' ('+definition+')')
            self.db.executemany("INSERT INTO "+table+" VALUES ("+",".join("?" for _ in columns)+")",
                                [[r[key] for key in columns] for r in rows])
        self.db.execute("CREATE UNIQUE INDEX population_year ON population(year)")
        self.db.execute("CREATE UNIQUE INDEX energy_year ON energy(year)")
        self.db.execute("CREATE UNIQUE INDEX structure_year_key ON structure(year,energy_key)")
        self.db.commit()
        self.dictionary = {r["field"]:r for r in read_csv("indicator_dictionary.csv")}
        self.years = list(range(FIRST,LAST+1))

    def query(self,sql,params=()):
        with self.lock:
            return [dict(row) for row in self.db.execute(sql,params)]

    def close(self):
        self.db.close()

    def payload(self,year=LAST,base=FIRST,energy="coal",mode="amount"):
        if type(year) is not int or type(base) is not int or year not in self.years or base not in self.years:
            raise ValueError(f"年份必须在 {FIRST}—{LAST} 年之间")
        if base>year: raise ValueError("比较基期不能晚于当前年份")
        if energy not in ENERGIES: raise ValueError("未知能源类别")
        if mode not in ("amount","share"): raise ValueError("未知数量/占比模式")
        population=self.query("SELECT * FROM population WHERE year BETWEEN ? AND ? ORDER BY year",(FIRST,LAST))
        totals=self.query("SELECT * FROM energy WHERE year BETWEEN ? AND ? ORDER BY year",(FIRST,LAST))
        structures=self.query("SELECT * FROM structure WHERE year BETWEEN ? AND ? ORDER BY year, energy_key",(FIRST,LAST))
        # The accepted CSV flag records the old complete-data window; the app
        # chooses its current window without rewriting that historical snapshot.
        for row in population+totals+structures:
            row["in_display_window"]=1
        p=next(r for r in population if r["year"]==year)
        e=next(r for r in totals if r["year"]==year)
        bp=next(r for r in population if r["year"]==base)
        be=next(r for r in totals if r["year"]==base)
        current=self.query("SELECT * FROM structure WHERE year=? ORDER BY energy_key",(year,))
        base_structure={r["energy_key"]:r for r in self.query("SELECT * FROM structure WHERE year=?",(base,))}
        changes=[]
        for key,label in ENERGIES.items():
            r=next(r for r in current if r["energy_key"]==key)
            changes.append({"key":key,"name":label,"delta":r["amount_estimated_tce_10k"]-base_structure[key]["amount_estimated_tce_10k"]})
        residual=e["rounding_residual_tce_10k"]-be["rounding_residual_tce_10k"]
        changes.append({"key":"rounding","name":"舍入差额","delta":residual})
        assert math.isclose(sum(r["delta"] for r in changes),e["energy_total"]-be["energy_total"],abs_tol=1e-6)
        delta_population=p["population_total"]-bp["population_total"]
        summary=(f'{year} 年末人口 {p["population_total"]:,.0f} 万人，较上年'
                 f'{"增加" if p["population_change"]>=0 else "减少"} {abs(p["population_change"]):,.0f} 万人；'
                 f'城镇人口比重 {p["urbanization_pct"]:.2f}%。'
                 f'能源消费总量 {e["energy_total"]/10000:.2f} 亿吨标准煤，按当前序列计算较上年变化 {e["energy_yoy_calculated_pct"]:+.2f}%。'
                 f'相对 {base} 年，人口变化 {delta_population:+,.0f} 万人，城镇人口比重变化 {p["urbanization_pct"]-bp["urbanization_pct"]:+.2f} 个百分点。')
        living_missing=[int(r["year"]) for r in totals if r["living_energy_per_capita"] is None]
        living_available=[int(r["year"]) for r in totals if r["living_energy_per_capita"] is not None]
        return {
            "years":self.years,"state":{"year":year,"base":base,"energy":energy,"mode":mode},
            "population":population,"energy":totals,"structure":structures,
            "current_population":p,"current_energy":e,"base_population":bp,"base_energy":be,
            "selected_energy_series":[r for r in structures if r["energy_key"]==energy],
            "energy_names":ENERGIES,"waterfall":{"start":be["energy_total"],"end":e["energy_total"],"changes":changes},
            "summary":summary,"source":{"provider":"国家统计局","retrieved":"2026-10-29","period":f"{FIRST}—{LAST}","region":"全国"},
            "availability":{"living_energy_per_capita":{"missing_years":living_missing,"last_available_year":max(living_available) if living_available else None}},
            "dictionary":{k:{name:v.get(name,"") for name in ("label","unit","method")} for k,v in self.dictionary.items()},
            "notes":[
                "年份播放切换历史年度数据。能源类别只联动能源分析，趋势图保留完整15年。",
                "人均生活能源在当前数据源中缺失2024、2025年；曲线保留空值，不补零、不插值，其他指标正常显示。",
                "能源年度变化为当前总量序列自算值，不等同官方可比口径增速。",
                "品种折标量=总量×官方占比，为估算值；一次电力及其他能源沿用官方名称。",
                "2018年年龄分组合计比总人口少1万人；2019年能源占比合计99.9%，均保留原值。",
                "瀑布图为基期增量的算术分解，舍入差额独立列示，不代表因果贡献。"
            ],
        }

    def export_rows(self,payload,scope="current"):
        if scope not in ("current","all"): raise ValueError("未知导出范围")
        year,base=payload["state"]["year"],payload["state"]["base"]
        rows=[]
        for group,values in [("人口",payload["population"]),("能源",payload["energy"])]:
            for r in values:
                if scope=="current" and r["year"]!=year: continue
                for field,value in r.items():
                    if field in ("year","in_display_window"):continue
                    meta=self.dictionary.get(field,{})
                    rows.append({"年份":int(r["year"]),"比较基期":base,"数据组":group,
                                 "指标":meta.get("label",field),"字段":field,"数值":value,
                                 "单位":meta.get("unit",""),"计算方法":meta.get("method",""),
                                 "数据来源":"国家统计局","获取日期":"2026-10-29"})
        for r in payload["structure"]:
            if r["energy_key"]!=payload["state"]["energy"]:continue
            if scope=="current" and r["year"]!=year:continue
            for field,unit in [("share_pct","%"),("amount_estimated_tce_10k","万吨标准煤"),("share_change_pp","百分点")]:
                rows.append({"年份":int(r["year"]),"比较基期":base,"数据组":r["energy_name"],
                             "指标":field,"字段":field,"数值":r[field],"单位":unit,
                             "计算方法":{"share_pct":"官方占比","amount_estimated_tce_10k":r["method"],"share_change_pp":"当年占比−上年占比"}[field],
                             "数据来源":"国家统计局","获取日期":"2026-10-29"})
        return rows

    def export_csv(self,payload,scope="current"):
        rows=self.export_rows(payload,scope)
        output=io.StringIO(newline="")
        writer=csv.DictWriter(output,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
        return ("\ufeff"+output.getvalue()).encode("utf-8")
