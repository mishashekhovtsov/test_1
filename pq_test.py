from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QTableWidgetItem
from mymain import Ui_MainWindow
import sys
import serial
import time
import serial.tools.list_ports
import datetime
import os

ser = serial.Serial()

def log(name_log,ion,tip,err_reg,err_ram):
    time = datetime.datetime.today()
    if not os.path.isdir("Log"):
        os.mkdir("Log")
    if not os.path.isdir("Log/" + tip):
        os.mkdir("Log/" + tip)
    if not os.path.isdir("Log/" + tip + "/" + ion):
        os.mkdir("Log/" + tip + "/" + ion)
    if err_reg == -1:
        with open("Log/{}/{}/{}.txt".format(tip,ion,name_log), "a", encoding='utf-8') as logs:
            logs.write(time.strftime("%Y-%m-%d\t%H:%M:%S") + "\tОшибки в ОЗУ:\t" + str(err_ram) + "\n")
    elif err_ram == -1:
        with open("Log/{}/{}/{}.txt".format(tip,ion,name_log), "a", encoding='utf-8') as logs:
            logs.write(time.strftime("%Y-%m-%d\t%H:%M:%S") + "\tОшибки в регистрах:\t" + str(err_reg) + "\n")
    else:
        with open("Log/{}/{}/{}.txt".format(tip,ion,name_log), "a", encoding='utf-8') as logs:
            logs.write(time.strftime("%Y-%m-%d\t%H:%M:%S") + "\tОшибки в регистрах:\t" + str(err_reg) + "\tОшибки в ОЗУ:\t" + str(err_ram) + "\n")

class TimeThread(QThread):
    time = pyqtSignal(str)

    def __init__(self):
        super(TimeThread,self).__init__()

    def run(self):
        while True:
            self.time.emit(time.strftime("%H:%M:%S"))

class SerialThread(QThread):
    message = pyqtSignal(str)
    messTable = pyqtSignal(str,str)
    stop = pyqtSignal(str)

    def __init__(self):
        super(SerialThread,self).__init__()
        self.log = ""
        self.ion = ""
        self.proverka = ""
        self.tip = ""
        self.start_loga = 0

    def run(self):
        if ser.isOpen():
            try:
                i = 0
                j = 0
                v = ""
                t = ""
                v_ram = ""
                sum_reg = 0
                sum_ram = 0
                while True:
                    for i in range(8):
                        b = int.from_bytes(ser.read(1),byteorder = 'big')
                        if b == 170:
                            v = ser.read(8).hex()
                        break
                    res = v[6:8] + v[4:6] + v[2:4] + v[0:2]
                    res_ram = v[14:16] + v[12:14] + v[10:12] + v[8:10]
                    v2 = int(res,16)
                    v_ram = int(res_ram,16)
                    sum_reg = sum_reg + v2
                    sum_ram = sum_ram + v_ram
                    time = datetime.datetime.today()
                    if self.proverka == "Все":
                        self.messTable.emit(str(v2),str(v_ram))
                        self.message.emit(time.strftime("%H:%M:%S") + " - Ошибки в регистрах: " + str(sum_reg))
                        self.message.emit(time.strftime("%H:%M:%S") + " - Ошибки в ОЗУ: " + str(sum_ram) + "\n")
                        if self.start_loga == 1:
                            log(self.log,self.ion,self.tip,sum_reg,sum_ram)
                    elif self.proverka == "Только регистры":
                        self.messTable.emit(v2)
                        self.message.emit(time.strftime("%H:%M:%S") + " - Ошибки в регистрах: " + str(sum_reg) + "\n")
                        if self.start_loga == 1:
                            log(self.log,self.ion,self.tip,sum_reg,-1)
                    elif self.proverka == "Только BRAM":
                        self.messTable.emit(v_ram)
                        self.message.emit(time.strftime("%H:%M:%S") + " - Ошибки в ОЗУ: " + str(sum_ram) + "\n")
                        if self.start_loga == 1:
                            log(self.log,self.ion,self.tip,-1,sum_ram)
                    v = ""
                    v2 = 0
                    v_ram = 0
            except Exception as e2:
                self.stop.emit(str(e2))
        else:
            self.stop.emit("Не получается открыть COM порт")

class mywindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(mywindow,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.baudrate.setCurrentIndex(12)
        
        self.myTimeThread = TimeThread()
        self.myTimeThread.time.connect(self.ui.Time.setText)
        self.myTimeThread.start()

        self.mySerialThread = SerialThread()
        self.mySerialThread.message.connect(self.ui.text.append)
        
        self.con_dis = 0
        self.count_reset = 1

        self.Log_name = ""
        self.ion = ""
        self.tip = ""
        self.mySerialThread.stop.connect(self.stop)

        self.mySerialThread.messTable.connect(self.Table_ERR)
        self.Sum_ERR = 0
        self.Sum_ERR_BRAM = 0

        p = sorted(serial.tools.list_ports.comports())

        for port, desc, hwid in p:
            self.ui.Box_COM_Port.addItem(port)

        self.ui.Clear_Table.clicked.connect(self.ClearTable)
        self.ui.Con_Dis_Button.clicked.connect(self.btnConnect)
        self.ui.Start_Seans.clicked.connect(self.btnStartStopSeans)

        self.ui.RESET_FPGA.clicked.connect(self.reset)

    #Функции RESET
    def reset(self):
        if ser.isOpen():
            ser.write(b"\x31")
            cellinfo = QTableWidgetItem(str(self.count_reset))
            cellinfo.setTextAlignment(QtCore.Qt.AlignCenter)
            self.ui.Sum_ERR.setItem(0,3,cellinfo)
            self.count_reset = self.count_reset + 1;
        else:
            result = QtWidgets.QMessageBox.question(self,"Ошибка", "COM порт закрыт!", QtWidgets.QMessageBox.Yes)
    #----------------------

    #def closeEvent(self,e):
        #result = QtWidgets.QMessageBox.question(self,"Подтверждение", "Точно выйти?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        #if result == QtWidgets.QMessageBox.Yes:
            #e.accept()
        #else:
            #e.ignore()

    # Функции для ЛОГОВ
    def btnStartStopSeans(self):
        if self.mySerialThread.start_loga == 0:
            self.mySerialThread.proverka = self.ui.proverka_Box.currentText()
            self.mySerialThread.start_loga = 1
            self.ui.Start_Seans.setText(QtWidgets.QApplication.translate("MainWindow","Стоп сеанс"))
        else:
            self.mySerialThread.start_loga = 0
            self.ui.Start_Seans.setText(QtWidgets.QApplication.translate("MainWindow","Старт сеанса"))

    def log_name_init(self):
        self.ion = self.ui.ion_Box.currentText()
        nomer_s = str(self.ui.Seans.value())
        self.tip = self.ui.Tiponominal.text()
        obr = str(self.ui.Obrazec.value())
        tipseans = self.ui.Tip_seans_Box.currentText()
        temp = str(self.ui.Temp.value())
        self.Log_name = self.ion + "_" + nomer_s + "_" + self.tip + "_" + "obr" + obr + "_" + tipseans + "_" + temp
        return self.Log_name
    #-----------------------------

    #Функции для вывода ошибок
    def stop(self,value):
        result = QtWidgets.QMessageBox.question(self,"Ошибка", "Ошибка приемо/передачи: " + value, QtWidgets.QMessageBox.Yes)
        if result == QtWidgets.QMessageBox.Yes:
            self.btnConnect()
    #-----------------------------

    # Функции для таблицы со сбоями
    def ClearTable(self):
        self.count_reset = 1
        self.Sum_ERR = 0
        self.Sum_ERR_BRAM = 0
        self.ui.Sum_ERR.clearContents()
        i = 0
        for i in range(4):
            cellinfo = QTableWidgetItem("0")
            cellinfo.setTextAlignment(QtCore.Qt.AlignCenter)
            self.ui.Sum_ERR.setItem(0,i,cellinfo)

    def Table_ERR(self,ERR,ERR_RAM):
        self.Sum_ERR += int(ERR)
        cellinfo = QTableWidgetItem(str(self.Sum_ERR))
        cellinfo.setTextAlignment(QtCore.Qt.AlignCenter)
        self.ui.Sum_ERR.setItem(0,0,cellinfo)
        self.Sum_ERR_BRAM += int(ERR_RAM)
        cellinfo = QTableWidgetItem(str(self.Sum_ERR_BRAM))
        cellinfo.setTextAlignment(QtCore.Qt.AlignCenter)
        self.ui.Sum_ERR.setItem(0,1,cellinfo)
    #-----------------------------

    def btnConnect(self):     
        try:
            if  self.con_dis == 0:
                self.ui.Con_Dis_Button.setText(QtWidgets.QApplication.translate("MainWindow","Отключить"))
                self.mySerialThread.proverka = self.ui.proverka_Box.currentText()
                ser.port = self.ui.Box_COM_Port.currentText()
                ser.baudrate = self.ui.baudrate.currentText()
                ser.timeout = 3
                ser.open()
                self.mySerialThread.log = self.log_name_init()
                self.mySerialThread.ion = self.ion
                self.mySerialThread.tip = self.tip
                self.mySerialThread.start()
                self.ui.text.append("------------\nCOM порт открыт\n------------\n")
                self.con_dis = 1
            else:
                self.mySerialThread.terminate()
                self.ui.Con_Dis_Button.setText(QtWidgets.QApplication.translate("MainWindow","Подключить"))
                ser.close()
                self.ui.text.append("------------\nCOM порт закрыт\n------------\n")
                self.con_dis = 0
        except Exception as e1:
            result = QtWidgets.QMessageBox.question(self,"Ошибка", "Ошибка COM порта: " + str(e1), QtWidgets.QMessageBox.Yes)
            if result == QtWidgets.QMessageBox.Yes:
                self.mySerialThread.terminate()
                self.con_dis = 0
                self.ui.Con_Dis_Button.setText(QtWidgets.QApplication.translate("MainWindow","Подключить"))


app = QtWidgets.QApplication([])
application = mywindow()
application.show()
ser.close()
sys.exit(app.exec())