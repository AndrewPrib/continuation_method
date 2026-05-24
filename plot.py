import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.font_manager")

matplotlib.rcParams['font.family'] = ['Arial Unicode MS', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False 

class Plotter:
    def __init__(self, p_f):
        self.fig, self.ax = plt.subplots(figsize=(6, 5), facecolor='#2b2b2b')
        self.fig.subplots_adjust(left=0.18, right=0.95, bottom=0.20, top=0.95)
        
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        
        for sp_ in self.ax.spines.values():
            sp_.set_color('white')
            
        self.ax.grid(True, linestyle="--", alpha=0.3)
        
        self.canv = FigureCanvasTkAgg(self.fig, master=p_f)
        self.canv.get_tk_widget().pack(fill="both", expand=True)

        self.colors = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b']

    def clear(self):
        self.ax.clear()
        self.ax.set_facecolor('#2b2b2b')
        self.ax.grid(True, linestyle="--", alpha=0.3)
        self.ax.tick_params(bottom=True, left=True, labelbottom=True, labelleft=True, colors='white')
        for sp_ in self.ax.spines.values():
            sp_.set_visible(True)
            sp_.set_color('white')
        self.canv.draw()

    def set_empty_labels(self, x_l, y_l):
        self.ax.set_xlabel(x_l, color='white', fontsize=12)
        self.ax.set_ylabel(y_l, color='white', fontsize=12)
        self.canv.draw()

    def show_under_dev(self, txt, c_txt="#ff5555"):
        self.ax.clear()
        self.ax.set_facecolor('#2b2b2b')
        self.ax.grid(False)
        self.ax.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)
        for sp_ in self.ax.spines.values():
            sp_.set_visible(False)
        self.ax.text(0.5, 0.5, txt, ha="center", va="center", transform=self.ax.transAxes, color=c_txt, fontsize=18, weight="bold")
        self.canv.draw()

    def plot_bvp_trajectories(self, ts, ys, n, colors=None, labels=None):
        self.clear()
        
        lbl_t = labels["t"] if labels and "t" in labels else "t"
        lbl_x = labels["x"] if labels and "x" in labels else "x(t)"
        
        self.ax.set_xlabel(lbl_t, color='white', fontsize=12)
        self.ax.set_ylabel(lbl_x, color='white', fontsize=12)

        for i in range(n):
            c = colors[i] if colors and i < len(colors) else self.colors[i % len(self.colors)]
            self.ax.plot(ts, ys[i], label=f"x{i+1}(t)", color=c, linewidth=2)
            
            self.ax.plot(ts[0], ys[i][0], marker='o', color=c, markersize=7) 
            self.ax.plot(ts[-1], ys[i][-1], marker='s', color=c, markersize=7)
        
        self.ax.legend(facecolor='#2b2b2b', labelcolor='white')
        self.canv.draw()

    def plot_phase_plane(self, ys, n, colors=None, labels=None, idx_x=0, idx_y=1):
        self.clear()
        
        if n < 2:
            e_m = labels["err_vars"] if labels and "err_vars" in labels else "Требуется ≥ 2 переменных"
            self.ax.text(0.5, 0.5, e_m, ha="center", va="center", color="#ff5555", fontsize=16)
            self.canv.draw()
            return
            
        lbl_x = labels.get(f"x{idx_x+1}", f"x{idx_x+1}") if labels else f"x{idx_x+1}"
        lbl_y = labels.get(f"x{idx_y+1}", f"x{idx_y+1}") if labels else f"x{idx_y+1}"
        
        self.ax.set_xlabel(lbl_x, color='white', fontsize=12)
        self.ax.set_ylabel(lbl_y, color='white', fontsize=12)
            
        c = colors[idx_x] if colors and len(colors) > idx_x else self.colors[0]
        
        lbl_tr = labels["traj"] if labels and "traj" in labels else "Траектория"
        lbl_st = labels["start"] if labels and "start" in labels else "Старт (t=a)"
        lbl_fn = labels["finish"] if labels and "finish" in labels else "Финиш (t=b)"
        
        self.ax.plot(ys[idx_x], ys[idx_y], color=c, linewidth=2, label=lbl_tr)
        self.ax.plot(ys[idx_x][0], ys[idx_y][0], 'go', markersize=8, label=lbl_st)
        self.ax.plot(ys[idx_x][-1], ys[idx_y][-1], 'ro', markersize=8, label=lbl_fn)
        
        self.ax.legend(facecolor='#2b2b2b', labelcolor='white')
        self.canv.draw()

    def plot_p_phase_plane(self, mus, ps, n, colors=None, labels=None, idx_x=0, idx_y=1):
        self.clear()
        
        if n < 2:
            e_m = labels["err_vars"] if labels and "err_vars" in labels else "Требуется ≥ 2 переменных"
            self.ax.text(0.5, 0.5, e_m, ha="center", va="center", color="#ff5555", fontsize=16)
            self.canv.draw()
            return
            
        lbl_x = labels.get(f"p{idx_x+1}", f"p{idx_x+1}") if labels else f"p{idx_x+1}"
        lbl_y = labels.get(f"p{idx_y+1}", f"p{idx_y+1}") if labels else f"p{idx_y+1}"
        
        self.ax.set_xlabel(lbl_x, color='white', fontsize=12)
        self.ax.set_ylabel(lbl_y, color='white', fontsize=12)

        c = colors[idx_x] if colors and len(colors) > idx_x else self.colors[0]
        
        lbl_tr = labels["traj"] if labels and "traj" in labels else "Траектория"
        lbl_st = labels["start"] if labels and "start" in labels else "Старт (μ=0)"
        lbl_fn = labels["finish"] if labels and "finish" in labels else "Финиш (μ=1)"
        
        self.ax.plot(ps[idx_x], ps[idx_y], color=c, linewidth=2, marker='.', markersize=5, label=lbl_tr)
        self.ax.plot(ps[idx_x][0], ps[idx_y][0], 'go', markersize=8, label=lbl_st)
        self.ax.plot(ps[idx_x][-1], ps[idx_y][-1], 'ro', markersize=8, label=lbl_fn)
        
        self.ax.legend(facecolor='#2b2b2b', labelcolor='white')
        self.canv.draw()

    def save(self, f_path):
        self.fig.savefig(f_path, facecolor=self.fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=300)