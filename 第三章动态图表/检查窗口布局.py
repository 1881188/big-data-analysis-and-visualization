"""Briefly render our own app window, capture only its client area, then close."""
import tkinter as tk
from PIL import ImageGrab
from app import ChartApp, create_root
from data_model import ROOT

root=create_root()
try:
    app=ChartApp(root); app.select_case(4)
    root.update(); root.after(300); root.update()
    widget=app.canvas.get_tk_widget()
    assert widget.winfo_width() >= 600, 'Chart canvas too narrow'
    assert widget.winfo_height() >= 400, 'Chart canvas too short'
    x,y=root.winfo_rootx(),root.winfo_rooty()
    assert x+root.winfo_width() <= root.winfo_screenwidth()
    assert y+root.winfo_height() <= root.winfo_screenheight()
    ImageGrab.grab(bbox=(x,y,x+root.winfo_width(),y+root.winfo_height())).save(ROOT/'输出'/'交互窗口.png')
finally:
    root.destroy()
