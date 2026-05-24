import sys
import os
import json
import inspect
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
try:
    from boundary_equation import solve_boundary
except ImportError:
    try:
        from boundary_equation import solve_boundary
    except ImportError:
        solve_boundary = None

def fix_syntax(eq):
    if not eq:
        return eq
    eq = re.sub(r'\bE\b', 'np.e', eq)
    eq = re.sub(r'\bpi\b', 'np.pi', eq)
    eq = re.sub(r'\b(sin|cos|tan|exp|log|sqrt)\b', r'np.\1', eq)
    def replacer(match):
        prefix = match.group(1)
        index = int(match.group(2)) - 1
        return f"{prefix}[{index}]"
    return re.sub(r'\b(x|xa|xb|p)(\d+)\b', replacer, eq)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.language = 'ru'
        self.init_translations()
        
        self.setMinimumSize(1200, 800) 
        
        self.ode_edits = []
        self.bc_edits = []
        self.init_approx_edits = []
        
        self.current_n = 2
        
        self.param_keys = ['a', 'b', 't_star', 'step_mu', 'tol', 'max_iter']
        self.param_defaults = ["0.0", "7.0", "0.0", "0.05", "1e-6", "100"]
        
        self.last_math_result = None
        
        self.setupUI()
        self.createMenuBar()
        self.createStatusBar()
        
        self.update_dimension()
        self.update_texts() 
        
    def init_translations(self):
        self.texts = {
            'ru': {
                'title': "Метод продолжения по параметру — решение краевых задач",
                'ode': "ОДУ: ẋ = f(t, x)",
                'add': "➕ Добавить поле",
                'remove': "➖ Убрать поле",
                'bc': "Краевые условия R(x(a), x(b)) = 0",
                'init': "Нач. приближение p₀ (в точке t*)",
                'params': "Параметры",
                'plot': "ГРАФИК РЕШЕНИЯ y(x)",
                'data': "ЧИСЛЕННЫЕ ДАННЫЕ",
                'solve': " РЕШИТЬ",
                'load': " ЗАГРУЗИТЬ",
                'save': " СОХРАНИТЬ",
                'clear': " ОЧИСТИТЬ",
                'file': "Файл",
                'load_action': "Загрузить задачу",
                'save_action': "Сохранить задачу",
                'exit': "Выход",
                'menu': "Меню",
                'switch_lang': "切换语言为中文 (Сменить на китайский)",
                'info': "Инфо",
                'about_author': "Об авторе",
                'about_project': "О проекте",
                'param_labels': ["Левый конец a:", "Правый конец b:", "Точка t*:", "Шаг по μ:", "Точность ε:", "Макс. итер.:"],
                'ready': " Готов. Уравнений в системе:",
                'vars_t': "Переменные:",
                'err': "Ошибка",
                'success_clear': "Очищено",
                'success_save': "Задача успешно сохранена",
                'success_load': "Задача загружена",
                'table_cols': ["Параметр / Итерация", "Значение / Невязка"],
                'plot_type_traj': "Траектория решения x(t)",
                'plot_type_phase': "Фазовая плоскость (x1, x2)",
                'plot_type_param': "Плоскость параметров / μ",
                'plot_type_iter': "График итераций (Невязка R)",
                'btn_save_plot': "💾 Сохранить график",
                'title_traj': "Решение краевой задачи",
                'title_phase': "Фазовая плоскость",
                'title_param': "Путь параметров",
                'title_iter': "Лог итераций"
            },
            'zh': {
                'title': "参数连续法 — 边值问题求解",
                'ode': "常微分方程: ẋ = f(t, x)",
                'add': "➕ 添加字段",
                'remove': "➖ 删除字段",
                'bc': "边界条件 R(x(a), x(b)) = 0",
                'init': "初始近似值 p₀ (在点 t*)",
                'params': "参数",
                'plot': "解的图形 y(x)",
                'data': "数值数据",
                'solve': " 求解",
                'load': " 加载",
                'save': " 保存",
                'clear': " 清除",
                'file': "文件",
                'load_action': "加载任务",
                'save_action': "保存任务",
                'exit': "退出",
                'menu': "菜单",
                'switch_lang': "Сменить язык на русский (切换为俄语)",
                'info': "信息",
                'about_author': "关于作者",
                'about_project': "关于项目",
                'param_labels': ["左端点 a:", "右端点 b:", "点 t*:", "步长 μ:", "精度 ε:", "最大迭代次数:"],
                'ready': " 准备就绪。系统中的方程数:",
                'vars_t': "变量:",
                'err': "错误",
                'success_clear': "已清除",
                'success_save': "任务已成功保存",
                'success_load': "任务已加载",
                'table_cols': ["参数 / 迭代", "数值 / 残差"],
                'plot_type_traj': "解的轨迹 x(t)",
                'plot_type_phase': "相平面 (x1, x2)",
                'plot_type_param': "参数平面 / μ",
                'plot_type_iter': "迭代图 (残差 R)",
                'btn_save_plot': "💾 保存图形",
                'title_traj': "边值问题的解",
                'title_phase': "相平面",
                'title_param': "参数路径",
                'title_iter': "迭代日志"
            }
        }

    def setupUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #f5ebd2; }
            QGroupBox {
                background-color: #faf3e0;
                border: 2px solid #d4a574;
                border-radius: 10px;
                margin-top: 18px;
                font-weight: bold;
                font-size: 13px;
                color: #6b3f1c;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #8b5a2b;
            }
            QLabel { color: #6b3f1c; font-size: 12px; font-weight: 500; }
            QLineEdit, QDoubleSpinBox, QComboBox {
                background-color: #fffef7; border: 1px solid #d4a574;
                border-radius: 6px; padding: 4px 8px; color: #4a2a0e;
                font-size: 12px; min-height: 24px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus { border: 1px solid #c49a6c; background-color: #ffffff; }
            QPushButton {
                background-color: #d4a574; color: white; border: none;
                border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #c49a6c; }
            QPushButton:pressed { background-color: #b08a5e; }
            QPushButton#SmallBtn { padding: 4px 8px; font-size: 11px; border-radius: 4px; background-color: #c49a6c; }
            QPushButton#SmallBtn:hover { background-color: #b08a5e; }
            QProgressBar {
                background-color: #fffef7; border: 1px solid #d4a574;
                border-radius: 6px; text-align: center; color: #6b3f1c;
                font-weight: bold; height: 20px;
            }
            QProgressBar::chunk { background-color: #c49a6c; border-radius: 5px; }
            QScrollArea { border: none; background-color: transparent; }
            QScrollArea > QWidget > QWidget { background-color: transparent; }
            QMenuBar { background-color: #f0e4cc; color: #6b3f1c; }
            QMenuBar::item:selected { background-color: #d4a574; color: white; }
            QMenu { background-color: #faf3e0; border: 1px solid #d4a574; }
            QMenu::item:selected { background-color: #d4a574; color: white; }
            QTableWidget { background-color: #fffef7; gridline-color: #d4a574; border: 1px solid #d4a574; color: #4a2a0e; border-radius: 6px; }
            QHeaderView::section { background-color: #d4a574; color: white; font-weight: bold; border: 1px solid #c49a6c; }
        """)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(350)
        
        top_params_widget = QWidget()
        top_layout = QHBoxLayout(top_params_widget)
        top_layout.setSpacing(15)
        top_layout.setContentsMargins(0, 0, 10, 0)
        
        self.ode_group = QGroupBox()
        self.ode_group_layout = QVBoxLayout()
        
        ctrl_layout = QHBoxLayout()
        self.btn_add = QPushButton()
        self.btn_remove = QPushButton()
        self.btn_add.setObjectName("SmallBtn")
        self.btn_remove.setObjectName("SmallBtn")
        
        self.btn_add.clicked.connect(self.add_field)
        self.btn_remove.clicked.connect(self.remove_field)
        
        ctrl_layout.addWidget(self.btn_add)
        ctrl_layout.addWidget(self.btn_remove)
        ctrl_layout.addStretch()
        self.ode_group_layout.addLayout(ctrl_layout)
        
        self.ode_vars_label = QLabel()
        self.ode_vars_label.setStyleSheet("color: #a37c58;")
        self.ode_group_layout.addWidget(self.ode_vars_label)
        
        self.dynamic_ode_layout = QVBoxLayout()
        self.ode_group_layout.addLayout(self.dynamic_ode_layout)
        self.ode_group_layout.addStretch()
        
        self.ode_group.setLayout(self.ode_group_layout)
        top_layout.addWidget(self.ode_group)
        
        col2_layout = QVBoxLayout()
        
        self.bc_group = QGroupBox()
        self.bc_group_layout = QVBoxLayout()
        self.bc_vars_label = QLabel()
        self.bc_vars_label.setStyleSheet("color: #a37c58;")
        self.bc_group_layout.addWidget(self.bc_vars_label)
        
        self.dynamic_bc_layout = QVBoxLayout()
        self.bc_group_layout.addLayout(self.dynamic_bc_layout)
        self.bc_group_layout.addStretch()
        self.bc_group.setLayout(self.bc_group_layout)
        col2_layout.addWidget(self.bc_group)
        
        self.init_group = QGroupBox()
        self.init_group_layout = QVBoxLayout()
        self.dynamic_init_layout = QVBoxLayout()
        self.init_group_layout.addLayout(self.dynamic_init_layout)
        self.init_group_layout.addStretch()
        self.init_group.setLayout(self.init_group_layout)
        col2_layout.addWidget(self.init_group)
        
        top_layout.addLayout(col2_layout)
        
        self.static_params_group = QGroupBox()
        sp_layout = QGridLayout()
        sp_layout.setVerticalSpacing(8)
        
        self.param_edits = {}
        self.param_label_widgets = {}
        
        for i, key in enumerate(self.param_keys):
            lbl = QLabel()
            self.param_label_widgets[key] = lbl
            sp_layout.addWidget(lbl, i, 0)
            edit = QLineEdit(self.param_defaults[i])
            self.param_edits[key] = edit
            sp_layout.addWidget(edit, i, 1)
            
        sp_layout.setRowStretch(len(self.param_keys), 1)
        self.static_params_group.setLayout(sp_layout)
        top_layout.addWidget(self.static_params_group)
        
        scroll_area.setWidget(top_params_widget)
        main_layout.addWidget(scroll_area, stretch=0)
        
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        results_h_layout = QHBoxLayout()
        
        self.plot_group = QGroupBox()
        plot_layout = QVBoxLayout()
        
        plot_ctrl_layout = QHBoxLayout()
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.currentIndexChanged.connect(self.redraw_current_graph)
        self.btn_save_plot = QPushButton()
        self.btn_save_plot.clicked.connect(self.save_plot_image)
        
        plot_ctrl_layout.addWidget(self.plot_type_combo)
        plot_ctrl_layout.addWidget(self.btn_save_plot)
        plot_ctrl_layout.addStretch()
        
        plot_layout.addLayout(plot_ctrl_layout)
        
        self.figure, self.ax = plt.subplots()
        self.figure.patch.set_facecolor('#fffef7')
        self.canvas = FigureCanvas(self.figure)
        plot_layout.addWidget(self.canvas)
        self.plot_group.setLayout(plot_layout)
        results_h_layout.addWidget(self.plot_group, stretch=2)
        
        self.data_group = QGroupBox()
        data_layout = QVBoxLayout()
        self.results_table = QTableWidget(0, 2)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        data_layout.addWidget(self.results_table)
        self.data_group.setLayout(data_layout)
        results_h_layout.addWidget(self.data_group, stretch=1)
        
        bottom_layout.addLayout(results_h_layout, stretch=1)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)
        
        btn_layout = QHBoxLayout()
        self.solve_btn = QPushButton()
        self.solve_btn.setMinimumWidth(150)
        self.solve_btn.clicked.connect(self.on_solve_clicked)
        
        self.load_btn = QPushButton()
        self.load_btn.clicked.connect(self.on_load_clicked)
        
        self.save_btn = QPushButton()
        self.save_btn.clicked.connect(self.on_save_clicked)
        
        self.clear_btn = QPushButton()
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.solve_btn)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        
        bottom_layout.addLayout(btn_layout)
        main_layout.addWidget(bottom_panel, stretch=1)

    def createMenuBar(self):
        menubar = self.menuBar()
        
        self.file_menu = menubar.addMenu("")
        self.load_action = QAction("", self)
        self.load_action.triggered.connect(self.on_load_clicked)
        self.file_menu.addAction(self.load_action)
        
        self.save_action = QAction("", self)
        self.save_action.triggered.connect(self.on_save_clicked)
        self.file_menu.addAction(self.save_action)
        
        self.file_menu.addSeparator()
        self.exit_action = QAction("", self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        self.settings_menu = menubar.addMenu("")
        self.lang_action = QAction("", self)
        self.lang_action.triggered.connect(self.change_language)
        self.settings_menu.addAction(self.lang_action)

        self.info_menu = menubar.addMenu("")
        self.author_action = QAction("", self)
        self.author_action.triggered.connect(self.show_author_info)
        self.info_menu.addAction(self.author_action)
        
        self.project_action = QAction("", self)
        self.project_action.triggered.connect(self.show_project_info)
        self.info_menu.addAction(self.project_action)

    def update_texts(self):
        t = self.texts[self.language]
        self.setWindowTitle(t['title'])
        self.ode_group.setTitle(t['ode'])
        self.btn_add.setText(t['add'])
        self.btn_remove.setText(t['remove'])
        self.bc_group.setTitle(t['bc'])
        self.init_group.setTitle(t['init'])
        self.static_params_group.setTitle(t['params'])
        self.plot_group.setTitle(t['plot'])
        self.data_group.setTitle(t['data'])
        self.solve_btn.setText(t['solve'])
        self.load_btn.setText(t['load'])
        self.save_btn.setText(t['save'])
        self.clear_btn.setText(t['clear'])
        
        self.file_menu.setTitle(t['file'])
        self.load_action.setText(t['load_action'])
        self.save_action.setText(t['save_action'])
        self.exit_action.setText(t['exit'])
        
        self.settings_menu.setTitle(t['menu'])
        self.lang_action.setText(t['switch_lang'])
        
        self.info_menu.setTitle(t['info'])
        self.author_action.setText(t['about_author'])
        self.project_action.setText(t['about_project'])
        
        self.results_table.setHorizontalHeaderLabels(t['table_cols'])
        
        idx = self.plot_type_combo.currentIndex()
        if idx < 0:
            idx = 0
        self.plot_type_combo.blockSignals(True)
        self.plot_type_combo.clear()
        self.plot_type_combo.addItems([
            t['plot_type_traj'],
            t['plot_type_phase'],
            t['plot_type_param'],
            t['plot_type_iter']
        ])
        self.plot_type_combo.setCurrentIndex(idx)
        self.plot_type_combo.blockSignals(False)
        self.btn_save_plot.setText(t['btn_save_plot'])
        
        for i, key in enumerate(self.param_keys):
            self.param_label_widgets[key].setText(t['param_labels'][i])
            
        self.update_dimension_texts()
        self.statusbar.showMessage(f"{t['ready']} {self.current_n}")

    def change_language(self):
        self.language = 'zh' if self.language == 'ru' else 'ru'
        self.update_texts()

    def add_field(self):
        if self.current_n < 10:
            self.current_n += 1
            self.update_dimension()
            self.update_dimension_texts()

    def remove_field(self):
        if self.current_n > 1:
            self.current_n -= 1
            self.update_dimension()
            self.update_dimension_texts()

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def update_dimension_texts(self):
        n = self.current_n
        t = self.texts[self.language]
        
        vars_str = ", ".join([f"x{i+1}" for i in range(n)])
        self.ode_vars_label.setText(f"{t['vars_t']} {vars_str}, t")
        
        bc_vars = ", ".join([f"xa{i+1}" for i in range(n)]) + ", " + ", ".join([f"xb{i+1}" for i in range(n)])
        self.bc_vars_label.setText(bc_vars)

    def update_dimension(self):
        self.clear_layout(self.dynamic_ode_layout)
        self.clear_layout(self.dynamic_bc_layout)
        self.clear_layout(self.dynamic_init_layout)
        
        self.ode_edits.clear()
        self.bc_edits.clear()
        self.init_approx_edits.clear()
        
        n = self.current_n
        
        for i in range(n):
            row_ode = QHBoxLayout()
            row_ode.addWidget(QLabel(f"ẋ{i+1} ="))
            edit_ode = QLineEdit()
            self.ode_edits.append(edit_ode)
            row_ode.addWidget(edit_ode)
            self.dynamic_ode_layout.addLayout(row_ode)
            
            row_bc = QHBoxLayout()
            row_bc.addWidget(QLabel(f"R{i+1} ="))
            edit_bc = QLineEdit()
            self.bc_edits.append(edit_bc)
            row_bc.addWidget(edit_bc)
            self.dynamic_bc_layout.addLayout(row_bc)
            
            row_init = QHBoxLayout()
            row_init.addWidget(QLabel(f"p{i+1}₀ ="))
            edit_init = QLineEdit("0.0")
            self.init_approx_edits.append(edit_init)
            row_init.addWidget(edit_init)
            self.dynamic_init_layout.addLayout(row_init)

    def show_author_info(self):
        author_dialog = QDialog(self)
        author_dialog.setWindowTitle(self.texts[self.language]['about_author'])
        author_dialog.setFixedSize(450, 500)
        author_dialog.setStyleSheet("background-color: #faf3e0;")
        
        layout = QVBoxLayout()
        text_label = QLabel(
            "Выполнил: Прибытков Андрей 313 группа.\n"
            "Старший преподаватель: Сергей Николаевич Аввакумов."
        )
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #6b3f1c;")
        layout.addWidget(text_label)
        
        img_label = QLabel()
        img_path = os.path.join("images", "photo.jpg")
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            img_label.setText("Фото не найдено в папке images/")
            img_label.setAlignment(Qt.AlignCenter)
        else:
            img_label.setPixmap(pixmap.scaled(300, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_label)
        
        close_btn = QPushButton("OK")
        close_btn.clicked.connect(author_dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        author_dialog.setLayout(layout)
        author_dialog.exec_()

    def show_project_info(self):
        msg = "Некоммерческий проект для решения краевых задач методом продолжения по параметру."
        QMessageBox.information(self, self.texts[self.language]['about_project'], msg)

    def createStatusBar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

    def redraw_current_graph(self):
        if not self.last_math_result:
            return
            
        t = self.texts[self.language]
        idx = self.plot_type_combo.currentIndex()
        res = self.last_math_result
        
        try:
            a = float(self.param_edits['a'].text())
            b = float(self.param_edits['b'].text())
        except ValueError:
            return
            
        self.ax.clear()
        self.ax.set_yscale('linear')
        
        if idx == 0:
            if res.get('sol_forward'):
                t_plot = np.linspace(a, b, 200)
                y_plot = res['sol_forward'].sol(t_plot)
                for i in range(self.current_n):
                    self.ax.plot(t_plot, y_plot[i], label=f'x{i+1}')
                self.ax.legend()
                self.ax.set_title(t['title_traj'])
                self.ax.grid(True, linestyle='--', alpha=0.7)
                
        elif idx == 1:
            if res.get('sol_forward') and self.current_n >= 2:
                t_plot = np.linspace(a, b, 200)
                y_plot = res['sol_forward'].sol(t_plot)
                self.ax.plot(y_plot[0], y_plot[1], '#1f77b4', linewidth=2, label="Траектория" if self.language == 'ru' else "轨迹")
                self.ax.plot(y_plot[0][0], y_plot[1][0], 'go', markersize=7, label="Старт (t=a)" if self.language == 'ru' else "起点")
                self.ax.plot(y_plot[0][-1], y_plot[1][-1], 'ro', markersize=7, label="Финиш (t=b)" if self.language == 'ru' else "终点")
                self.ax.set_xlabel("x1")
                self.ax.set_ylabel("x2")
                self.ax.set_title(t['title_phase'])
                self.ax.legend()
                self.ax.grid(True, linestyle='--', alpha=0.7)
                
        elif idx == 2:
            p_hist = res.get('p_history', [])
            mu_hist = res.get('mu_history', [])
            if p_hist and mu_hist:
                p_arr = np.array(p_hist)
                if p_arr.shape[1] >= 2:
                    self.ax.plot(p_arr[:, 0], p_arr[:, 1], '#2ca02c', linewidth=2, marker='.', markersize=4, label="Путь параметров" if self.language == 'ru' else "参数路径")
                    self.ax.plot(p_arr[0, 0], p_arr[0, 1], 'go', label="μ = 0")
                    self.ax.plot(p_arr[-1, 0], p_arr[-1, 1], 'ro', label="μ = 1")
                    self.ax.set_xlabel("p1")
                    self.ax.set_ylabel("p2")
                else:
                    self.ax.plot(mu_hist, p_arr[:, 0], '#2ca02c', linewidth=2, marker='.')
                    self.ax.set_xlabel("μ")
                    self.ax.set_ylabel("p1")
                self.ax.set_title(t['title_param'])
                self.ax.legend()
                self.ax.grid(True, linestyle='--', alpha=0.7)
            else:
                self.ax.text(0.5, 0.5, "Нет данных пути параметров", ha="center", va="center")
                
        elif idx == 3:
            residuals = res.get('residuals', [])
            if not residuals and 'history' in res:
                residuals = []
                for h in res['history']:
                    if isinstance(h, tuple):
                        residuals.append(h[1])
                    elif isinstance(h, str) and "R=" in h:
                        try:
                            r_val = float(h.split("R=")[-1].strip())
                            residuals.append(r_val)
                        except Exception:
                            pass
            if residuals:
                iters = list(range(1, len(residuals) + 1))
                self.ax.plot(iters, residuals, '#ff7f0e', linewidth=2, marker='o', markersize=5, label="||R||")
                self.ax.set_yscale('log')
                self.ax.set_xlabel("Итерация" if self.language == 'ru' else "迭代")
                self.ax.set_ylabel("Невязка (log)" if self.language == 'ru' else "残差 (log)")
                self.ax.set_title(t['title_iter'])
                self.ax.legend()
                self.ax.grid(True, linestyle='--', alpha=0.7)
            else:
                self.ax.text(0.5, 0.5, "Нет данных лога итераций", ha="center", va="center")
        
        self.canvas.draw()

    def save_plot_image(self):
        t = self.texts[self.language]
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, t['save_action'], "", "PNG Images (*.png);;JPEG Images (*.jpg);;All Files (*)", options=options)
        
        if file_name:
            try:
                self.figure.savefig(file_name, facecolor=self.figure.get_facecolor(), edgecolor='none', dpi=300)
                QMessageBox.information(self, t['info'], t['success_save'])
            except Exception as e:
                QMessageBox.critical(self, t['err'], str(e))

    def on_solve_clicked(self):
        t = self.texts[self.language]
        try:
            if solve_boundary is None:
                raise ImportError("Не найден модуль расчёта.")

            raw_equations = [edit.text().strip() for edit in self.ode_edits]
            raw_conditions = [edit.text().strip() for edit in self.bc_edits]
            p0_strs = [edit.text().strip() for edit in self.init_approx_edits]

            while raw_equations and raw_equations[-1] == "" and raw_conditions[-1] == "":
                raw_equations.pop()
                raw_conditions.pop()
                p0_strs.pop()

            if not raw_equations:
                QMessageBox.critical(self, t['err'], "Введите уравнения.")
                return

            if any(not eq for eq in raw_equations) or any(not cond for cond in raw_conditions):
                QMessageBox.critical(self, t['err'], "Увидено пустое поле.")
                return

            equations = [fix_syntax(eq) for eq in raw_equations]
            conditions = [fix_syntax(cond) for cond in raw_conditions]

            try:
                p0 = [float(val) for val in p0_strs]
            except ValueError:
                QMessageBox.critical(self, t['err'], "Ошибка формата.")
                return
            
            a = float(self.param_edits['a'].text())
            b = float(self.param_edits['b'].text())
            t_star = float(self.param_edits['t_star'].text())
            step_mu = float(self.param_edits['step_mu'].text())
            tol = float(self.param_edits['tol'].text())
            max_iter = int(self.param_edits['max_iter'].text())

            sig = inspect.signature(solve_boundary)
            if 't_star' in sig.parameters:
                result = solve_boundary(equations, conditions, p0, t_star, a, b, step_mu, tol, max_iter)
            else:
                result = solve_boundary(equations, conditions, p0, a, b, step_mu, tol, max_iter)

            self.last_math_result = result
            
            msg = result.get('message', "Расчет завершен.")
            self.statusbar.showMessage(msg)
            self.results_table.setRowCount(0)
            
            if 'history' in result:
                for item in result['history']:
                    if isinstance(item, tuple):
                        it, err = item
                        row = self.results_table.rowCount()
                        self.results_table.insertRow(row)
                        self.results_table.setItem(row, 0, QTableWidgetItem(f"Итерация {it}" if self.language == 'ru' else f"迭代 {it}"))
                        self.results_table.setItem(row, 1, QTableWidgetItem(f"{err:.4e}"))
                    elif isinstance(item, str):
                        row = self.results_table.rowCount()
                        self.results_table.insertRow(row)
                        self.results_table.setItem(row, 0, QTableWidgetItem("Итерация"))
                        self.results_table.setItem(row, 1, QTableWidgetItem(item))
            
            xa_list = []
            xb_list = []
            if result.get('sol_forward') is not None:
                xa_list = result['sol_forward'].y[:, 0]
                xb_list = result['sol_forward'].y[:, -1]
            
            if len(xa_list) == self.current_n and len(xb_list) == self.current_n:
                for i, (va, vb) in enumerate(zip(xa_list, xb_list)):
                    r = self.results_table.rowCount()
                    self.results_table.insertRow(r)
                    self.results_table.setItem(r, 0, QTableWidgetItem(f"x{i+1} в a" if self.language == 'ru' else f"x{i+1} 在 a"))
                    self.results_table.setItem(r, 1, QTableWidgetItem(f"{va:.4f}"))
                    r = self.results_table.rowCount()
                    self.results_table.insertRow(r)
                    self.results_table.setItem(r, 0, QTableWidgetItem(f"x{i+1} в b" if self.language == 'ru' else f"x{i+1} 在 b"))
                    self.results_table.setItem(r, 1, QTableWidgetItem(f"{vb:.4f}"))

            if result.get('sol_forward') is None and 'message' in result:
                pass 
            
            self.redraw_current_graph()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, t['err'], f"Ошибка при расчете:\n{str(e)}")

    def on_save_clicked(self):
        t = self.texts[self.language]
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, t['save_action'], "", "JSON Files (*.json);;All Files (*)", options=options)
        
        if file_name:
            data = {
                "n": self.current_n,
                "equations": [edit.text() for edit in self.ode_edits],
                "conditions": [edit.text() for edit in self.bc_edits],
                "p0": [edit.text() for edit in self.init_approx_edits],
                "params": {k: edit.text() for k, edit in self.param_edits.items()}
            }
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                self.statusbar.showMessage(t['success_save'])
            except Exception as e:
                QMessageBox.critical(self, t['err'], f"Ошибка сохранения:\n{str(e)}")

    def on_load_clicked(self):
        t = self.texts[self.language]
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, t['load_action'], "", "JSON Files (*.json);;All Files (*)", options=options)
        
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.current_n = data.get("n", 2)
                self.update_dimension()
                self.update_dimension_texts()
                
                for edit, text in zip(self.ode_edits, data.get("equations", [])):
                    edit.setText(text)
                for edit, text in zip(self.bc_edits, data.get("conditions", [])):
                    edit.setText(text)
                for edit, text in zip(self.init_approx_edits, data.get("p0", [])):
                    edit.setText(text)
                
                loaded_params = data.get("params", {})
                for key in self.param_keys:
                    if key in loaded_params:
                        self.param_edits[key].setText(loaded_params[key])
                        
                self.statusbar.showMessage(t['success_load'])
            except Exception as e:
                QMessageBox.critical(self, t['err'], f"Ошибка загрузки:\n{str(e)}")

    def on_clear_clicked(self):
        self.current_n = 2
        self.update_dimension()
        self.update_dimension_texts()
        
        for i, key in enumerate(self.param_keys):
            self.param_edits[key].setText(self.param_defaults[i])
            
        self.ax.clear()
        self.canvas.draw()
        self.results_table.setRowCount(0)
        self.statusbar.showMessage(self.texts[self.language]['success_clear'])
        self.last_math_result = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())