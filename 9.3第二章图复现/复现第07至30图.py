from __future__ import annotations

import argparse
import math
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle, Wedge
from openpyxl import load_workbook
from PIL import Image


BG = "#1A1E43"
WHITE = "#FFFFFF"
GRID = "#404361"
BLUE = "#0070C0"
CYAN = "#00B0F0"
PINK = "#E94C6A"
YELLOW = "#FFC000"
FONT = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = FontProperties(fname=r"C:\Windows\Fonts\msyhbd.ttc")


def make_figure(width: int, height: int) -> plt.Figure:
    return plt.figure(figsize=(width / 100, height / 100), dpi=100, facecolor=BG)


def text_px(
    fig: plt.Figure,
    width: int,
    height: int,
    x: float,
    y: float,
    value: str,
    size: float,
    *,
    color: str = WHITE,
    bold: bool = False,
    ha: str = "left",
    va: str = "top",
    rotation: float = 0,
) -> None:
    fig.text(
        x / width,
        1 - y / height,
        value,
        color=color,
        fontsize=size,
        fontproperties=FONT_BOLD if bold else FONT,
        ha=ha,
        va=va,
        rotation=rotation,
    )


def add_header(
    fig: plt.Figure,
    width: int,
    height: int,
    title: str,
    subtitle: str,
    *,
    x: int = 54,
    title_y: int = 45,
    subtitle_y: int = 100,
    title_size: float = 27,
    subtitle_size: float = 17,
) -> None:
    text_px(fig, width, height, x, title_y, title, title_size, bold=True)
    text_px(fig, width, height, x, subtitle_y, subtitle, subtitle_size)


def add_note(
    fig: plt.Figure,
    width: int,
    height: int,
    note: str,
    *,
    x: int = 50,
    y: int | None = None,
) -> None:
    text_px(fig, width, height, x, height - 35 if y is None else y, note, 10.5)


def style_axes(ax: plt.Axes, *, grid_axis: str | None = "y") -> None:
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=WHITE, length=0, labelsize=11, pad=10)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(FONT)
        label.set_fontsize(11)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linestyle=(0, (6, 3)), linewidth=1)
        ax.set_axisbelow(True)


def output_path(directory: Path, number: int, name: str) -> Path:
    return directory / f"{number:02d}_{name}_Python复现.png"


def save(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, dpi=100, facecolor=BG, edgecolor="none")
    plt.close(fig)


def chart07(front, directory: Path) -> None:
    width,height=832,427
    ws=front["7 蝴蝶图"]
    rows=[(str(ws.cell(r,2).value),float(ws.cell(r,3).value),float(ws.cell(r,4).value)) for r in range(3,8)]
    fig=make_figure(width,height); ax=pixel_axes(fig,width,height)
    add_header(fig,width,height,"2022年第一季度销售目标完成情况","华东区域完成率最高达到36%，但是相比去年的42%有所下降",x=50,title_y=36,subtitle_y=89,title_size=25,subtitle_size=17)
    for i,(label,current,previous) in enumerate(rows):
        y=167+i*35
        # Excel uses REPT("|", rate*200): reproduce the separate vertical strokes.
        for value,anchor,direction,color in [(current,335,-1,BLUE),(previous,469,1,PINK)]:
            count=int(value*200)
            xs=anchor+direction*np.arange(count)*3.45
            xs=xs[(xs >= 128) & (xs <= 711)]
            ax.vlines(xs,height-y-12,height-y+12,colors=color,lw=1)
        text_px(fig,width,height,120,y,f"{current:.0%}",14,ha="right",va="center")
        text_px(fig,width,height,401,y,label,14,ha="center",va="center")
        text_px(fig,width,height,715,y,f"{previous:.0%}",14,va="center")
    for y in (91,123,361):
        ax.plot([0,width],[height-y,height-y],color="#303356",lw=.45)
    add_note(fig,width,height,"*注：数据来源于公司销售系统，统计日期截至2022.03.31",x=32,y=389)
    fig.texts[-1].set_fontsize(14)
    save(fig,output_path(directory,7,"蝴蝶图"))


