"""Pixel-aligned Matplotlib reconstructions; controls live outside the chart."""
import math
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Wedge, Circle, Rectangle
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.font_manager import FontProperties
from data_model import get_data, default_state, EDUCATION

BG = '#1a1e43'
WHITE = '#ffffff'
COLORS = ['#7030a0', '#0070c0', '#37a2da', '#11a7ad', '#f5c353', '#e74e69']
SIZES = [(732,535), (728,420), (730,563), (828,592), (854,578), (730,537), (714,513)]
FONT = FontProperties(family='Microsoft YaHei')
BODY = FontProperties(family='DengXian')

def text(ax, x, y, value, size=16, bold=False, align='left', color=WHITE, body=False):
    prop = (BODY if body else FONT).copy()
    prop.set_size(size * 0.72)
    prop.set_weight('bold' if bold else 'normal')
    return ax.text(x,y,str(value),fontproperties=prop,color=color,ha=align,va='center',zorder=8)

def base(case):
    w,h = SIZES[case]
    # Agg truncates fractional pixel dimensions; nextafter avoids 828 -> 827.
    fig = Figure(figsize=(np.nextafter(w/100,np.inf),np.nextafter(h/100,np.inf)),dpi=100,facecolor=BG)
    ax = fig.add_axes([0,0,1,1],facecolor=BG)
    ax.set(xlim=(0,w),ylim=(h,0)); ax.axis('off')
    return fig,ax

def rect(ax,x,y,w,h,color):
    return ax.add_patch(Rectangle((x,y),w,h,facecolor=color,edgecolor='none',zorder=3))

def arc(ax,cx,cy,r,width,angle,color):
    ax.add_patch(Wedge((cx,cy),r,-90,-90+angle,width=width,facecolor=color,edgecolor=BG,linewidth=0,zorder=3))

def note(ax,y,value='*注：数据来源公司销售系统',x=55):
    text(ax,x,y,value,16,body=True)

def nice_top(maximum, step):
    return max(step, math.ceil(maximum/step)*step)

def render(case, state=None, data=None):
    data = data or get_data()
    state = default_state(case) if state is None else state
    fig,ax = base(case)
    FUNCTIONS[case](ax,data,state)
    ax.set_aspect('equal',adjustable='box')
    return fig

def bars(ax,d,s):
    text(ax,55,65,'2022年上半年各区域销售情况',36,True)
    values=d.sales[s['index']]; top=nice_top(max(values),200)
    for value in range(0,top+1,200):
        y=440-291*value/top
        ax.plot([101,688],[y,y],color='#444764',lw=.6,ls=(0,(7,5)),zorder=1)
        text(ax,85,y,value,16,align='right')
    for i,(name,value) in enumerate(zip(d.regions,values)):
        x=150+i*97.4
        rect(ax,x-19.5,440-291*value/top,39,291*value/top,'#0097e0')
        text(ax,x,463,name,20,align='center',body=True)
    note(ax,504)

def runway(ax,d,s):
    values=[r[s['index']] for r in d.staff]; total=sum(values)
    for i,value in enumerate(values):
        arc(ax,329,182,94+i*16.8,11,720*value/total,COLORS[i])
    note(ax,388,'*注：数据来源公司人力资源系统',59)

def nightingale(ax,d,s):
    text(ax,52,64,'2022年6月30日流量来源分布',36,True)
    values=d.traffic[s['index']]
    colors=['#4a5bd1','#6073f3','#11a7ad','#ffc000','#e66b4c']
    # Five constant-ranked radii match the source's layered doughnut construction.
    radii=[160,147,135,122,110]; cx,cy=369,307; start=-90
    label_pos=[(564,195,'left'),(461,483,'center'),(171,399,'center'),(174,225,'center'),(222,160,'center')]
    line_ends=[(663,189),(549,517),(114,451),(107,257),(158,173)]
    elbows=[(554,189),(446,517),(222,451),(215,257),(270,173)]
    anchors=[(526,226),(426,481),(262,418),(240,294),(294,210)]
    for i,(name,value,r,color) in enumerate(zip(d.traffic_names,values,radii,colors)):
        end=start+value*360
        ax.add_patch(Wedge((cx,cy),r,start,end,width=r-84,facecolor=color,edgecolor='none'))
        for rr in np.arange(96,r,13):
            ax.add_patch(Wedge((cx,cy),rr,start,end,width=.35,facecolor=BG,alpha=.23,edgecolor='none'))
        # Source leader lines are manual shapes, not auto-routed chart labels.
        point=anchors[i]
        elbow=elbows[i]; dest=line_ends[i]
        ax.plot([point[0],elbow[0],dest[0]],[point[1],elbow[1],dest[1]],color=color,lw=.7)
        ax.add_patch(Circle(point,4,color=color,zorder=5))
        x,y,ha=label_pos[i]; text(ax,x,y,f'{name}, {value:.0%}',19,align=ha,body=True)
        start=end
    note(ax,523,'*注：数据来源公司网站',43)
    ax.add_patch(Rectangle((1,1),728,561,fill=False,edgecolor='#dddddd',lw=1))

