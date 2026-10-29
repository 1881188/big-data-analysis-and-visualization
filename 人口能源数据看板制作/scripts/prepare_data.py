"""Build auditable UTF-8 CSV/JSON data from local, unchanged NBS responses."""
from pathlib import Path
from decimal import Decimal
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
OUT = ROOT / "data/processed"
YEARS = list(range(2008, 2026))
WINDOW = list(range(2009, 2024))
SOURCE = "https://data.stats.gov.cn/dg/website/page.html#/pc/national/yearData"
# Stable official indicator identifiers, never matched by column position.
CORE = {
"population_total": "806083491dbe46a08995783945a30b9d",
"population_male": "b808a4131bd041c4abc87b52385cd578",
"population_female": "30d59b42875145c696883366172bb3d1",
"population_urban": "07e1e3444cd34c43b4fd749f060bba5f",
"population_rural": "2dd9894936d448fcb88605863d90d85c",
"birth_rate": "3d4006d356d94bdd9d75700b9788e230",
"death_rate": "ee4b8be1ad68498e81d9ecddf4d4f2de",
"natural_growth_rate": "3969129b26a846968a7dddff5f326f55",
"population_age_total": "9f39d77c761d4824940fc3c23d8281b0",
"population_age_0_14": "067f5f3ec585402e9f31037e5f27eb17",
"population_age_15_64": "a6051fc22d394d81b2007dc7c7c761fa",
"population_age_65_plus": "c2627d8e6b5843bfa3372bacdf858804",
"dependency_total": "0d2db39cd5424f5fbca859052413f4ad",
"dependency_child": "93c00898dbeb4aff881fa97723901739",
"dependency_old": "9d77e24ce8c94679937b07188f4e7fbc",
"energy_total": "b7efa87515d54d2fa20f9349fbdf9b26",
"share_coal": "2afcc6fcd8544170a42b46fc3e2e4f6c",
"share_oil": "045599fa695944519eac1102848623d3",
"share_gas": "4fded3548afe4ddc8220d19a1649e306",
"share_primary_electricity_other": "325140927609462fb26f2fc79c74f309",
"living_energy_per_capita": "52b933f658314e1cbb1a21e9c4474a5f",
"living_electricity_per_capita": "db860633c5ca4f73ad960975487325bb",
}
REVERSE = {v:k for k,v in CORE.items()}
REQUIRED = [k for k in CORE if k not in {
    "population_male", "population_female", "population_age_total",
    "dependency_total", "dependency_child", "dependency_old",
    "living_electricity_per_capita"}]
ENERGIES = {
"coal":"煤炭", "oil":"石油", "gas":"天然气",
"primary_electricity_other":"一次电力及其他能源",
}
def read(path):
    return json.loads(path.read_text(encoding="utf-8"))
