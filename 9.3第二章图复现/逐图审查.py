from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '逐图审查'
OUT.mkdir(exist_ok=True)
for i in range(1, 31):
    ref = next((ROOT / 'Excel参考原图').glob(f'{i:02d}_*.png'))
    if i == 7 and (OUT / '07_有效参考.png').exists():
        ref = OUT / '07_有效参考.png'
    if i == 21 and (OUT / '21_用户参考.png').exists():
        ref = OUT / '21_用户参考.png'
    actual = next(ROOT.glob(f'{i:02d}_*_Python复现.png'))
    a, b = Image.open(ref).convert('RGB'), Image.open(actual).convert('RGB')
    canvas = Image.new('RGB', (a.width + b.width, max(a.height, b.height) + 28), '#eeeeee')
    canvas.paste(a, (0, 28)); canvas.paste(b, (a.width, 28))
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 5), f'{i:02d} Excel reference', fill='black')
    draw.text((a.width + 8, 5), f'{i:02d} Python', fill='black')
    canvas.save(OUT / f'{i:02d}_compare.png')
print('30 comparison images saved')

# Regenerate the README overview so it cannot retain old chart versions.
overview = Image.new('RGB', (5*360, 6*300), '#1A1E43')
for i in range(1, 31):
    path = next(ROOT.glob(f'{i:02d}_*_Python复现.png'))
    chart = Image.open(path).convert('RGB')
    chart.thumbnail((350, 270), Image.Resampling.LANCZOS)
    x, y = ((i-1)%5)*360, ((i-1)//5)*300
    overview.paste(chart, (x+(360-chart.width)//2, y+25))
    ImageDraw.Draw(overview).text((x+10,y+5), f'{i:02d}', fill='white')
overview.save(ROOT / '30图复现总览.png')
