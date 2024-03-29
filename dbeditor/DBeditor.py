import os.path
from sys import exit, argv
from typing import List, Optional

from PyQt5 import QtCore, QtWidgets, QtGui

from dbeditor.database import Database
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import types, Column, MetaData
from dbeditor.uri_builder import build_uri, DatabaseKind, Netloc
from dbeditor.table_builder import BuilderGroup
from dbeditor.loaders.csv_loader import CSVLoader
from dbeditor.loaders.xls_loader import XLSLoader
from dbeditor.loaders.merger import Merger


class DBeditor(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._database: Optional[Database] = None
        self._builder_group: Optional[BuilderGroup] = None
        self.setupUi()

    def on_database_open(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget,
            "Select database",
            "",
            "",
        )
        if not filename:
            return
        self._database = Database(build_uri(DatabaseKind.SQLITE, filename))
        self._builder_group = BuilderGroup(self._database.engine)
        self.addedRows = {}
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.tables = self._database.get_tables()
        self.initTablesMenu(self.tables)
        if self.tables:
            self.initTable(self.tables[0])
        else:
            self.chosenTable = ""
            self.chosenTableLabel.clear()
        self.setWindowTitle(f"DBeditor - {os.path.basename(filename)}")
        self.tableWidget.itemDoubleClicked.connect(self.saveItem)
        self.tableWidget.itemChanged.connect(self.editDBfunc)

    def on_database_create(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget,
            "Create database",
            "",
            "",
        )
        if not filename:
            return
        # TODO: create method for db reinit.
        self._database = Database(build_uri(DatabaseKind.SQLITE, filename))
        self._builder_group = BuilderGroup(self._database.engine)
        self.addedRows, self.tables = {}, []
        self.initTablesMenu([])
        self.chosenTable = ""
        self.chosenTableLabel.clear()
        self.setWindowTitle(f"DBeditor - {os.path.basename(filename)}")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.tableWidget.itemDoubleClicked.connect(self.saveItem)
        self.tableWidget.itemChanged.connect(self.editDBfunc)

    def on_remote_connect(self) -> None:
        translateKind = {
            "SQLite": DatabaseKind.SQLITE,
            "PostgreSQL": DatabaseKind.POSTGRESQL,
            "MySQL": DatabaseKind.MYSQL,
        }
        netlocation = Netloc(
            self.remoteConnectionWindow.username.text(),
            self.remoteConnectionWindow.password.text(),
            self.remoteConnectionWindow.ip.text(),
            self.remoteConnectionWindow.port.text(),
        )
        uri = build_uri(
            translateKind[self.remoteConnectionWindow.DBkind.currentText()],
            self.remoteConnectionWindow.DBlocation.text(),
            netlocation,
        )
        try:
            self._database = Database(uri)
            self._builder_group = BuilderGroup(self._database.engine)
            self.addedRows = {}
            self.tableWidget.setColumnCount(0)
            self.tableWidget.setRowCount(0)
            self.tables = self._database.get_tables()
            self.initTablesMenu(self.tables)
            if self.tables:
                self.initTable(self.tables[0])
            else:
                self.chosenTable = ""
                self.chosenTableLabel.clear()
            self.setWindowTitle(
                f"DBeditor - {self.remoteConnectionWindow.DBlocation.text()}"
            )
            self.tableWidget.itemDoubleClicked.connect(self.saveItem)
            self.tableWidget.itemChanged.connect(self.editDBfunc)
        except SQLAlchemyError as error:
            self.remoteConnectionWindow.displayError(error)

    def initRemoteConWindow(self) -> None:
        self.remoteConnectionWindow = remoteConnectionWindow()
        self.remoteConnectionWindow.connect.clicked.connect(
            self.on_remote_connect
        )
        self.remoteConnectionWindow.show()

    def importCSV(self) -> None:
        if self._database:
            if self.chosenTable not in self._builder_group:
                filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self.centralwidget,
                    "Select сsv",
                    "",
                    "*.csv",
                )
                if not filename:
                    return
                try:
                    with open(filename) as file:
                        loader = CSVLoader(file)
                        merger = Merger(
                            self._database.get_table(self.chosenTable)
                        )
                        # FIXME: file closed during merge
                        with self._database.session as s:
                            merger.merge(s, loader)
                    self.initTable(self.chosenTable)
                except SQLAlchemyError as error:
                    self.displayError(str(error))
            else:
                self.displayError("Save the table before importing the data")

    def importXls(self) -> None:
        if self._database:
            if self.chosenTable not in self._builder_group:
                filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self.centralwidget,
                    "Select excel file",
                    "",
                    "*.xls, *.xlsx",
                )
                if not filename:
                    return
                worksheet, okPressed = QtWidgets.QInputDialog.getText(
                    self, "Import xls", "Enter the title of the worksheet"
                )
                if okPressed and worksheet:
                    try:
                        with open(filename, "rb") as file:
                            loader = XLSLoader(file, worksheet)
                            merger = Merger(
                                self._database.get_table(self.chosenTable)
                            )
                            # FIXME: file closed during merge
                            with self._database.session as s:
                                merger.merge(s, loader)
                        self.initTable(self.chosenTable)
                    except SQLAlchemyError as error:
                        self.displayError(str(error))
            else:
                self.displayError("Save the table before importing the data")

    def initTablesMenu(self, tables: List[str]) -> None:
        if self.tablesMenuCreated:
            self.menubar.removeAction(self.tableMenu.menuAction())
        self.tableMenu = QtWidgets.QMenu("Table", self.menubar)
        self.tablesActionGroup = QtWidgets.QActionGroup(self.menubar)
        for i, table in enumerate(tables):
            action = QtWidgets.QAction(
                table, self.menubar, checkable=True, checked=i == 0
            )
            self.tablesActionGroup.addAction(action)
            self.tableMenu.addAction(action)
        self.menubar.addAction(self.tableMenu.menuAction())
        self.tablesMenuCreated = True
        self.tablesActionGroup.triggered.connect(
            lambda sender: self.initTable(sender.text(), True)
        )

    def saveItem(self, item: QtWidgets.QTableWidgetItem) -> None:
        if self.chosenTable not in self._builder_group:
            self.selItemText = item.text()
            self.addrToDBRow = self.findRowFromUI(item.row())

    def displayError(self, err: str, close: bool = False) -> None:
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(err)
        if close:
            msg.setStandardButtons(
                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Close
            )
            msg.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        return msg.exec_()

    def findRowFromUI(self, row) -> dict:
        pkItemValues = []
        for uiColIndex in [
            self.names.index(title) for title in self.primeKeyColumns
        ]:
            pkItemValues.append(self.tableWidget.item(row, uiColIndex).text())
        if out := dict(zip(self.primeKeyColumns, pkItemValues)):
            return out
        return False

    def editDBfunc(self, item: QtWidgets.QTableWidgetItem) -> None:
        try:
            if self.chosenTable not in self._builder_group:
                if (
                    self.chosenTable not in self.addedRows
                    or item.row() not in self.addedRows[self.chosenTable]
                ):
                    if self.settingsWindow.rowid.isChecked():
                        rowid = self._database.select_rowid(self.chosenTable)[
                            self.tableWidget.selectedRanges()[-1].bottomRow()
                        ][0]
                        self._database.update_row_through_rowid(
                            self.chosenTable,
                            rowid,
                            {
                                self.names[item.column()]: self.translateString(
                                    item.text()
                                )
                            },
                        )
                    else:
                        self._database.update_row(
                            self.chosenTable,
                            self.addrToDBRow,
                            {
                                self.names[item.column()]: self.translateString(
                                    item.text()
                                )
                            },
                        )
                else:
                    self.addedRows[self.chosenTable][item.row()][
                        item.column()
                    ] = item.text()
            else:
                if self.chosenTable not in self.addedRows:
                    self.addedRows[self.chosenTable] = {
                        item.row(): {item.column(): item.text()}
                    }
                else:
                    self.addedRows[self.chosenTable][item.row()][
                        item.column()
                    ] = item.text()
        except SQLAlchemyError as error:
            self.tableWidget.blockSignals(True)
            self.displayError(str(error))
            self.tableWidget.setItem(
                item.row(),
                item.column(),
                QtWidgets.QTableWidgetItem(self.selItemText),
            )
            self.tableWidget.blockSignals(False)

    def insertRowsDB(self) -> None:
        for table, rows in self.addedRows.items():
            for row in rows:
                rowItems = {}
                for col in self.addedRows[self.chosenTable][row]:
                    rowItems[self.names[col]] = self.addedRows[table][row][col]
                self._database.insert_row(table, rowItems)

    def addTablesUI(self) -> None:
        if self._database:
            self.tableWidget.blockSignals(True)
            table, okPressed = QtWidgets.QInputDialog.getText(
                self, "New table", "Enter the title of the table"
            )
            if okPressed and table:
                if table in self.tables or table in self._builder_group:
                    self.displayError("Table with this name already exists")
                else:
                    self._builder_group.start_building(table)
                    if self.tableMenu.isEmpty():
                        action = QtWidgets.QAction(
                            table + "*",
                            self.menubar,
                            checkable=True,
                            checked=True,
                        )
                        self.initTable(table)
                    else:
                        action = QtWidgets.QAction(
                            table + "*", self.menubar, checkable=True
                        )
                    self.tablesActionGroup.addAction(action)
                    self.tableMenu.addAction(action)
            self.tableWidget.blockSignals(False)

    def translateString(self, string: str):
        translate = {"True": True, "False": False, "None": None, "Null": None}
        if string in translate:
            return translate[string]
        return string

    def addColumnUI(self) -> None:
        if not self.addColumnWindow.title.text():
            self.addColumnWindow.displayError("Enter title of the column")
        elif (
            self.chosenTable in self._builder_group
            and self.addColumnWindow.title.text()
            in self._builder_group[self.chosenTable]
        ):
            self.addColumnWindow.displayError(
                "Column with this name already exists"
            )
        else:
            translateConstraints = {
                "Primary key": "primary_key",
                "Not null": "nullable",
                "Unique": "unique",
                "Autoincrement": "autoincrement",
            }
            translateTypes = {
                "BigInteger": types.BigInteger,
                "Boolean": types.Boolean,
                "Date": types.Date,
                "DateTime": types.DateTime,
                "Integer": types.Integer,
                "Float": types.Float,
                "Numeric": types.Numeric,
                "Text": types.Text,
                "String": types.String,
            }
            constraints = {}
            for btn in self.addColumnWindow.btnGroup.buttons():
                if btn.isChecked():
                    constraints[translateConstraints[btn.text()]] = True
            if self.addColumnWindow.default.isChecked():
                constraints["default"] = self.translateString(
                    self.addColumnWindow.defVallue.text()
                )

            column = Column(
                name=self.addColumnWindow.title.text(),
                type_=translateTypes[self.addColumnWindow.type.currentText()],
                **constraints,
            )
            self._builder_group[self.chosenTable].add_column(column)
            self.initTable(self.chosenTable)

    def addTablesDB(self) -> None:
        self._builder_group.create_table(
            self.chosenTable, self._database.metadata
        )

    def dropTableDB(self) -> None:
        if self._database:
            if (
                self.chosenTableLabel.text()
                and self.chosenTable not in self._builder_group
            ):
                self._database.get_table(self.chosenTable).drop(
                    self._database._engine
                )
                self._database._metadata = MetaData()
                self._database._metadata.reflect(bind=self._database._engine)
            if self.chosenTable in self.addedRows:
                del self.addedRows[self.chosenTable]
            if self.chosenTable in self._builder_group:
                del self._builder_group[self.chosenTable]
            if self.chosenTable in self.tables:
                self.tables.remove(self.chosenTable)
            if self.chosenTable in self._builder_group:
                del self._builder_group[self.chosenTable]
            action = self.tablesActionGroup.checkedAction()
            self.tableMenu.removeAction(action)
            self.tablesActionGroup.removeAction(action)
            self.tableWidget.setColumnCount(0)
            self.tableWidget.setRowCount(0)
            self.chosenTableLabel.setText("")

    def initAddColumnWindow(self) -> None:
        if self._database:
            if self.chosenTable in self._builder_group:
                self.addColumnWindow = addColumnWindow()
                self.addColumnWindow.add.clicked.connect(self.addColumnUI)
                self.addColumnWindow.show()
            else:
                self.displayError(
                    "Adding columns to an existing table is not supported"
                )

    def renderExisting(self):
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
        if self.chosenTable in self.addedRows:
            for row in self.addedRows[self.chosenTable]:
                self.tableWidget.insertRow(row)
                for col in range(len(self.names)):
                    if col in self.addedRows[self.chosenTable][row]:
                        self.tableWidget.setItem(
                            row,
                            col,
                            QtWidgets.QTableWidgetItem(
                                self.addedRows[self.chosenTable][row][col]
                            ),
                        )
                    else:
                        self.tableWidget.setItem(
                            row,
                            col,
                            QtWidgets.QTableWidgetItem(),
                        )

    def renderNew(self, render):
        if self.chosenTable in self._builder_group:
            self.names = list(self._builder_group[self.chosenTable])
            self.tableWidget.setColumnCount(
                len(self._builder_group[self.chosenTable])
            )
            self.tableWidget.setHorizontalHeaderLabels(self.names)
            if self.chosenTable in self.addedRows:
                if render:
                    self.tableWidget.setRowCount(
                        len(self.addedRows[self.chosenTable].keys())
                    )
                    for row in self.addedRows[self.chosenTable]:
                        for col in range(len(self.names)):
                            if col in self.addedRows[self.chosenTable][row]:
                                self.tableWidget.setItem(
                                    row,
                                    col,
                                    QtWidgets.QTableWidgetItem(
                                        self.addedRows[self.chosenTable][row][
                                            col
                                        ]
                                    ),
                                )
                            else:
                                self.tableWidget.setItem(
                                    row,
                                    col,
                                    QtWidgets.QTableWidgetItem(),
                                )
            else:
                self.tableWidget.setRowCount(1)
                builder = self._builder_group[self.chosenTable]
                for col in range(len(builder)):
                    self.tableWidget.setItem(
                        0,
                        col,
                        QtWidgets.QTableWidgetItem(),
                    )
        else:
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(0)

    def initTable(self, table: str, render: bool = False) -> None:
        self.chosenTable = table.rstrip("*")
        self.chosenTableLabel.setText(self.chosenTable)
        self.tableWidget.blockSignals(True)
        if self.chosenTable not in self._builder_group:
            self.renderExisting()
        else:
            self.renderNew(render)
        self.tableWidget.blockSignals(False)

    def delRowDB(self) -> None:
        try:
            self.tableWidget.blockSignals(True)
            selItems = self.tableWidget.selectedRanges()
            ok = True
            for selItem in selItems:
                if self.chosenTable not in self.addedRows or (
                    self.chosenTable in self.addedRows
                    and selItem.bottomRow()
                    not in self.addedRows[self.chosenTable]
                ):
                    if self.settingsWindow.rowid.isChecked():
                        rowid = self._database.select_rowid(self.chosenTable)[
                            selItem.bottomRow()
                        ][0]
                        self._database.delete_row_through_rowid(
                            self.chosenTable, rowid
                        )
                    else:
                        pks = self.findRowFromUI(selItem.bottomRow())
                        if pks:
                            self._database.delete_row(self.chosenTable, pks)
                        else:
                            ok = False
                            self.displayError(
                                "It's unable to automatically locate row. "
                                "Table doesn't have any primary key"
                            )
                else:
                    del self.addedRows[self.chosenTable][selItem.bottomRow()]
                if ok:
                    self.tableWidget.removeRow(selItem.bottomRow())
                if (
                    ok
                    and self.chosenTable in self.addedRows
                    and not self.addedRows[self.chosenTable]
                    and self.chosenTable not in self._builder_group
                ):
                    action1 = self.tablesActionGroup.checkedAction()
                    self.tablesActionGroup.removeAction(action1)
                    self.tableMenu.removeAction(action1)
                    action2 = QtWidgets.QAction(
                        self.chosenTable,
                        self.menubar,
                        checkable=True,
                        checked=True,
                    )
                    self.tablesActionGroup.addAction(action2)
                    self.tableMenu.addAction(action2)
                    self.tableWidget.blockSignals(False)
        except SQLAlchemyError as error:
            self.displayError(str(error))

    def addRowUI(self) -> None:
        self.tableWidget.blockSignals(True)
        if (
            self.chosenTable not in self.addedRows
            and self.chosenTable not in self._builder_group
        ):
            action1 = self.tablesActionGroup.checkedAction()
            self.tablesActionGroup.removeAction(action1)
            self.tableMenu.removeAction(action1)
            action2 = QtWidgets.QAction(
                self.chosenTable + "*",
                self.menubar,
                checkable=True,
                checked=True,
            )
            self.tablesActionGroup.addAction(action2)
            self.tableMenu.addAction(action2)
        if self.tableWidget.rowCount():
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            if self.chosenTable not in self.addedRows:
                self.addedRows[self.chosenTable] = {
                    self.tableWidget.rowCount() - 1: {}
                }
            else:
                self.addedRows[self.chosenTable][
                    self.tableWidget.rowCount() - 1
                ] = {}
            self.tableWidget.scrollToBottom()
        else:
            self.tableWidget.insertRow(0)
            self.addedRows[self.chosenTable] = {0: {}}
        self.tableWidget.blockSignals(False)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self._database:
            try:
                if len(self._builder_group) != 0:
                    self.addTablesDB()
                if self.addedRows:
                    self.insertRowsDB()
                event.accept()
            except SQLAlchemyError as error:
                reply = self.displayError(str(error), True)
                if reply == QtWidgets.QMessageBox.Cancel:
                    event.ignore()
                else:
                    event.accept()
        else:
            event.accept()

    def saveTableDB(self) -> None:
        if not self._database:
            return
        try:
            if self.chosenTable in self._builder_group:
                self.addTablesDB()
            if self.addedRows:
                self.insertRowsDB()
                del self.addedRows[self.chosenTable]
            self.initTable(self.chosenTable)
            action1 = self.tablesActionGroup.checkedAction()
            self.tablesActionGroup.removeAction(action1)
            self.tableMenu.removeAction(action1)
            action2 = QtWidgets.QAction(
                self.chosenTable, self.menubar, checkable=True, checked=True
            )
            self.tablesActionGroup.addAction(action2)
            self.tableMenu.addAction(action2)
        except SQLAlchemyError as error:
            self.displayError(str(error))

    def executeCustomQuery(self) -> None:
        query = self.customQueryWindow.query.toPlainText()
        try:
            result = self._database.execute_raw(query)
            if result:
                columns, data = result
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
            tables = self._database.get_tables()
            self.menubar.removeAction(self.tableMenu.menuAction())
            self.initTablesMenu(tables)
            self.initTable(self.chosenTable)
        except SQLAlchemyError as error:
            self.customQueryWindow.displayError(str(error))

    def contextMenuEvent(self, event) -> None:
        if self._database:
            self.addRowAct = QtWidgets.QAction("Add row", self.centralwidget)
            self.delAct = QtWidgets.QAction("Delete row", self.centralwidget)
            self.contextMenu = QtWidgets.QMenu(self.centralwidget)
            if self.chosenTable not in self._builder_group:
                self.customQueryAct = QtWidgets.QAction(
                    "Custom query", self.centralwidget
                )
                self.contextMenu.addAction(self.customQueryAct)
            else:
                self.customQueryAct = -1
            self.contextMenu.addActions((self.addRowAct, self.delAct))
            action = self.contextMenu.exec_(self.mapToGlobal(event.pos()))
            if action == self.delAct:
                self.delRowDB()
            elif action == self.customQueryAct:
                self.initCustomQueryWindow()
            elif action == self.addRowAct:
                self.addRowUI()

    def initCustomQueryWindow(self) -> None:
        self.customQueryWindow = CustomQueryWindow()
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

    def initSettingsMenu(self) -> None:
        self.settingsWindow.show()

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
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.gridLayout.addWidget(self.tableWidget, 2, 0, 1, 2)
        self.chosenTableLabel = QtWidgets.QLabel(self.centralwidget)
        self.chosenTableLabel.setText("")
        self.gridLayout.addWidget(self.chosenTableLabel, 1, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 569, 21))
        self.fileMenu = QtWidgets.QMenu("File", self.menubar)
        self.structureMenu = QtWidgets.QMenu("Structure", self.menubar)
        self.settingsWindow = settingsWindow()
        self.toolsMenu = QtWidgets.QMenu("Tools", self.menubar)
        self.setMenuBar(self.menubar)
        self.openDB = QtWidgets.QAction("Open DB", self.centralwidget)
        self.createDB = QtWidgets.QAction("Create DB", self.centralwidget)
        self.remoteConAct = QtWidgets.QAction(
            "Connect remotely", self.centralwidget
        )
        self.importCsvAct = QtWidgets.QAction(
            "Import data from CSV", self.centralwidget
        )
        self.saveTableAct = QtWidgets.QAction("Save table", self.centralwidget)
        self.importXlsAct = QtWidgets.QAction(
            "Import data from XLS", self.centralwidget
        )
        self.addTableAct = QtWidgets.QAction("Add table", self.centralwidget)
        self.addColumnAct = QtWidgets.QAction("Add column", self.centralwidget)
        self.dropTableAct = QtWidgets.QAction("Drop table", self.centralwidget)
        self.settingsAct = QtWidgets.QAction("Settings", self.centralwidget)

        self.fileMenu.addActions(
            (
                self.openDB,
                self.createDB,
                self.remoteConAct,
                self.importCsvAct,
                self.importXlsAct,
                self.saveTableAct,
            )
        )
        self.structureMenu.addActions(
            (self.addTableAct, self.addColumnAct, self.dropTableAct)
        )
        self.toolsMenu.addAction(self.settingsAct)
        self.menubar.addActions(
            (
                self.fileMenu.menuAction(),
                self.structureMenu.menuAction(),
                self.toolsMenu.menuAction(),
            )
        )

        self.settingsAct.triggered.connect(self.initSettingsMenu)
        self.openDB.triggered.connect(self.on_database_open)
        self.createDB.triggered.connect(self.on_database_create)
        self.saveTableAct.triggered.connect(self.saveTableDB)
        self.remoteConAct.triggered.connect(self.initRemoteConWindow)
        self.importCsvAct.triggered.connect(self.importCSV)
        self.importXlsAct.triggered.connect(self.importXls)
        self.addTableAct.triggered.connect(self.addTablesUI)
        self.addColumnAct.triggered.connect(self.initAddColumnWindow)
        self.dropTableAct.triggered.connect(self.dropTableDB)
        self.startSearch.clicked.connect(self.searchAcrossTable)

        self.tablesMenuCreated = False


