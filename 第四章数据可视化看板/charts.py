"""Original-style dashboard panels drawn with Matplotlib, no screenshot backgrounds."""
import math
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Wedge,Rectangle,FancyBboxPatch,Circle,Polygon
from matplotlib.font_manager import FontProperties
from matplotlib.colors import LinearSegmentedColormap
from data_model import get_data,AGE_LABELS,EDUCATION,DEPARTMENTS,REGIONS,COURIERS,CATEGORIES,COSTS

HR_BG='#2c3b79'; HR_PANEL='#1d244a'; SALES_BG='#1a1e43'; SALES_PANEL='#2c3560'
WHITE='#f2f2f2'; CYAN='#7bbdd5'; PINK='#fc6c9d'; BLUE='#4a5bd1'; LIGHT='#7ad5fe'
FONT=FontProperties(family='Microsoft YaHei')
HR_SIZES=[(361,220),(361,220),(368,312),(368,220),(361,312),(361,312)]
SALES_SIZES=[(245,194),(249,194),(249,194),(245,194),(551,265),(553,265),(554,236),(553,324),(548,383),(554,293),(554,324)]
HR_POS=[(24,70),(807,70),(411,313),(412,70),(26,313),(806,313)]
SALES_POS=[(44,592),(311,804),(312,594),(44,802),(1152,745),(1152,466),(589,128),(1152,128),(28,128),(589,377),(589,686)]

def txt(ax,x,y,s,size=16,ha='left',bold=False,color=WHITE):
    prop=FONT.copy(); prop.set_size(size*.72); prop.set_weight('bold' if bold else 'normal')
    return ax.text(x,y,str(s),ha=ha,va='center',fontproperties=prop,color=color,zorder=8)

def rect(ax,x,y,w,h,color): return ax.add_patch(Rectangle((x,y),w,h,color=color,lw=0,zorder=1))

def rounded(ax,x,y,w,h,color,radius=20,lw=1.5):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={radius}',fill=False,edgecolor=color,lw=lw,zorder=6))

def ring(ax,cx,cy,r,width,values,colors):
    total=sum(values); start=-90
    if total<=0: return
    for v,color in zip(values,colors):
        angle=360*v/total
        ax.add_patch(Wedge((cx,cy),r,start,start+angle,width=width,facecolor=color,edgecolor='none',zorder=3))
        start+=angle

def pie_labels(ax,cx,cy,r,values):
    start=-90; total=sum(values)
    raw=np.array(values)*100/total
    displayed=np.floor(raw).astype(int)
    for index in np.argsort(-(raw-displayed),kind='stable')[:100-int(displayed.sum())]: displayed[index]+=1
    for v,percent in zip(values,displayed):
        angle=360*v/total; a=math.radians(start+angle/2)
        txt(ax,cx+r*math.cos(a),cy+r*math.sin(a),f'{percent}%',14,ha='center')
        start+=angle

def legend(ax,x,y,labels,colors,gap=31):
    for i,(label,color) in enumerate(zip(labels,colors)):
        rect(ax,x,y+i*gap-4,9,9,color); txt(ax,x+12,y+i*gap,label,14)

def figure(size,bg):
    w,h=size; return Figure(figsize=(np.nextafter(w/100,np.inf),np.nextafter(h/100,np.inf)),dpi=100,facecolor=bg)

def axes(fig,box,size,bg):
    x,y,w,h=box; fw,fh=fig.get_size_inches()*fig.dpi
    ax=fig.add_axes([x/fw,1-(y+h)/fh,w/fw,h/fh],facecolor=bg)
    ax.set(xlim=(0,size[0]),ylim=(size[1],0)); ax.set_aspect('equal',adjustable='box'); ax.axis('off')
    rect(ax,0,0,*size,bg)
    return ax

