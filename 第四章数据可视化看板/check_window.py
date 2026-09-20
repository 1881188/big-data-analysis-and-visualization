"""Capture only this app's client area for local visual QA; closes afterwards."""
from PIL import ImageGrab
from app import DashboardApp,create_root
from data_model import ROOT

root=create_root()
try:
    app=DashboardApp(root)
    for index,name in [(0,'人力资源'),(1,'销售')]:
        app.selector.current(index);app.select();root.update()
        root.after(200);root.update()
        x,y=root.winfo_rootx(),root.winfo_rooty();w,h=root.winfo_width(),root.winfo_height()
        assert x>=0 and y>=0 and x+w<=root.winfo_screenwidth() and y+h<=root.winfo_screenheight()
        ImageGrab.grab(bbox=(x,y,x+w,y+h)).save(ROOT/'输出'/f'{name}_窗口.png')
finally:root.destroy()
