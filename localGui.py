# import PyQt5 as qt
import sys
from PyQt5.QtWidgets import *
from UI_localProxy import *


class MyMainForm(QMainWindow, Ui_Dialog):
    def __init__(self, parent=None):
        super(MyMainForm, self).__init__(parent)
        self.setupUi(self)
        self.remoteAddr = ""
        self.remotePort = int
        self.username = ""
        self.password = ""
        self.isConnect = False
        self.socket = False
        self.pushButton.clicked.connect(self.startProxy)

    def startProxy(self):
        self.remoteAddr = self.ui_remoteAddr.text()
        self.remotePort = self.ui_remotePort.text()
        self.username = self.ui_username.text()
        self.password = self.ui_password.text()


def main():
    app = QApplication(sys.argv)
    myWin = MyMainForm()
    myWin.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
