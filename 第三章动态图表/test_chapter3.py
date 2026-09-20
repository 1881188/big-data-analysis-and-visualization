"""unittest only; checks source data, all dynamic states and real Tk callbacks."""
import hashlib
import itertools
import unittest
import tkinter as tk
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.patches import Wedge
from data_model import SOURCE, get_data, default_state, EDUCATION, ROOT
from charts import render, SIZES

class ChapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        cls.d=get_data()

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==cls.digest, 'Original workbook changed!'

    def draw(self,case,state):
        fig=render(case,state,self.d); canvas=FigureCanvasAgg(fig); canvas.draw()
        self.assertEqual(canvas.get_width_height(),SIZES[case]); return fig

    def test_01_monthly_bars(self):
        self.assertEqual(self.d.sales[4],[282,323,705,486,405,308])
        for index in range(6):
            fig=self.draw(0,dict(index=index)); ax=fig.axes[0]
            heights=[p.get_height() for p in ax.patches]
            np.testing.assert_allclose(np.array(heights)/heights[0],np.array(self.d.sales[index])/self.d.sales[index][0])
            fig.clear()

    def test_02_runway_angles(self):
        for index,total in enumerate([1664,1682,1638,1637]):
            vals=[r[index] for r in self.d.staff]; self.assertEqual(sum(vals),total)
            fig=self.draw(1,dict(index=index))
            np.testing.assert_allclose([p.theta2-p.theta1 for p in fig.axes[0].patches],np.array(vals)*720/total)
            fig.clear()

    def test_03_traffic_periods(self):
        for index in range(2):
            self.assertAlmostEqual(sum(self.d.traffic[index]),1)
            fig=self.draw(2,dict(index=index))
            labels=[t.get_text() for t in fig.axes[0].texts]
            for name,v in zip(self.d.traffic_names,self.d.traffic[index]): self.assertIn(f'{name}, {v:.0%}',labels)
            fig.clear()

    def test_04_all_metric_combinations(self):
        for flags in itertools.product([False,True],repeat=3):
            fig=self.draw(3,dict(visible=flags)); ax=fig.axes[0]
            self.assertEqual(len(ax.patches),4*sum(flags[:2]))
            self.assertEqual(len(ax.lines),1+int(flags[2]))
            if flags[2]: np.testing.assert_allclose(ax.lines[-1].get_ydata(),490-(np.array(self.d.margin)+1)*120/2800*4000)
            fig.clear()

    def test_05_salary_all_128_subsets(self):
        expected=[6138.317391304347,7187,5853.630136986301,6739.0123456790125,6908.042016806723]
        np.testing.assert_allclose(self.d.salaries(['市场拓展']),expected)
        self.assertEqual(len(self.d.people),1470)
        for flags in itertools.product([False,True],repeat=len(self.d.departments)):
            selected=[n for n,v in zip(self.d.departments,flags) if v]
            result=self.d.salaries(selected)
            for name,actual in zip(EDUCATION,result):
                rows=[r[6] for r in self.d.people if r[2] in selected and r[3]==name]
                if rows: self.assertAlmostEqual(actual,sum(rows)/len(rows))
                else: self.assertIsNone(actual)
            fig=self.draw(4,dict(departments=selected)); fig.clear()
        with self.assertRaises(ValueError): self.d.salaries(['不存在'])

    def test_06_jade_both_periods(self):
        for index in range(2):
            fig=self.draw(5,dict(index=index))
            np.testing.assert_allclose([p.theta2-p.theta1 for p in fig.axes[0].patches],np.array(self.d.jade[index])*720)
            fig.clear()

    def test_07_beads_both_modes_all_options(self):
        for mode,index in itertools.product(range(2),range(6)):
            labels,values=self.d.beads(mode,index)
            expected=np.array(self.d.rates)[:,index] if mode==0 else np.array(self.d.rates)[index,:]
            np.testing.assert_allclose(values,expected)
            fig=self.draw(6,dict(mode=mode,index=index))
            dots=[p for p in fig.axes[0].patches if hasattr(p,'center')]
            np.testing.assert_allclose([p.center[0] for p in dots],85+585*expected)
            fig.clear()

    def test_08_tk_real_controls(self):
        from app import ChartApp
        root=tk.Tk(); root.withdraw()
        try:
            app=ChartApp(root)
            for case in range(7):
                app.select_case(case); root.update()
                if case in (0,1,2):
                    app.option.current(1); app.option.event_generate('<<ComboboxSelected>>'); root.update()
                    self.assertEqual(app.states[case]['index'],1)
                elif case==3:
                    app.flags[0].set(False); app.change_flags(); self.assertFalse(app.states[3]['visible'][0])
                elif case==4:
                    app.set_departments(False); self.assertEqual(app.states[4]['departments'],())
                    app.set_departments(True); self.assertEqual(len(app.states[4]['departments']),7)
                elif case==5:
                    app.period.set(0)
                    for child in app.controls.winfo_children():
                        if isinstance(child,__import__('tkinter').ttk.Radiobutton) and child.cget('value')==0: child.invoke()
                    self.assertEqual(app.states[5]['index'],0)
                else:
                    app.mode.set(1); app.change_mode(); self.assertEqual(app.states[6]['mode'],1)
                    self.assertEqual(tuple(app.option['values']),tuple(self.d.regions))
                    app.option.current(5); app.option.event_generate('<<ComboboxSelected>>'); root.update()
                    self.assertEqual(app.states[6]['index'],5)
                app.reset(); self.assertEqual(app.states[case],default_state(case))
            path=app.save_current(); self.assertTrue(path.is_relative_to(ROOT)); self.assertTrue(path.exists())
            self.assertTrue(path.with_suffix('.json').exists())
        finally: root.destroy()

if __name__=='__main__': unittest.main(verbosity=2)
