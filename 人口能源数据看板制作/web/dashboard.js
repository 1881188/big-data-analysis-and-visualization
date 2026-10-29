"use strict";
(() => {
const $=id=>document.getElementById(id);
const colors={coal:"#63a8f5",oil:"#eac17a",gas:"#a895df",primary_electricity_other:"#47d7b2"};
const keys=Object.keys(colors), years=Array.from({length:15},(_,i)=>2011+i);
const fmt=(v,d=2)=>v===null||v===undefined||v==="-"||!Number.isFinite(Number(v))?"—":Number(v).toLocaleString("zh-CN",{minimumFractionDigits:d,maximumFractionDigits:d});
const signed=(v,d=2)=>(v>=0?"+":"")+fmt(v,d);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let state={year:2025,base:2011,energy:"coal",mode:"amount"}, data=null, timer=null, pending=null, large=null, largeId=null;
const charts={}, options={}, chartTitles={};
let toastTimeout, sliderTimeout;
const tooltip={backgroundColor:"#0b1928",borderColor:"#3a5368",textStyle:{color:"#dce9f3",fontSize:12},confine:true,extraCssText:"box-shadow:0 8px 24px #0005;border-radius:7px;"};
const axis={axisLine:{lineStyle:{color:"#365066"}},axisTick:{show:false},axisLabel:{color:"#809bb0",fontSize:10},splitLine:{lineStyle:{color:"#203446",type:"dashed"}}};
function baseOption(unit="",rightUnit){
 const right=rightUnit!==undefined?66:22;
 const y={...axis,type:"value",name:unit,nameTextStyle:{color:"#6e8da4",fontSize:10,padding:[0,0,0,0]},nameGap:9};
 return {animation:false,backgroundColor:"transparent",color:Object.values(colors),textStyle:{fontFamily:"Microsoft YaHei, sans-serif"},
  tooltip:{...tooltip,trigger:"axis"},grid:{left:54,right,top:34,bottom:29},
  legend:{top:0,textStyle:{color:"#9bb2c5",fontSize:10},itemWidth:12,itemHeight:6,selectedMode:false},
  xAxis:{...axis,type:"category",data:years.map(String),boundaryGap:false,axisLabel:{...axis.axisLabel,interval:2,showMaxLabel:true}},
  yAxis:rightUnit!==undefined?[y,{...axis,type:"value",name:rightUnit,nameTextStyle:{color:"#6e8da4",fontSize:10},splitLine:{show:false}}]:y};
}
function mark(){
 return {silent:true,symbol:"none",label:{show:false},lineStyle:{color:"#eac17a",width:1,type:"dashed",opacity:.65},data:[{xAxis:String(state.year)}]};
}
function line(name,values,color,extra={}){
 return {name,type:"line",data:values.map((value,i)=>({value,symbolSize:years[i]===state.year?7:3})),symbol:"circle",showSymbol:true,
 itemStyle:{color},lineStyle:{width:2,color},markLine:mark(),...extra};
}
function axisTip(unit,d=2){
 return params=>params[0].axisValue+" 年<br>"+params.filter(p=>p.seriesName!=="offset").map(p=>p.marker+esc(p.seriesName)+"　"+fmt(p.value,d)+(unit?" "+unit:"")).join("<br>");
}
function buildOptions(){
 const p=data.population,e=data.energy,c=data.current_population;
 let o=baseOption("亿人");
 o.yAxis.scale=true;o.tooltip.formatter=axisTip("亿人");
 o.series=[line("年末总人口",p.map(r=>r.population_total/10000),colors.coal,{areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:"#63a8f54a"},{offset:1,color:"#63a8f503"}])}})];
 options["01"]=o;
 o=baseOption("‰");o.tooltip.formatter=axisTip("‰");
 o.series=[line("出生率",p.map(r=>r.birth_rate),colors.coal),line("死亡率",p.map(r=>r.death_rate),colors.oil),line("自然增长率",p.map(r=>r.natural_growth_rate),colors.primary_electricity_other)];
 options["02"]=o;
 o=baseOption(state.mode==="share"?"%":"亿人");
 o.xAxis.boundaryGap=true;if(state.mode==="share"){o.yAxis.max=100;}
 o.tooltip.formatter=axisTip(state.mode==="share"?"%":"亿人");
 o.series=[["城镇","population_urban",colors.coal],["乡村","population_rural",colors.primary_electricity_other]].map(([name,key,color])=>({
 name,type:"bar",stack:"population",barMaxWidth:24,itemStyle:{color},
 data:p.map(r=>({value:state.mode==="share"?r[key]/r.population_total*100:r[key]/10000,itemStyle:{color,opacity:r.year===state.year?1:.65}})),markLine:mark()}));
 options["03"]=o;
 const ageNames=["0—14岁","15—64岁","65岁及以上"],ageKeys=["0_14","15_64","65_plus"],ageColors=[colors.coal,colors.primary_electricity_other,colors.oil];
 const ageValues=ageKeys.map((k,i)=>({name:ageNames[i],value:c["population_age_"+k],share:c["age_share_"+k+"_pct"],itemStyle:{color:ageColors[i]}}));
 options["04"]={animation:false,backgroundColor:"transparent",textStyle:{fontFamily:"Microsoft YaHei"},
 tooltip:{...tooltip,trigger:"item",formatter:q=>esc(q.name)+"<br>"+fmt(q.value,0)+" 万人<br>占年末总人口 "+fmt(q.data.share)+"%"},
 legend:{orient:"vertical",right:"6%",top:"center",itemWidth:9,itemHeight:9,itemGap:17,selectedMode:false,textStyle:{color:"#afc3d2",fontSize:11},
 formatter:name=>{const v=ageValues.find(x=>x.name===name);return name+"  "+(state.mode==="share"?fmt(v.share,1)+"%":fmt(v.value/10000,2)+"亿人");}},
 graphic:[{type:"text",left:"25%",top:"34%",style:{text:String(state.year),fill:"#e7f1f7",font:'26px "Bahnschrift", sans-serif',align:"center"}},
 {type:"text",left:"25%",top:"54%",style:{text:"年龄结构",fill:"#7f9aaf",font:'11px "Microsoft YaHei"',align:"center"}}],
 series:[{name:"年龄结构",type:"pie",center:["32%","48%"],radius:["50%","72%"],avoidLabelOverlap:true,label:{show:false},labelLine:{show:false},itemStyle:{borderColor:"#102130",borderWidth:3},data:ageValues}]};
 o=baseOption("亿吨标准煤","%");o.xAxis.boundaryGap=true;
 o.tooltip.formatter=params=>params[0].axisValue+" 年<br>"+params.map(q=>q.marker+q.seriesName+"　"+fmt(q.value)+(q.seriesIndex===0?" 亿吨标准煤":"%（序列自算）")).join("<br>");
 o.series=[{name:"能源消费总量",type:"bar",barMaxWidth:23,itemStyle:{color:"#4387b0"},data:e.map(r=>({value:r.energy_total/10000,itemStyle:{color:r.year===state.year?"#eac17a":"#4387b0"}})),markLine:mark()},
 line("较上年变化",e.map(r=>r.energy_yoy_calculated_pct),colors.primary_electricity_other,{yAxisIndex:1})];
 options["05"]=o;
 o=baseOption("%");o.grid.top=43;o.legend.textStyle.fontSize=9;o.legend.itemGap=8;
 o.yAxis.max=100;o.tooltip.formatter=axisTip("%",1);
 o.series=keys.map(key=>({name:data.energy_names[key],type:"line",stack:"energy",symbol:"none",
 data:years.map(y=>data.structure.find(r=>r.year===y&&r.energy_key===key).share_pct),
 itemStyle:{color:colors[key]},lineStyle:{color:colors[key],width:key===state.energy?2:1},
 areaStyle:{color:colors[key],opacity:key===state.energy?.85:.55},markLine:key===state.energy?mark():undefined}));
 options["06"]=o;
 const selected=data.selected_energy_series;
 o=baseOption(state.mode==="share"?"%":"亿吨标准煤");
 o.tooltip.formatter=axisTip(state.mode==="share"?"%":"亿吨标准煤（折标量估算）");
 o.series=[line(data.energy_names[state.energy],selected.map(r=>state.mode==="share"?r.share_pct:r.amount_estimated_tce_10k/10000),colors[state.energy],
 {areaStyle:{color:colors[state.energy],opacity:.12}})];
 options["07"]=o;
 o=baseOption("千克标准煤/人");o.grid.left=51;o.tooltip.formatter=axisTip("千克标准煤/人",0);
 o.series=[line("人均生活能源",e.map(r=>r.living_energy_per_capita),colors.primary_electricity_other,{connectNulls:false,areaStyle:{color:colors.primary_electricity_other,opacity:.10}})];
 o.tooltip.formatter=params=>{
  if(!params.length)return "";
  const q=params[0];
  return q.axisValue+" 年<br>"+(q.value==null||q.value==="-"?"当前数据源缺失":fmt(q.value,0)+" 千克标准煤／人");
 };
 const missing=data.availability.living_energy_per_capita.missing_years;
 if(missing.length)o.series[0].markArea={silent:true,itemStyle:{color:"#eac17a0b"},data:[[{xAxis:String(missing[0])},{xAxis:String(missing.at(-1))}]]};
 if(data.current_energy.living_energy_per_capita===null)o.graphic=[{type:"text",right:16,top:22,style:{text:state.year+" 年：当前数据源缺失",fill:"#eac17a",font:'11px "Microsoft YaHei"'}}];
 options["08"]=o;
 const w=data.waterfall, labels=[String(state.base),...w.changes.map(r=>r.name),String(state.year)];
 const offsets=[],heights=[],items=[];let running=w.start/10000;
 labels.forEach((label,i)=>{
  if(i===0||i===labels.length-1){offsets.push(0);heights.push((i===0?w.start:w.end)/10000);items.push({color:"#4b7fa8"});}
  else {const change=w.changes[i-1],delta=change.delta/10000,next=running+delta;
   offsets.push(Math.min(running,next));heights.push(Math.abs(delta));items.push({color:delta>=0?"#47b69b":"#d8818a",borderWidth:change.key===state.energy?1:0,borderColor:"#dae9f0"});running=next;}
 });
 o=baseOption("亿吨标准煤");o.grid.left=49;o.grid.top=22;o.grid.bottom=35;o.legend.show=false;
 o.xAxis.data=labels;o.xAxis.boundaryGap=true;o.xAxis.axisLabel={...axis.axisLabel,interval:0,fontSize:9,formatter:v=>v==="一次电力及其他能源"?"一次电力\n及其他":v==="舍入差额"?"舍入\n差额":v};
 o.tooltip.formatter=params=>{
  const i=params[0].dataIndex;
  return esc(labels[i])+"<br>"+(i===0?fmt(w.start/10000):i===labels.length-1?fmt(w.end/10000):signed(w.changes[i-1].delta/10000,4))+" 亿吨标准煤"+(i>0&&i<labels.length-1?"（增减量）":"");
 };
 o.series=[{name:"offset",type:"bar",stack:"waterfall",silent:true,itemStyle:{color:"transparent"},emphasis:{disabled:true},data:offsets},
 {name:"增量分解",type:"bar",stack:"waterfall",barMaxWidth:30,
 data:heights.map((value,i)=>({value,itemStyle:items[i]})),label:{show:true,position:"top",fontSize:9,color:"#9bb7cb",formatter:q=>q.dataIndex===0||q.dataIndex===labels.length-1?fmt(q.value,1):signed(w.changes[q.dataIndex-1].delta/10000,2)}}];
 options["09"]=o;
 const cells=data.structure.map(r=>({value:[years.indexOf(r.year),keys.indexOf(r.energy_key),r.share_change_pp],
 itemStyle:{borderWidth:r.year===state.year?2:1,borderColor:r.year===state.year?"#eac17a":"#142738"}}));
 const max=Math.ceil(Math.max(...cells.map(r=>Math.abs(r.value[2])))*10)/10;
 options["10"]={animation:false,backgroundColor:"transparent",textStyle:{fontFamily:"Microsoft YaHei"},
 tooltip:{...tooltip,formatter:q=>years[q.value[0]]+" 年 · "+esc(data.energy_names[keys[q.value[1]]])+"<br>占比较上年变化 "+signed(q.value[2],1)+" 个百分点"},
 grid:{left:145,right:40,top:35,bottom:90},xAxis:{...axis,type:"category",data:years.map(String),splitArea:{show:true},axisLabel:{...axis.axisLabel,interval:0}},
 yAxis:{...axis,type:"category",data:keys.map(k=>data.energy_names[k]),axisLabel:{color:"#acbfd0",fontSize:11,formatter:v=>v==="一次电力及其他能源"?"一次电力\n及其他能源":v},splitArea:{show:true}},
 visualMap:{min:-max,max,left:"center",bottom:12,orient:"horizontal",calculable:false,text:["占比上升（百分点）","占比下降"],textStyle:{color:"#9db5c7"},inRange:{color:["#c87987","#25394d","#46bb9e"]}},
 series:[{name:"占比变化",type:"heatmap",data:cells,label:{show:true,fontSize:11,color:"#edf5f8",formatter:q=>signed(q.value[2],1)},emphasis:{itemStyle:{borderColor:"#eac17a",borderWidth:2}}}]};
}
function chartClick(id,params,instance=charts[id]){
 if(params.componentType!=="series")return;
 if(id==="10"){
  const y=years[params.value[0]],key=keys[params.value[1]];setState({year:y,energy:key});return;
 }
 if(id==="09"){
  const row=data.waterfall.changes[params.dataIndex-1];
  if(row&&keys.includes(row.key))setState({energy:row.key});return;
 }
 if(["01","02","03","05","06","07","08"].includes(id)){
  const y=Number(params.name),updates={};
  if(years.includes(y))updates.year=y;
  if(id==="06"){
   const key=keys.find(k=>data.energy_names[k]===params.seriesName);if(key)updates.energy=key;
   if(!years.includes(y)&&params.event&&instance){
    const index=Math.round(instance.convertFromPixel({xAxisIndex:0},params.event.offsetX));
    if(years[index])updates.year=years[index];
   }
  }
  if(Object.keys(updates).length)setState(updates);
 }
}
function setChart(id){
 if(!charts[id]){
  charts[id]=echarts.init($("chart"+id),null,{renderer:"canvas"});
  bindChartClick(id,charts[id]);
 }
 charts[id].setOption(optionFor(id,charts[id]),{notMerge:true});
}
function bindChartClick(id,chart){
 if(id!=="06"){chart.on("click",p=>chartClick(id,p,chart));return;}
 chart.getZr().on("click",event=>{
  const point=[event.offsetX,event.offsetY];
  if(!chart.containPixel({gridIndex:0},point))return;
  const value=chart.convertFromPixel({xAxisIndex:0,yAxisIndex:0},point);
  const year=years[Math.max(0,Math.min(years.length-1,Math.round(value[0])))];
  let sum=0,key=keys.at(-1);
  for(const candidate of keys){
   sum+=data.structure.find(r=>r.year===year&&r.energy_key===candidate).share_pct;
   if(value[1]<=sum){key=candidate;break;}
  }
  setState({year,energy:key});
 });
}
function optionFor(id,chart){
 if(id!=="04")return options[id];
 return {...options[id],graphic:[{type:"group",x:chart.getWidth()*.32,y:chart.getHeight()*.48,children:[
  {type:"text",style:{x:0,y:-10,text:String(state.year),fill:"#e7f1f7",font:'26px "Bahnschrift",sans-serif',align:"center",verticalAlign:"middle"}},
  {type:"text",style:{x:0,y:16,text:"年龄结构",fill:"#7f9aaf",font:'11px "Microsoft YaHei"',align:"center",verticalAlign:"middle"}}
 ]}]};
}
function resizeCharts(){
 Object.entries(charts).forEach(([id,c])=>{c.resize();if(id==="04")c.setOption(optionFor(id,c),{notMerge:true});});
 if(large){large.resize();if(largeId==="04")large.setOption(optionFor(largeId,large),{notMerge:true});}
}
function render(){
 buildOptions();years.forEach(y=>$("tick"+y)?.classList.toggle("active",y===state.year));
 $("yearRange").value=state.year;$("currentYear").textContent=state.year;
 $("baseSelect").value=state.base;[...$("baseSelect").options].forEach(o=>o.disabled=Number(o.value)>state.year);
 $("energySelect").value=state.energy;
 $("amountMode").setAttribute("aria-pressed",state.mode==="amount");$("shareMode").setAttribute("aria-pressed",state.mode==="share");
 $("filterStatus").textContent=state.year+" 年 / 基期 "+state.base+" 年";
 const p=data.current_population,bp=data.base_population,e=data.current_energy,be=data.base_energy;
 $("populationKpi").textContent=fmt(p.population_total/10000,4);
 $("urbanKpi").textContent=fmt(p.urbanization_pct,2);
 $("ageKpi").textContent=fmt(p.age_share_65_plus_pct,2);
 $("energyKpi").textContent=fmt(e.energy_total/10000,2);
 $("populationDelta").textContent="较 "+state.base+" 年 "+signed(p.population_total-bp.population_total,0)+" 万人";
 $("urbanDelta").textContent="较 "+state.base+" 年 "+signed(p.urbanization_pct-bp.urbanization_pct)+" 个百分点";
 $("ageDelta").textContent="较 "+state.base+" 年 "+signed(p.age_share_65_plus_pct-bp.age_share_65_plus_pct)+" 个百分点";
 $("energyDelta").textContent="较 "+state.base+" 年 "+signed((e.energy_total/be.energy_total-1)*100)+"%";
 $("selectedTitle").innerHTML="<span>07</span>"+esc(data.energy_names[state.energy])+(state.mode==="share"?"占比趋势":"消费趋势");
 $("selectedNote").textContent=state.mode==="share"?"单位：% · 所选能源官方占比":"亿吨标准煤 · 总量×占比的折标量估算";
 $("urbanNote").textContent=state.mode==="share"?"单位：% · 城乡人口占比（计算值）":"单位：亿人 · 城乡人口规模";
 $("ageNote").textContent=p.age_sum_difference?"分组合计与总人口相差 "+fmt(p.age_sum_difference,0)+" 万人，保留原值":"0—14 岁 / 15—64 岁 / 65 岁及以上";
 const living=data.availability.living_energy_per_capita;
 $("livingNote").textContent=e.living_energy_per_capita===null?state.year+" 年缺失 · 最近可用 "+living.last_available_year+" 年 · 不补零、不插值":"千克标准煤／人 · 官方指标；2024、2025 年缺失";
 $("livingNote").style.color=e.living_energy_per_capita===null?"#eac17a":"";
 $("waterfallNote").textContent=state.base+"→"+state.year+" · 亿吨标准煤 · 算术分解，含舍入差额";
 $("summary").textContent=data.summary;
 $("previousYear").disabled=state.year===years[0];$("nextYear").disabled=state.year===years.at(-1);
 $("methodList").innerHTML=data.notes.map(n=>"<li>"+esc(n)+"</li>").join("");
 for(let i=1;i<=9;i++){const id=String(i).padStart(2,"0");setChart(id);chartTitles[id]=document.querySelector('[data-chart="'+id+'"] h2').textContent.slice(2).trim();}
 if($("analysisDialog").open&&large){large.setOption(optionFor(largeId,large),{notMerge:true});updateDialogCaption();}
 if($("detailDialog").open)renderTable();
 $("dashboard").setAttribute("aria-busy","false");$("error").hidden=true;
 window.Dashboard.state={...state};window.Dashboard.data=data;
}
async function setState(patch,manual=true){
 if(manual)pause();
 const next={...state,...patch};next.base=Math.min(next.base,next.year);
 pending?.abort();pending=new AbortController();
 $("dashboard").setAttribute("aria-busy","true");
 try{
  const response=await fetch("/api/data?"+new URLSearchParams(next),{signal:pending.signal});
  const result=await response.json();if(!response.ok)throw new Error(result.error||"数据读取失败");
  data=result;state={...result.state};render();
 }catch(error){
  if(error.name==="AbortError")return;
  pause();$("dashboard").setAttribute("aria-busy","false");$("error").hidden=false;
  $("error").textContent="无法读取本地数据："+error.message+"。请确认 Python 服务仍在运行。";
 }
}
function pause(){
 if(timer){clearInterval(timer);timer=null;}
 $("play").textContent="▶";$("play").setAttribute("aria-label","播放年份");$("play").setAttribute("aria-pressed","false");
}
function play(){
 if(timer){pause();return;}
 if(state.year===years.at(-1))setState({year:years[0]},false);
 $("play").textContent="Ⅱ";$("play").setAttribute("aria-label","暂停播放");$("play").setAttribute("aria-pressed","true");
 timer=setInterval(()=>{if(state.year===years.at(-1)){pause();return;}setState({year:state.year+1},false);},1200);
}
function updateDialogCaption(){
 $("dialogTitle").textContent=largeId==="10"?"能源品种 × 年份变化热力图":chartTitles[largeId];
 $("dialogDescription").textContent=largeId==="10"?"占比较上年变化，单位：百分点。点击色块切换年份与能源；金色边框标记当前年份。":document.querySelector('[data-chart="'+largeId+'"] .chart-note').textContent;
}
function openChart(id){
 pause();largeId=id;
 if(!$("analysisDialog").open)$("analysisDialog").showModal();
 updateDialogCaption();
 requestAnimationFrame(()=>{
  large?.dispose();large=echarts.init($("largeChart"),null,{renderer:"canvas"});
  large.setOption(optionFor(id,large),{notMerge:true});bindChartClick(id,large);
 });
}
function tableRows(){
 const all=$("tableScope").value==="all",out=[];
 for(const [group,values] of [["人口",data.population],["能源",data.energy]]){
  for(const r of values){if(!all&&r.year!==state.year)continue;
   for(const [field,value]of Object.entries(r)){if(["year","in_display_window"].includes(field))continue;
    const meta=data.dictionary[field]||{};
    out.push([r.year,meta.label||field,value,meta.unit||"",meta.method||group]);
   }
  }
 }
 for(const r of data.selected_energy_series){
  if(!all&&r.year!==state.year)continue;
  out.push([r.year,r.energy_name+"占比",r.share_pct,"%","官方占比"]);
  out.push([r.year,r.energy_name+"折标量估算",r.amount_estimated_tce_10k,"万吨标准煤",r.method]);
  out.push([r.year,r.energy_name+"占比较上年变化",r.share_change_pp,"百分点","当年占比−上年占比"]);
 }
 return out;
}
function renderTable(){
 $("tableContext").textContent=state.year+" 年 · 基期 "+state.base+" 年 · "+data.energy_names[state.energy];
 $("detailBody").innerHTML=tableRows().map(r=>"<tr>"+r.map((v,i)=>"<td>"+(i===2?fmt(v,3):esc(v??"—"))+"</td>").join("")+"</tr>").join("");
}
function toast(message){
 clearTimeout(toastTimeout);$("toast").textContent=message;$("toast").style.display="block";
 toastTimeout=setTimeout(()=>$("toast").style.display="none",7000);
}
async function save(kind,scope="current"){
 try{
  const body={...state,kind,scope};
  if(kind==="png"){
   if(!large)throw new Error("请先打开图表");
   body.chart=largeId;body.image=large.getDataURL({type:"png",pixelRatio:2,backgroundColor:"#0d1c2b"});
  }
  const response=await fetch("/api/save",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const result=await response.json();if(!response.ok)throw new Error(result.error);
  toast("已保存："+result.saved);
 }catch(error){toast("导出失败："+error.message);}
}
years.forEach(y=>{
 const option=new Option(y+" 年",y);$("baseSelect").append(option);
 const tick=document.createElement("button");tick.textContent=y;tick.id="tick"+y;tick.title="切换至 "+y+" 年";tick.onclick=()=>setState({year:y});$("yearTicks").append(tick);
});
for(const [key,label]of Object.entries({coal:"煤炭",oil:"石油",gas:"天然气",primary_electricity_other:"一次电力及其他能源"}))$("energySelect").append(new Option(label,key));
$("baseSelect").onchange=e=>setState({base:Number(e.target.value)});
$("energySelect").onchange=e=>setState({energy:e.target.value});
$("amountMode").onclick=()=>setState({mode:"amount"});$("shareMode").onclick=()=>setState({mode:"share"});
$("yearRange").oninput=e=>{pause();clearTimeout(sliderTimeout);const year=Number(e.target.value);sliderTimeout=setTimeout(()=>setState({year}),60);};
$("previousYear").onclick=()=>setState({year:Math.max(years[0],state.year-1)});
$("nextYear").onclick=()=>setState({year:Math.min(years.at(-1),state.year+1)});
$("play").onclick=play;
$("reset").onclick=()=>setState({year:2025,base:2011,energy:"coal",mode:"amount"});
$("heatButton").onclick=()=>openChart("10");
document.querySelectorAll("[data-expand]").forEach(button=>button.onclick=()=>openChart(button.dataset.expand));
document.querySelectorAll("[data-close]").forEach(button=>button.onclick=()=>$(button.dataset.close).close());
$("analysisDialog").addEventListener("close",()=>{large?.dispose();large=null;largeId=null;});
$("methodButton").onclick=()=>{pause();$("methodDialog").showModal();};
$("detailButton").onclick=()=>{pause();renderTable();$("detailDialog").showModal();};
$("tableScope").onchange=renderTable;
$("exportButton").onclick=()=>save("csv");
$("saveTableCsv").onclick=()=>save("csv",$("tableScope").value);
$("saveState").onclick=()=>save("json");
$("savePng").onclick=()=>save("png");
$("fullscreen").onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{toast("当前浏览器未允许全屏，可使用 F11。");}};
const resize=new ResizeObserver(resizeCharts);
resize.observe($("dashboard"));window.addEventListener("resize",resizeCharts);
window.Dashboard={state:{...state},charts,data:null,setState,options};
setState({},false);
})();
