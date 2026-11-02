"""PyQt5 HTML Table Extractor UI.

Provides a window to load an HTML file, select a table, assign roles to columns
and filter/export data. Layout adjusted: taller table view, compact selectors,
single-click toggling of checkboxes (no tiny checkbox click needed).
"""

import sys
from typing import Any, cast, List
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QComboBox, QListWidget, QListWidgetItem, QTableView, QMessageBox,
    QGroupBox, QAbstractItemView, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant
import pandas as pd
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QSplitter
# Fallback numeric constants
ITEM_IS_USER_CHECKABLE = 0x0100
CHECKED = 2
UNCHECKED = 0

class DataFrameModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df.copy()

    def rowCount(self, parent=None):  # type: ignore[override]
        return len(self._df.index)

    def columnCount(self, parent=None):  # type: ignore[override]
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):  # type: ignore[attr-defined]
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:  # type: ignore[attr-defined]
            val = self._df.iat[index.row(), index.column()]
            return "" if pd.isna(val) else str(val)
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # type: ignore[attr-defined]
        if role != Qt.DisplayRole:  # type: ignore[attr-defined]
            return QVariant()
        if orientation == Qt.Horizontal:  # type: ignore[attr-defined]
            return str(self._df.columns[section])
        return str(self._df.index[section])

class TableExtractorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Extraction from scope using html file")
        self.resize(1100, 700)
        self.tables: List[Any] = []
        self.current_df = pd.DataFrame()
        self._build_ui()

    def _build_ui(self):
        # Root layout with splitter for adjustable sidebar width
        root_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(splitter)

        # Sidebar container with scroll area (so all controls visible even if window short)
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_scroll.setWidget(sidebar_widget)

        # File open controls
        file_group = QGroupBox("File")
        file_layout = QHBoxLayout()
        self.open_btn = QPushButton("Open HTML File")
        self.open_btn.clicked.connect(self.open_file)
        self.table_select = QComboBox()
        self.table_select.currentIndexChanged.connect(self.load_selected_table)
        file_layout.addWidget(self.open_btn)
        file_layout.addWidget(QLabel("Table:"))
        file_layout.addWidget(self.table_select)
        file_group.setLayout(file_layout)
        sidebar_layout.addWidget(file_group)

        # Roles group (channel/measurement/statistics)
        roles_group = QGroupBox("Column Roles")
        roles_layout = QVBoxLayout()
        self.channel_combo = QComboBox()
        self.param_combo = QComboBox()
        self.channel_combo.currentIndexChanged.connect(self._roles_changed)
        self.param_combo.currentIndexChanged.connect(self._roles_changed)
        roles_layout.addWidget(QLabel("Channel Column:"))
        roles_layout.addWidget(self.channel_combo)
        roles_layout.addWidget(QLabel("Measurement Column:"))
        roles_layout.addWidget(self.param_combo)
        roles_layout.addWidget(QLabel("Statistics Columns:"))
        self.stats_list = QListWidget()
        self.stats_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.stats_list.itemClicked.connect(self._toggle_item_check)
        roles_layout.addWidget(self.stats_list)
        stats_btn_row = QHBoxLayout()
        self.stats_all_btn = QPushButton("All")
        self.stats_none_btn = QPushButton("None")
        self.stats_all_btn.clicked.connect(lambda: self._set_all_checks(self.stats_list, True))
        self.stats_none_btn.clicked.connect(lambda: self._set_all_checks(self.stats_list, False))
        stats_btn_row.addWidget(self.stats_all_btn)
        stats_btn_row.addWidget(self.stats_none_btn)
        roles_layout.addLayout(stats_btn_row)
        roles_group.setLayout(roles_layout)
        sidebar_layout.addWidget(roles_group)

        # Filtering group (channels/parameters + actions)
        filter_group = QGroupBox("Filtering")
        filter_layout = QVBoxLayout()
        filter_layout.addWidget(QLabel("Channels:"))
        self.channel_filter_list = QListWidget()
        self.channel_filter_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.channel_filter_list.itemClicked.connect(self._toggle_item_check)
        filter_layout.addWidget(self.channel_filter_list)
        ch_btn_row = QHBoxLayout()
        self.channels_all_btn = QPushButton("All")
        self.channels_none_btn = QPushButton("None")
        self.channels_all_btn.clicked.connect(lambda: self._set_all_checks(self.channel_filter_list, True))
        self.channels_none_btn.clicked.connect(lambda: self._set_all_checks(self.channel_filter_list, False))
        ch_btn_row.addWidget(self.channels_all_btn)
        ch_btn_row.addWidget(self.channels_none_btn)
        filter_layout.addLayout(ch_btn_row)
        filter_layout.addWidget(QLabel("Parameters:"))
        self.param_filter_list = QListWidget()
        self.param_filter_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.param_filter_list.itemClicked.connect(self._toggle_item_check)
        filter_layout.addWidget(self.param_filter_list)
        param_btn_row = QHBoxLayout()
        self.params_all_btn = QPushButton("All")
        self.params_none_btn = QPushButton("None")
        self.params_all_btn.clicked.connect(lambda: self._set_all_checks(self.param_filter_list, True))
        self.params_none_btn.clicked.connect(lambda: self._set_all_checks(self.param_filter_list, False))
        param_btn_row.addWidget(self.params_all_btn)
        param_btn_row.addWidget(self.params_none_btn)
        filter_layout.addLayout(param_btn_row)
        actions_row = QHBoxLayout()
        self.apply_filter_btn = QPushButton("Apply")
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.clicked.connect(self.export_csv)
        actions_row.addStretch(1)
        actions_row.addWidget(self.apply_filter_btn)
        actions_row.addWidget(self.export_btn)
        filter_layout.addLayout(actions_row)
        filter_group.setLayout(filter_layout)
        sidebar_layout.addWidget(filter_group)

        # Status label at bottom sticks but scrolls with sidebar content
        self.status_lbl = QLabel("Ready")
        sidebar_layout.addWidget(self.status_lbl)
        sidebar_layout.addStretch(1)

        # Table view on right gets all remaining space
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add widgets to splitter
        splitter.addWidget(sidebar_scroll)
        splitter.addWidget(self.table_view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

    def _toggle_item_check(self, item: QListWidgetItem):
        if item.checkState() == CHECKED:
            item.setCheckState(cast(Any, UNCHECKED))
        else:
            item.setCheckState(cast(Any, CHECKED))

    def _roles_changed(self):
        self._refresh_stats_list()
        self.populate_filter_lists()

    def _refresh_stats_list(self):
        self.stats_list.clear()
        channel_col = self.channel_combo.currentText()
        param_col = self.param_combo.currentText()
        for c in [str(x) for x in self.current_df.columns]:
            if c in (channel_col, param_col):
                continue
            item = QListWidgetItem(c)
            item.setFlags(cast(Any, item.flags() | ITEM_IS_USER_CHECKABLE))
            item.setCheckState(cast(Any, CHECKED))
            self.stats_list.addItem(item)

    def _set_all_checks(self, list_widget: QListWidget, checked: bool):
        state = cast(Any, CHECKED if checked else UNCHECKED)
        for i in range(list_widget.count()):
            it = list_widget.item(i)
            if it:
                it.setCheckState(state)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open HTML File", "", "HTML Files (*.html *.htm)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                html = f.read()
            soup = BeautifulSoup(html, 'html.parser')
            self.tables = soup.find_all('table')
            if not self.tables:
                QMessageBox.warning(self, "No Tables", "No <table> tags found.")
                self.table_select.clear()
                self.current_df = pd.DataFrame()
                self.update_table_view()
                return
            self.table_select.clear()
            for i, _ in enumerate(self.tables):
                self.table_select.addItem(f"Table {i}")
            self.table_select.setCurrentIndex(0)
            self.load_selected_table()
            self.status_lbl.setText(f"Loaded {len(self.tables)} tables from file.")
        except (OSError, UnicodeDecodeError, ValueError) as e:
            QMessageBox.critical(self, "Error", f"Failed to read file: {e}")

    def load_selected_table(self):
        idx = self.table_select.currentIndex()
        if idx < 0 or idx >= len(self.tables):
            return
        table = self.tables[idx]
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        rows = []
        trs = table.find_all('tr')
        for tr in trs[1:]:
            cells = tr.find_all(['td', 'th'])
            row = [cell.get_text(strip=True) for cell in cells]
            if row:
                rows.append(row)
        if headers and all(len(r) == len(headers) for r in rows):
            self.current_df = pd.DataFrame(rows, columns=headers)
        else:
            self.current_df = pd.DataFrame(rows)
        self.update_table_view()
        self.populate_role_controls()
        self.status_lbl.setText(f"Table {idx} loaded: {self.current_df.shape[0]} rows, {self.current_df.shape[1]} cols")

    def update_table_view(self, df=None):
        if df is None:
            df = self.current_df
        model = DataFrameModel(df)
        self.table_view.setModel(model)

    def populate_role_controls(self):
        cols = [str(c) for c in list(self.current_df.columns)]
        self.channel_combo.clear()
        self.param_combo.clear()
        self.stats_list.clear()
        if not cols:
            return
        for c in cols:
            self.channel_combo.addItem(c)
            self.param_combo.addItem(c)
        channel_col = self.channel_combo.currentText()
        param_col = self.param_combo.currentText()
        for c in cols:
            if c in (channel_col, param_col):
                continue
            item = QListWidgetItem(c)
            item.setFlags(cast(Any, item.flags() | ITEM_IS_USER_CHECKABLE))
            item.setCheckState(cast(Any, CHECKED))
            self.stats_list.addItem(item)
        self.populate_filter_lists()

    def populate_filter_lists(self):
        channel_col = self.channel_combo.currentText()
        param_col = self.param_combo.currentText()
        df = self.current_df
        self.channel_filter_list.clear()
        self.param_filter_list.clear()
        if channel_col in df.columns:
            for v in sorted(df[channel_col].dropna().unique()):
                item = QListWidgetItem(str(v))
                item.setFlags(cast(Any, item.flags() | ITEM_IS_USER_CHECKABLE))
                item.setCheckState(cast(Any, CHECKED))
                self.channel_filter_list.addItem(item)
        if param_col in df.columns:
            for v in sorted(df[param_col].dropna().unique()):
                item = QListWidgetItem(str(v))
                item.setFlags(cast(Any, item.flags() | ITEM_IS_USER_CHECKABLE))
                item.setCheckState(cast(Any, CHECKED))
                self.param_filter_list.addItem(item)

    def apply_filter(self):
        if self.current_df.empty:
            return
        channel_col = self.channel_combo.currentText()
        param_col = self.param_combo.currentText()
        stat_cols = []
        for i in range(self.stats_list.count()):
            it = self.stats_list.item(i)
            if it and it.checkState() == CHECKED:
                stat_cols.append(it.text())
        if not channel_col or not param_col:
            QMessageBox.information(self, "Info", "Select channel and parameter columns.")
            return
        channels = []
        for i in range(self.channel_filter_list.count()):
            it = self.channel_filter_list.item(i)
            if it and it.checkState() == CHECKED:
                channels.append(it.text())
        params = []
        for i in range(self.param_filter_list.count()):
            it = self.param_filter_list.item(i)
            if it and it.checkState() == CHECKED:
                params.append(it.text())
        df = self.current_df.copy()
        if channels:
            df = df[df[channel_col].isin(channels)]
        if params:
            df = df[df[param_col].isin(params)]
        if df.empty:
            QMessageBox.information(self, "No Data", "No data matches the selected filters.")
            return
        display_cols = [channel_col, param_col] + stat_cols
        display_cols = [c for c in display_cols if c in df.columns]
        filtered_df = df[display_cols]
        self.update_table_view(filtered_df)
        self.status_lbl.setText(f"Filtered: {filtered_df.shape[0]} rows")

    def export_csv(self):
        model = self.table_view.model()
        if model is None or model.rowCount() == 0:
            QMessageBox.information(self, "Export", "No data to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "filtered.csv", "CSV Files (*.csv)")
        if not path:
            return
        cols = [model.headerData(c, Qt.Horizontal) for c in range(model.columnCount())]  # type: ignore[attr-defined]
        rows = []
        for r in range(model.rowCount()):
            row = []
            for c in range(model.columnCount()):
                row.append(model.data(model.index(r, c), Qt.DisplayRole))  # type: ignore[attr-defined]
            rows.append(row)
        out_df = pd.DataFrame(rows, columns=cols)
        try:
            out_df.to_csv(path, index=False)
            QMessageBox.information(self, "Export", f"Saved to {path}")
        except (OSError, IOError, ValueError) as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = TableExtractorWindow()
    win.show()
    sys.exit(app.exec_())