class CustomQueryWindow(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi()

    def displayError(self, err: str) -> None:
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(err)
        return msg.exec_()

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
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.gridLayout2.addWidget(self.tableWidget, 1, 0, 1, 1)
        self.horizontalLayout.addWidget(self.outputFrame)


class addColumnWindow(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi()

    def displayError(self, err: str) -> None:
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(err)
        return msg.exec_()

    def unblockAutoinc(self) -> None:
        if self.pk.isChecked():
            self.autoinc.setDisabled(False)
        else:
            self.autoinc.setDisabled(True)

    def unblockDefaultValue(self) -> None:
        if self.default.isChecked():
            self.defVallue.setDisabled(False)
        else:
            self.defVallue.setDisabled(True)

    def setupUi(self) -> None:
        self.setWindowTitle("New column")
        self.resize(485, 240)
        self.gridLayout2 = QtWidgets.QGridLayout(self)
        self.add = QtWidgets.QPushButton("Add", self)
        self.gridLayout2.addWidget(self.add, 2, 0, 1, 1)
        self.frame1 = QtWidgets.QFrame(self)
        self.frame1.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame1.setFrameShadow(QtWidgets.QFrame.Raised)
        self.formLayout = QtWidgets.QFormLayout(self.frame1)
        self.label1 = QtWidgets.QLabel("Column title:", self.frame1)
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.label1
        )
        self.label2 = QtWidgets.QLabel("Type:", self.frame1)
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.label2
        )
        self.title = QtWidgets.QLineEdit(self.frame1)
        self.formLayout.setWidget(
            1, QtWidgets.QFormLayout.LabelRole, self.title
        )
        self.type = QtWidgets.QComboBox(self.frame1)
        self.type.addItems(
            (
                "BigInteger",
                "Boolean",
                "Date",
                "DateTime",
                "Integer",
                "Float",
                "Numeric",
                "Text",
                "String",
            )
        )
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.type)
        self.gridLayout2.addWidget(self.frame1, 0, 0, 1, 1)
        self.frame2 = QtWidgets.QFrame(self)
        self.frame2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.gridLayout1 = QtWidgets.QGridLayout(self.frame2)
        self.btnGroup = QtWidgets.QButtonGroup(self, exclusive=False)
        self.pk = QtWidgets.QCheckBox("Primary key", self.frame2)
        self.pk.stateChanged.connect(self.unblockAutoinc)
        self.btnGroup.addButton(self.pk)
        self.gridLayout1.addWidget(self.pk, 0, 0, 1, 1)
        self.autoinc = QtWidgets.QCheckBox("Autoincrement", self.frame2)
        self.autoinc.setDisabled(True)
        self.btnGroup.addButton(self.autoinc)
        self.gridLayout1.addWidget(self.autoinc, 0, 1, 1, 1)
        self.notnull = QtWidgets.QCheckBox("Not null", self.frame2)
        self.btnGroup.addButton(self.notnull)
        self.gridLayout1.addWidget(self.notnull, 1, 0, 1, 1)
        self.default = QtWidgets.QCheckBox("Default", self.frame2)
        self.default.stateChanged.connect(self.unblockDefaultValue)
        self.gridLayout1.addWidget(self.default, 2, 0, 1, 1)
        self.defVallue = QtWidgets.QLineEdit(self.frame2)
        self.defVallue.setDisabled(True)
        self.gridLayout1.addWidget(self.defVallue, 2, 1, 1, 1)
        self.unique = QtWidgets.QCheckBox("Unique", self.frame2)
        self.btnGroup.addButton(self.unique)
        self.gridLayout1.addWidget(self.unique, 3, 0, 1, 1)
        self.gridLayout2.addWidget(self.frame2, 1, 0, 1, 1)