def combo(ax,d,s):
    text(ax,69,64,'2022年化妆品销售情况',40,True,body=True)
    xs=np.array([130,318,505,693]); visible=s['visible']
    ax.plot([37,787],[490,490],color='#303451',lw=.8)
    for i,x in enumerate(xs):
        for enabled,values,offset,color in [(visible[0],d.amount,-48,'#0070c0'),(visible[1],d.profit,5,'#e74e69')]:
            if enabled:
                v=values[i]; y=490-v*240/2800
                rect(ax,x+offset,y,42,490-y,color)
                text(ax,x+offset+21,y+20,v,16,align='center')
        text(ax,x,516,d.products[i],21,align='center',body=True)
    if visible[2]:
        # Excel secondary axis: min=-1, max=1; primary axis: 0..4000.
        ys=490-(np.array(d.margin)+1)*(240/2800*4000)/2
        ax.plot(xs,ys,color='#ffc000',lw=2,zorder=6)
        for x,y,v in zip(xs,ys,d.margin): text(ax,x,y-25,f'{v:.0%}',16,align='center')
    if not any(visible): text(ax,414,300,'请勾选至少一个指标',24,align='center')
    note(ax,563,x=58)

def salaries(ax,d,s):
    text(ax,49,73,'各学历平均工资情况',36,True)
    values=d.salaries(s['departments'])
    top=max(10000,nice_top(max((v for v in values if v is not None),default=0),2500))
    for fraction in [.25,.5,.75,1]:
        y=475-323*fraction
        ax.plot([56,794],[y,y],color='#60617c',lw=.8,ls=(0,(12,5)),zorder=1)
    ax.plot([56,794],[475,475],color='#61637f',lw=.8)
    cmap=LinearSegmentedColormap.from_list('salary',['#0070c0','#00b0f0'])
    for i,(name,v) in enumerate(zip(EDUCATION,values)):
        x=130+i*147.5
        if v is not None:
            y=475-v*323/top
            ax.imshow(np.linspace(0,1,256).reshape(-1,1),cmap=cmap,extent=(x-23,x+23,475,y),aspect='auto',zorder=3)
            text(ax,x,y-19,f'{v:.2f}',16,align='center')
        else: text(ax,x,450,'无数据',15,align='center',color='#b9bbcf')
        text(ax,x,501,name,21,align='center',body=True)
    for x in np.linspace(56,794,6): ax.plot([x,x],[475,482],color='#61637f',lw=.8)
    if not s['departments']: text(ax,427,210,'请选择部门',24,align='center')
    note(ax,545,'注：数据来源于人力资源管理系统，统计日期截至2022.03.31',38)

def jade(ax,d,s):
    text(ax,182,59,'流量来源分布',36,True)
    colors=['#00b0f0','#11a7ad','#ffc000','#e74e69']; cx,cy=352,296
    for i,(name,value) in enumerate(zip(d.jade_names,d.jade[s['index']])):
        r=89+28*i
        arc(ax,cx,cy,r,25,720*value,colors[i])
        text(ax,341,cy-r+10,name,22,align='right',body=True)
        theta=math.radians(-90+360*value)
        text(ax,cx+(r-12.5)*math.cos(theta),cy+(r-12.5)*math.sin(theta),f'{value:.0%}',16,align='center')
    note(ax,505,'*注：数据来源公司网站',45)

def beads(ax,d,s):
    text(ax,40,53,'2022年上半年区域销量目标达成率情况',35,True)
    names,values=d.beads(s['mode'],s['index'])
    for i,(name,value) in enumerate(zip(names,values)):
        y=435-i*54.3
        text(ax,68,y,name,20,align='right',body=True)
        rect(ax,85,y-9,585,18,'#5b5e78')
        rect(ax,85,y-9,585*value,18,'#0070c0')
        x=85+585*value
        ax.add_patch(Circle((x,y),14.5,facecolor='#0070c0',edgecolor=WHITE,lw=1.5,zorder=5))
        text(ax,x+27,y+1,f'{value:.0%}',16)
    note(ax,489,'*注:数据来源公司销售系统,日期截至2022.06.30',35)

FUNCTIONS=[bars,runway,nightingale,combo,salaries,jade,beads]
