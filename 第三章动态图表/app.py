"""Launch with: python app.py. No Excel or VBA process is required."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from data_model import ROOT, NAMES, get_data, default_state
from charts import render

def create_root():
    # Windows display scaling otherwise makes the window larger than the desktop.
    import sys
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    root=tk.Tk()
    root.tk.call('tk','scaling',96/72)
    return root

class ChartApp:
    def __init__(self, root):
        self.root=root; self.data=get_data(); self.case=0; self.canvas=None
        self.states=[default_state(i) for i in range(7)]
        root.title('第三章 · Python动态图表复现')
        width=min(1130,root.winfo_screenwidth()-80)
        height=min(780,root.winfo_screenheight()-100)
        root.geometry(f'{width}x{height}+20+30'); root.minsize(min(1000,width),min(620,height))
        top=ttk.Frame(root,padding=12); top.pack(fill='x')
        ttk.Label(top,text='第三章：选择案例',font=('Microsoft YaHei',12,'bold')).pack(side='left')
        self.selector=ttk.Combobox(top,state='readonly',width=28,values=[f'{i+1}. {n}' for i,n in enumerate(NAMES)])
        self.selector.current(0); self.selector.pack(side='left',padx=15)
        self.selector.bind('<<ComboboxSelected>>',lambda _: self.select_case(self.selector.current()))
        ttk.Button(top,text='恢复本图默认',command=self.reset).pack(side='left',padx=5)
        ttk.Button(top,text='导出当前PNG',command=self.export).pack(side='left',padx=5)
        middle=ttk.Frame(root); middle.pack(fill='both',expand=True)
        self.controls=ttk.Frame(middle,padding=12,width=220); self.controls.pack(side='left',fill='y')
        self.plot=ttk.Frame(middle); self.plot.pack(side='left',fill='both',expand=True)
        self.status=tk.StringVar()
        ttk.Label(root,textvariable=self.status,padding=12,wraplength=1080).pack(fill='x')
        self.select_case(0)

    def select_case(self,case):
        self.case=case; self.selector.current(case)
        for child in self.controls.winfo_children(): child.destroy()
        state=self.states[case]
        ttk.Label(self.controls,text=NAMES[case],font=('Microsoft YaHei',11,'bold')).pack(anchor='w',pady=(0,20))
        if case in (0,1,2,5):
            options=self.data.months[:4] if case==1 else self.data.months if case==0 else ['近7天','近30天']
            ttk.Label(self.controls,text='选择月份' if case<2 else '统计周期').pack(anchor='w',pady=5)
            if case==5:
                self.period=tk.IntVar(value=state['index'])
                for i,name in enumerate(options):
                    ttk.Radiobutton(self.controls,text=name,value=i,variable=self.period,
                                    command=lambda:self.change(index=self.period.get())).pack(anchor='w',pady=8)
            else:
                self.option=ttk.Combobox(self.controls,values=options,state='readonly',width=17)
                self.option.current(state['index']); self.option.pack(anchor='w')
                self.option.bind('<<ComboboxSelected>>',lambda _:self.change(index=self.option.current()))
        elif case==3:
            ttk.Label(self.controls,text='显示指标（可多选）').pack(anchor='w',pady=5)
            self.flags=[]
            for i,name in enumerate(['销售额','利润','利润率']):
                flag=tk.BooleanVar(value=state['visible'][i]); self.flags.append(flag)
                ttk.Checkbutton(self.controls,text=name,variable=flag,command=self.change_flags).pack(anchor='w',pady=8)
        elif case==4:
            ttk.Label(self.controls,text='部门筛选（可多选）').pack(anchor='w',pady=5)
            self.department_flags={}
            for name in self.data.departments:
                flag=tk.BooleanVar(value=name in state['departments']); self.department_flags[name]=flag
                ttk.Checkbutton(self.controls,text=name,variable=flag,command=self.change_departments).pack(anchor='w',pady=5)
            ttk.Button(self.controls,text='全选',command=lambda:self.set_departments(True)).pack(fill='x',pady=5)
            ttk.Button(self.controls,text='清空',command=lambda:self.set_departments(False)).pack(fill='x',pady=5)
        else:
            self.mode=tk.IntVar(value=state['mode'])
            for i,name in enumerate(['按月份查看各区域','按区域查看各月份']):
                ttk.Radiobutton(self.controls,text=name,value=i,variable=self.mode,command=self.change_mode).pack(anchor='w',pady=8)
            self.option=ttk.Combobox(self.controls,values=self.data.months if state['mode']==0 else self.data.regions,state='readonly',width=17)
            self.option.current(state['index']); self.option.pack(anchor='w',pady=10)
            self.option.bind('<<ComboboxSelected>>',lambda _:self.change(index=self.option.current()))
        ttk.Label(self.controls,text='图表保留源图风格；\n当前筛选条件见底部。\n导出仅写入本章目录。',wraplength=190).pack(anchor='w',pady=30)
        self.redraw()

    def change(self,**values):
        self.states[self.case].update(values); self.redraw()

    def change_flags(self):
        self.change(visible=tuple(v.get() for v in self.flags))

    def change_departments(self):
        self.change(departments=tuple(n for n,v in self.department_flags.items() if v.get()))

    def set_departments(self,selected):
        for flag in self.department_flags.values(): flag.set(selected)
        self.change_departments()

    def change_mode(self):
        self.states[6].update(mode=self.mode.get(),index=0); self.select_case(6)

    def reset(self):
        self.states[self.case]=default_state(self.case); self.select_case(self.case)

    def describe(self):
        s=self.states[self.case]; d=self.data
        if self.case==0: return f"当前月份：{d.months[s['index']]}"
        if self.case==1:
            vals=[r[s['index']] for r in d.staff]
            return f"{d.months[s['index']]}公司总人数为{sum(vals)}；"+'，'.join(f'{n} {v}' for n,v in zip(d.staff_names,vals))
        if self.case in (2,5): return '统计周期：'+['近7天','近30天'][s['index']]
        if self.case==3: return '已显示：'+('、'.join(n for n,v in zip(['销售额','利润','利润率'],s['visible']) if v) or '无')
        if self.case==4:
            count=sum(r[2] in s['departments'] for r in d.people)
            return '部门：'+('、'.join(s['departments']) or '未选')+f'；记录数：{count}；按员工明细计算各学历平均月收入，缺失类别显示“无数据”。'
        return ('按月份：'+d.months[s['index']]) if s['mode']==0 else ('按区域：'+d.regions[s['index']])

    def redraw(self):
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy(); self.figure.clear()
        self.figure=render(self.case,self.states[self.case],self.data)
        self.canvas=FigureCanvasTkAgg(self.figure,master=self.plot)
        self.canvas.draw(); self.canvas.get_tk_widget().pack(anchor='center',expand=True)
        self.status.set(self.describe())

    def save_current(self):
        # Deliberately no file picker: keep all outputs inside the authorized chapter folder.
        from datetime import datetime
        folder=ROOT/'输出'/'手动导出'; folder.mkdir(parents=True,exist_ok=True)
        path=folder/f'{self.case+1:02d}_{NAMES[self.case]}_{datetime.now():%Y%m%d_%H%M%S_%f}.png'
        # UI canvases may resize: render again at the exact reference dimensions.
        figure=render(self.case,self.states[self.case],self.data)
        figure.savefig(path,dpi=100,facecolor=figure.get_facecolor()); figure.clear()
        path.with_suffix('.json').write_text(__import__('json').dumps(self.states[self.case],ensure_ascii=False,indent=2),encoding='utf-8')
        return path

    def export(self):
        try: messagebox.showinfo('导出完成',str(self.save_current()),parent=self.root)
        except OSError as exc: messagebox.showerror('导出失败',str(exc),parent=self.root)

def main():
    root=create_root()
    try: ChartApp(root)
    except Exception as exc:
        messagebox.showerror('启动失败',str(exc),parent=root); root.destroy(); raise
    root.mainloop()

if __name__=='__main__': main()
