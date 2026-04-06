import sys
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Метод продолжения по параметру — решение краевых задач")
        self.setMinimumSize(1200, 800)
        self.setupUI()
        self.createMenuBar()
        self.createStatusBar()
        
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
                margin-top: 12px;
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
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background-color: #fffef7;
                border: 1px solid #d4a574;
                border-radius: 6px;
                padding: 4px 8px;
                color: #4a2a0e;
                font-size: 12px;
                min-height: 24px;
                max-width: 250px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
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
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c49a6c;
            }
            QPushButton:pressed {
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
            QMenuBar {
                background-color: #f0e4cc;
                color: #6b3f1c;
                border-bottom: 1px solid #d4a574;
            }
            QMenuBar::item:selected {
                background-color: #d4a574;
                color: white;
            }
            QMenu {
                background-color: #faf3e0;
                color: #6b3f1c;
                border: 1px solid #d4a574;
            }
            QMenu::item:selected {
                background-color: #d4a574;
                color: white;
            }
            QStatusBar {
                background-color: #f0e4cc;
                color: #6b3f1c;
                border-top: 1px solid #d4a574;
            }
        """)
        
        params_group = QGroupBox("ПАРАМЕТРЫ КРАЕВОЙ ЗАДАЧИ")
        params_layout = QGridLayout()
        params_layout.setVerticalSpacing(10)
        params_layout.setHorizontalSpacing(15)
        params_layout.setContentsMargins(15, 15, 15, 15)
        
        params_layout.addWidget(QLabel("Уравнение:"), 0, 0)
        self.equation_edit = QLineEdit("y'' + mu*exp(y)")
        params_layout.addWidget(self.equation_edit, 0, 1)
        
        params_layout.addWidget(QLabel("Левое ГУ:"), 1, 0)
        self.bc_left_edit = QLineEdit("y(0)=0")
        params_layout.addWidget(self.bc_left_edit, 1, 1)
        
        params_layout.addWidget(QLabel("Правое ГУ:"), 2, 0)
        self.bc_right_edit = QLineEdit("y(1)=0")
        params_layout.addWidget(self.bc_right_edit, 2, 1)
        
        params_layout.addWidget(QLabel("Параметр μ:"), 3, 0)
        self.lam_spin = QDoubleSpinBox()
        self.lam_spin.setRange(0.1, 10.0)
        self.lam_spin.setValue(2.0)
        self.lam_spin.setSingleStep(0.1)
        params_layout.addWidget(self.lam_spin, 3, 1)
        
        params_layout.addWidget(QLabel("Границы [a, b]:"), 4, 0)
        bounds_layout = QHBoxLayout()
        self.a_spin = QDoubleSpinBox()
        self.a_spin.setRange(-10, 10)
        self.a_spin.setValue(0)
        self.b_spin = QDoubleSpinBox()
        self.b_spin.setRange(-10, 10)
        self.b_spin.setValue(1)
        self.a_spin.setMaximumWidth(80)
        self.b_spin.setMaximumWidth(80)
        bounds_layout.addWidget(self.a_spin)
        bounds_layout.addWidget(QLabel("→"))
        bounds_layout.addWidget(self.b_spin)
        bounds_layout.addStretch()
        params_layout.addLayout(bounds_layout, 4, 1)
        
        params_layout.addWidget(QLabel("Узлов сетки N:"), 5, 0)
        self.n_nodes_spin = QSpinBox()
        self.n_nodes_spin.setRange(10, 500)
        self.n_nodes_spin.setValue(50)
        params_layout.addWidget(self.n_nodes_spin, 5, 1)

        params_layout.addWidget(QLabel("Шагов по t:"), 6, 0)
        self.n_steps_spin = QSpinBox()
        self.n_steps_spin.setRange(5, 100)
        self.n_steps_spin.setValue(20)
        params_layout.addWidget(self.n_steps_spin, 6, 1)

        params_layout.addWidget(QLabel("Точность:"), 7, 0)
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(1e-8, 1e-3)
        self.tolerance_spin.setValue(1e-6)
        self.tolerance_spin.setDecimals(8)
        self.tolerance_spin.setSingleStep(1e-7)
        params_layout.addWidget(self.tolerance_spin, 7, 1)
        
        # Начальное приближение
        params_layout.addWidget(QLabel("Нач. приближение:"), 8, 0)
        self.init_approx_edit = QLineEdit("0")
        params_layout.addWidget(self.init_approx_edit, 8, 1)
        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.solve_btn = QPushButton(" РЕШИТЬ")
        self.solve_btn.clicked.connect(self.on_solve_clicked)
        
        self.load_btn = QPushButton(" ЗАГРУЗИТЬ")
        self.load_btn.clicked.connect(self.on_load_clicked)
        
        self.save_btn = QPushButton(" СОХРАНИТЬ")
        self.save_btn.clicked.connect(self.on_save_clicked)
        
        self.clear_btn = QPushButton(" ОЧИСТИТЬ")
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        
        btn_layout.addWidget(self.solve_btn)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        plot_group = QGroupBox("ГРАФИК РЕШЕНИЯ y(x)")
        plot_layout = QVBoxLayout()
        plot_layout.setContentsMargins(10, 10, 10, 10)
        
        self.plot_label = QLabel("Здесь будет отображаться график решения")
        self.plot_label.setAlignment(Qt.AlignCenter)
        self.plot_label.setStyleSheet("""
            background-color: #fffef7; 
            border: 1px solid #d4a574; 
            border-radius: 8px; 
            min-height: 320px;
            color: #6b3f1c;
            font-size: 13px;
        """)
        plot_layout.addWidget(self.plot_label)
        
        plot_group.setLayout(plot_layout)
        main_layout.addWidget(plot_group)
    
    def createMenuBar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Файл")
        
        load_action = QAction("Загрузить задачу", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.on_load_clicked)
        file_menu.addAction(load_action)
        
        save_action = QAction("Сохранить задачу", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.on_save_clicked)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("Об авторе", self)
        about_action.setShortcut("Ctrl+Z")
        about_action.triggered.connect(self.open_author_window)
        help_menu.addAction(about_action)
        
        help_action = QAction("Справка", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.on_help_clicked)
        help_menu.addAction(help_action)
    
    def createStatusBar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage(" Готов. F1 - справка")
    
    def open_author_window(self):
        self.author_window = AuthorWindow()
        self.author_window.show()
    
    def on_solve_clicked(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(50)
        
        QMessageBox.information(
            self, 
            "Решение задачи", 
            f"Демонстрационный режим\n\n"
            f"Уравнение: {self.equation_edit.text()}\n"
            f"μ = {self.lam_spin.value()}\n"
            f"Нач. приближение: {self.init_approx_edit.text()}"
        )
        
        self.statusbar.showMessage(" Демонстрационный режим")
        self.progress_bar.setVisible(False)
    
    def on_load_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Загрузить задачу", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.equation_edit.setText(data.get("equation", "y'' + mu*exp(y)"))
                self.bc_left_edit.setText(data.get("bc_left", "y(0)=0"))
                self.bc_right_edit.setText(data.get("bc_right", "y(1)=0"))
                self.lam_spin.setValue(float(data.get("mu", 2.0)))
                self.a_spin.setValue(float(data.get("a", 0)))
                self.b_spin.setValue(float(data.get("b", 1)))
                self.n_nodes_spin.setValue(int(data.get("n_nodes", 50)))
                self.n_steps_spin.setValue(int(data.get("n_steps", 20)))
                self.tolerance_spin.setValue(float(data.get("tolerance", 1e-6)))
                self.init_approx_edit.setText(data.get("init_approx", "0"))
                
                self.statusbar.showMessage(f" Загружено")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить:\n{str(e)}")
    
    def on_save_clicked(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить задачу", "task.json", "JSON Files (*.json)")
        if file_path:
            try:
                data = {
                    "equation": self.equation_edit.text(),
                    "bc_left": self.bc_left_edit.text(),
                    "bc_right": self.bc_right_edit.text(),
                    "mu": self.lam_spin.value(),
                    "a": self.a_spin.value(),
                    "b": self.b_spin.value(),
                    "n_nodes": self.n_nodes_spin.value(),
                    "n_steps": self.n_steps_spin.value(),
                    "tolerance": self.tolerance_spin.value(),
                    "init_approx": self.init_approx_edit.text()
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                self.statusbar.showMessage(f" Сохранено")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить:\n{str(e)}")
    
    def on_clear_clicked(self):
        self.equation_edit.setText("y'' + mu*exp(y)")
        self.bc_left_edit.setText("y(0)=0")
        self.bc_right_edit.setText("y(1)=0")
        self.lam_spin.setValue(2.0)
        self.a_spin.setValue(0)
        self.b_spin.setValue(1)
        self.n_nodes_spin.setValue(50)
        self.n_steps_spin.setValue(20)
        self.tolerance_spin.setValue(1e-6)
        self.init_approx_edit.setText("0.1*sin(pi*x)")
        self.statusbar.showMessage(" Очищено")
    
    def on_help_clicked(self):
        QMessageBox.information(
            self, 
            "Справка",
            "Метод продолжения по параметру\n\n"
            "Горячие клавиши:\n"
            "Ctrl+O - загрузить\n"
            "Ctrl+S - сохранить\n"
            "Ctrl+Z - об авторе\n"
            "F1 - справка\n"
            "Ctrl+Q - выход"
        )
    
    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Close):
            self.close()
        elif event.matches(QKeySequence.Open):
            self.on_load_clicked()
        elif event.matches(QKeySequence.Save):
            self.on_save_clicked()
        elif event.matches(QKeySequence.Undo):
            self.open_author_window()
        elif event.key() == Qt.Key_F1:
            self.on_help_clicked()


class AuthorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Об авторе")
        self.setFixedSize(400, 480)
        self.setupUI()
    
    def setupUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #faf3e0;
            }
            QLabel {
                color: #6b3f1c;
            }
            QPushButton {
                background-color: #d4a574;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c49a6c;
            }
        """)
        
        # Место для фото
        photo_label = QLabel()
        photo_label.setFixedSize(130, 130)
        photo_label.setStyleSheet("""
            border: 3px solid #d4a574; 
            border-radius: 65px; 
            background-color: #fffef7;
        """)
        photo_label.setAlignment(Qt.AlignCenter)
        photo_label.setText("📷\nФОТО")
        photo_label.setWordWrap(True)
        layout.addWidget(photo_label, alignment=Qt.AlignCenter)

        info_label = QLabel(
            "<html><body style='text-align: center;'>"
            "<h2 style='color:#8b5a2b;'>Прибытков</h2>"
            "<p><b>Фамилия:</b> Прибытков</p>"
            "<p><b>Имя:</b> Андрей</p>"
            "<p><b>Группа:</b> 313</p>"
            "<br>"
            "<p>Метод продолжения по параметру<br>"
            "Решение краевых задач</p>"
            "<p>© 2026</p>"
            "</body></html>"
        )
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
    
    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Close):
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())