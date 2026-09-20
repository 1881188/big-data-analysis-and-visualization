"""Export all seven defaults and full-resolution left/right comparison boards."""
from PIL import Image, ImageDraw, ImageFont
from matplotlib.backends.backend_agg import FigureCanvasAgg
from data_model import ROOT, NAMES, default_state
from charts import render

def main():
    output=ROOT/'输出'; compare=ROOT/'逐图对照'
    output.mkdir(exist_ok=True); compare.mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
    for case,name in enumerate(NAMES):
        fig=render(case); FigureCanvasAgg(fig)
        path=output/f'{case+1:02d}_{name}.png'
        fig.savefig(path,dpi=100,facecolor=fig.get_facecolor()); fig.clear()
        ref=Image.open(ROOT/'Excel参考图'/f'{case+1} {name}.png').convert('RGB')
        result=Image.open(path).convert('RGB')
        board=Image.new('RGB',(ref.width+result.width,max(ref.height,result.height)+42),'#eeeeee')
        board.paste(ref,(0,42)); board.paste(result,(ref.width,42))
        draw=ImageDraw.Draw(board)
        draw.text((12,8),'Excel原图',font=font,fill='black')
        draw.text((ref.width+12,8),'Python复现（相同默认筛选）',font=font,fill='black')
        board.save(compare/f'{case+1:02d}_对照.png')
        print(path)
    # Additional states are Python functional previews, not Excel reference images.
    alternatives=[dict(index=5),dict(index=0),dict(index=1),dict(visible=(True,False,True)),
                  dict(departments=('工程',)),dict(index=0),dict(mode=1,index=5)]
    folder=output/'交互示例'; folder.mkdir(exist_ok=True)
    for case,state in enumerate(alternatives):
        fig=render(case,state); FigureCanvasAgg(fig)
        fig.savefig(folder/f'{case+1:02d}_{NAMES[case]}.png',dpi=100,facecolor=fig.get_facecolor()); fig.clear()

if __name__=='__main__': main()
