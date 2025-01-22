import sys
import os
import sqlite3
import numpy as np
from stl import mesh
from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
                             QLineEdit, QTextEdit, QComboBox, QGroupBox, QScrollArea, QFileDialog)
from PyQt6.QtGui import QPixmap, QPalette, QColor, QDesktopServices
from PyQt6.QtCore import Qt, QUrl
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler


class ProstheticCalculator(QWidget): # Класс рабочей программы - калькулятора
    def __init__(self, window_main, user):
        super().__init__()
        self.window_main = window_main
        self.user = user
        self.setWindowTitle("Калькулятор протезов локтевого сустава")
        uic.loadUi('./templates/calc.ui', self)
        self.exitMainButton.clicked.connect(self.exit_main)
        
        # Стили для кнопок и текстовых полей, установка палитры цветов
        self.setAutoFillBackground(True)
        button_style = """
            QPushButton {background-color: #4CAF50; color: white; padding: 10px;
                border-radius: 5px; font-size: 16px;}
            QPushButton:hover {background-color: #45a049;}
        """

        input_style = "QLineEdit {padding: 5px; border: 1px solid #ccc; border-radius: 5px; font-size: 14px;}"
        self.setStyleSheet(button_style + input_style)
        
        self.select_db_button.clicked.connect(self.select_database)
        self.load_patient_button.clicked.connect(self.load_selected_patient_data)
        self.gender_input.addItems(["Мужчина", "Женщина"])

        self.bone_shape_input.addItems(["Округлая", "Треугольная", "Овальная"])
        self.joint_position_input.addItems(["Верхнее", "Среднее", "Нижнее"])

        self.calc_button.clicked.connect(self.calculate_prosthetic)
        self.open_stl_button.clicked.connect(self.open_existing_stl_model)
        self.classify_button.clicked.connect(self.classify_prosthetic)
        self.ct_scan_button.clicked.connect(self.load_ct_scan_image)
        self.xray_button.clicked.connect(self.load_xray_image)
        self.clearButton.clicked.connect(lambda: self.result_output.clear())

    def exit_main(self): # Выход в главное меню
        self.window_main.show()
        self.close()

    def select_database(self): # Выборка БД
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл базы данных",
                                                   "", "Database Files (*.db *.sqlite)")
        if file_path:
            self.db_file = file_path
            self.load_patients_button_clicked() # Автоматическая загрузка списка пациентов

    def load_patients_button_clicked(self): # Автоматическая загрузка списка пациентов
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT patient_id, name FROM patients")
            patients = cursor.fetchall()
            conn.close()

            self.patient_selection_combo.clear()
            for patient_id, name in patients:
                self.patient_selection_combo.addItem(f"{patient_id} - {name}", patient_id)

        except Exception as e:
            self.result_output.setText(f"Ошибка загрузки списка пациентов: {e}")

    def load_selected_patient_data(self):
        try:
            patient_id = self.patient_selection_combo.currentData()
            if patient_id: self.load_patient_data(patient_id)
            else: self.result_output.setText("Пожалуйста, выберите пациента.")
        except Exception as e:
            self.result_output.setText(f"Ошибка загрузки данных пациента: {e}")

    def load_xray_image(self): # Подгрузка и вывод рентгеновского изображения
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите рентгеновское изображение",
                                                   "", "Images (*.png *.jpg *.bmp)")
        if file_path: self.show_image(file_path, self.xray_label)

    def load_ct_scan_image(self): # Подгрузка и вывод КТ-снимка
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите КТ-снимок", "", "Images (*.png *.jpg *.bmp)")
        if file_path: self.show_image(file_path, self.ct_scan_label)

    def show_image(self, file_path, label):
        if os.path.exists(file_path):
            label.setPixmap(QPixmap(file_path))
        else: label.setText("Изображение не найдено")

    def calculate_prosthetic(self): # Вычисления необходимых характеристик протеза
        try:
            age, weight, results = int(self.age_input.text()), float(self.weight_input.text()), []
            density, gender = float(self.density_input.text()), self.gender_input.currentText()
            joint_size, bone_shape = float(self.joint_size_input.text()), self.bone_shape_input.currentText()
            joint_position, joint_angle = self.joint_position_input.currentText(), float(self.joint_angle_input.text())

            # Базовый коэффициент
            base_factor = (weight / density) * joint_size * (90 - joint_angle) / 100
            results.append(f"1. Базовый коэффициент: {base_factor:.2f}")

            # Корректировка по материалу
            material_factor = 1.1 if gender == "Мужчина" else 1.0
            results.append(f"2. Корректировка по материалу (пол пациента - {gender}): {material_factor:.2f}")

            # Возрастной коэффициент
            age_factor = 0.9 if age > 50 else 1.0
            results.append(f"3. Возрастной коэффициент (возраст - {age}): {age_factor:.2f}")

            # Окончательный расчет
            prosthetic_score = base_factor * material_factor * age_factor
            results.append(f"4. Окончательный расчет протеза: {prosthetic_score:.2f}")

            # Вес протеза в граммах
            prosthetic_weight = max(500, min(5000, prosthetic_score * 1.5))  # Вес от 500 до 5000 г
            results.append(f"5. Вес протеза: {prosthetic_weight:.2f} г")

            # Время изготовления протеза
            manufacturing_time = max(20, min(200, prosthetic_score * 0.5)) # Время от 20 до 200 часов
            results.append(f"6. Время изготовления: {manufacturing_time:.2f} часов")

            # Рекомендации по типу протеза
            if prosthetic_score < 50:
                recommendations = "Рекомендуется использовать легкий алюминиевый протез."
            elif 50 <= prosthetic_score < 100:
                recommendations = "Рекомендуется использовать стандартный титановый протез."
            else:
                recommendations = "Рекомендуется использовать усиленный титановый протез для тяжелых нагрузок."
            results.append(f"7. Рекомендации: {recommendations}")


            # Отображение результатов
            result_window = QWidget()
            result_window.setWindowTitle("Результаты расчета")
            result_layout = QVBoxLayout()
            result_text = QTextEdit()
            result_text.setReadOnly(True)
            result_text.setText("\n".join([f". {result}" for i, result in enumerate(results)]))
            result_layout.addWidget(result_text)
            result_window.setLayout(result_layout)
            result_window.setGeometry(200, 200, 400, 300)
            result_window.show()
            self.result_window = result_window

        except ValueError as e:
            self.result_output.setText(f"Ошибка ввода: {e}")
        except Exception as e:
            self.result_output.setText(f"Произошла ошибка: {e}")

    def load_patient_data(self, patient_id): # Автоматическая загрузка данных пациента
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
            patient = cursor.fetchone()
            conn.close()

            if patient:
                _, _, age, weight, bone_density, gender, joint_size, bone_shape, joint_position, joint_angle = patient
                self.age_input.setText(str(age))
                self.weight_input.setText(str(weight))
                self.density_input.setText(str(bone_density))
                self.gender_input.setCurrentText(gender)
                self.joint_size_input.setText(str(joint_size))
                self.bone_shape_input.setCurrentText(bone_shape)
                self.joint_position_input.setCurrentText(joint_position)
                self.joint_angle_input.setText(str(joint_angle))
            else:
                self.result_output.setText(f"Пациент с ID {patient_id} не найден.")

        except Exception as e:
            self.result_output.setText(f"Ошибка загрузки данных пациента: {e}")

    def open_existing_stl_model(self): # Открытие 3D модели протеза
        file_path = "./data/prosthetic.stl"
        if os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def classify_prosthetic(self): # Классификация для поиска подходящего протеза
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT age, weight, bone_density, joint_size, joint_angle FROM patients")
            data = cursor.fetchall()
            conn.close()

            # Преобразование данных для классификации
            X = np.array(data)
            y = np.array([1 if weight > 70 and density > 1.2 and joint_size > 50
                          else 0 for _, weight, density, joint_size, _ in data])

            # Стандартизация данных
            scaler = StandardScaler()
            X = scaler.fit_transform(X)

            # Создание модели K-Nearest Neighbors
            knn = KNeighborsClassifier(n_neighbors=5)
            knn.fit(X, y)

            # Подготовка данных пациента для классификации
            age = int(self.age_input.text())
            weight = float(self.weight_input.text())
            density = float(self.density_input.text())
            joint_size = float(self.joint_size_input.text())
            joint_angle = float(self.joint_angle_input.text())

            patient_data = scaler.transform(np.array([[age, weight, density, joint_size, joint_angle]]))

            # Предсказание класса протеза
            prosthetic_class = knn.predict(patient_data)[0]
            if prosthetic_class == 1:
                self.result_output.append("Рекомендуется использовать усиленный протез")
            else:
                self.result_output.append("Рекомендуется использовать стандартный протез.")

        except Exception as e:
            self.result_output.setText(f"Ошибка классификации: {e}")