def chart08(front, directory: Path) -> None:
    width, height = 832, 588
    ws = front["8 数值百分比"]
    rows = [(str(ws.cell(r, 2).value), float(ws.cell(r, 3).value), float(ws.cell(r, 6).value)) for r in range(3, 9)]
    cats, sales, yoy = zip(*rows)
    sales = np.array(sales)
    max_sales = float(max(sales))
    red_width = max_sales / 4
    middle = max_sales - sales
    fig = make_figure(width, height)
    add_header(fig, width, height, "2021年各区域销量及同比情况", "各区域商品销量同比去年均有下降，其中华南下降最多，同比下降20.8%", x=55, title_y=54, subtitle_y=109, title_size=27, subtitle_size=16)
    ax = fig.add_axes([106 / width, (height - 524) / height, 611 / width, 358 / height], facecolor=BG)
    y = np.arange(len(cats))
    ax.barh(y, sales, color="#0D397B", height=0.77)
    ax.barh(y, middle, left=sales, color="#82ADD2", height=0.77)
    ax.barh(y, np.full(len(cats), red_width), left=max_sales, color="#993B54", height=0.77)
    ax.set_xlim(0, max_sales + red_width)
    ax.set_ylim(-0.5, len(cats) - 0.5)
    ax.set_yticks(y, cats)
    ax.set_xticks([])
    style_axes(ax, grid_axis=None)
    ax.tick_params(axis="y", pad=12)
    for i, (value, pct) in enumerate(zip(sales, yoy)):
        ax.text(value - max_sales * 0.025, i, f"{value:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="right", va="center")
        ax.text(max_sales + red_width / 2, i, f"{pct:.1%}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center", va="center")
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2022.01.01", y=552)
    save(fig, output_path(directory, 8, "数值百分比"))


def chart09(front, directory: Path) -> None:
    width, height = 832, 645
    ws = front["9 对比柱形图"]
    cats = [str(ws.cell(r, 2).value) for r in range(3, 8)]
    old = np.array([float(ws.cell(r, 3).value) for r in range(3, 8)])
    new = np.array([float(ws.cell(r, 4).value) for r in range(3, 8)])
    diff = old - new
    fig = make_figure(width, height)
    add_header(fig, width, height, "2022年商品对比去年销售情况", "商品整体比去年销量有所下降，其中隔离下降最多，下降33%", x=61, title_y=52, subtitle_y=116)
    ax = fig.add_axes([53 / width, (height - 540) / height, 711 / width, 352 / height], facecolor=BG)
    x = np.arange(len(cats)); bw = 0.23
    ax.bar(x - 0.14, old, width=bw, color="#0070C0", label="2021销量")
    ax.bar(x + 0.14, new, width=bw, color="#8BB8D9", label="2022销量")
    ax.set_ylim(0, 6000); ax.set_xlim(-0.5, 4.5); ax.set_yticks([]); ax.set_xticks(x, cats); style_axes(ax, grid_axis=None)
    ax.spines["bottom"].set_visible(True); ax.spines["bottom"].set_color("#565A76")
    for i, (a, b, d) in enumerate(zip(old, new, diff)):
        ax.text(i - 0.14, a + 130, f"{a:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
        ax.text(i + 0.14, b - 280, f"{b:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
        arrow_x = i + 0.14
        ax.plot([i - 0.14, arrow_x], [a, a], color="#0070C0", lw=1)
        ax.annotate("", xy=(arrow_x, a), xytext=(arrow_x, b), arrowprops=dict(arrowstyle="-|>", color=WHITE, lw=1.2))
        ax.text(arrow_x + 0.055, (a + b) / 2, f"{d:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, va="center")
    leg = ax.legend(loc="upper left", bbox_to_anchor=(0, 1.05), ncol=2, frameon=False, fontsize=11, handlelength=0.7, handletextpad=0.4)
    for t in leg.get_texts(): t.set_color(WHITE); t.set_fontproperties(FONT)
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2022.01.01", y=604)
    save(fig, output_path(directory, 9, "对比柱形图"))


def chart10(front, directory: Path) -> None:
    width, height = 886, 588
    ws = front["10 甘特图"]
    rows = [(str(ws.cell(r, 2).value), ws.cell(r, 3).value, float(ws.cell(r, 4).value), float(ws.cell(r, 5).value)) for r in range(4, 11)]
    fig = make_figure(width, height)
    text_px(fig, width, height, width / 2, 22, "2022年化妆品类目采购项目进度", 24, bold=True, ha="center")
    ax = fig.add_axes([146 / width, (height - 553) / height, 659 / width, 422 / height], facecolor=BG)
    base = datetime(2022, 3, 1)
    for i, (name, start, days, progress) in enumerate(rows):
        y = len(rows) - 1 - i
        start_num = mdates.date2num(start)
        ax.barh(y, days, left=start_num, height=0.48, color="#087DBF")
        ax.barh(y, days * progress, left=start_num, height=0.48, color="#00A9DF")
        ax.text(start_num + days / 2, y, f"{progress:.0%}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center", va="center")
    ax.set_yticks(np.arange(len(rows)), [r[0] for r in rows][::-1])
    ticks = [datetime(2022, 3, 1), datetime(2022, 3, 16), datetime(2022, 3, 31), datetime(2022, 4, 15), datetime(2022, 4, 30), datetime(2022, 5, 15), datetime(2022, 5, 30), datetime(2022, 6, 14)]
    ax.set_xticks([mdates.date2num(t) for t in ticks], [f"{t.year}/{t.month}/{t.day}" for t in ticks])
    ax.xaxis.tick_top(); ax.tick_params(axis="x", pad=10, labelsize=8.5); ax.tick_params(axis="y", pad=12)
    ax.set_xlim(mdates.date2num(base), mdates.date2num(datetime(2022, 6, 14)))
    ax.set_ylim(-0.5, 6.5)
    style_axes(ax, grid_axis="x")
    save(fig, output_path(directory, 10, "甘特图"))


def smooth_curve(values: np.ndarray, points: int = 500) -> tuple[np.ndarray, np.ndarray]:
    # Cubic Hermite interpolation passes through every source value, including the peak.
    slopes = np.empty_like(values)
    slopes[1:-1] = (values[2:] - values[:-2]) / 2
    slopes[0], slopes[-1] = values[1] - values[0], values[-1] - values[-2]
    x = np.linspace(0, len(values) - 1, points)
    j = np.minimum(x.astype(int), len(values) - 2)
    t = x - j
    y = (2*t**3-3*t**2+1)*values[j] + (t**3-2*t**2+t)*slopes[j] + (-2*t**3+3*t**2)*values[j+1] + (t**3-t**2)*slopes[j+1]
    return x, y


def chart11(front, directory: Path) -> None:
    width, height = 832, 616
    ws = front["11 平滑折线图"]
    months = [str(ws.cell(r, 3).value) for r in range(3, 14)]
    values = np.array([float(ws.cell(r, 4).value) for r in range(3, 14)])
    fig = make_figure(width, height)
    add_header(fig, width, height, "化妆品类月度销量走势", "2022年销量迅速增加，1月最高，销量达到3782", x=41, title_y=39, subtitle_y=97, title_size=30, subtitle_size=20)
    ax = fig.add_axes([97 / width, (height - 470) / height, 702 / width, 291 / height], facecolor=BG)
    sx, sy = smooth_curve(values)
    ax.plot(sx, sy, color="#F36A52", linewidth=2)
    peak = int(np.argmax(values)); ax.vlines(peak, 0, values[peak], color="#B84C63", linestyle=(0, (4, 3)), lw=1)
    ax.text(peak, values[peak] + 140, f"{values[peak]:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    ax.set_xlim(-0.4, len(months) - 0.6); ax.set_ylim(0, 4000); ax.set_xticks(np.arange(len(months)), months); ax.set_yticks(np.arange(0, 4001, 1000)); style_axes(ax, grid_axis=None)
    ax.tick_params(axis="y", colors="#F36A52", pad=12)
    ax.set_yticklabels([f"{v:,}" for v in range(0, 4001, 1000)])
    ax.spines["bottom"].set_visible(True); ax.spines["bottom"].set_color("#686B83")
    strip_bottom = (height - 546) / height
    fig.add_artist(Rectangle((78 / width, strip_bottom), 532 / width, 31 / height, transform=fig.transFigure, facecolor="#62C8D8", edgecolor="none"))
    fig.add_artist(Rectangle((618 / width, strip_bottom), 195 / width, 31 / height, transform=fig.transFigure, facecolor="#F8C54D", edgecolor="none"))
    text_px(fig, width, height, 344, 531, "2021", 12, ha="center", va="center")
    text_px(fig, width, height, 715, 531, "2022", 12, ha="center", va="center")
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2022.03.31", x=40, y=575)
    save(fig, output_path(directory, 11, "平滑折线图"))


def chart12(front, directory: Path) -> None:
    width, height = 832, 590
    ws = front["12 菱形走势图"]
    months = [str(ws.cell(r, 2).value) for r in range(3, 11)]
    rates = np.array([float(ws.cell(r, 3).value) for r in range(3, 11)])
    fig = make_figure(width, height)
    add_header(fig, width, height, "2022年1-8月公司计划完成率", "公司整体完成率55%，4月和8月超过70%，2月和6月较低未过半", x=58, title_y=45, subtitle_y=107, title_size=28, subtitle_size=17)
    ax = fig.add_axes([67 / width, (height - 486) / height, 720 / width, 321 / height], facecolor=BG)
    x = np.arange(len(months)); base = 0
    for i, value in enumerate(rates):
        ax.vlines(i, base, value, color="#C34865", linewidth=1.5)
        ax.scatter(i, value, marker="D", s=60, facecolor=BG, edgecolor="#C34865", linewidth=1.2, zorder=3)
        ax.text(i, value + 0.055, f"{value:.2%}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    ax.set_xlim(-0.5, len(months) - 0.5); ax.set_ylim(base, 0.8); ax.set_xticks(x, months); ax.set_yticks([]); style_axes(ax, grid_axis=None)
    ax.spines["bottom"].set_visible(True); ax.spines["bottom"].set_color("#565A76")
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2022.08.31", y=553)
    save(fig, output_path(directory, 12, "菱形走势图"))


def chart13(front, directory: Path) -> None:
    width, height = 832, 622
    ws = front["13 对比折线图"]
    months = [str(ws.cell(r, 2).value) for r in range(3, 9)]
    old = np.array([float(ws.cell(r, 3).value) for r in range(3, 9)])
    new = np.array([float(ws.cell(r, 4).value) for r in range(3, 9)])
    fig = make_figure(width, height)
    add_header(fig, width, height, "2022年上半年各月同比去年销量", "上半年同比去年增长明显，5月份同比增长最多，增长近40%", x=54, title_y=40, subtitle_y=106, title_size=28, subtitle_size=17)
    ax = fig.add_axes([108 / width, (height - 528) / height, 678 / width, 305 / height], facecolor=BG)
    x = np.arange(len(months))
    ax.plot(x, old, color="#F05070", marker="o", markersize=5, linewidth=2, label="2021年")
    ax.plot(x, new, color="#0070C0", marker="o", markersize=5, linewidth=2, label="2022年")
    ax.set_xlim(-0.5, 5.5); ax.set_ylim(0, 3000); ax.set_xticks(x, months); ax.set_yticks(np.arange(0, 3001, 500)); style_axes(ax)
    for i, v in enumerate(old): ax.text(i, v + (180 if v > new[i] else -330), f"{v:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    for i, v in enumerate(new): ax.text(i, v + (180 if v > old[i] else -380), f"{v:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    leg = ax.legend(loc="upper right", bbox_to_anchor=(0.98, 1.19), frameon=False, ncol=2, fontsize=9)
    for t in leg.get_texts(): t.set_color(WHITE); t.set_fontproperties(FONT)
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2022.06.30", y=584)
    save(fig, output_path(directory, 13, "对比折线图"))


def pixel_axes(fig, width, height):
    ax = fig.add_axes([0, 0, 1, 1], facecolor=BG)
    ax.set_xlim(0, width); ax.set_ylim(0, height); ax.set_aspect("equal"); ax.axis("off")
    return ax


def leader(ax, height, points, color):
    ax.plot([p[0] for p in points], [height-p[1] for p in points], color=color, lw=0.65)
    ax.scatter(points[0][0], height-points[0][1], s=22, color=color, edgecolors="none", zorder=5)


def chart14(front, directory: Path) -> None:
    width, height = 832, 617
    value = float(front["14 单值圆环图"].cell(3, 2).value)
    fig = make_figure(width, height)
    add_header(fig, width, height, "2022年上半年目标完成率", f"截至6月30日销售目标总体完成率达到{value:.0%}", x=49, title_y=49, subtitle_y=105, title_size=26, subtitle_size=17)
    ax = pixel_axes(fig, width, height)
    center, radius, thickness = (423, height-346), 174, 17
    ax.add_patch(Wedge(center, radius, 0, 360, width=thickness, facecolor="#303356", edgecolor="none"))
    # Angular color interpolation: purple above, pink below; 15% gap on the left.
    cmap = LinearSegmentedColormap.from_list("ring", ["#7030A0", "#E94B6B"])
    gradient = np.linspace(1, 0, 1000).reshape(-1, 1)
    im = ax.imshow(gradient, extent=(center[0]-radius,center[0]+radius,center[1]-radius,center[1]+radius), origin="lower", cmap=cmap, interpolation="bicubic", zorder=2)
    clip = Wedge(center,radius,150-360*value,150,width=thickness,transform=ax.transData)
    im.set_clip_path(clip)
    text_px(fig, width, height, 423, 330, f"{value:.0%}", 44, ha="center", va="center")
    text_px(fig, width, height, 423, 408, "目标完成率", 15, ha="center", va="center")
    add_note(fig, width, height, "*注：数据来源于公司销售系统", x=46, y=576)
    save(fig, output_path(directory, 14, "单值圆环图"))


def chart15(front, directory: Path) -> None:
    width, height = 375, 372
    value = float(front["15 水球图"].cell(3, 2).value)
    fig = make_figure(width, height); ax = pixel_axes(fig, width, height)
    center = (186, height-186)
    ax.add_patch(Circle(center, 177, facecolor="none", edgecolor=BLUE, lw=2.5))
    inner = Circle(center, 164, facecolor="none", edgecolor=BLUE, lw=2.5)
    ax.add_patch(inner)
    fill = Rectangle((22, center[1]-164), 328, 328*value, facecolor=BLUE, edgecolor="none")
    fill.set_clip_path(inner); ax.add_patch(fill)
    text_px(fig, width, height, 195, 183, f"{value:.0%}", 48, ha="center", va="center")
    save(fig, output_path(directory, 15, "水球图"))


def chart16(back, directory: Path) -> None:
    width, height = 405, 400
    value = float(back["16 波浪水球图 "].cell(4, 2).value)
    fig = make_figure(width, height); ax = pixel_axes(fig, width, height)
    center = (200, height-198)
    ax.add_patch(Circle(center, 190, facecolor="none", edgecolor=BLUE, lw=2))
    inner = Circle(center, 175, facecolor="none", edgecolor="none"); ax.add_patch(inner)
    x = np.linspace(25, 375, 1000)
    # The Excel shape uses a shallow two-cycle wave with an inset border.
    baseline = center[1] + (value-.5)*350*.67
    wave = baseline + 11*np.cos(4*np.pi*(x-55)/350)
    fill = ax.fill_between(x, center[1]-175, wave, color=BLUE, linewidth=0)
    fill.set_clip_path(inner)
    text_px(fig, width, height, 210, 185, f"{value:.0%}", 48, ha="center", va="center")
    save(fig, output_path(directory, 16, "波浪水球图"))


def chart17(back, directory: Path) -> None:
    width, height = 834, 594
    ws = back["17 玉玦图"]
    labels = [str(ws.cell(r,2).value) for r in range(3,7)]
    values = [float(ws.cell(r,3).value) for r in range(3,7)]
    colors = ["#35A4D3", "#10A4AA", "#F6C44F", "#E94B6B"]
    fig = make_figure(width,height)
    add_header(fig,width,height,"2022年上半年年龄分布","公司平均年龄32.5，23-30员工比例最高",x=55,title_y=43,subtitle_y=101,title_size=28,subtitle_size=20)
    ax=pixel_axes(fig,width,height); center=(423,height-347)
    for label,value,color,radius in zip(labels,values,colors,[91,121,150,180]):
        end=90-720*value
        ax.add_patch(Wedge(center,radius,end,90,width=27,facecolor=color,edgecolor="none"))
        a=math.radians(end-12)
        tx=center[0]+(radius-13)*math.cos(a); ty=height-(center[1]+(radius-13)*math.sin(a))
        text_px(fig,width,height,tx,ty,f"{value:.1%}",11,ha="center",va="center")
    for i,label in enumerate(labels[::-1]):
        text_px(fig,width,height,414,179+30*i,label,14,ha="right",va="center")
    add_note(fig,width,height,"*注：数据来源于公司人力资源系统，统计日期截至2022.06.30",y=558)
    save(fig,output_path(directory,17,"玉玦图"))


def chart18(back, directory: Path) -> None:
    width,height=832,622
    ws=back["18 跑道图"]
    labels=[str(ws.cell(r,2).value).strip() for r in range(3,9)]
    values=[float(ws.cell(r,3).value) for r in range(3,9)]
    colors=["#7030A0","#0070C0","#35A4D3","#10A4AA","#F6C44F","#E94B6B"]
    fig=make_figure(width,height)
    add_header(fig,width,height,"2022年上半年各部门人数","公司总人数1664，销售部人数最多451，占比27%",x=54,title_y=47,subtitle_y=105,title_size=28,subtitle_size=20)
    ax=pixel_axes(fig,width,height); center=(377,height-357)
    for label,value,color,radius in zip(labels,values,colors,[107,126,145,164,183,202]):
        ax.add_patch(Wedge(center,radius,90-360*value/(sum(values)/2),90,width=13,facecolor=color,edgecolor="none"))
    for i,(label,value) in enumerate(zip(labels[::-1],values[::-1])):
        text_px(fig,width,height,367,164+i*18.5,f"{label} {value:.0f}",9,ha="right",va="center")
    add_note(fig,width,height,"*注：数据来源于公司人力资源系统，统计日期截止2022.06.30",x=39,y=584)
    save(fig,output_path(directory,18,"跑道图"))


def chart19(back, directory: Path) -> None:
    width,height=832,622
    ws=back["19 南丁格尔圆饼图"]
    values=np.array([float(ws.cell(r,3).value) for r in range(3,9)])
    colors=["#E94B6B","#F6C44F","#10A4AA","#0070C0","#35A4D3","#7030A0"]
    fig=make_figure(width,height)
    add_header(fig,width,height,"2021年各部门人数分布","公司总人数1664，销售部人数最多451，占比29.2%",x=53,title_y=32,subtitle_y=88,title_size=27,subtitle_size=17)
    ax=pixel_axes(fig,width,height)
    lines=[[(623,253),(655,214),(774,214)],[(575,493),(597,529),(717,529)],[(284,498),(253,537),(133,537)],[(262,357),(232,394),(113,394)],[(339,289),(317,253),(158,253)],[(395,257),(373,221),(253,221)]]
    for pts,color in zip(lines,colors): leader(ax,height,pts,color)
    angle=90.
    for v,color in zip(values,colors):
        end=angle-360*v/values.sum()
        ax.add_patch(Wedge((414,height-367),217,end,angle,facecolor=color,edgecolor="none",zorder=3))
        angle=end
    add_note(fig,width,height,"*注：数据来源于公司人力资源系统，统计日期截至2022.01.01",x=53,y=585)
    save(fig,output_path(directory,19,"南丁格尔圆饼图"))


def chart20(back, directory: Path) -> None:
    width,height=835,624
    ws=back["20 南丁格尔圆环图"]
    labels=[str(ws.cell(r,2).value) for r in range(3,7)]
    values=[float(ws.cell(r,3).value) for r in range(3,7)]
    colors=["#532AC9","#6272F2","#63CADA","#F6C44F"]
    fig=make_figure(width,height)
    add_header(fig,width,height,"2022年上半年各年龄段人数分布","公司平均年龄32.5，20-30员工比例最高占比37.5%",x=53,title_y=31,subtitle_y=87,title_size=27,subtitle_size=17)
    ax=pixel_axes(fig,width,height); center=(417,height-376); angle=90.
    for v,color,radius in zip(values,colors,[180,165,151,137]):
        end=angle-360*v
        ax.add_patch(Wedge(center,radius,end,angle,width=radius-108,facecolor=color,edgecolor="none"))
        for r in np.arange(122,radius,14.4):
            ax.add_patch(Wedge(center,r,end,angle,width=.35,facecolor="#526180",edgecolor="none",alpha=.5))
        angle=end
    specs=[([(612,260),(645,222),(770,222)],698,185), ([(532,533),(558,573),(695,573)],635,530), ([(246,342),(218,380),(78,380)],151,337), ([(320,226),(297,191),(164,191)],240,149)]
    for label,v,color,(pts,x,y) in zip(labels,values,colors,specs):
        leader(ax,height,pts,color)
        text_px(fig,width,height,x,y,label,11,ha="center",va="center")
        text_px(fig,width,height,x,y+22,f"{v:.1%}",11,color=color,ha="center",va="center",bold=True)
    add_note(fig,width,height,"*注：数据来源于公司人力资源系统，统计日期截至2022.06.30",x=53,y=586)
    save(fig,output_path(directory,20,"南丁格尔圆环图"))


def chart21(back, directory: Path) -> None:
    # Geometry follows the supplied complete screenshot, not the incomplete Excel export.
    width,height=867,648
    ws=back["20 南丁格尔（PPT）"]
    values=np.array([float(ws.cell(r,3).value) for r in range(3,9)])
    colors=["#E94B6B","#F6C44F","#10A4AA","#35A4D3","#0070C0","#7030A0"]
    fig=make_figure(width,height); ax=pixel_axes(fig,width,height)
    angle=90.
    # PPT shape radii are independent of sector angles; source shares determine angles.
    for v,color,radius in zip(values,colors,[247,185,147,117,83,41]):
        end=angle-360*v/values.sum()
        wedge = Wedge((421,height-386),radius,end,angle,facecolor=color,edgecolor="none")
        if color == colors[0]:
            from matplotlib.transforms import Affine2D
            wedge.set_transform(Affine2D().translate(-421,-(height-386)).scale(1,239/247).translate(421,height-386)+ax.transData)
        ax.add_patch(wedge)
        if color == colors[0]:
            end = math.degrees(math.atan2((239/247)*math.sin(math.radians(end)),math.cos(math.radians(end))))
        angle=end
    lines=[[(650,264),(682,223),(806,223)],[(598,513),(623,551),(747,551)],[(296,519),(264,560),(139,560)],[(273,372),(242,411),(118,411)],[(354,301),(330,263),(165,263)],[(412,269),(389,231),(264,231)]]
    for pts,color in zip(lines,["#E94B6B","#F6C44F","#10A4AA","#0070C0","#35A4D3","#7030A0"]):
        leader(ax,height,pts,color)
    save(fig,output_path(directory,21,"南丁格尔PPT"))


def chart22(back, directory: Path) -> None:
    width,height=832,638
    value=float(back["22 仪表盘图"].cell(3,8).value)
    fig=make_figure(width,height)
    text_px(fig,width,height,width/2,63,"2022年6月29公司整体运营指数良好",26,bold=True,ha="center")
    ax=pixel_axes(fig,width,height); center=(431,height-394)
    ax.add_patch(Wedge(center,197,0,360,width=19,facecolor=BLUE,edgecolor="none"))
    for lo,hi,color in [(50,80,"#098795"),(80,120,"#FFCC4F"),(120,150,"#FF4567")]:
        a,b=225-(lo-50)*2.7,225-(hi-50)*2.7
        ax.add_patch(Wedge(center,178,b,a,width=19,facecolor=color,edgecolor="none"))
    for tick in range(50,151,10):
        a=math.radians(225-(tick-50)*2.7)
        ax.plot([center[0]+159*math.cos(a),center[0]+197*math.cos(a)],[center[1]+159*math.sin(a),center[1]+197*math.sin(a)],color=BG,lw=.65)
        ax.text(center[0]+146*math.cos(a),center[1]+146*math.sin(a),str(tick),color=WHITE,fontsize=12,fontproperties=FONT,ha="center",va="center")
    a=math.radians(225-(value-50)*2.7)
    ax.plot([center[0],center[0]+139*math.cos(a)],[center[1],center[1]+139*math.sin(a)],color=WHITE,lw=1.4)
    text_px(fig,width,height,431,505,f"{value:.0f}",28,ha="center",va="center")
    save(fig,output_path(directory,22,"仪表盘图"))


def chart23(back, directory: Path) -> None:
    width, height = 832, 594
    ws = back["23 柱形折线图"]
    years = [str(ws.cell(r, 2).value) for r in range(3, 9)]
    sales = np.array([float(ws.cell(r, 3).value) for r in range(3, 9)])
    yoy = np.array([float(ws.cell(r, 4).value) for r in range(3, 9)])
    fig = make_figure(width, height)
    add_header(fig, width, height, "近六年销售量及增长率", "平台销量近6年持续增长，但近两年增长率有所放缓", x=52, title_y=42, subtitle_y=97, title_size=25, subtitle_size=16)
    ax = fig.add_axes([63 / width, (height - 500) / height, 704 / width, 352 / height], facecolor=BG)
    x = np.arange(len(years)); bars = ax.bar(x, sales, width=0.32, color=BLUE)
    ax.set_ylim(0, 6000); ax.set_xlim(-.5,5.5); ax.set_yticks([]); ax.set_xticks(x, years); style_axes(ax, grid_axis=None)
    for bar, value in zip(bars, sales):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 100, f"{value:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    ax2 = ax.twinx(); ax2.plot(x, yoy, color="#F05070", marker="o", markersize=5, linewidth=2)
    ax2.set_ylim(-1.2, 0.5); ax2.set_yticks([])
    for spine in ax2.spines.values(): spine.set_visible(False)
    for i, value in enumerate(yoy): ax2.text(i, value + 0.09, f"{value:.0%}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    fig.legend(handles=[Rectangle((0,0),1,1,color=BLUE,label="销售量"),Line2D([0],[0],color=PINK,marker="o",label="同比")],loc="upper right",bbox_to_anchor=(.9,.77),frameon=False,ncol=2,labelcolor=WHITE,prop=FONT)
    
    add_note(fig, width, height, "*注：数据来源于公司销售系统", y=558)
    save(fig, output_path(directory, 23, "柱形折线图"))


def chart24(back, directory: Path) -> None:
    width, height = 844, 589
    ws = back["24 目标柱形图"]
    cats = [str(ws.cell(r, 2).value) for r in range(3, 9)]
    actual = np.array([float(ws.cell(r, 3).value) for r in range(3, 9)])
    target = np.array([float(ws.cell(r, 4).value) for r in range(3, 9)])
    fig = make_figure(width, height)
    add_header(fig, width, height, "2022年上半年各商品销量完成情况", "防晒整体销量最好，达到856，面霜远超目标，超额完成30%", x=55, title_y=42, subtitle_y=98, title_size=25, subtitle_size=16)
    ax = fig.add_axes([63 / width, (height - 477) / height, 716 / width, 321 / height], facecolor=BG)
    x = np.arange(len(cats)); bw = 0.24
    ax.bar(x, target, width=bw, facecolor="none", edgecolor="#A9B1C1", linewidth=1.1, label="目标销量")
    bars = ax.bar(x, actual, width=bw * 0.65, color=BLUE, label="实际销量")
    ax.set_ylim(0, 1000); ax.set_xlim(-.5,5.5); ax.set_yticks([]); ax.set_xticks(x, cats); style_axes(ax, grid_axis=None)
    for bar, value in zip(bars, actual): ax.text(bar.get_x() + bar.get_width() / 2, max(value,target[int(round(bar.get_x()+bar.get_width()/2))]) + 28, f"{value:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    leg = ax.legend(loc="upper left", bbox_to_anchor=(0.025, 1.05), frameon=False, ncol=2, fontsize=11, handlelength=0.8)
    for t in leg.get_texts(): t.set_color(WHITE); t.set_fontproperties(FONT)
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2022.06.30", y=553)
    save(fig, output_path(directory, 24, "目标柱形图"))


def chart25(back, directory: Path) -> None:
    width, height = 842, 589
    ws = back["25 子弹图"]
    cats = [str(ws.cell(r, 2).value) for r in range(4, 10)]
    actual = np.array([float(ws.cell(r, 3).value) for r in range(4, 10)])
    target = np.array([float(ws.cell(r, 4).value) for r in range(4, 10)])
    fig = make_figure(width, height)
    add_header(fig, width, height, "2022年上半年各商品销量完成情况", "防晒整体销量最好，达到856，面霜远超目标，超额完成30%", x=54, title_y=42, subtitle_y=98, title_size=25, subtitle_size=16)
    ax = fig.add_axes([107 / width, (height - 490) / height, 662 / width, 319 / height], facecolor=BG)
    x = np.arange(len(cats)); bw = 0.29
    ax.bar(x, 600, width=bw, color="#82ADD2", label="及格")
    ax.bar(x, 200, bottom=600, width=bw, color="#0984B8", label="良好")
    ax.bar(x, 200, bottom=800, width=bw, color="#0070C0", label="优秀")
    ax.bar(x, actual, width=bw * 0.6, color="#1265FF", label="实际", zorder=3)
    for i, t in enumerate(target): ax.hlines(t, i - bw * 0.34, i + bw * 0.34, color=YELLOW, linewidth=3, zorder=4)
    ax.set_ylim(0, 1200); ax.set_xlim(-.5,5.5); ax.set_yticks(np.arange(0, 1201, 200)); ax.set_xticks(x, cats); style_axes(ax, grid_axis=None)
    ax.spines["bottom"].set_visible(True); ax.spines["bottom"].set_color("#565A76")
    ax.plot([],[],color=YELLOW,lw=2,label="目标")
    handles, labels = ax.get_legend_handles_labels()
    order = [labels.index(v) for v in ["及格","良好","优秀","实际","目标"]]
    leg = ax.legend([handles[i] for i in order], [labels[i] for i in order], loc="upper left", bbox_to_anchor=(0.045, 1.04), frameon=False, ncol=5, fontsize=11, handlelength=0.7, handletextpad=0.3)
    for t in leg.get_texts(): t.set_color(WHITE); t.set_fontproperties(FONT)
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2022.06.30", y=553)
    save(fig, output_path(directory, 25, "子弹图"))


def chart26(back, directory: Path) -> None:
    width, height = 831, 591
    ws = back["26 柱形圆"]
    cats = [str(ws.cell(r, 2).value) for r in range(3, 9)]
    values = np.array([float(ws.cell(r, 3).value) for r in range(3, 9)])
    yoy = np.array([float(ws.cell(r, 5).value) for r in range(3, 9)])
    fig = make_figure(width, height)
    add_header(fig, width, height, "各区域上半年销量以同比", "东北区域销量持续保持第一，华东和华南同比去年增长最多", x=53, title_y=42, subtitle_y=98, title_size=25, subtitle_size=16)
    ax = fig.add_axes([68 / width, (height - 502) / height, 686 / width, 354 / height], facecolor=BG)
    x = np.arange(len(cats)); bars = ax.bar(x, values, width=0.32, color="#E94C6A")
    ax.set_ylim(0, 5000); ax.set_xlim(-.5,5.5); ax.set_yticks([]); ax.set_xticks(x, cats); style_axes(ax, grid_axis=None)
    for bar, value in zip(bars, values): ax.text(bar.get_x() + bar.get_width() / 2, value + 100, f"{value:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    # 百分比气泡固定在柱顶上方同一基准线上。
    for i, value in enumerate(yoy):
        ax.scatter(i, 4500, s=(value * 200 * 72/100)**2, color=BLUE, edgecolors="none", zorder=3)
        ax.text(i, 4500, f"{value:.0%}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center", va="center", zorder=4)
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2022.06.30", y=555)
    save(fig, output_path(directory, 26, "柱形圆"))


def chart27(back, directory: Path) -> None:
    width, height = 832, 616
    ws = back["27 簇状柱形折线图"]
    cats = [str(ws.cell(r, 2).value) for r in range(3, 9)]
    current = np.array([float(ws.cell(r, 3).value) for r in range(3, 9)])
    previous = np.array([float(ws.cell(r, 4).value) for r in range(3, 9)])
    yoy = np.array([float(ws.cell(r, 5).value) for r in range(3, 9)])
    fig = make_figure(width, height)
    add_header(fig, width, height, "上半年各月商品销量同比去年情况", "2022年相比于2021年销量都有提升，半年整体提升17%", x=45, title_y=40, subtitle_y=96, title_size=25, subtitle_size=16)
    ax = fig.add_axes([67 / width, (height - 522) / height, 703 / width, 358 / height], facecolor=BG)
    x = np.arange(len(cats)); bw = 0.24
    a = ax.bar(x - bw / 2, current, width=bw, color=BLUE)
    b = ax.bar(x + bw / 2, previous, width=bw, color="#E94C6A")
    ax.set_ylim(0, 5000); ax.set_xlim(-.5,5.5); ax.set_yticks([]); ax.set_xticks(x, cats); style_axes(ax, grid_axis=None)
    for bars, vals in ((a, current), (b, previous)):
        for bar, v in zip(bars, vals): ax.text(bar.get_x() + bar.get_width()/2, v + 80, f"{v:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    ax2 = ax.twinx(); ax2.plot(x, yoy, color=YELLOW, marker="o", markersize=5, linewidth=2)
    ax2.set_ylim(-1.1, 0.3); ax2.set_yticks([])
    for spine in ax2.spines.values(): spine.set_visible(False)
    for i, v in enumerate(yoy): ax2.text(i, v + 0.07, f"{v:.0%}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    text_px(fig, width, height, 723, 422, "2022", 11, ha="center", va="center")
    fig.add_artist(Rectangle((689/width,(height-436)/height),69/width,28/height,transform=fig.transFigure,facecolor=BG,edgecolor=BLUE,zorder=1))
    text_px(fig, width, height, 723, 465, "2021", 11, ha="center", va="center")
    fig.add_artist(Rectangle((689/width,(height-479)/height),70/width,28/height,transform=fig.transFigure,facecolor=BG,edgecolor=PINK,zorder=1))
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2022.06.30", y=580)
    save(fig, output_path(directory, 27, "簇状柱形折线图"))


def chart28(back, directory: Path) -> None:
    width, height = 844, 603
    ws = back["28 复合柱形图"]
    source_rows = [3, 4, 5, 7, 8, 9, 11, 12, 13, 15, 16, 17]
    months = [str(ws.cell(r, 2).value) for r in source_rows]
    monthly = np.array([float(ws.cell(r, 3).value) for r in source_rows])
    quarters = np.array([float(ws.cell(r, 4).value) for r in source_rows])
    fig = make_figure(width, height)
    add_header(fig, width, height, "2021年各月化妆品销量走势", "2021年第三季度销量最多9673，9月单月销量最大3621", x=53, title_y=41, subtitle_y=96, title_size=25, subtitle_size=16)
    ax = fig.add_axes([82 / width, (height - 502) / height, 669 / width, 365 / height], facecolor=BG)
    x = np.array([q*4+m for q in range(4) for m in range(3)]); quarter_colors = ["#28306E", "#563A48", "#59473F", "#412B5C"]
    for q in range(4):
        center = q * 4 + 1
        ax.bar(center, quarters[q * 3], width=3, color=quarter_colors[q], alpha=0.85, zorder=1)
        ax.text(center, quarters[q * 3] + 250, f"{quarters[q*3]:.0f}", color=WHITE, fontsize=11, fontproperties=FONT, ha="center")
    bar_colors = ["#5263DF"] * 3 + ["#F1791A"] * 3 + ["#F2AB13"] * 3 + ["#B74283"] * 3
    bars = ax.bar(x, monthly, width=0.36, color=bar_colors, zorder=3)
    for bar, value in zip(bars, monthly): ax.text(bar.get_x()+bar.get_width()/2, value + 90, f"{value:.0f}", color=WHITE, fontsize=10.5, fontproperties=FONT, ha="center")
    ax.set_ylim(0, 11000); ax.set_xlim(-.5,14.5); ax.set_yticks([]); ax.set_xticks(x, months); style_axes(ax, grid_axis=None)
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2021.12.31", y=565)
    save(fig, output_path(directory, 28, "复合柱形图"))


def chart29(back, directory: Path) -> None:
    width, height = 844, 593
    ws = back["29 滑珠图"]
    rows = [(str(ws.cell(r, 2).value), float(ws.cell(r, 3).value)) for r in range(3, 8)]
    fig = make_figure(width, height)
    add_header(fig, width, height, "2022年上半年产品销量目标达成率情况", "华南完成率最高达到86%，华东最低35%", x=56, title_y=42, subtitle_y=99, title_size=25, subtitle_size=16)
    ax = fig.add_axes([151 / width, (height - 515) / height, 446 / width, 364 / height], facecolor=BG)
    y = np.arange(len(rows)); labels=[r[0] for r in rows]; vals=np.array([r[1] for r in rows])
    for i, value in enumerate(vals):
        ax.plot([0, 1], [i, i], color="#74758C", lw=21, solid_capstyle="round",clip_on=False)
        ax.plot([0, value], [i, i], color=BLUE, lw=21, solid_capstyle="round",clip_on=False)
        ax.scatter(value, i, s=470, color=BLUE, edgecolor=WHITE, linewidth=1.4, zorder=3,clip_on=False)
        ax.text(value - 0.04, i, f"{value:.0%}", color=WHITE, fontsize=11, fontproperties=FONT, ha="right", va="center")
    ax.set_xlim(0,1); ax.set_ylim(-.5,len(rows)-.5); ax.set_yticks(y,labels); ax.set_xticks([]); style_axes(ax,grid_axis=None); ax.tick_params(axis="y",pad=24)
    add_note(fig, width, height, "*注：数据来源于公司销售系统，统计日期截至2022.06.30", y=557)
    save(fig, output_path(directory, 29, "滑珠图"))


def chart30(back, directory: Path) -> None:
    width, height = 831, 593
    ws = back["30 对比滑珠图"]
    rows = [(str(ws.cell(r, 2).value), float(ws.cell(r, 3).value), float(ws.cell(r, 4).value)) for r in range(4, 9)]
    fig = make_figure(width, height)
    add_header(fig, width, height, "2022年上半年销量目标达成率同比去年情况", "华南完成率最高达到86%，华东最低35%，其中华南和华东不及2021年", x=56, title_y=42, subtitle_y=99, title_size=25, subtitle_size=15)
    fig.legend(handles=[Line2D([0],[0],marker="o",color=BG,markerfacecolor=BLUE,markeredgecolor=WHITE,markersize=12,label="2022完成率"),Line2D([0],[0],marker="o",color=BG,markerfacecolor="#A6A6A6",markeredgecolor=WHITE,markersize=12,label="2021完率")],loc="upper left",bbox_to_anchor=(.065,.77),ncol=2,frameon=False,labelcolor=WHITE,prop=FONT)
    
    ax = fig.add_axes([124 / width, (height - 530) / height, 537 / width, 370 / height], facecolor=BG)
    y=np.arange(len(rows)); labels=[r[0] for r in rows]; cur=np.array([r[1] for r in rows]); prev=np.array([r[2] for r in rows])
    for i,(a,b) in enumerate(zip(cur,prev)):
        ax.plot([0,1],[i,i],color="#74758C",lw=8,solid_capstyle="butt")
        ax.plot([0,a],[i,i],color="#0070C0",lw=8,solid_capstyle="butt")
        ax.scatter(a,i,s=220,color="#0070C0",edgecolor=WHITE,linewidth=1.2,zorder=4)
        ax.scatter(b,i,s=220,color="#A6A6A6",edgecolor=WHITE,linewidth=1.2,zorder=3)
        ax.text(a,i+0.28,f"{a:.0%}",color=WHITE,fontsize=11,fontproperties=FONT,ha="center")
    ax.set_xlim(0,1); ax.set_ylim(-.5,len(rows)-.5); ax.set_yticks(y,labels); ax.set_xticks([]); style_axes(ax,grid_axis=None); ax.tick_params(axis="y",pad=18)
    add_note(fig,width,height,"*注：数据来源于公司销售系统，统计日期截至2022.06.30",y=557)
    save(fig, output_path(directory, 30, "对比滑珠图"))


def parse_args() -> argparse.Namespace:
    directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="复现第二章第07至30图")
    parser.add_argument("--start", type=int, default=7)
    parser.add_argument("--end", type=int, default=30)
    parser.add_argument("--front", type=Path, default=directory / "第二章 图表(前15).xlsx")
    parser.add_argument("--back", type=Path, default=directory / "第二章 图表(后15).xlsx")
    parser.add_argument("--output-dir", type=Path, default=directory)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.start < 7 or args.end > 30 or args.start > args.end:
        raise ValueError("编号范围必须满足 7 <= start <= end <= 30")
    front = load_workbook(args.front.resolve(), data_only=True, read_only=True)
    back = load_workbook(args.back.resolve(), data_only=True, read_only=True)
    functions = {
        7: lambda: chart07(front, args.output_dir), 8: lambda: chart08(front, args.output_dir),
        9: lambda: chart09(front, args.output_dir), 10: lambda: chart10(front, args.output_dir),
        11: lambda: chart11(front, args.output_dir), 12: lambda: chart12(front, args.output_dir),
        13: lambda: chart13(front, args.output_dir), 14: lambda: chart14(front, args.output_dir),
        15: lambda: chart15(front, args.output_dir), 16: lambda: chart16(back, args.output_dir),
        17: lambda: chart17(back, args.output_dir), 18: lambda: chart18(back, args.output_dir),
        19: lambda: chart19(back, args.output_dir), 20: lambda: chart20(back, args.output_dir),
        21: lambda: chart21(back, args.output_dir), 22: lambda: chart22(back, args.output_dir),
        23: lambda: chart23(back, args.output_dir), 24: lambda: chart24(back, args.output_dir),
        25: lambda: chart25(back, args.output_dir), 26: lambda: chart26(back, args.output_dir),
        27: lambda: chart27(back, args.output_dir), 28: lambda: chart28(back, args.output_dir),
        29: lambda: chart29(back, args.output_dir), 30: lambda: chart30(back, args.output_dir),
    }
    try:
        for number in range(args.start, args.end + 1):
            functions[number]()
            print(f"已生成第 {number:02d} 图")
    finally:
        front.close(); back.close()


if __name__ == "__main__":
    main()
