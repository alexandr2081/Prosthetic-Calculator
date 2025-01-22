from PyQt6 import uic
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog


# Инициализация класса
class DialogAboutApp(QDialog):
    # Функция инициализации
    def __init__(self, helper):
        super().__init__()
        self.helper = helper
        uic.loadUi('templates/dialog_about_app.ui', self)
        self.setWindowIcon(QIcon('icon.png'))

        self.nameLabel.setText(self.helper.name_app)
        self.logoLabel.setPixmap(QPixmap("icon.png"))

        text = "Калькулятор протезов - оконное приложение для подборки протеза под индивидуальные параметры пользователя, надеюсь, оно вам поможет"
        text += "\n\n Разработчик: Булычев А. А."
        self.infoTextEdit.setText(text)

        self.okPushButton.clicked.connect(lambda: self.close())
