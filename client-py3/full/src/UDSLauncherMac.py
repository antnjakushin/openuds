# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UDSLauncherMac.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MacLauncher(object):
    def setupUi(self, MacLauncher):
        MacLauncher.setObjectName("MacLauncher")
        MacLauncher.setWindowModality(QtCore.Qt.NonModal)
        MacLauncher.resize(235, 120)
        MacLauncher.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/logo-uds-small"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MacLauncher.setWindowIcon(icon)
        MacLauncher.setWindowOpacity(1.0)
        self.centralwidget = QtWidgets.QWidget(MacLauncher)
        self.centralwidget.setAutoFillBackground(True)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout_2.setSpacing(4)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName("verticalLayout")
        self.topLabel = QtWidgets.QLabel(self.frame)
        self.topLabel.setTextFormat(QtCore.Qt.RichText)
        self.topLabel.setObjectName("topLabel")
        self.verticalLayout.addWidget(self.topLabel)
        self.image = QtWidgets.QLabel(self.frame)
        self.image.setMinimumSize(QtCore.QSize(0, 32))
        self.image.setAutoFillBackground(True)
        self.image.setText("")
        self.image.setPixmap(QtGui.QPixmap(":/images/logo-uds-small"))
        self.image.setScaledContents(False)
        self.image.setAlignment(QtCore.Qt.AlignCenter)
        self.image.setObjectName("image")
        self.verticalLayout.addWidget(self.image)
        self.label_2 = QtWidgets.QLabel(self.frame)
        self.label_2.setTextFormat(QtCore.Qt.RichText)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.verticalLayout_2.addWidget(self.frame)
        MacLauncher.setCentralWidget(self.centralwidget)

        self.retranslateUi(MacLauncher)
        QtCore.QMetaObject.connectSlotsByName(MacLauncher)

    def retranslateUi(self, MacLauncher):
        _translate = QtCore.QCoreApplication.translate
        MacLauncher.setWindowTitle(_translate("MacLauncher", "UDS Launcher"))
        self.topLabel.setText(_translate("MacLauncher", "<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">UDS Launcher</span></p></body></html>"))
        self.label_2.setText(_translate("MacLauncher", "<html><head/><body><p align=\"center\"><span style=\" font-size:6pt;\">Closing this window will end all UDS tunnels</span></p></body></html>"))
import UDSResources_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MacLauncher = QtWidgets.QMainWindow()
    ui = Ui_MacLauncher()
    ui.setupUi(MacLauncher)
    MacLauncher.show()
    sys.exit(app.exec())