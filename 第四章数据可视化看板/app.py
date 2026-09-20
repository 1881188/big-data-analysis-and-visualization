"""Matplotlib renders numerical charts; Tkinter displays them with aspect-fit resizing."""
import io,json,sys,tkinter as tk
from tkinter import ttk,messagebox
from datetime import datetime
from PIL import Image,ImageTk
from matplotlib.backends.backend_agg import FigureCanvasAgg
from data_model import ROOT,get_data
from charts import render_dashboard

def create_root():
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    root=tk.Tk(); root.tk.call('tk','scaling',96/72); return root

def figure_image(fig):
    canvas=FigureCanvasAgg(fig); canvas.draw()
    return Image.fromarray(__import__('numpy').asarray(canvas.buffer_rgba()).copy()).convert('RGB')

class DashboardApp:
    def __init__(self,root):
        self.root=root; self.data=get_data(); self.kind='hr'; self.month=9; self.image=None; self.pending=None
        root.title('第四章 · 人力资源与销售看板 · Python复现')
        width=min(1280,root.winfo_screenwidth()-60); height=min(900,root.winfo_screenheight()-100)
        root.geometry(f'{width}x{height}+20+30'); root.minsize(800,580)
        toolbar=ttk.Frame(root,padding=10); toolbar.pack(fill='x')
        ttk.Label(toolbar,text='第四章看板',font=('Microsoft YaHei',12,'bold')).pack(side='left',padx=(0,15))
        self.selector=ttk.Combobox(toolbar,values=['人力资源看板','销售看板'],state='readonly',width=17)
        self.selector.current(0); self.selector.pack(side='left'); self.selector.bind('<<ComboboxSelected>>',self.select)
        ttk.Label(toolbar,text='月份').pack(side='left',padx=(15,5))
        self.month_box=ttk.Combobox(toolbar,values=[f'{m}月' for m in range(1,13)],state='disabled',width=6)
        self.month_box.current(8); self.month_box.pack(side='left'); self.month_box.bind('<<ComboboxSelected>>',self.change_month)
        ttk.Button(toolbar,text='默认视图',command=self.reset).pack(side='left',padx=8)
        ttk.Button(toolbar,text='导出PNG及数据',command=self.export).pack(side='left',padx=4)
        ttk.Button(toolbar,text='原尺寸查看',command=self.full_size).pack(side='left',padx=4)
        self.canvas=tk.Canvas(root,bg='#151932',highlightthickness=0)
        self.canvas.pack(fill='both',expand=True); self.canvas.bind('<Configure>',self.resize)
        self.status=tk.StringVar(); ttk.Label(root,textvariable=self.status,padding=10,wraplength=1150).pack(fill='x')
        self.render()

    def select(self,event=None):
        self.kind=['hr','sales'][self.selector.current()]
        self.month_box.configure(state='readonly' if self.kind=='sales' else 'disabled'); self.render()

    def change_month(self,event=None):
        self.month=self.month_box.current()+1; self.render()

    def reset(self):
        self.month=9; self.month_box.current(8); self.render()

    def render(self):
        fig=render_dashboard(self.kind,self.month,self.data)
        self.image=figure_image(fig); fig.clear(); self.display()
        if self.kind=='hr':
            msg='2022年3月人员结构：1470人。学历人数已按明细纠正：专科以下170人、专科282人。'
        else:
            d=self.data.sales(self.month)
            msg=f"{d['year']}年{self.month}月：订单{d['count']}单，销售额{d['amount']:.2f}万，利润额{d['profit']:.2f}万。销量按订单数统计；成本保留源表单位（未注明）。"
            msg+='环比条形采用原图截断坐标，请以数值为准。' if self.month>1 else '缺少上年12月数据，环比不可计算。'
        self.status.set(msg)

    def resize(self,event=None):
        if self.pending: self.root.after_cancel(self.pending)
        self.pending=self.root.after(80,self.display)

    def display(self):
        self.pending=None
        if self.image is None:return
        w=max(1,self.canvas.winfo_width()); h=max(1,self.canvas.winfo_height())
        scale=min(w/self.image.width,h/self.image.height)
        size=(max(1,int(self.image.width*scale)),max(1,int(self.image.height*scale)))
        self.photo=ImageTk.PhotoImage(self.image.resize(size,Image.Resampling.LANCZOS))
        self.canvas.delete('all'); self.canvas.create_image(w/2,h/2,image=self.photo,anchor='center')

    def save_current(self):
        folder=ROOT/'输出'/'手动导出'; folder.mkdir(parents=True,exist_ok=True)
        name=('人力资源' if self.kind=='hr' else f'销售_{self.month:02d}月')+'_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        path=folder/(name+'.png'); self.image.save(path)
        metrics=self.data.hr() if self.kind=='hr' else self.data.sales(self.month)
        payload={'看板':self.kind,'数据':metrics,'说明':'学历已按明细纠正；销量为订单数；成本源单位未注明；环比不是同比。'}
        path.with_suffix('.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
        return path

    def export(self):
        try: messagebox.showinfo('导出成功',str(self.save_current()),parent=self.root)
        except OSError as e:messagebox.showerror('导出失败',str(e),parent=self.root)

    def full_size(self):
        win=tk.Toplevel(self.root); win.title('原尺寸查看（可滚动）'); win.geometry('1100x730')
        frame=ttk.Frame(win); frame.pack(fill='both',expand=True)
        canvas=tk.Canvas(frame,bg='#151932'); sx=ttk.Scrollbar(frame,orient='horizontal',command=canvas.xview)
        sy=ttk.Scrollbar(frame,orient='vertical',command=canvas.yview)
        canvas.configure(xscrollcommand=sx.set,yscrollcommand=sy.set)
        canvas.grid(row=0,column=0,sticky='nsew'); sy.grid(row=0,column=1,sticky='ns'); sx.grid(row=1,column=0,sticky='ew')
        frame.rowconfigure(0,weight=1); frame.columnconfigure(0,weight=1)
        canvas.photo=ImageTk.PhotoImage(self.image); canvas.create_image(0,0,image=canvas.photo,anchor='nw')
        canvas.configure(scrollregion=(0,0,self.image.width,self.image.height)); return win

def main():
    root=create_root()
    try: DashboardApp(root)
    except Exception as e:
        messagebox.showerror('启动失败',str(e),parent=root); root.destroy(); raise
    root.mainloop()

if __name__=='__main__':main()
