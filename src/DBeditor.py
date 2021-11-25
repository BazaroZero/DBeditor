import os.path
from sys import exit, argv
from typing import Optional

from PyQt5 import QtCore, QtWidgets

from database import Database
from sqlalchemy.exc import SQLAlchemyError


class DBeditor(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._database: Optional[Database] = None
        self.setupUi()

    def on_database_open(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget,
            "Select database",
            "",
            "All SQLite databases (*.db *.sdb *.sqlite *.db3 *.s3db *.sqlite3 *.sl3)",
        )
        if not filename:
            return
        self._database = Database(filename)
        tables = self._database.get_tables()

        self.tableMenu = QtWidgets.QMenu("Table", self.menubar)
        self.tablesActionGroup = QtWidgets.QActionGroup(self.menubar)
        for i, table in enumerate(tables):
            action = QtWidgets.QAction(
                table, self.menubar, checkable=True, checked=i == 0
            )
            self.tablesActionGroup.addAction(action)
            self.tableMenu.addAction(action)
        self.menubar.addAction(self.tableMenu.menuAction())
        self.tablesActionGroup.triggered.connect(
            lambda sender: self.initTable(sender.text())
        )

        self.initTable(tables[0])
        self.setWindowTitle(f"DBeditor - {os.path.basename(filename)}")
        self.tableWidget.itemDoubleClicked.connect(self.saveItem)
        self.tableWidget.itemChanged.connect(self.editBDfunc)

    def on_database_create(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget,
            "Create database",
            "",
            "All SQLite databases (*.db *.sdb *.sqlite *.db3 *.s3db *.sqlite3 *.sl3)",
        )
        self._database = Database(filename)
        self.setWindowTitle(f"DBeditor - {os.path.basename(filename)}*")

    def saveItem(self, item: QtWidgets.QTableWidgetItem) -> None:
        self.selItem = item.text()
        self.addrToDBRow = self.findRowFromUI(item.row())

    def displayError(self, err: str) -> None:
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(err)
        msg.exec_()
    
    def findRowFromUI(self, row) -> dict:
        pkItemValues = []
        for uiColIndex in [self.names.index(title) for title in self.primeKeyColumns]:
            pkItemValues.append(self.tableWidget.item(row, uiColIndex).text())
        return dict(zip(self.primeKeyColumns, pkItemValues))
    
    def editBDfunc(self, item: QtWidgets.QTableWidgetItem) -> None:
        try:
            self._database.update_row(self.chosenTable, self.addrToDBRow, {self.names[item.column()]: item.text()})
        except SQLAlchemyError as error:
            self.displayError(str(error.__dict__['orig']))
            self.tableWidget.setItem(
                item.row(), item.column(), 
                QtWidgets.QTableWidgetItem(self.selItem)
            )

    def initTable(self, action: QtWidgets.QAction) -> None:
        self.chosenTable = action
        self.chosenTableLabel.setText(self.chosenTable)
        self.tableWidget.blockSignals(True)
        data = self._database.select_all(self.chosenTable)
        self.names = self._database.get_table_column_names(self.chosenTable)
        self.primeKeyColumns = self._database.get_pk_column_names(self.chosenTable)
        self.tableWidget.setColumnCount(len(self.names))
        self.tableWidget.setHorizontalHeaderLabels(self.names)
        self.tableWidget.setRowCount(len(data))
        for row in range(len(data)):
            for col in range(len(self.names)):
                self.tableWidget.setItem(
                    row,
                    col,
                    QtWidgets.QTableWidgetItem(str(data[row][col])),
                )
        header = self.tableWidget.horizontalHeader()
        for col in range(len(self.names)):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.Stretch)
        self.tableWidget.blockSignals(False)

    def delRowDB(self) -> None:
        try:
            self.tableWidget.blockSignals(True)
            for selItem in self.selItems:
                self._database.delete_row(self.chosenTable, self.addrToDBRow)
                self.tableWidget.removeRow(selItem.row())
            self.tableWidget.blockSignals(False)
        except SQLAlchemyError as error:
            self.tableWidget.setItem(
                self.selItems.row(), self.selItems.column(), self.selItems
            )
            self.displayError(error)

    # TODO: Insert row with default values
    def addRowBD(self) -> None:
        try:
            pass
            # self._database.insert_row(self.chosenTable)
        except SQLAlchemyError as error:
            self.tableWidget.setItem(
                self.selItems.row(), self.selItems.column(), self.selItems
            )
            self.displayError(error)

    def addBottomRow(self) -> None:
        self.tableWidget.blockSignals(True)
        data = self.addRowBD()
        self.tableWidget.insertRow(self.selItems[-1].row() + 1)
        for col in range(len(self.names)):
            self.tableWidget.setItem(
                self.selItems[-1].row() + 1,
                col,
                QtWidgets.QTableWidgetItem(str(data[col])),
            )
        self.saved = False
        # if not self.windowTitle().endswith("*"):
        #     self.setWindowTitle(self.windowTitle() + "*")
        self.tableWidget.blockSignals(False)

    def addTopRow(self) -> None:
        self.tableWidget.blockSignals(True)
        data = self.addRowBD()
        self.tableWidget.insertRow(self.selItems[-1].row())
        for col in range(len(self.names)):
            self.tableWidget.setItem(
                self.selItems[-1].row() - 1,
                col,
                QtWidgets.QTableWidgetItem(str(data[col])),
            )
        self.saved = False
        # if not self.windowTitle().endswith("*"):
        #     self.setWindowTitle(self.windowTitle() + "*")
        self.tableWidget.blockSignals(False)

    def executeCustomQuery(self) -> None:
        # ВЫПОЛНЕНИЕ КАСТОМНОГО ЗАПРОСА
        self.customQueryWindow.close()
        self.customQueryWindow = None

    def contextMenuEvent(self, event) -> None:
        contextMenu = QtWidgets.QMenu(self)
        self.customQueryAct = QtWidgets.QAction("Custom query", self)
        self.customQueryAct.setShortcut("Ctrl+Q")
        contextMenu.addAction(self.customQueryAct)
        self.addTopAct = QtWidgets.QAction("Add line on top", self)
        contextMenu.addAction(self.addTopAct)
        self.addBottomAct = QtWidgets.QAction("Add line below", self)
        contextMenu.addAction(self.addBottomAct)
        self.delAct = QtWidgets.QAction("Delete", self)
        self.delAct.setShortcut("Del")
        contextMenu.addAction(self.delAct)
        action = contextMenu.exec_(self.mapToGlobal(event.pos()))
        if action == self.delAct:
            self.delRowDB()
        elif action == self.addTopAct:
            self.addTopRow()
        elif action == self.addBottomAct:
            self.addBottomRow()
        elif action == self.customQueryAct:
            self.customQueryWindow = customQueryWindow()
            self.customQueryWindow.show()
            self.customQueryWindow.execute.clicked.connect(
                self.executeCustomQuery
            )

    def searchAcrossTable(self) -> None:
        self.tableWidget.setCurrentItem(None)
        if self.search:
            matchingItems = self.tableWidget.findItems(
                self.search.text(), QtCore.Qt.MatchContains
            )
            if matchingItems:
                for item in matchingItems:
                    item.setSelected(True)

    def setupUi(self) -> None:
        self.setWindowTitle("DBeditor")
        self.resize(569, 425)
        self.centralwidget = QtWidgets.QWidget(self)
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.search = QtWidgets.QLineEdit(self.centralwidget)
        self.search.setPlaceholderText("Type here to search...")
        self.gridLayout.addWidget(self.search, 0, 0, 1, 1)
        self.startSearch = QtWidgets.QPushButton("Search", self.centralwidget)
        self.gridLayout.addWidget(self.startSearch, 0, 1, 1, 1)
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.gridLayout.addWidget(self.tableWidget, 2, 0, 1, 2)
        self.chosenTableLabel = QtWidgets.QLabel(self.centralwidget)
        self.chosenTableLabel.setText("")
        self.gridLayout.addWidget(self.chosenTableLabel, 1, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 569, 21))
        self.fileMenu = QtWidgets.QMenu("File", self.menubar)
        self.setMenuBar(self.menubar)
        self.openDB = QtWidgets.QAction("Open DB", self)
        self.createDB = QtWidgets.QAction("Create DB", self)

        self.fileMenu.addAction(self.openDB)
        self.fileMenu.addAction(self.createDB)
        self.menubar.addAction(self.fileMenu.menuAction())

        self.openDB.triggered.connect(self.on_database_open)
        self.createDB.triggered.connect(self.on_database_create)
        self.startSearch.clicked.connect(self.searchAcrossTable)

        self.saved = True
        self.customQueryWindow = None


class customQueryWindow(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi()

    def setupUi(self) -> None:
        self.setWindowTitle("Custom query window")
        self.resize(398, 282)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.label = QtWidgets.QLabel("Type your query:", self)
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.query = QtWidgets.QPlainTextEdit(self)
        self.gridLayout.addWidget(self.query, 1, 0, 1, 2)
        self.execute = QtWidgets.QPushButton("Search", self)
        self.gridLayout.addWidget(self.execute, 2, 1, 1, 1)


if __name__ == "__main__":
    app = QtWidgets.QApplication(argv)
    ex = DBeditor()
    ex.show()
    exit(app.exec())