def hr_panel(ax,index,d):
    w,h=HR_SIZES[index]
    if index in (0,1,3):
        key,title,colors,labels,cx=(
            ('age','年龄',['#00b0f0','#ed7d31',LIGHT,'#f4aa27','#0070c0'],AGE_LABELS,141) if index==0 else
            ('marriage','婚姻状况',['#f4aa27','#0070c0',LIGHT],['单身','已婚','离异'],147) if index==1 else
            ('gender','性别',['#f4aa27','#0070c0'],['男','女'],157))
        txt(ax,w/2,33,title,22,ha='center',bold=True)
        ring(ax,cx,137,51.5,13,d[key],colors); pie_labels(ax,cx,137,71,d[key])
        legend(ax,280 if index==0 else 301 if index==1 else 322,69 if index==0 else 106 if index==1 else 121,labels,colors)
    elif index==2:
        txt(ax,w/2,38,f"总人数：{d['total']}",24,ha='center',bold=True)
        txt(ax,w/2,90,'入转调',22,ha='center',bold=True)
        for x,label,v in zip([77,184,291],['入职','转入','转出'],d['changes']):
            height=v*113/40; rect(ax,x-17,264-height,34,height,LIGHT)
            txt(ax,x,244-height,v,14,ha='center'); txt(ax,x,287,label,14,ha='center')
    else:
        is_edu=index==4; values=d['education'] if is_edu else d['departments']
        labels=EDUCATION if is_edu else DEPARTMENTS
        txt(ax,w/2,33,'学历' if is_edu else '部门',22,ha='center',bold=True)
        for i,(label,v) in enumerate(zip(labels,values)):
            y=(268-i*43) if is_edu else (272-i*36)
            length=v*(173/572 if is_edu else 193/799)
            txt(ax,83,y,label,14,ha='right'); rect(ax,97,y-7,length,14 if is_edu else 12,LIGHT)
            txt(ax,110+length,y,v,14)

def sales_panel(ax,index,d):
    w,h=SALES_SIZES[index]
    if index in (0,1,2,3):
        ci={0:0,1:3,2:1,3:2}[index]; label=COSTS[ci]; value=d['costs'][ci]
        share=value/d['cost_total'] if d['cost_total'] else 0
        rounded(ax,1,1,w-2,h-2,CYAN)
        txt(ax,76,35,label,22,ha='center')
        ring(ax,73,121,43,7,[share,1-share],[CYAN,'#555d83'])
        txt(ax,73,121,f'{share:.2%}',16,ha='center')
        txt(ax,143,77,label+'费用',16); txt(ax,143,101,'合计',16)
        txt(ax,143,138,f'{value:.2f}',19)
    elif index in (4,5):
        vals=d['couriers'] if index==4 else d['regions']; labels=COURIERS if index==4 else REGIONS
        txt(ax,w/2,37,'快递公司销量' if index==4 else '区域销量',25,ha='center')
        top=max(400,math.ceil(max(vals)/100)*100)
        for x,label,v in zip(np.linspace(64,487,6),labels,vals):
            height=v*133/top; rect(ax,x-13,214-height,26,height,PINK if index==4 else CYAN)
            txt(ax,x,194-height,v,16,ha='center'); txt(ax,x,240,label,16,ha='center')
    elif index==6:
        txt(ax,w/2,38,'销量环比',25,ha='center')
        if d['previous'] is None:
            rect(ax,54,106,340,22,CYAN); txt(ax,420,117,d['count'],16,ha='right')
            txt(ax,10,117,f"{d['month']}月",16); txt(ax,277,179,'无上年12月数据，环比不可计算',17,ha='center')
        else:
            low=min(d['count'],d['previous']); high=max(d['count'],d['previous'])
            # Preserve Excel's shortened comparison axis (9月 default: 680..760).
            base=max(0,math.floor((low-(high-low)*.5)/20)*20)
            top=max(base+20,math.ceil(high/20)*20)
            for y,value,label,color in [(117,d['count'],f"{d['month']}月",CYAN),(182,d['previous'],f"{d['month']-1}月",BLUE)]:
                length=(value-base)/(top-base)*383
                rect(ax,54,y-11,length,22,color); txt(ax,54+length+12,y,value,16)
                txt(ax,10,y,label,16)
            txt(ax,512,114,f"{d['mom']:.2%}",25,ha='right',bold=True)
            txt(ax,480,173,'环比',20,ha='center')
    elif index==7:
        txt(ax,w/2,38,'各月销售额(万)',25,ha='center')
        xs=np.linspace(80,514,12); ys=273-np.array(d['trend'])*192/200
        verts=[(80,273),*zip(xs,ys),(514,273)]
        poly=Polygon(verts,closed=True,facecolor='none',edgecolor='none'); ax.add_patch(poly)
        cmap=LinearSegmentedColormap.from_list('area',[BLUE,'#333e73'])
        im=ax.imshow(np.linspace(0,1,256).reshape(-1,1),extent=(80,514,273,80),cmap=cmap,aspect='auto',zorder=2)
        im.set_clip_path(poly)
        for value in [0,50,100,150,200]: txt(ax,63,273-value*192/200,f'{value:.2f}',16,ha='right')
        for x,month in zip(xs,range(1,13)): txt(ax,x,300,f'{month}月',16,ha='center')
    elif index==8:
        txt(ax,w/2,38,'产品类别销量',25,ha='center')
        ring(ax,192,230,112,17,d['category'],[PINK,BLUE,'#f6a576'])
        pie_labels(ax,192,230,143,d['category'])
        txt(ax,192,224,d['count'],44,ha='center'); txt(ax,192,281,'总销量',21,ha='center')
        legend(ax,413,168,CATEGORIES,[PINK,BLUE,'#f6a576'],gap=64)
    elif index==9:
        txt(ax,w/2,37,'商品销售额Top3',25,ha='center')
        txt(ax,193,93,'产品',17,ha='center'); txt(ax,383,93,'销售额(万)',17,ha='center'); txt(ax,454,93,'销量',17,ha='center')
        for i,p in enumerate(d['top3']):
            y=139+i*56; color=['#ffd13d','#b8dffc','#eea064'][i]
            rect(ax,74,y-25,12,18,color); rect(ax,71,y-25,18,2,'#161933')
            ax.add_patch(Circle((80,y-2),11,facecolor=color,edgecolor=WHITE,lw=1.2,zorder=4))
            txt(ax,80,y-2,i+1,18,ha='center',color='#263153')
            # Long product names wrap; never silently truncate labels.
            name=p['name']; name=name if len(name)<29 else name[:27]+'\n'+name[27:]
            txt(ax,151,y-2,name,15)
            rect(ax,343,y-17,53,33,BLUE); txt(ax,369,y,p['amount'].__format__('.2f'),16,ha='center')
            txt(ax,441,y,p['count'],16,ha='center')
    else:
        margin=d['margin']; share=max(0,min(1,margin)) if margin is not None else 0
        ring(ax,154,138,92,14,[share,1-share],[PINK,'#555d83'])
        txt(ax,154,132,f'{margin:.2%}' if margin is not None else '无数据',41,ha='center')
        txt(ax,154,174,'利润率',20,ha='center')
        txt(ax,351,114,'利润额(万)',17,ha='center'); txt(ax,351,141,'/',19,ha='center')
        txt(ax,351,169,'销售额(万)',17,ha='center')
        txt(ax,444,112,f"{d['profit']:.2f}",26,ha='center',bold=True,color=PINK)
        txt(ax,444,174,f"{d['amount']:.2f}",26,ha='center',bold=True,color=PINK)
        rounded(ax,162,252,214,58,BLUE,17,2)
        txt(ax,269,281,'利润额占比销售额',25,ha='center')

