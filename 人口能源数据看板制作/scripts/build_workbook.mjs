import fs from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {Workbook, SpreadsheetFile} from "@oai/artifact-tool";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const data = JSON.parse(await fs.readFile(path.join(root,"data/processed/data_package.json"),"utf8"));
const out = path.join(root,"outputs/data-review");
await fs.mkdir(out,{recursive:true});
const wb = Workbook.create();
const sheets = [];
function sheet(name, headers, rows, widths, note) {
  const s=wb.worksheets.add(name);
  s.showGridLines=false;
  const n=headers.length, last=String.fromCharCode(64+n), end=rows.length+4;
  const area=s.getRange("A1:"+last+end);
  area.format.font={name:"Microsoft YaHei",size:10};
  area.format.rowHeight=23;
  area.format.verticalAlignment="center";
  s.getRange("A1").values=[[name]];
  s.getRange("A1").format.font={name:"Microsoft YaHei",size:14,bold:true};
  s.getRange("A2").values=[[note]];
  s.getRange("A2").format.font={name:"Microsoft YaHei",size:10,color:"#526174"};
  s.getRange("A4:"+last+"4").values=[headers];
  s.getRange("A4:"+last+"4").format={
    fill:"#263d57",font:{name:"Microsoft YaHei",size:10,color:"#FFFFFF",bold:true},
    horizontalAlignment:"center",rowHeight:34,wrapText:true
  };
  if(rows.length) s.getRange("A5:"+last+end).values=rows;
  if(typeof rows[0]?.[0]==="number"){
    s.getRange("A5:A"+end).setNumberFormat("0");
    s.getRange("A5:A"+end).format.horizontalAlignment="center";
  }
  widths.forEach((w,i)=>s.getRange(String.fromCharCode(65+i)+"1:"+String.fromCharCode(65+i)+end).format.columnWidth=w);
  s.freezePanes.freezeRows(4);
  sheets.push({s,name,rows:rows.length,cols:n,end});
  return s;
}
const pop=sheet("人口年度",
["年份","年末总人口\n万人","城镇人口\n万人","乡村人口\n万人","城镇人口比重\n计算值","出生率\n‰","死亡率\n‰","自然增长率\n‰","男性人口\n万人","女性人口\n万人"],
data.population.map(r=>[r.year,r.population_total,r.population_urban,r.population_rural,null,r.birth_rate,r.death_rate,r.natural_growth_rate,r.population_male,r.population_female]),
[10,18,18,18,20,15,15,18,18,18],
"来源：国家统计局国家数据；2008 为同比辅助年，2009—2023 为完整展示期，2024—2025 为扩展数据。");
pop.getRange("A5:D22").setNumberFormat("#,##0");
pop.getRange("A5:A22").setNumberFormat("0");
pop.getRange("I5:J22").setNumberFormat("#,##0");
pop.getRange("F5:H22").setNumberFormat("0.00");
data.population.forEach((r,i)=>pop.getRange("E"+(i+5)).formulas=[["=C"+(i+5)+"/B"+(i+5)]]);
pop.getRange("E5:E22").setNumberFormat("0.00%");
const age=sheet("年龄结构",
["年份","年末总人口\n万人","0—14 岁\n万人","15—64 岁\n万人","65 岁及以上\n万人","0—14 岁占比","15—64 岁占比","65 岁及以上占比","分组合计差额\n万人"],
data.population.map(r=>[r.year,r.population_total,r.population_age_0_14,r.population_age_15_64,r.population_age_65_plus,null,null,null,null]),
[10,18,18,18,19,20,20,23,22],
"来源：国家统计局人口年龄结构表；2018 年分组合计少 1 万人，保留原值，占比不强制归一。");
age.getRange("A5:E22").setNumberFormat("#,##0");
age.getRange("A5:A22").setNumberFormat("0");
age.getRange("I5:I22").setNumberFormat("#,##0");
for(let row=5;row<=22;row++){
  age.getRange("F"+row+":I"+row).formulas=[["=C"+row+"/B"+row,"=D"+row+"/B"+row,"=E"+row+"/B"+row,"=SUM(C"+row+":E"+row+")-B"+row]];
}
age.getRange("F5:H22").setNumberFormat("0.00%");
const energy=sheet("能源年度",
["年份","能源消费总量\n万吨标准煤","较上年变化\n序列计算值","官方可比增速\n本次未取得","人均生活能源\n千克标准煤/人","人均生活用电\n千瓦小时/人"],
data.energy.map(r=>[r.year,r.energy_total,null,null,r.living_energy_per_capita,r.living_electricity_per_capita]),
[10,27,24,26,28,28],
"来源：国家统计局能源表；2024、2025 年人均生活用能为空。序列计算值不等同官方可比增速。");
energy.getRange("A5:B22").setNumberFormat("#,##0");
energy.getRange("A5:A22").setNumberFormat("0");
energy.getRange("E5:F22").setNumberFormat("#,##0");
for(let row=6;row<=22;row++) energy.getRange("C"+row).formulas=[["=B"+row+"/B"+(row-1)+"-1"]];
energy.getRange("C5:D22").setNumberFormat("0.00%");
const structure=sheet("能源结构",
["年份","能源类别","官方占比","全国总量\n万吨标准煤","品种折标量估算\n万吨标准煤","占比较上年变化\n百分点","四类占比合计"],
data.structure.map(r=>[r.year,r.energy_name,r.share_pct/100,data.energy.find(e=>e.year===r.year).energy_total,null,r.share_change_pp,data.energy.find(e=>e.year===r.year).share_sum_pct/100]),
[10,28,18,26,28,26,23],
"来源：国家统计局能源总量及占比；估算值=总量×占比。2019 年占比合计 99.9%，差额另见 CSV。");
for(let row=5;row<=76;row++) structure.getRange("E"+row).formulas=[["=C"+row+"*D"+row]];
structure.getRange("A5:A76").setNumberFormat("0");
structure.getRange("C5:C76").setNumberFormat("0.0%");
structure.getRange("G5:G76").setNumberFormat("0.0%");
structure.getRange("D5:E76").setNumberFormat("#,##0.00");
structure.getRange("F5:F76").setNumberFormat("0.0");
const dict=sheet("指标字典",
["字段名","指标名称","单位","取值或计算方法","来源组","看板核心字段"],
data.dictionary.map(r=>[r.field,r.label,r.unit,r.method,r.source_group,r.required_for_dashboard?"是":"否"]),
[38,48,23,76,32,18],
"字段名用于 CSV 与 Python；原始指标 ID、定义与官方注释完整保存在 indicator_dictionary.csv。");
dict.getRange("A5:F"+(data.dictionary.length+4)).format.wrapText=true;
dict.getRange("A5:F"+(data.dictionary.length+4)).format.rowHeight=44;
const cov=sheet("覆盖情况",
["指标名称","首个非空年","最后非空年","缺失年份","看板核心字段"],
data.coverage.map(r=>[r.label,r.first_available,r.last_available,r.missing_years,r.required_for_dashboard?"是":"否"]),
[50,18,18,80,20],
"查询范围 2008—2025；空值未补零或插值。15 项核心指标在 2009—2023 年均完整。");
cov.getRange("D5:D"+(data.coverage.length+4)).format.wrapText=true;
cov.getRange("B5:C"+(data.coverage.length+4)).format.horizontalAlignment="center";
cov.getRange("A5:E"+(data.coverage.length+4)).format.rowHeight=32;
const notes=[
["数据来源", "国家统计局国家数据，全国年度数据；地区代码 000000000000。"],
["查询页面","https://data.stats.gov.cn/dg/website/page.html#/pc/national/yearData"],
["获取日期","2026-10-29；逐请求 UTC 时间及 SHA-256 见 data/raw/manifest.json。"],
["完整展示期","2009—2023 年，共 15 年；2008 年用于计算第一年同比。"],
["最新扩展期","保留查询库中的 2024—2025 年数据；人均生活用能等缺失值为空，不代表其他官方渠道尚未发布。"],
["人口原始来源","data/raw/population_total_data.json、population_rates_data.json、population_age_data.json"],
["能源原始来源","data/raw/energy_total_data.json、energy_living_per_capita_data.json；弹性系数为备用原始数据。"],
["能源分组","煤炭、石油、天然气、一次电力及其他能源；保留官方分类，不改名为清洁能源。"],
["能源折标量","由总量×占比推算，仅为标准煤口径估算值；不可与实物煤炭吨数或电量等混合相加。"],
["增速口径","能源年度表提供当前总量序列的自算变化，官方可比增速未取得并保留空值。"],
["人口修订","官方年龄表注释：2011—2019 年数据根据 2020 年人口普查数据修订。"],
["舍入差异","2018 年年龄分组合计少 1 万人；2019 年能源占比合计 99.9%，保留原值。"],
["人均口径","采用官方人均生活能源消费量，不用全国总能源÷年末人口代替。"],
["文件关系","原始响应不改写；CSV 是可复现清洗结果；本工作簿为便于人工核验的整理版。"],
];
const source=sheet("来源与口径",["项目","说明"],notes,[26,132],
"公开年度统计数据；数据下载与整理阶段，尚未制作交互看板。");
source.getRange("A5:B"+(notes.length+4)).format.wrapText=true;
source.getRange("A5:B"+(notes.length+4)).format.rowHeight=42;
wb.recalculate();
const errors=await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!",options:{useRegex:true,maxResults:30},maxChars:3000});
console.log(errors.ndjson);
for(const entry of sheets){
 const end=Math.min(entry.end,12);
 const blob=await wb.render({sheetName:entry.name,range:"A1:"+String.fromCharCode(64+entry.cols)+end,scale:1.25});
 await fs.writeFile(path.join(out,entry.name+"_preview.png"),new Uint8Array(await blob.arrayBuffer()));
}
const result=await SpreadsheetFile.exportXlsx(wb);
await result.save(path.join(out,"全国人口与能源_数据核验.xlsx"));
console.log("Workbook exported: "+out);