class remoteConnectionWindow(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi()

    def displayError(self, err: str) -> None:
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(err)
        return msg.exec_()

    def setupUi(self) -> None:
        self.setWindowTitle("Remote connection")
        self.resize(430, 300)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.DBkind = QtWidgets.QComboBox(self)
        self.DBkind.addItems(("SQLite", "PostgreSQL", "MySQL"))
        self.gridLayout.addWidget(self.DBkind, 1, 0, 1, 1)
        self.password = QtWidgets.QLineEdit(self)
        self.gridLayout.addWidget(self.password, 5, 0, 1, 1)
        self.label6 = QtWidgets.QLabel(":", self)
        self.gridLayout.addWidget(self.label6, 7, 1, 1, 1)
        self.label3 = QtWidgets.QLabel("Password:", self)
        self.gridLayout.addWidget(self.label3, 4, 0, 1, 1)
        self.username = QtWidgets.QLineEdit(self)
        self.gridLayout.addWidget(self.username, 3, 0, 1, 1)
        self.label4 = QtWidgets.QLabel("Network location:", self)
        self.gridLayout.addWidget(self.label4, 6, 0, 1, 1)
        self.label5 = QtWidgets.QLabel("Database location:", self)
        self.gridLayout.addWidget(self.label5, 8, 0, 1, 1)
        self.label2 = QtWidgets.QLabel("Username:", self)
        self.gridLayout.addWidget(self.label2, 2, 0, 1, 1)
        self.ip = QtWidgets.QLineEdit(self)
        self.gridLayout.addWidget(self.ip, 7, 0, 1, 1)
        self.DBlocation = QtWidgets.QLineEdit(self)
        self.gridLayout.addWidget(self.DBlocation, 9, 0, 1, 1)
        self.label1 = QtWidgets.QLabel("Database kind:", self)
        self.gridLayout.addWidget(self.label1, 0, 0, 1, 1)
        self.port = QtWidgets.QLineEdit(self)
        self.gridLayout.addWidget(self.port, 7, 2, 1, 1)
        self.connect = QtWidgets.QPushButton("Connect", self)
        self.gridLayout.addWidget(self.connect, 10, 2, 1, 1)


class settingsWindow(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi()

    def setupUi(self) -> None:
        self.setWindowTitle("Settings")
        self.resize(230, 100)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.label = QtWidgets.QLabel("How to find a row in a table?", self)
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.rowid = QtWidgets.QRadioButton("By rowid", self)
        self.rowid.setChecked(True)
        self.pks = QtWidgets.QRadioButton("By primary keys", self)
        self.findRowSettings = QtWidgets.QButtonGroup(self)
        self.findRowSettings.addButton(self.rowid)
        self.findRowSettings.addButton(self.pks)
        self.gridLayout.addWidget(self.rowid, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.pks, 2, 0, 1, 1)


def run():
    app = QtWidgets.QApplication(argv)
    ex = DBeditor()
    ex.show()
    exit(app.exec())
