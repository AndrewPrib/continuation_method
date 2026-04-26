import sys
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

try:
    from src.solver import solve_boundary
except ImportError:
    pass

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
        self.param_defaults = ["0", "0", "0", "0", "0", "0"]
        
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
                'table_cols': ["Параметр / Итерация", "Значение / Невязка"]
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
                'table_cols': ["参数 / 迭代", "数值 / 残差"]
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
            QLineEdit, QDoubleSpinBox {
                background-color: #fffef7; border: 1px solid #d4a574;
                border-radius: 6px; padding: 4px 8px; color: #4a2a0e;
                font-size: 12px; min-height: 24px;
            }
            QLineEdit:focus { border: 1px solid #c49a6c; background-color: #ffffff; }
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
        vars_str = ", ".join([f"x[{i}]" for i in range(n)])
        self.ode_vars_label.setText(f"{t['vars_t']} {vars_str}, t")
        bc_vars = ", ".join([f"xa[{i}]" for i in range(n)]) + ", " + ", ".join([f"xb[{i}]" for i in range(n)])
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
            edit_init = QLineEdit("0")
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
            "Преподаватель: Сергей Николаевич Аввакумов."
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

    def on_solve_clicked(self):
        t = self.texts[self.language]
        try:
            equations = [edit.text() for edit in self.ode_edits]
            conditions = [edit.text() for edit in self.bc_edits]
            p0 = [float(edit.text()) for edit in self.init_approx_edits]
            
            a = float(self.param_edits['a'].text())
            b = float(self.param_edits['b'].text())
            t_star = float(self.param_edits['t_star'].text())
            step_mu = float(self.param_edits['step_mu'].text())
            tol = float(self.param_edits['tol'].text())
            max_iter = int(self.param_edits['max_iter'].text())

            result = solve_boundary(equations, conditions, p0, t_star, a, b, step_mu, tol, max_iter)
            
            self.statusbar.showMessage(result['message'])
            self.results_table.setRowCount(0)
            
            if 'history' in result:
                for it, err in result['history']:
                    row = self.results_table.rowCount()
                    self.results_table.insertRow(row)
                    self.results_table.setItem(row, 0, QTableWidgetItem(f"Итерация {it}" if self.language == 'ru' else f"迭代 {it}"))
                    self.results_table.setItem(row, 1, QTableWidgetItem(f"{err:.4e}"))
                
                for i, (va, vb) in enumerate(zip(result.get('xa', []), result.get('xb', []))):
                    r = self.results_table.rowCount()
                    self.results_table.insertRow(r)
                    self.results_table.setItem(r, 0, QTableWidgetItem(f"x[{i}] в a" if self.language == 'ru' else f"x[{i}] 在 a"))
                    self.results_table.setItem(r, 1, QTableWidgetItem(f"{va:.4f}"))
                    r = self.results_table.rowCount()
                    self.results_table.insertRow(r)
                    self.results_table.setItem(r, 0, QTableWidgetItem(f"x[{i}] в b" if self.language == 'ru' else f"x[{i}] 在 b"))
                    self.results_table.setItem(r, 1, QTableWidgetItem(f"{vb:.4f}"))

            if result['sol_forward']:
                self.ax.clear()
                t_plot = np.linspace(a, b, 200)
                y_plot = result['sol_forward'].sol(t_plot)
                for i in range(self.current_n):
                    self.ax.plot(t_plot, y_plot[i], label=f'x[{i}]')
                self.ax.legend()
                title_str = "Решение краевой задачи" if self.language == 'ru' else "边值问题的解"
                self.ax.set_title(title_str)
                self.ax.grid(True, linestyle='--', alpha=0.7)
                self.canvas.draw()
            else:
                QMessageBox.warning(self, t['err'], result['message'])

        except Exception as e:
            QMessageBox.critical(self, t['err'], f"Ошибка при расчете / 计算错误:\n{str(e)}")

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