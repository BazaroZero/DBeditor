from PyQt5 import QtCore, QtWidgets
from sys import exit, argv
import sqlite3


class DBeditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def openDBfunc(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self.centralwidget, 'Выберите базу данных', '',
                                                      'Все базы данных SQLite (*.db *.sdb *.sqlite *.db3 *.s3db *.sqlite3 *.sl3)')
        if fname[0]:
            self.con = sqlite3.connect(fname[0])
            self.cur = self.con.cursor()
            self.tables = self.cur.execute("""SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite%'""").fetchall()
            self.tableMenu = QtWidgets.QMenu('Таблица', self.menubar)
            self.tablesActionGroup = QtWidgets.QActionGroup(self.menubar)
            for tableInd in range(len(self.tables)):
                action = QtWidgets.QAction(
                    self.tables[tableInd][0], self.menubar, checkable=True, checked=tableInd == 0)
                self.tablesActionGroup.addAction(action)
                self.tableMenu.addAction(action)
            self.menubar.addAction(self.tableMenu.menuAction())
            self.tablesActionGroup.triggered.connect(self.initTable)
            self.initTable(self.tables[0][0])
            self.setWindowTitle(
                f'Редактор базы данных - {fname[0][fname[0].rfind("/") + 1:]}')
            self.tableWidget.itemSelectionChanged.connect(self.saveItem)
            self.tableWidget.itemChanged.connect(self.editBDfunc)

    def createDBfunc(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(self.centralwidget, 'Создайте базу данных', '',
                                                      'Все базы данных SQLite (*.db *.sdb *.sqlite *.db3 *.s3db *.sqlite3 *.sl3)')
        self.con = sqlite3.connect(fname[0])
        self.cur = self.con.cursor()
        self.setWindowTitle(f'Редактор базы данных - {fname[0][fname[0].rfind("/") + 1:]}*')

    def commitDBfunc(self):
        self.con.commit()
        self.setWindowTitle(self.windowTitle()[:-1])
        self.unsaved = False

    def saveItem(self):
        self.selItems = self.tableWidget.selectedItems()

    def displayError(self, err):
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(err)
        msg.exec_()

    def editBDfunc(self, item):
        try:
            self.cur.execute(f"""UPDATE {self.chosenTable} SET {self.names[item.column()]} = ?
                                    WHERE {self.names[self.primeKeyTables[0]]} = ?""",
                             (item.text(), self.tableWidget.item(item.row(), self.primeKeyTables[0]).text()))
            self.saved = False
            self.setWindowTitle(self.windowTitle() + '*')
        except sqlite3.Error as error:
            self.tableWidget.setItem(self.selItems.row(), self.selItems.column(), self.selItems)
            self.displayError(error)

    def initTable(self, action):
        self.tableWidget.blockSignals(True)
        if isinstance(action, str):
            self.chosenTable = action
        else:
            self.chosenTable = action.text()
        data = self.cur.execute(f'SELECT * FROM {self.chosenTable}')
        self.names = list(map(lambda x: x[0], data.description))
        data = data.fetchall()
        self.primeKeyTables = [self.names.index(col) for col in self.cur.execute(f"""SELECT name 
                                FROM pragma_table_info('{self.chosenTable}') WHERE pk = 1""").fetchall()[0]]
        self.tableWidget.setColumnCount(len(self.names))
        self.tableWidget.setHorizontalHeaderLabels(self.names)
        self.tableWidget.setRowCount(len(data))
        for row in range(len(data)):
            for col in range(len(self.names)):
                if col in self.primeKeyTables:
                    item = QtWidgets.QTableWidgetItem(str(data[row][col]))
                    item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                    self.tableWidget.setItem(row, col, item)
                else:
                    self.tableWidget.setItem(
                        row, col, QtWidgets.QTableWidgetItem(str(data[row][col])))
        header = self.tableWidget.horizontalHeader()
        for col in range(len(self.names)):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.Stretch)
        self.tableWidget.blockSignals(False)

    def closeEvent(self, event):
        if not self.saved:
            msg = QtWidgets.QMessageBox(self.centralwidget)
            msg.setWindowTitle('')
            msg.setIcon(QtWidgets.QMessageBox.Question)
            msg.setText("В базу данных были внесены изменения")
            msg.setInformativeText("Сохранить?")
            msg.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
            msg.setDefaultButton(QtWidgets.QMessageBox.Save)
            reply = msg.exec_()
            if reply == QtWidgets.QMessageBox.Save:
                self.commitDBfunc()
                event.accept()
            elif reply == QtWidgets.QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()

    def delRowDB(self):
        try:
            self.tableWidget.blockSignals(True)
            for selItem in self.selItems:
                self.cur.execute(f"""DELETE from {self.chosenTable} 
                                    WHERE {self.names[self.primeKeyTables[0]]} = ?""",
                                 (self.tableWidget.item(selItem.row(), self.primeKeyTables[0]).text(),))
                self.tableWidget.removeRow(selItem.row())
            self.saved = False
            if not self.windowTitle().endswith('*'):
                self.setWindowTitle(self.windowTitle() + '*')
            self.tableWidget.blockSignals(False)
        except sqlite3.Error as error:
            self.tableWidget.setItem(self.selItems.row(), self.selItems.column(), self.selItems)
            self.displayError(error)

    def addRowBD(self):
        try:
            self.cur.execute(f"""INSERT INTO {self.chosenTable} DEFAULT VALUES""")
            return self.cur.execute(f"""SELECT * FROM {self.chosenTable} 
                                    WHERE {self.names[self.primeKeyTables[0]]} = 
                                    (SELECT MAX({self.names[self.primeKeyTables[0]]}) FROM {self.chosenTable})""").fetchone()
        except sqlite3.Error as error:
            self.tableWidget.setItem(self.selItems.row(), self.selItems.column(), self.selItems)
            self.displayError(error)
       
    def addBottomRow(self):
        self.tableWidget.blockSignals(True)
        data = self.addRowBD()
        self.tableWidget.insertRow(self.selItems[-1].row() + 1)
        for col in range(len(self.names)):
            self.tableWidget.setItem(self.selItems[-1].row() + 1, col, QtWidgets.QTableWidgetItem(str(data[col])))
        self.saved = False
        if not self.windowTitle().endswith('*'):
            self.setWindowTitle(self.windowTitle() + '*')
        self.tableWidget.blockSignals(False)

    def addTopRow(self):
        self.tableWidget.blockSignals(True)
        data = self.addRowBD()
        self.tableWidget.insertRow(self.selItems[-1].row())
        for col in range(len(self.names)):
            self.tableWidget.setItem(self.selItems[-1].row() - 1, col, QtWidgets.QTableWidgetItem(str(data[col])))
        self.saved = False
        if not self.windowTitle().endswith('*'):
            self.setWindowTitle(self.windowTitle() + '*')
        self.tableWidget.blockSignals(False)

    def contextMenuEvent(self, event):
        contextMenu = QtWidgets.QMenu(self)
        self.addTopAct = contextMenu.addAction("Добавить строку сверху")
        self.addBottomAct = contextMenu.addAction("Добавить строку снизу")
        self.delAct = contextMenu.addAction("Удалить")
        action = contextMenu.exec_(self.mapToGlobal(event.pos()))
        if action == self.delAct:
            self.delRowDB()
        elif action == self.addTopAct:
            self.addTopRow()
        elif action == self.addBottomAct:
            self.addBottomRow()

    def setupUi(self):
        self.setGeometry(200, 200, 770, 480)
        self.setWindowTitle('Редактор базы данных')
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 770, 21))
        self.fileMenu = QtWidgets.QMenu('Файл', self.menubar)
        self.setMenuBar(self.menubar)
        self.openDB = QtWidgets.QAction('Открыть', self.fileMenu)
        self.createDB = QtWidgets.QAction('Создать', self.fileMenu)
        self.commitDB = QtWidgets.QAction('Сохранить', self.fileMenu)
        self.fileMenu.addAction(self.openDB)
        self.fileMenu.addAction(self.createDB)
        self.fileMenu.addAction(self.commitDB)
        self.menubar.addAction(self.fileMenu.menuAction())
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.gridLayout.addWidget(self.tableWidget, 0, 0, 1, 1)
        self.openDB.triggered.connect(self.openDBfunc)
        self.commitDB.triggered.connect(self.commitDBfunc)
        self.createDB.triggered.connect(self.createDBfunc)
        self.saved = True


if __name__ == '__main__':
    app = QtWidgets.QApplication(argv)
    ex = DBeditor()
    ex.show()
    exit(app.exec())
