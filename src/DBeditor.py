import os.path
from sys import exit, argv
from typing import List, Optional

from PyQt5 import QtCore, QtWidgets, QtGui

from database import Database
from sqlalchemy.exc import SQLAlchemyError

from uri_builder import build_uri, DatabaseKind


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
        self._database = Database(build_uri(DatabaseKind.SQLITE, filename))
        tables = self._database.get_tables()
        self.initTablesMenu(tables)
        self.initTable(tables[0])
        self.setWindowTitle(f"DBeditor - {os.path.basename(filename)}")
        self.tableWidget.itemDoubleClicked.connect(self.saveItem)
        self.tableWidget.itemChanged.connect(self.editBDfunc)
        self.addedRows = []

    def on_database_create(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget,
            "Create database",
            "",
            "All SQLite databases (*.db *.sdb *.sqlite *.db3 *.s3db *.sqlite3 *.sl3)",
        )
        if not filename:
            return
        self._database = Database(build_uri(DatabaseKind.SQLITE, filename))
        self.setWindowTitle(f"DBeditor - {os.path.basename(filename)}")

    def initTablesMenu(self, tables: List[str]) -> None:
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

    def saveItem(self, item: QtWidgets.QTableWidgetItem) -> None:
        self.selItemText = item.text()
        self.addrToDBRow = self.findRowFromUI(item.row())

    def displayError(self, err: str) -> None:
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(err)
        msg.exec_()

    def findRowFromUI(self, row) -> dict:
        pkItemValues = []
        for uiColIndex in [
            self.names.index(title) for title in self.primeKeyColumns
        ]:
            pkItemValues.append(self.tableWidget.item(row, uiColIndex).text())
        return dict(zip(self.primeKeyColumns, pkItemValues))

    def editBDfunc(self, item: QtWidgets.QTableWidgetItem) -> None:
        try:
            self._database.update_row(
                self.chosenTable,
                self.addrToDBRow,
                {self.names[item.column()]: item.text()},
            )
        except SQLAlchemyError as error:
            self.displayError(str(error.__dict__["orig"]))
            self.tableWidget.setItem(
                item.row(),
                item.column(),
                QtWidgets.QTableWidgetItem(self.selItemText),
            )

    def initTable(self, table: str) -> None:
        self.chosenTable = table
        self.chosenTableLabel.setText(self.chosenTable)
        self.tableWidget.blockSignals(True)
        data = self._database.select_all(self.chosenTable)
        self.names = self._database.get_table_column_names(self.chosenTable)
        self.primeKeyColumns = self._database.get_pk_column_names(
            self.chosenTable
        )
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
        header.setSectionResizeMode(
            len(self.names) - 1, QtWidgets.QHeaderView.Stretch
        )
        self.tableWidget.blockSignals(False)

    def delRowDB(self) -> None:
        try:
            self.tableWidget.blockSignals(True)
            self.selItems = self.tableWidget.selectedItems()
            for selItem in self.selItems:
                self._database.delete_row(
                    self.chosenTable, self.findRowFromUI(selItem.row())
                )
                self.tableWidget.removeRow(selItem.row())
            self.tableWidget.blockSignals(False)
        except SQLAlchemyError as error:
            self.displayError(str(error.__dict__["orig"]))

    def addBottomRowDB(self) -> None:
        self.tableWidget.blockSignals(True)
        self.selItems = self.tableWidget.selectedItems()
        self.tableWidget.insertRow(self.selItems[-1].row() + 1)
        self.addedRows.append(self.selItems[-1].row())
        for col in range(len(self.names)):
            self.tableWidget.setItem(
                self.selItems[-1].row() + 1,
                col,
                QtWidgets.QTableWidgetItem(""),
            )
        self.tableWidget.blockSignals(False)

    def addTopRowDB(self) -> None:
        self.tableWidget.blockSignals(True)
        self.selItems = self.tableWidget.selectedItems()
        self.tableWidget.insertRow(self.selItems[-1].row())
        self.addedRows.append(self.selItems[-1].row())
        for col in range(len(self.names)):
            self.tableWidget.setItem(
                self.selItems[-1].row() - 1,
                col,
                QtWidgets.QTableWidgetItem(),
            )
        self.tableWidget.blockSignals(False)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self.addedRows:
            try:
                if self.addedRows:
                    for row in self.addedRows:
                        rowItems = []
                        for col in range(len(self.names)):
                            rowItems.append(
                                (
                                    col,
                                    self.tableWidget.item(row - 1, col).text(),
                                )
                            )
                        if any(rowItems):
                            self._database.insert_row(self.chosenTable, {})
                        else:
                            self._database.insert_row(
                                self.chosenTable,
                                {key: value for key, value in rowItems},
                            )
                else:
                    event.accept()
            except SQLAlchemyError as error:
                msg = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Warning,
                    "Fill in all the gaps in the new rows",
                    str(error.__dict__["orig"]),
                    QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Cancel,
                    self.centralwidget,
                )
                msg.setInformativeText(
                    """Maybe you haven't set the default value somewhere, or some of your primary keys should be entered manually"""
                )
                msg.setDefaultButton(QtWidgets.QMessageBox.Cancel)
                reply = msg.exec_()
                if reply == QtWidgets.QMessageBox.Close:
                    event.accept()
                elif reply == QtWidgets.QMessageBox.Cancel:
                    event.ignore()

    def executeCustomQuery(self) -> None:
        query = self.customQueryWindow.query.toPlainText()
        try:
            columns, data = self._database.execute_raw(query)
            if data:
                print(columns)
                print(data)
                self.customQueryWindow.tableWidget.setColumnCount(len(columns))
                self.customQueryWindow.tableWidget.setHorizontalHeaderLabels(
                    columns
                )
                self.customQueryWindow.tableWidget.setRowCount(len(data))
                for row in range(len(data)):
                    for col in range(len(columns)):
                        self.customQueryWindow.tableWidget.setItem(
                            row,
                            col,
                            QtWidgets.QTableWidgetItem(str(data[row][col])),
                        )
                header = self.customQueryWindow.tableWidget.horizontalHeader()
                header.setSectionResizeMode(
                    len(columns) - 1, QtWidgets.QHeaderView.Stretch
                )
            tables = self._database.get_tables()
            self.menubar.removeAction(self.tableMenu.menuAction())
            self.initTablesMenu(tables)
            self.initTable(self.chosenTable)
        except SQLAlchemyError as error:
            self.displayError(str(error.__dict__["orig"]))

    def contextMenuEvent(self, event) -> None:
        self.contextMenu.exec_(self.mapToGlobal(event.pos()))

    def initCustomQueryWindow(self) -> None:
        self.customQueryWindow = customQueryWindow()
        self.customQueryWindow.show()
        self.customQueryWindow.execute.clicked.connect(self.executeCustomQuery)

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
        self.resize(900, 500)
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
        self.customQueryAct = QtWidgets.QAction("Custom query", self)
        self.customQueryAct.setShortcut("Ctrl+Q")
        self.addTopAct = QtWidgets.QAction("Add line on top", self)
        self.addBottomAct = QtWidgets.QAction("Add line below", self)
        self.delAct = QtWidgets.QAction("Delete", self)
        self.delAct.setShortcut("Del")

        self.contextMenu = QtWidgets.QMenu(self.centralwidget)
        self.contextMenu.addAction(self.customQueryAct)
        self.centralwidget.addAction(self.customQueryAct)
        self.contextMenu.addAction(self.addTopAct)
        self.contextMenu.addAction(self.addBottomAct)
        self.contextMenu.addAction(self.delAct)
        self.centralwidget.addAction(self.delAct)

        self.fileMenu.addAction(self.openDB)
        self.fileMenu.addAction(self.createDB)
        self.menubar.addAction(self.fileMenu.menuAction())

        self.customQueryAct.triggered.connect(self.initCustomQueryWindow)
        self.delAct.triggered.connect(self.delRowDB)
        self.addTopAct.triggered.connect(self.addTopRowDB)
        self.addBottomAct.triggered.connect(self.addBottomRowDB)
        self.openDB.triggered.connect(self.on_database_open)
        self.createDB.triggered.connect(self.on_database_create)
        self.startSearch.clicked.connect(self.searchAcrossTable)

        self.saved = True