def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
def write_csv(path, rows, columns=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
def number(s):
    if s is None or str(s).strip() in ("", "-", "…", "..."):
        return None
    x = Decimal(str(s).replace(",", ""))
    return int(x) if x == x.to_integral_value() else float(x)
def ratio(a,b):
    return None if a is None or b in (None,0) else a/b*100
def growth(a,b):
    return None if a is None or b in (None,0) else (a/b-1)*100
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = read(RAW/"manifest.json")
    checks = []
    def check(name, condition, detail):
        checks.append({"check":name, "passed":bool(condition), "detail":detail})
    for item in manifest:
        check("原始文件哈希:"+item["file"],
              hashlib.sha256((ROOT/item["file"]).read_bytes()).hexdigest()==item["sha256"],
              "文件与下载时SHA-256一致")
    observations, definitions, bykey, coverage = [], [], {}, []
    for file in sorted(RAW.glob("*_indicators.json")):
        group = file.name.removesuffix("_indicators.json")
        metadata = read(file)["data"]["list"]
        response = read(RAW/(group+"_data.json"))["data"]
        yearmap = {int(r["code"][:4]):r for r in response}
        check("年份唯一:"+group, len(yearmap)==len(response), str(sorted(yearmap)))
        for meta in metadata:
            iid = meta["_id"]
            key = REVERSE.get(iid, "extra_"+iid[:8])
            label = meta["i_showname"].strip()
            unit = meta.get("du_name","")
            definition = {
                "field":key, "label":label, "unit":unit,
                "method":"官方原值", "source_group":group,
                "indicator_id":iid, "catalog_id":meta["catalogid"],
                "annotation":meta.get("i_annotation") or "",
                "definition":meta.get("i_mark") or "",
                "required_for_dashboard":key in REQUIRED,
                "source_url":SOURCE,
            }
            definitions.append(definition)
            values = {}
            for year in YEARS:
                found = [v for v in yearmap[year]["values"] if v["_id"]==iid]
                check("单元格唯一:"+key+":"+str(year), len(found)==1, "按年份及官方指标ID定位")
                value = number(found[0]["value"]) if found else None
                values[year] = value
                observations.append({
                    "year":year,"field":key,"indicator_id":iid,"label":label,
                    "value":value,"unit":unit,"raw_text":found[0]["value"] if found else "",
                    "is_missing":value is None, "source_group":group,
                    "source_file":"data/raw/"+group+"_data.json",
                })
            bykey[key] = values
            good = [y for y,v in values.items() if v is not None]
            coverage.append({
                "field":key,"label":label,"unit":unit,
                "first_available":min(good) if good else None,
                "last_available":max(good) if good else None,
                "missing_years":",".join(str(y) for y,v in values.items() if v is None),
                "required_for_dashboard":key in REQUIRED,
            })
    common = [y for y in YEARS if all(bykey[k][y] is not None for k in REQUIRED)]
    check("核心15年连续完整", all(y in common for y in WINDOW), str(common))
    check("2008辅助年完整", 2008 in common, "用于2009年同比")
    pop, energy, structure = [], [], []
    warnings = []
    for y in YEARS:
        v = lambda k:bykey[k][y]
        previous = lambda k:bykey[k].get(y-1)
        p = {"year":y,"in_display_window":y in WINDOW}
        p.update({k:v(k) for k in CORE if k.startswith("population_") or k in
                  ("birth_rate","death_rate","natural_growth_rate",
                   "dependency_total","dependency_child","dependency_old")})
        p["urbanization_pct"] = ratio(v("population_urban"),v("population_total"))
        p["population_change"] = None if previous("population_total") is None else v("population_total")-previous("population_total")
        for key in ("0_14","15_64","65_plus"):
            p["age_share_"+key+"_pct"] = ratio(v("population_age_"+key),v("population_total"))
        age_sum = sum(v("population_age_"+k) for k in ("0_14","15_64","65_plus"))
        p["age_sum_difference"] = age_sum-v("population_total")
        check("城乡合计:"+str(y), v("population_urban")+v("population_rural")==v("population_total"), "万人")
        check("性别合计:"+str(y), v("population_male")+v("population_female")==v("population_total"), "万人")
        check("年龄表总人口核对:"+str(y), v("population_age_total")==v("population_total"), "与总人口表核对")
        check("年龄合计舍入容差:"+str(y), abs(p["age_sum_difference"])<=2, str(p["age_sum_difference"])+"万人")
        rate_diff = Decimal(str(v("birth_rate")))-Decimal(str(v("death_rate")))-Decimal(str(v("natural_growth_rate")))
        check("出生减死亡核对:"+str(y), abs(rate_diff)<=Decimal("0.01"), str(rate_diff)+"‰")
        if p["age_sum_difference"]:
            warnings.append({"year":y,"issue":"年龄分组加总与总人口不等","difference":p["age_sum_difference"],"unit":"万人","action":"保留原值，不改写分组；占比不强制归一"})
        pop.append(p)
        e = {"year":y,"in_display_window":y in WINDOW,
             "energy_total":v("energy_total"),
             "energy_yoy_calculated_pct":growth(v("energy_total"),previous("energy_total")),
             "energy_yoy_official_pct":None,
             "living_energy_per_capita":v("living_energy_per_capita"),
             "living_electricity_per_capita":v("living_electricity_per_capita")}
        e.update({"share_"+k:v("share_"+k) for k in ENERGIES})
        total_share = sum(Decimal(str(e["share_"+k])) for k in ENERGIES)
        e["share_sum_pct"] = float(total_share)
        e["rounding_residual_tce_10k"] = float(Decimal(str(e["energy_total"]))*(Decimal(100)-total_share)/100)
        check("能源占比合计容差:"+str(y), abs(total_share-100)<=Decimal("0.2"), str(total_share)+"%")
        if total_share != 100:
            warnings.append({"year":y,"issue":"能源占比合计不等于100%","difference":float(total_share-100),"unit":"百分点","action":"保留官方占比；瀑布图单列舍入差额"})
        energy.append(e)
        for k,label in ENERGIES.items():
            amount = v("energy_total")*v("share_"+k)/100
            old_amount = None if previous("energy_total") is None else previous("energy_total")*previous("share_"+k)/100
            structure.append({
                "year":y,"in_display_window":y in WINDOW,"energy_key":k,"energy_name":label,
                "share_pct":v("share_"+k),"amount_estimated_tce_10k":amount,
                "amount_yoy_calculated_pct":growth(amount,old_amount),
                "share_change_pp":None if previous("share_"+k) is None else v("share_"+k)-previous("share_"+k),
                "method":"能源消费总量×官方占比÷100；折标量估算值",
            })
    derived = [
        ("urbanization_pct","城镇人口比重（计算值）","%","城镇人口÷年末总人口×100","population_total"),
        ("population_change","年末人口较上年增减","万人","本年年末人口−上年年末人口","population_total"),
        ("age_share_0_14_pct","0—14岁人口占比（计算值）","%","0—14岁人口÷年末总人口×100","population_age"),
        ("age_share_15_64_pct","15—64岁人口占比（计算值）","%","15—64岁人口÷年末总人口×100","population_age"),
        ("age_share_65_plus_pct","65岁及以上人口占比（计算值）","%","65岁及以上人口÷年末总人口×100","population_age"),
        ("age_sum_difference","年龄分组加总差额","万人","年龄三组合计−年末总人口","population_age"),
        ("energy_yoy_calculated_pct","能源总量较上年变化（序列计算）","%","(本年总量÷上年总量−1)×100；不等同官方可比增速","energy_total"),
        ("energy_yoy_official_pct","能源消费总量官方可比增速","%","本次所取指标未单列，留空；不得由弹性系数推断","energy_total"),
        ("share_sum_pct","能源占比合计","%","四类官方占比相加","energy_total"),
        ("rounding_residual_tce_10k","能源结构舍入差额","万吨标准煤","总量×(100−四类占比合计)÷100","energy_total"),
        ("amount_estimated_tce_10k","能源品种折标消费量估算值","万吨标准煤","总量×品种占比÷100；不是实物量","energy_total"),
        ("amount_yoy_calculated_pct","能源品种估算折标量较上年变化","%","(当年估算折标量÷上年估算折标量−1)×100","energy_total"),
        ("share_change_pp","能源品种占比较上年变化","百分点","当年占比−上年占比","energy_total"),
    ]
    for key,label,unit,method,group in derived:
        definitions.append({"field":key,"label":label,"unit":unit,"method":method,
                            "source_group":group,"indicator_id":"","catalog_id":"",
                            "annotation":"","definition":"","required_for_dashboard":False,"source_url":SOURCE})
    write_csv(OUT/"observations.csv", observations)
    write_csv(OUT/"population_annual.csv", pop)
    write_csv(OUT/"energy_annual.csv", energy)
    write_csv(OUT/"energy_structure.csv", structure)
    write_csv(OUT/"indicator_dictionary.csv", definitions)
    write_csv(OUT/"coverage.csv", coverage)
    write_csv(OUT/"source_manifest.csv", [{k:v for k,v in x.items() if k!="request_body"} for x in manifest])
    report = {
        "display_years":WINDOW,"previous_year":2008,"raw_years":YEARS,
        "raw_indicator_count":len(coverage),"raw_observations":len(observations),
        "missing_observations":sum(x["is_missing"] for x in observations),
        "core_fields":REQUIRED, "core_missing_in_display":sum(bykey[k][y] is None for k in REQUIRED for y in WINDOW),
        "checks_total":len(checks),"checks_failed":[x for x in checks if not x["passed"]],
        "rounding_warnings":warnings,
        "limitations":[
            "查询库人均生活用能2024、2025为空；主屏使用2009—2023完整窗口。",
            "能源官方可比增速未从本次指标取得；提供当前序列自算增速并明确命名。",
            "一次电力及其他能源沿用官方类别，不直接改名为清洁能源或非化石能源。",
            "结构折标量由总量和占比推算；实物量另存原始长表，不混合相加。",
            "2011—2019人口年龄数据已按2020人口普查修订，见原始指标注释。",
            "若能源口径存在未回溯修订的断点，自算跨年变化不能解释为实际增速；制作看板时保留提示。",
        ],
    }
    write_json(OUT/"quality_report.json",report)
    write_json(OUT/"data_package.json",{
        "population":pop,"energy":energy,"structure":structure,
        "dictionary":definitions,"coverage":coverage,
        "manifest":manifest,"quality":report,
    })
    write_json(OUT/"validation_checks.json",checks)
    assert not report["checks_failed"], report["checks_failed"]
    print(json.dumps({k:v for k,v in report.items() if k not in ("core_fields","limitations")},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
