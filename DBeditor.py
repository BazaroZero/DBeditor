from PyQt5 import QtCore, QtWidgets
from sys import exit, argv
import sqlite3

class DBeditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.setGeometry(200, 200, 770, 480)
        self.setWindowTitle('Редактор базы данных')
        self.openDB.triggered.connect(self.openDBfunc)
        self.commitDB.triggered.connect(self.commitDBfunc)
        self.createDB.triggered.connect(self.createDBfunc)

    def openDBfunc(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self.centralwidget, 'Выберите базу данных', '', 
        'Все базы данных SQLite (*.db *.sdb *.sqlite *.db3 *.s3db *.sqlite3 *.sl3)')
        if fname[0]:
            self.con = sqlite3.connect(fname[0])
            self.cur = self.con.cursor()
            self.tables = self.cur.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite%'""").fetchall()
            self.tableMenu = QtWidgets.QMenu('Таблица', self.menubar)
            self.tablesActionGroup = QtWidgets.QActionGroup(self.menubar)
            for tableInd in range(len(self.tables)):
                action = QtWidgets.QAction(self.tables[tableInd][0], self.menubar, checkable=True, checked=tableInd==0)
                self.tablesActionGroup.addAction(action)
                self.tableMenu.addAction(action)
            self.menubar.addAction(self.tableMenu.menuAction())
            self.tablesActionGroup.triggered.connect(self.initTable)
            self.initTable(self.tables[0][0])
            self.setWindowTitle(f'Редактор базы данных - {fname[0][fname[0].rfind("/") + 1:]}')
            self.tableWidget.itemDoubleClicked.connect(self.saveItem)
            self.tableWidget.itemChanged.connect(self.editBDfunc)
    
    def createDBfunc(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(self.centralwidget, 'Создайте базу данных', '', 'Все базы данных SQLite (*.db *.sdb *.sqlite *.db3 *.s3db *.sqlite3 *.sl3)')
        self.con = sqlite3.connect(fname[0])
        self.cur = self.con.cursor()
        self.setWindowTitle(f'Редактор базы данных - {fname[0][fname[0].rfind("/") + 1:]}')

    def commitDBfunc(self):
        self.con.commit()
    
    def saveItem(self, item):
        self.prevItem = item.text()
    
    def editBDfunc(self, item):
        try:
            self.cur.execute(f"""UPDATE {self.chosenTable} SET {self.names[item.column()]} = ?
                                    WHERE {self.names[self.primeKeyTables[0]]} = {self.tableWidget.item(item.row(), self.primeKeyTables[0]).text()}""", (item.text(),))
        except sqlite3.Error as error:
            self.tableWidget.setItem(self.prevItem.row(), self.prevItem.column(), self.prevItem)
            self.status.setText(error)

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
                    self.tableWidget.setItem(row, col, QtWidgets.QTableWidgetItem(str(data[row][col])))
        header = self.tableWidget.horizontalHeader()
        for col in range(len(self.names)):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.Stretch)
        self.tableWidget.blockSignals(False)
        

    def setupUi(self):
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 770, 21))
        self.fileMenu = QtWidgets.QMenu('Файл', self.menubar)
        self.structureMenu = QtWidgets.QMenu('Структура', self.menubar)
        self.setMenuBar(self.menubar)
        self.openDB = QtWidgets.QAction('Открыть', self.fileMenu)
        self.createDB = QtWidgets.QAction('Создать', self.fileMenu)
        self.createTable = QtWidgets.QAction('Создать таблицу', self.structureMenu)
        self.commitDB = QtWidgets.QAction('Сохранить', self.fileMenu)
        self.createColumn = QtWidgets.QAction('Создать столбец', self.structureMenu)
        self.fileMenu.addAction(self.openDB)
        self.fileMenu.addAction(self.createDB)
        self.fileMenu.addAction(self.commitDB)
        self.structureMenu.addAction(self.createTable)
        self.structureMenu.addAction(self.createColumn)
        self.menubar.addAction(self.fileMenu.menuAction())
        self.menubar.addAction(self.structureMenu.menuAction())
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.gridLayout.addWidget(self.tableWidget, 0, 0, 1, 1)
        self.status = QtWidgets.QLabel(self.centralwidget)
        self.gridLayout.addWidget(self.status, 1, 0, 1, 1)


if __name__ == '__main__':
    app = QtWidgets.QApplication(argv)
    ex = DBeditor()
    ex.show()
    exit(app.exec())