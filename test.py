# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Метод продолжения по параметру — решение краевых задач")
        self.setMinimumSize(1000, 700)
        self.setupUI()
        self.createMenuBar()
        self.createStatusBar()
        
    def setupUI(self):
        """Создание интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # ==================== Верхняя панель с параметрами ====================
        params_group = QGroupBox("Параметры краевой задачи")
        params_layout = QGridLayout()
        
        # Уравнение
        params_layout.addWidget(QLabel("Уравнение (y'' + ... = 0):"), 0, 0)
        self.equation_edit = QLineEdit("y'' + lam*exp(y)")
        self.equation_edit.setMinimumWidth(400)
        params_layout.addWidget(self.equation_edit, 0, 1)
        
        # Граничные условия
        params_layout.addWidget(QLabel("Левое ГУ (y(a)=...):"), 1, 0)
        self.bc_left_edit = QLineEdit("y(0)=0")
        params_layout.addWidget(self.bc_left_edit, 1, 1)
        
        params_layout.addWidget(QLabel("Правое ГУ (y(b)=...):"), 2, 0)
        self.bc_right_edit = QLineEdit("y(1)=0")
        params_layout.addWidget(self.bc_right_edit, 2, 1)
        
        # Параметры задачи
        params_layout.addWidget(QLabel("Параметр λ (ламбда):"), 3, 0)
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
        bounds_layout.addWidget(self.a_spin)
        bounds_layout.addWidget(QLabel(" — "))
        bounds_layout.addWidget(self.b_spin)
        bounds_layout.addStretch()
        params_layout.addLayout(bounds_layout, 4, 1)
        
        # Численные параметры
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
        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # ==================== Панель с кнопками ====================
        buttons_group = QGroupBox("Управление")
        buttons_layout = QHBoxLayout()
        
        self.solve_btn = QPushButton("▶ Решить задачу")
        self.solve_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 8px;")
        self.solve_btn.clicked.connect(self.on_solve_clicked)
        
        self.add_btn = QPushButton("➕ Добавить строку")
        self.add_btn.clicked.connect(self.on_add_clicked)
        
        self.del_btn = QPushButton("➖ Удалить строку")
        self.del_btn.clicked.connect(self.on_del_clicked)
        
        self.clear_btn = QPushButton("🗑 Очистить таблицу")
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        
        buttons_layout.addWidget(self.solve_btn)
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.del_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addStretch()
        
        buttons_group.setLayout(buttons_layout)
        main_layout.addWidget(buttons_group)
        
        # ==================== Таблица с данными ====================
        table_group = QGroupBox("Система уравнений / Данные задачи")
        table_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Уравнение", "Левая часть", "Нач. условие", "Значение"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        
        # Добавим несколько строк для примера
        self.add_default_rows()
        
        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)
        
        # ==================== Прогресс-бар ====================
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # ==================== Таблица результатов ====================
        result_group = QGroupBox("Результаты решения")
        result_layout = QVBoxLayout()
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(0)
        self.result_table.setRowCount(0)
        result_layout.addWidget(self.result_table)
        
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)
        
    def add_default_rows(self):
        """Добавляет строки по умолчанию (для примера)"""
        self.table.setRowCount(3)
        
        # Заголовки строк
        headers = ["Уравнение 1", "Уравнение 2", "Уравнение 3"]
        self.table.setVerticalHeaderLabels(headers)
        
        # Данные
        default_data = [
            ["f1(x)=g1(x)", "f1(x)=0", "(x1)0", "0"],
            ["f2(x)=g2(x)", "f2(x)=0", "(x2)0", "0"],
            ["f3(x)=g3(x)", "f3(x)=0", "(x3)0", "0"]
        ]
        
        for row, data in enumerate(default_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                if col in [0, 2]:  # Запрещаем редактирование первых двух колонок
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, col, item)
    
    def createMenuBar(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Меню Файл
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
        
        # Меню Правка
        edit_menu = menubar.addMenu("Правка")
        
        add_action = QAction("Добавить строку", self)
        add_action.setShortcut("Ctrl+N")
        add_action.triggered.connect(self.on_add_clicked)
        edit_menu.addAction(add_action)
        
        del_action = QAction("Удалить строку", self)
        del_action.setShortcut("Ctrl+X")
        del_action.triggered.connect(self.on_del_clicked)
        edit_menu.addAction(del_action)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("Об авторе", self)
        about_action.setShortcut("Ctrl+Z")
        about_action.triggered.connect(self.on_about_clicked)
        help_menu.addAction(about_action)
        
        help_action = QAction("Справка", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.on_help_clicked)
        help_menu.addAction(help_action)
    
    def createStatusBar(self):
        """Создание строки состояния"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Готов к работе. Нажмите 'Решить задачу'")
    
    # ==================== Обработчики кнопок (пока просто сообщения) ====================
    
    def on_solve_clicked(self):
        """Обработчик кнопки 'Решить задачу'"""
        QMessageBox.information(
            self, 
            "Решение задачи", 
            f"🔧 Здесь будет решение краевой задачи\n\n"
            f"Уравнение: {self.equation_edit.text()}\n"
            f"Границы: [{self.a_spin.value()}, {self.b_spin.value()}]\n"
            f"λ = {self.lam_spin.value()}\n"
            f"N = {self.n_nodes_spin.value()}\n"
            f"Шагов по t = {self.n_steps_spin.value()}\n\n"
            f"Пока это демонстрация интерфейса."
        )
        self.statusbar.showMessage("Кнопка 'Решить задачу' нажата (демонстрация)")
    
    def on_add_clicked(self):
        """Обработчик кнопки 'Добавить строку'"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        item1 = QTableWidgetItem(f"f{row+1}(x)=g{row+1}(x)")
        item2 = QTableWidgetItem(f"f_{row+1}(x)=0")
        item3 = QTableWidgetItem(f"(x{row+1})0")
        item4 = QTableWidgetItem("0")
        
        item1.setFlags(item1.flags() & ~Qt.ItemIsEditable)
        item3.setFlags(item3.flags() & ~Qt.ItemIsEditable)
        
        self.table.setItem(row, 0, item1)
        self.table.setItem(row, 1, item2)
        self.table.setItem(row, 2, item3)
        self.table.setItem(row, 3, item4)
        
        self.statusbar.showMessage(f"Добавлена строка {row+1}")
        QMessageBox.information(self, "Добавление", f"Добавлена строка {row+1}")
    
    def on_del_clicked(self):
        """Обработчик кнопки 'Удалить строку'"""
        row = self.table.rowCount()
        if row > 0:
            self.table.removeRow(row - 1)
            self.statusbar.showMessage(f"Удалена строка {row}")
            QMessageBox.information(self, "Удаление", f"Удалена строка {row}")
        else:
            QMessageBox.warning(self, "Ошибка", "Нет строк для удаления")
    
    def on_clear_clicked(self):
        """Обработчик кнопки 'Очистить таблицу'"""
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            "Вы уверены, что хотите очистить всю таблицу?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.table.setRowCount(0)
            self.statusbar.showMessage("Таблица очищена")
            QMessageBox.information(self, "Очистка", "Таблица очищена")
    
    def on_load_clicked(self):
        """Обработчик меню 'Загрузить задачу'"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выбор файла", 
            "user_files", 
            "JSON Files (*.json)"
        )
        if file_path:
            QMessageBox.information(self, "Загрузка", f"Загружен файл:\n{file_path}")
            self.statusbar.showMessage(f"Загружен файл: {file_path}")
        else:
            self.statusbar.showMessage("Загрузка отменена")
    
    def on_save_clicked(self):
        """Обработчик меню 'Сохранить задачу'"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить задачу", 
            "user_files/task.json", 
            "JSON Files (*.json)"
        )
        if file_path:
            QMessageBox.information(self, "Сохранение", f"Сохранён файл:\n{file_path}")
            self.statusbar.showMessage(f"Сохранён файл: {file_path}")
        else:
            self.statusbar.showMessage("Сохранение отменено")
    
    def on_about_clicked(self):
        """Обработчик меню 'Об авторе'"""
        QMessageBox.about(
            self,
            "Об авторе",
            "Метод продолжения по параметру\n"
            "Решение краевых задач\n\n"
            "Разработчик: Студент\n"
            "Группа: ИУ5-XX\n"
            "2026 г.\n\n"
            "Демонстрационная версия интерфейса"
        )
    
    def on_help_clicked(self):
        """Обработчик меню 'Справка'"""
        QMessageBox.information(
            self,
            "Справка",
            "Метод продолжения по параметру (гомотопический метод)\n\n"
            "Алгоритм:\n"
            "1. Задаётся нелинейная краевая задача\n"
            "2. Строится гомотопия с линейной задачей\n"
            "3. Решение находится методом продолжения по параметру t ∈ [0,1]\n\n"
            "Горячие клавиши:\n"
            "Ctrl+O - загрузить задачу\n"
            "Ctrl+S - сохранить задачу\n"
            "Ctrl+N - добавить строку\n"
            "Ctrl+X - удалить строку\n"
            "Ctrl+Z - об авторе\n"
            "F1 - справка\n"
            "Ctrl+Q - выход\n\n"
            "Демонстрационная версия интерфейса"
        )
    
    def keyPressEvent(self, event):
        """Обработка горячих клавиш"""
        if event.matches(QKeySequence.Close):
            self.close()
        elif event.matches(QKeySequence.New):
            self.on_add_clicked()
        elif event.matches(QKeySequence.Cut):
            self.on_del_clicked()
        elif event.matches(QKeySequence.Open):
            self.on_load_clicked()
        elif event.matches(QKeySequence.Save):
            self.on_save_clicked()
        elif event.matches(QKeySequence.Undo):
            self.on_about_clicked()
        elif event.key() == Qt.Key_F1:
            self.on_help_clicked()
        else:
            super().keyPressEvent(event)


# Перехват ошибок
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Современный стиль
    
    # Настройка палитры
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())