class customQueryWindow(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi()

    def setupUi(self) -> None:
        self.setWindowTitle("Custom query window")
        self.resize(640, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.inputFrame = QtWidgets.QFrame(self)
        self.inputFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.inputFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.gridLayout1 = QtWidgets.QGridLayout(self.inputFrame)
        self.label1 = QtWidgets.QLabel("Type your query:", self.inputFrame)
        self.gridLayout1.addWidget(self.label1, 0, 0, 1, 1)
        self.query = QtWidgets.QPlainTextEdit(self.inputFrame)
        self.gridLayout1.addWidget(self.query, 1, 0, 1, 2)
        self.execute = QtWidgets.QPushButton("Execute", self.inputFrame)
        self.gridLayout1.addWidget(self.execute, 2, 1, 1, 1)
        self.horizontalLayout.addWidget(self.inputFrame)
        self.outputFrame = QtWidgets.QFrame(self)
        self.outputFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.outputFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.gridLayout2 = QtWidgets.QGridLayout(self.outputFrame)
        self.label2 = QtWidgets.QLabel("Output:", self.outputFrame)
        self.gridLayout2.addWidget(self.label2, 0, 0, 1, 1)
        self.tableWidget = QtWidgets.QTableWidget(self.outputFrame)
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.gridLayout2.addWidget(self.tableWidget, 1, 0, 1, 1)
        self.horizontalLayout.addWidget(self.outputFrame)


if __name__ == "__main__":
    app = QtWidgets.QApplication(argv)
    ex = DBeditor()
    ex.show()
    exit(app.exec())
