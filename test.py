import sys
import os
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
        self.setWindowTitle("Метод продолжения по параметру — решение краевых задач")
        self.setMinimumSize(1200, 800)
        
        self.ode_edits = []
        self.bc_edits = []
        self.init_approx_edits = []
        
        self.current_n = 2
        
        self.setupUI()
        self.createMenuBar()
        self.createStatusBar()
        
        self.update_dimension()
        
    def setupUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5ebd2;
            }
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
            QLabel {
                color: #6b3f1c;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit, QDoubleSpinBox {
                background-color: #fffef7;
                border: 1px solid #d4a574;
                border-radius: 6px;
                padding: 4px 8px;
                color: #4a2a0e;
                font-size: 12px;
                min-height: 24px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border: 1px solid #c49a6c;
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #d4a574;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c49a6c;
            }
            QPushButton:pressed {
                background-color: #b08a5e;
            }
            QPushButton#SmallBtn {
                padding: 4px 8px;
                font-size: 11px;
                border-radius: 4px;
                background-color: #c49a6c;
            }
            QPushButton#SmallBtn:hover {
                background-color: #b08a5e;
            }
            QProgressBar {
                background-color: #fffef7;
                border: 1px solid #d4a574;
                border-radius: 6px;
                text-align: center;
                color: #6b3f1c;
                font-weight: bold;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #c49a6c;
                border-radius: 5px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QMenuBar {
                background-color: #f0e4cc;
                color: #6b3f1c;
            }
            QMenuBar::item:selected {
                background-color: #d4a574;
                color: white;
            }
            QMenu {
                background-color: #faf3e0;
                border: 1px solid #d4a574;
            }
            QMenu::item:selected {
                background-color: #d4a574;
                color: white;
            }
        """)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(350)
        
        top_params_widget = QWidget()
        top_layout = QHBoxLayout(top_params_widget)
        top_layout.setSpacing(15)
        top_layout.setContentsMargins(0, 0, 10, 0)
        
        ode_group = QGroupBox("ОДУ: ẋ = f(t, x)")
        self.ode_group_layout = QVBoxLayout()
        
        ctrl_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Добавить поле")
        self.btn_remove = QPushButton("➖ Убрать поле")
        self.btn_add.setObjectName("SmallBtn")
        self.btn_remove.setObjectName("SmallBtn")
        
        self.btn_add.clicked.connect(self.add_field)
        self.btn_remove.clicked.connect(self.remove_field)
        
        ctrl_layout.addWidget(self.btn_add)
        ctrl_layout.addWidget(self.btn_remove)
        ctrl_layout.addStretch()
        self.ode_group_layout.addLayout(ctrl_layout)
        
        self.ode_vars_label = QLabel("Переменные: x[0], x[1], ..., t")
        self.ode_vars_label.setStyleSheet("color: #a37c58;")
        self.ode_group_layout.addWidget(self.ode_vars_label)
        
        self.dynamic_ode_layout = QVBoxLayout()
        self.ode_group_layout.addLayout(self.dynamic_ode_layout)
        self.ode_group_layout.addStretch()
        
        ode_group.setLayout(self.ode_group_layout)
        top_layout.addWidget(ode_group)
        
        col2_layout = QVBoxLayout()
        
        bc_group = QGroupBox("Краевые условия R(x(a), x(b)) = 0")
        self.bc_group_layout = QVBoxLayout()
        self.bc_vars_label = QLabel("xa[0], xa[1], ..., xb[0], xb[1]")
        self.bc_vars_label.setStyleSheet("color: #a37c58;")
        self.bc_group_layout.addWidget(self.bc_vars_label)
        
        self.dynamic_bc_layout = QVBoxLayout()
        self.bc_group_layout.addLayout(self.dynamic_bc_layout)
        self.bc_group_layout.addStretch()
        bc_group.setLayout(self.bc_group_layout)
        col2_layout.addWidget(bc_group)
        
        init_group = QGroupBox("Нач. приближение p₀ (в точке t*)")
        self.init_group_layout = QVBoxLayout()
        self.dynamic_init_layout = QVBoxLayout()
        self.init_group_layout.addLayout(self.dynamic_init_layout)
        self.init_group_layout.addStretch()
        init_group.setLayout(self.init_group_layout)
        col2_layout.addWidget(init_group)
        
        top_layout.addLayout(col2_layout)
        
        static_params_group = QGroupBox("Параметры")
        sp_layout = QGridLayout()
        sp_layout.setVerticalSpacing(8)
        
        labels = ["Левый конец a:", "Правый конец b:", "Точка t*:", 
                  "Шаг по μ:", "Точность ε:", "Макс. итер.:"]
        defaults = ["0.0", "1.57", "0.0", "0.1", "1e-6", "50"]
        self.param_edits = {}
        
        for i, (text, default) in enumerate(zip(labels, defaults)):
            sp_layout.addWidget(QLabel(text), i, 0)
            edit = QLineEdit(default)
            self.param_edits[text] = edit
            sp_layout.addWidget(edit, i, 1)
            
        sp_layout.setRowStretch(len(labels), 1)
        static_params_group.setLayout(sp_layout)
        top_layout.addWidget(static_params_group)
        
        scroll_area.setWidget(top_params_widget)
        main_layout.addWidget(scroll_area, stretch=0)
        
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        plot_group = QGroupBox("ГРАФИК РЕШЕНИЯ y(x)")
        plot_layout = QVBoxLayout()
        
        self.figure, self.ax = plt.subplots()
        self.figure.patch.set_facecolor('#fffef7')
        self.canvas = FigureCanvas(self.figure)
        plot_layout.addWidget(self.canvas)
        plot_group.setLayout(plot_layout)
        bottom_layout.addWidget(plot_group, stretch=1)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)
        
        btn_layout = QHBoxLayout()
        self.solve_btn = QPushButton(" РЕШИТЬ")
        self.solve_btn.setMinimumWidth(150)
        self.solve_btn.clicked.connect(self.on_solve_clicked)
        
        self.load_btn = QPushButton(" ЗАГРУЗИТЬ")
        self.load_btn.clicked.connect(self.on_load_clicked)
        
        self.save_btn = QPushButton(" СОХРАНИТЬ")
        self.save_btn.clicked.connect(self.on_save_clicked)
        
        self.clear_btn = QPushButton(" ОЧИСТИТЬ")
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.solve_btn)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        
        bottom_layout.addLayout(btn_layout)
        
        main_layout.addWidget(bottom_panel, stretch=1)

    def add_field(self):
        if self.current_n < 10:
            self.current_n += 1
            self.update_dimension()

    def remove_field(self):
        if self.current_n > 1:
            self.current_n -= 1
            self.update_dimension()

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def update_dimension(self):
        self.clear_layout(self.dynamic_ode_layout)
        self.clear_layout(self.dynamic_bc_layout)
        self.clear_layout(self.dynamic_init_layout)
        
        self.ode_edits.clear()
        self.bc_edits.clear()
        self.init_approx_edits.clear()
        
        n = self.current_n
        
        vars_str = ", ".join([f"x[{i}]" for i in range(n)])
        self.ode_vars_label.setText(f"Переменные: {vars_str}, t")
        
        bc_vars = ", ".join([f"xa[{i}]" for i in range(n)]) + ", " + ", ".join([f"xb[{i}]" for i in range(n)])
        self.bc_vars_label.setText(bc_vars)
        
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
            edit_init = QLineEdit("0.1")
            self.init_approx_edits.append(edit_init)
            row_init.addWidget(edit_init)
            self.dynamic_init_layout.addLayout(row_init)

    def createMenuBar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Файл")
        load_action = QAction("Загрузить", self)
        load_action.triggered.connect(self.on_load_clicked)
        file_menu.addAction(load_action)
        
        save_action = QAction("Сохранить", self)
        save_action.triggered.connect(self.on_save_clicked)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("Меню")
        lang_action = QAction("Сменить язык на китайский", self)
        lang_action.triggered.connect(self.change_language)
        settings_menu.addAction(lang_action)

        info_menu = menubar.addMenu("Инфо")
        author_action = QAction("Об авторе", self)
        author_action.triggered.connect(self.show_author_info)
        info_menu.addAction(author_action)
        
        project_action = QAction("О проекте", self)
        project_action.triggered.connect(self.show_project_info)
        info_menu.addAction(project_action)

    def change_language(self):
        QMessageBox.information(self, "Language", "语言已更改为中文 (Смена языка в разработке)")

    def show_author_info(self):
        author_dialog = QDialog(self)
        author_dialog.setWindowTitle("Об авторе")
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
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(author_dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        author_dialog.setLayout(layout)
        author_dialog.exec_()

    def show_project_info(self):
        QMessageBox.information(self, "О проекте", "Некоммерческий проект для решения краевых задач методом продолжения по параметру.")

    def createStatusBar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage(f" Готов. Уравнений в системе: {self.current_n}")

    def on_solve_clicked(self):
        try:
            equations = [edit.text() for edit in self.ode_edits]
            conditions = [edit.text() for edit in self.bc_edits]
            p0 = [float(edit.text()) for edit in self.init_approx_edits]
            
            a = float(self.param_edits["Левый конец a:"].text())
            b = float(self.param_edits["Правый конец b:"].text())
            t_star = float(self.param_edits["Точка t*:"].text())
            step_mu = float(self.param_edits["Шаг по μ:"].text())
            tol = float(self.param_edits["Точность ε:"].text())
            max_iter = int(self.param_edits["Макс. итер.:"].text())

            result = solve_boundary(equations, conditions, p0, t_star, a, b, step_mu, tol, max_iter)
            
            self.statusbar.showMessage(result['message'])

            if result['sol_forward']:
                self.ax.clear()
                t_plot = np.linspace(a, b, 200)
                y_plot = result['sol_forward'].sol(t_plot)
                for i in range(self.current_n):
                    self.ax.plot(t_plot, y_plot[i], label=f'x[{i}]')
                self.ax.legend()
                self.ax.set_title("Решение краевой задачи")
                self.ax.grid(True, linestyle='--', alpha=0.7)
                self.canvas.draw()
            else:
                QMessageBox.warning(self, "Ошбка", result['message'])

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при расчете:\n{str(e)}")

    def on_load_clicked(self):
        QMessageBox.information(self, "Инфо", "Функция загрузки будет.")

    def on_save_clicked(self):
        QMessageBox.information(self, "Инфо", "Функция сохранения будет .")

    def on_clear_clicked(self):
        self.current_n = 2
        self.update_dimension()
        for edit in self.param_edits.values():
            if "0.01" in edit.text(): edit.setText("0.01")
            elif "1e-6" in edit.text(): edit.setText("1e-6")
            elif "100" in edit.text(): edit.setText("100")
            elif "1.0" in edit.text(): edit.setText("1.0")
            else: edit.setText("0.0")
        self.ax.clear()
        self.canvas.draw()
        self.statusbar.showMessage("Очистено")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())