import {chromium} from "playwright";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),".."),out=path.join(root,"outputs/dashboard");
await fs.mkdir(out,{recursive:true});
const context=await chromium.launchPersistentContext(path.join(out,"browser-profile"),{
 executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
 headless:true,viewport:{width:1920,height:1080},deviceScaleFactor:1,acceptDownloads:false
});
const page=await context.newPage(),errors=[],external=[];
page.on("pageerror",e=>errors.push(e.message));
page.on("request",r=>{if(!r.url().startsWith("http://127.0.0.1:8765/"))external.push(r.url());});
const ready=()=>page.waitForFunction(()=>window.Dashboard?.data&&document.querySelector("#dashboard").getAttribute("aria-busy")==="false");
const wait=async(key,value)=>{await page.waitForFunction(([k,v])=>window.Dashboard?.state[k]===v&&document.querySelector("#dashboard").getAttribute("aria-busy")==="false",[key,value]);};
async function clickPoint(id,year,seriesIndex=0){
 const xy=await page.evaluate(({id,year,seriesIndex})=>{
  const chart=window.Dashboard.charts[id],index=window.Dashboard.data.years.indexOf(year),raw=chart.getOption().series[seriesIndex].data[index];
  let value=typeof raw==="object"?raw.value:raw;
  if(id==="06")value=chart.getOption().series.slice(0,seriesIndex).reduce((s,r)=>s+Number(r.data[index]),0)+value/2;
  return chart.convertToPixel({seriesIndex},[String(year),value]);
 },{id,year,seriesIndex});
 const box=await page.locator("#chart"+id).boundingBox();
 await page.mouse.click(box.x+xy[0],box.y+xy[1]);
}
async function saveClick(selector){
 const responsePromise=page.waitForResponse(r=>r.url().endsWith("/api/save")&&r.request().method()==="POST");
 await page.locator(selector).click();
 const response=await responsePromise;
 assert.equal(response.status(),200);
 const result=await response.json();
 assert(result.saved.startsWith("outputs/dashboard/exports/"));
 const target=path.join(root,result.saved);assert((await fs.stat(target)).size>0);
 return target;
}
const passed=[];
try{
 await page.goto("http://127.0.0.1:8765/",{waitUntil:"networkidle"});await ready();
 assert.equal(await page.locator(".chart-card").count(),9);
 const bounds=await page.locator("#dashboard").boundingBox();
 assert(bounds.height<=1080,"1080p dashboard should fit the viewport");
 assert.equal(await page.locator("#populationKpi").textContent(),"14.0489");
 await page.screenshot({path:path.join(out,"看板_1920x1080.png"),fullPage:true});
 passed.push("9张主屏图、1080p完整布局与默认指标");
 for(const year of [2024,2025]){
  await page.locator("#tick"+year).click();await wait("year",year);
  assert((await page.locator("#livingNote").textContent()).includes(year+" 年缺失"));
  assert(await page.evaluate(()=>window.Dashboard.options["08"].series[0].data.slice(-2).every(r=>r.value===null)));
  assert.equal(await page.evaluate(()=>window.Dashboard.options["08"].series[0].connectNulls),false);
  assert.equal(await page.evaluate(()=>window.Dashboard.data.current_energy.living_energy_per_capita),null);
  await page.locator("#detailButton").click();
  const livingRow=page.locator("#detailBody tr").filter({hasText:"人均生活能源消费量"});
  assert.equal(await livingRow.locator("td").nth(2).textContent(),"—");
  const exported=await saveClick("#saveState"),savedMissing=JSON.parse(await fs.readFile(exported,"utf8"));
  assert.equal(savedMissing.current_energy.living_energy_per_capita,null);
  await page.locator('[data-close="detailDialog"]').click();
  await page.evaluate(()=>document.querySelector("#toast").style.display="none");
  await page.screenshot({path:path.join(out,"看板_"+year+"缺失提示.png"),fullPage:true});
 }
 passed.push("2024/2025最新数据正常显示，人均缺失保持断点、明细横杠和JSON空值");
 const initialPop=await page.evaluate(()=>JSON.stringify(window.Dashboard.data.current_population));
 await page.locator("#energySelect").selectOption("gas");await wait("energy","gas");
 assert.equal(await page.evaluate(()=>JSON.stringify(window.Dashboard.data.current_population)),initialPop);
 assert((await page.locator("#selectedTitle").textContent()).includes("天然气"));
 passed.push("能源类别只联动能源分析");
 await page.locator("#shareMode").click();await wait("mode","share");
 assert.equal(await page.evaluate(()=>window.Dashboard.options["03"].yAxis.max),100);
 assert((await page.locator("#selectedNote").textContent()).includes("%"));
 await page.locator("#amountMode").click();await wait("mode","amount");
 passed.push("数量/占比切换");
 await page.locator("#tick2018").click();await wait("year",2018);
 assert((await page.locator("#ageNote").textContent()).includes("-1"));
 await page.screenshot({path:path.join(out,"看板_2018舍入提示.png"),fullPage:true});
 await page.locator("#baseSelect").selectOption("2018");await wait("base",2018);
 await page.locator("#tick2012").click();await wait("year",2012);
 assert.equal(await page.evaluate(()=>window.Dashboard.state.base),2012);
 assert(await page.evaluate(()=>window.Dashboard.data.waterfall.changes.every(r=>r.delta===0)));
 passed.push("年龄舍入提示、基期约束与同年零变化");
 await page.locator("#reset").click();await wait("year",2025);
 const xy=await page.evaluate(()=>window.Dashboard.charts["01"].convertToPixel({seriesIndex:0},["2015",window.Dashboard.data.population.find(r=>r.year===2015).population_total/10000]));
 const box=await page.locator("#chart01").boundingBox();
 await page.mouse.move(box.x+xy[0],box.y+xy[1]);await page.waitForTimeout(150);
 assert.equal(await page.evaluate(()=>window.Dashboard.state.year),2025);
 await clickPoint("01",2015);await wait("year",2015);
 passed.push("悬停不改变状态，实际点击折线确定年份");
 await page.locator("#reset").click();await wait("year",2025);
 await clickPoint("06",2017,1);await wait("year",2017);await wait("energy","oil");
 passed.push("点击能源结构图同时联动年份与品种");
 await page.locator("#heatButton").click();await page.waitForTimeout(100);
 const heat=await page.evaluate(()=>echarts.getInstanceByDom(document.getElementById("largeChart")).convertToPixel({seriesIndex:0},[8,2]));
 const hb=await page.locator("#largeChart").boundingBox();
 await page.mouse.click(hb.x+heat[0],hb.y+heat[1]);await wait("year",2019);await wait("energy","gas");
 const png=await saveClick("#savePng");
 assert.equal((await fs.readFile(png)).subarray(0,8).toString("hex"),"89504e470d0a1a0a");
 await page.locator("#analysisDialog").screenshot({path:path.join(out,"热力图_点击联动.png")});
 await page.locator('[data-close="analysisDialog"]').click();
 passed.push("热力图实际点击联动与PNG本地导出");
 await page.locator("#detailButton").click();
 assert((await page.locator("#tableContext").textContent()).includes("2019"));
 const csv=await saveClick("#saveTableCsv"),text=await fs.readFile(csv,"utf8");
 assert(text.includes("2019")&&text.includes("国家统计局"));
 await page.locator("#tableScope").selectOption("all");
 assert(await page.locator("#detailBody tr").count()>500);
 const jsonPath=await saveClick("#saveState"),saved=JSON.parse(await fs.readFile(jsonPath,"utf8"));
 assert.equal(saved.state.energy,"gas");assert.equal(saved.state.year,2019);
 await page.locator("#detailDialog").screenshot({path:path.join(out,"数据明细_完整15年.png")});
 await page.locator('[data-close="detailDialog"]').click();
 passed.push("明细表范围、CSV和带筛选条件的JSON导出");
 await page.locator("#yearRange").focus();await page.keyboard.press("Home");await wait("year",2011);
 assert(await page.locator("#previousYear").isDisabled());
 await page.locator("#play").click();
 await page.waitForFunction(()=>window.Dashboard.state.year>=2012);
 await page.locator("#play").click();
 const stopped=await page.evaluate(()=>window.Dashboard.state.year);
 await page.waitForTimeout(1450);assert.equal(await page.evaluate(()=>window.Dashboard.state.year),stopped);
 await page.locator("#nextYear").click();await wait("year",stopped+1);
 await page.locator("#previousYear").click();await wait("year",stopped);
 passed.push("时间轴键盘操作、播放、暂停与前后切换");
 for(const year of Array.from({length:15},(_,i)=>2011+i)){
  await page.locator("#tick"+year).click();await wait("year",year);
  assert(await page.evaluate(()=>["01","02","03","05","06","07","08"].every(id=>window.Dashboard.options[id].series.every(s=>s.data.length===15))));
 }
 passed.push("全部15年实际切换，趋势历史始终保留");
 await page.locator("#reset").click();await wait("year",2025);
 for(let n=1;n<=10;n++){
  const id=String(n).padStart(2,"0");
  await page.locator(n===10?"#heatButton":'[data-expand="'+id+'"]').click();
  await page.waitForTimeout(80);
  await page.locator("#analysisDialog").screenshot({path:path.join(out,"chart_"+id+".png")});
  await page.locator('[data-close="analysisDialog"]').click();
 }
 passed.push("十图独立预览");
 await page.locator("#fullscreen").click();
 await page.waitForFunction(()=>document.fullscreenElement!==null);
 await page.locator("#fullscreen").click();await page.waitForFunction(()=>document.fullscreenElement===null);
 passed.push("全屏进入与退出");
 for(const [width,height,name] of [[1366,768,"看板_1366x768"],[390,844,"看板_手机宽度"]]){
  await page.setViewportSize({width,height});await page.waitForTimeout(100);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),"No horizontal page overflow at "+width);
  assert(await page.evaluate(()=>[...document.querySelectorAll(".chart")].every(e=>e.clientWidth>0&&e.clientHeight>100)));
  await page.screenshot({path:path.join(out,name+".png"),fullPage:true});
 }
 passed.push("1366px和390px布局、图表尺寸及横向溢出检查");
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 passed.push("浏览器无脚本错误、无外部资源请求");
 await fs.writeFile(path.join(out,"browser_test_results.json"),JSON.stringify({passed,errors,external},null,2));
 console.log(JSON.stringify({passed,errors,external},null,2));
}finally{await context.close();}
