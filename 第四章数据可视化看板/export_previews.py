from PIL import Image,ImageDraw,ImageFont
from matplotlib.backends.backend_agg import FigureCanvasAgg
from data_model import ROOT,get_data
from charts import render_component,render_dashboard
import json

def save(fig,path):
    FigureCanvasAgg(fig); fig.savefig(path,dpi=100,facecolor=fig.get_facecolor()); fig.clear()

def compare(left,right,path,label='Python复现'):
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    out=Image.new('RGB',(left.width+right.width,max(left.height,right.height)+38),'#eeeeee')
    # Excel's transparent component PNGs are flattened onto their true dashboard panel.
    out.paste(left,(0,38)); out.paste(right,(left.width,38))
    draw=ImageDraw.Draw(out); draw.text((8,6),'Excel原图',fill='black',font=font)
    draw.text((left.width+8,6),label,fill='black',font=font); out.save(path)

def reference(path):
    im=Image.open(path).convert('RGBA'); bg=Image.new('RGBA',im.size,'#2c3560'); bg.alpha_composite(im)
    return bg.convert('RGB')

def main():
    output=ROOT/'输出'; comparisons=ROOT/'逐图对照'; pieces=output/'组件'
    for p in (output,comparisons,pieces):p.mkdir(parents=True,exist_ok=True)
    for kind,count in [('hr',6),('sales',11)]:
        prefix='HR' if kind=='hr' else 'Sales'; sheet='202203人员基础信息' if kind=='hr' else '数据大屏'
        for i in range(count):
            name=f'{prefix}_{i+1:02d}.png'; path=pieces/name
            save(render_component(kind,i),path)
            left=reference(ROOT/'Excel参考图'/f'{prefix}_{sheet}_{i+1}.png')
            compare(left,Image.open(path).convert('RGB'),comparisons/name,
                    'Python（学历人数已纠正）' if kind=='hr' and i==4 else 'Python复现')
        path=output/('人力资源看板.png' if kind=='hr' else '销售看板_09月.png')
        save(render_dashboard(kind),path)
        ref=reference(ROOT/'Excel参考图'/f'{prefix}_整屏.png')
        ref=ref.crop((1,1,1201,651)) if kind=='hr' else ref.crop((1,29,1729,1121))
        compare(ref,Image.open(path).convert('RGB'),comparisons/f'{prefix}_整体.png')
    for month in [1,2,12]:save(render_dashboard('sales',month),output/f'销售看板_{month:02d}月.png')
    data=get_data()
    (output/'默认指标.json').write_text(json.dumps({'hr':data.hr(),'sales':data.sales(9)},ensure_ascii=False,indent=2),encoding='utf8')
    print('Exported 17 components, 17 comparisons, 2 whole-dashboard comparisons and 4 monthly sales views.')

if __name__=='__main__':main()