def render_component(kind,index,month=9,data=None):
    data=data or get_data(); sizes=HR_SIZES if kind=='hr' else SALES_SIZES
    bg=HR_PANEL if kind=='hr' else SALES_PANEL; w,h=sizes[index]
    fig=figure((w,h),bg); ax=axes(fig,(0,0,w,h),(w,h),bg)
    (hr_panel if kind=='hr' else sales_panel)(ax,index,data.hr() if kind=='hr' else data.sales(month))
    ax.set_aspect('equal',adjustable='box'); return fig

def render_dashboard(kind='hr',month=9,data=None):
    if kind not in ('hr','sales'): raise ValueError('未知看板')
    data=data or get_data(); hr=kind=='hr'
    size=(1200,650) if hr else (1728,1092); bg=HR_BG if hr else SALES_BG
    fig=figure(size,bg); ax=axes(fig,(0,0,*size),size,bg)
    if hr: txt(ax,600,36,'公司人员结构看板',28,ha='center',bold=True)
    else:
        rect(ax,32,11,1674,106,SALES_PANEL); rect(ax,28,1019,1678,59,SALES_PANEL)
        txt(ax,51,61,'公司销售数据可视化看板',39,bold=True)
        txt(ax,1590,83,f'{month}月',25,ha='center')
        rect(ax,28,527,548,483,SALES_PANEL); txt(ax,302,560,'成本费用',26,ha='center')
    sizes=HR_SIZES if hr else SALES_SIZES; positions=HR_POS if hr else SALES_POS
    values=data.hr() if hr else data.sales(month)
    for i,((w,h),(x,y)) in enumerate(zip(sizes,positions)):
        a=axes(fig,(x,y,w,h),(w,h),HR_PANEL if hr else SALES_PANEL)
        (hr_panel if hr else sales_panel)(a,i,values); a.set_aspect('equal',adjustable='box')
    return fig
