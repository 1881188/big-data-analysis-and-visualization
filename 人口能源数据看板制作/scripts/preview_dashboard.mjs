import {chromium} from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const out=path.join(root,"outputs/dashboard");
await fs.mkdir(out,{recursive:true});
const context=await chromium.launchPersistentContext(path.join(out,"browser-profile"),{
 executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
 headless:true,viewport:{width:1920,height:1080},deviceScaleFactor:1,acceptDownloads:false
});
const page=await context.newPage(), errors=[];
page.on("pageerror",e=>errors.push(e.message));
await page.goto("http://127.0.0.1:8765/",{waitUntil:"networkidle"});
await page.waitForFunction(()=>window.Dashboard?.data&&document.querySelector("#dashboard").getAttribute("aria-busy")==="false");
await page.screenshot({path:path.join(out,"看板_1920x1080.png"),fullPage:true});
const info=await page.evaluate(()=>({
 title:document.title,charts:Object.keys(window.Dashboard.charts).length,
 height:document.querySelector("#dashboard").getBoundingClientRect().height,
 width:document.documentElement.scrollWidth,viewport:innerWidth,
 chartSizes:[...document.querySelectorAll(".chart")].map(e=>[e.id,e.clientWidth,e.clientHeight])
}));
console.log(JSON.stringify({info,errors},null,2));
for(let n=1;n<=10;n++){
 const id=String(n).padStart(2,"0");
 await page.locator(n===10?"#heatButton":'[data-expand="'+id+'"]').click();
 await page.waitForTimeout(100);
 await page.locator("#analysisDialog").screenshot({path:path.join(out,"chart_"+id+".png")});
 await page.locator('[data-close="analysisDialog"]').click();
}
await context.close();
