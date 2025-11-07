#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABB UI Replica (PySide6)
- Orange vertical action bar (right)
- Header strip with branding/time/mode
- Stacked pages: Status, Model Tray Config, Material I/O Search, Tray Partition, Call Tray History
- System tray with the same "Model Tray Configuration" default action for now
- No console logs (except critical errors)
"""
import math
import sys

from PySide6.QtCore import QDateTime, QPointF, QRectF, Qt, QTimer, QSize
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QStyle,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

ORANGE = "#ea6a1f"  # close to screenshot
ORANGE_DARK = "#d85f1c"
GRAY_BG = "#f3f4f6"
LIGHT = "#ffffff"
DARK = "#1f2937"
GREEN = "#2ea043"
RED = "#e11d48"

ICON_DIAMETER = 58
STATUS_PILL_TEXT = "98% Machine Slots Utilized"


def _draw_icon(draw_fn, size=64, *, pen_color=LIGHT, pen_width=4, padding=10):
    """Render a stroked icon with the supplied painter callback."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    rect = QRectF(padding, padding, size - padding * 2, size - padding * 2)
    painter.setPen(QPen(QColor(pen_color), pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    draw_fn(painter, rect)
    painter.end()
    return QIcon(pm)


def _draw_user(painter, rect):
    center = rect.center()
    head_radius = rect.width() * 0.24
    painter.drawEllipse(QPointF(center.x(), rect.top() + head_radius + 2), head_radius, head_radius)
    body_rect = QRectF(
        center.x() - rect.width() * 0.32,
        rect.top() + rect.height() * 0.45,
        rect.width() * 0.64,
        rect.height() * 0.40,
    )
    path = QPainterPath()
    path.addRoundedRect(body_rect, body_rect.height() / 2, body_rect.height() / 2)
    painter.drawPath(path)


def _draw_home(painter, rect):
    roof_height = rect.height() * 0.42
    path = QPainterPath()
    path.moveTo(rect.center().x(), rect.top())
    path.lineTo(rect.left() + rect.width() * 0.08, rect.top() + roof_height)
    path.lineTo(rect.left() + rect.width() * 0.08, rect.bottom())
    path.lineTo(rect.right() - rect.width() * 0.08, rect.bottom())
    path.lineTo(rect.right() - rect.width() * 0.08, rect.top() + roof_height)
    path.closeSubpath()
    painter.drawPath(path)
    door_rect = QRectF(
        rect.center().x() - rect.width() * 0.12,
        rect.bottom() - rect.height() * 0.28,
        rect.width() * 0.24,
        rect.height() * 0.28,
    )
    painter.drawRoundedRect(door_rect, 6, 6)


def _draw_fetch(painter, rect):
    top = rect.top() + rect.height() * 0.15
    mid = rect.center().y()
    painter.drawLine(QPointF(rect.center().x(), top), QPointF(rect.center().x(), mid))
    painter.drawLine(
        QPointF(rect.center().x(), mid),
        QPointF(rect.center().x() - rect.width() * 0.1, mid - rect.height() * 0.1),
    )
    painter.drawLine(
        QPointF(rect.center().x(), mid),
        QPointF(rect.center().x() + rect.width() * 0.1, mid - rect.height() * 0.1),
    )
    tray_rect = QRectF(
        rect.left() + rect.width() * 0.18,
        rect.bottom() - rect.height() * 0.30,
        rect.width() * 0.64,
        rect.height() * 0.22,
    )
    painter.drawRoundedRect(tray_rect, 6, 6)


def _draw_storage(painter, rect):
    cols = 2
    rows = 3
    cell_w = rect.width() * 0.42
    cell_h = rect.height() * 0.26
    start_x = rect.left() + rect.width() * 0.04
    start_y = rect.top() + rect.height() * 0.06
    gap_x = rect.width() * 0.06
    gap_y = rect.height() * 0.07
    for r in range(rows):
        for c in range(cols):
            painter.drawRoundedRect(
                QRectF(
                    start_x + c * (cell_w + gap_x),
                    start_y + r * (cell_h + gap_y),
                    cell_w,
                    cell_h,
                ),
                6,
                6,
            )


def _draw_settings(painter, rect):
    center = rect.center()
    outer = rect.width() * 0.32
    inner = rect.width() * 0.14
    for i in range(6):
        angle = math.radians(60 * i)
        start = QPointF(
            center.x() + math.cos(angle) * (outer - 2),
            center.y() + math.sin(angle) * (outer - 2),
        )
        end = QPointF(
            center.x() + math.cos(angle) * (outer + 8),
            center.y() + math.sin(angle) * (outer + 8),
        )
        painter.drawLine(start, end)
    painter.drawEllipse(center, outer, outer)
    painter.drawEllipse(center, inner, inner)


def _draw_monitor(painter, rect):
    screen = QRectF(
        rect.left() + rect.width() * 0.08,
        rect.top() + rect.height() * 0.20,
        rect.width() * 0.84,
        rect.height() * 0.42,
    )
    painter.drawRoundedRect(screen, 6, 6)
    stem_top = screen.bottom() + rect.height() * 0.08
    painter.drawLine(
        QPointF(rect.center().x(), screen.bottom()),
        QPointF(rect.center().x(), stem_top),
    )
    base = QRectF(
        rect.center().x() - rect.width() * 0.22,
        stem_top,
        rect.width() * 0.44,
        rect.height() * 0.16,
    )
    painter.drawRoundedRect(base, 6, 6)


def _draw_power(painter, rect):
    center = rect.center()
    radius = rect.width() * 0.34
    painter.drawArc(
        QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2),
        45 * 16,
        270 * 16,
    )
    painter.drawLine(
        QPointF(center.x(), rect.top() + rect.height() * 0.05),
        QPointF(center.x(), center.y()),
    )


def icon_user():
    return _draw_icon(_draw_user)


def icon_home():
    return _draw_icon(_draw_home)


def icon_fetch():
    return _draw_icon(_draw_fetch)


def icon_storage():
    return _draw_icon(_draw_storage)


def icon_settings():
    return _draw_icon(_draw_settings)


def icon_monitor():
    return _draw_icon(_draw_monitor)


def icon_power():
    return _draw_icon(_draw_power)


def orange_button(text):
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setProperty("accent", True)
    b.setMinimumWidth(120)
    b.setFixedHeight(44)
    return b


def gray_button(text):
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setMinimumWidth(120)
    b.setFixedHeight(44)
    return b


def tile_button(text, color):
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setObjectName("HomeTile")
    b.setStyleSheet(
        f"QPushButton#HomeTile {{ background:{color}; color:white; border:none; border-radius:14px; padding:18px 16px; font-weight:600; font-size:14px; }}"
    )
    b.setMinimumSize(50, 90)
    return b


def label(text, bold=False, size=12, color=DARK):
    l = QLabel(text)
    f = QFont("Segoe UI")
    f.setPointSize(size)
    f.setBold(bold)
    l.setFont(f)
    l.setStyleSheet(f"color:{color};")
    return l


class Header(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Header")
        self.setFixedHeight(96)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(28, 14, 28, 14)
        hl.setSpacing(20)

        logos_widget = QWidget()
        logos_layout = QHBoxLayout(logos_widget)
        logos_layout.setContentsMargins(0, 0, 0, 0)
        logos_layout.setSpacing(18)
        
        hl.addWidget(logos_widget, 0, Qt.AlignVCenter)

        info_widget = QWidget()
        info_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(12)

        self.statusText = self._info_label("", 15)
        self.statusText.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        info_layout.addWidget(self.statusText, 0, Qt.AlignLeft)
        hl.addWidget(info_widget, 0, Qt.AlignLeft)
        hl.addStretch(1)

        self.setStyleSheet(f"""
        #Header {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ORANGE}, stop:1 {ORANGE_DARK});
            border-bottom: 2px solid {ORANGE_DARK};
        }}
        #Header QLabel {{
            color: {LIGHT};
        }}
        """)

        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)
        self._tick()

    def _divider(self):
        d = QFrame()
        d.setFrameShape(QFrame.VLine)
        d.setFrameShadow(QFrame.Plain)
        d.setLineWidth(1)
        d.setStyleSheet("color: rgba(255, 255, 255, 0.4);")
        return d

    def _logo_label(self, text, size, weight, italic=False):
        lbl = QLabel(text)
        font = QFont("Segoe UI")
        font.setPointSize(size)
        font.setWeight(weight)
        font.setItalic(italic)
        font.setBold(weight >= QFont.Weight.Bold)
        lbl.setFont(font)
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        return lbl

    def _info_label(self, text, size, bold=False):
        lbl = QLabel(text)
        font = QFont("Segoe UI")
        font.setPointSize(size)
        font.setBold(bold)
        lbl.setFont(font)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return lbl

    def _tick(self):
        timestamp = QDateTime.currentDateTime().toString("dd/MM/yyyy hh:mm:ss")
        self.statusText.setText(f"HI service    Mode: Auto    {timestamp}")


class TopActionBar(QFrame):
    def __init__(self, on_nav):
        super().__init__()
        self.setObjectName("TopBar")
        self.setFixedHeight(112)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(28, 10, 28, 10)
        hl.setSpacing(18)

        self.btnAlarm = self._icon_button(icon_monitor(), "Alarm History")
        self.btnUser = self._icon_button(icon_user(), "User")
        self.btnHome = self._icon_button(icon_home(), "Home")
        self.btnFetch = self._icon_button(icon_fetch(), "Fetch Tray")
        self.btnStorage = self._icon_button(icon_storage(), "Tray Overview")
        self.btnSettings = self._icon_button(icon_settings(), "Settings")

        for btn in [self.btnAlarm, self.btnUser, self.btnHome, self.btnFetch, self.btnStorage, self.btnSettings]:
            hl.addWidget(btn)

        hl.addStretch(1)

        indicator_widget = QWidget()
        indicator_widget.setObjectName("IndicatorWidget")
        indicator_layout = QHBoxLayout(indicator_widget)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        indicator_layout.setSpacing(6)
        for text in ["1", "2"]:
            lbl = QLabel(text)
            lbl.setObjectName("IndicatorChip")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedSize(32, 22)
            indicator_layout.addWidget(lbl)
        hl.addWidget(indicator_widget)

        self.statusPill = QLabel(STATUS_PILL_TEXT)
        self.statusPill.setObjectName("StatusPill")
        self.statusPill.setAlignment(Qt.AlignCenter)
        self.statusPill.setFixedHeight(40)
        hl.addWidget(self.statusPill)

        self.btnPower = self._icon_button(icon_power(), "Power")
        hl.addWidget(self.btnPower)

        self.btnUser.clicked.connect(lambda: on_nav(0))
        self.btnHome.clicked.connect(lambda: on_nav(0))
        self.btnFetch.clicked.connect(lambda: on_nav(1))
        self.btnStorage.clicked.connect(lambda: on_nav(2))
        self.btnSettings.clicked.connect(lambda: on_nav(3))
        self.btnAlarm.clicked.connect(lambda: on_nav(4))
        self.btnPower.clicked.connect(lambda: QApplication.instance().quit() if QApplication.instance() else None)

        self.setStyleSheet(f"""
        #TopBar {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ORANGE}, stop:1 {ORANGE_DARK});
            border-bottom: 2px solid {ORANGE_DARK};
        }}
        #TopBar QToolButton {{
            border: none;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.18);
            padding: 10px;
        }}
        #TopBar QToolButton::hover {{
            background: rgba(255, 255, 255, 0.32);
        }}
        #TopBar QLabel#StatusPill {{
            background: rgba(255, 255, 255, 0.92);
            color: {ORANGE_DARK};
            border-radius: 18px;
            font-weight: 600;
            padding: 10px 18px;
        }}
        #TopBar QLabel#IndicatorChip {{
            background: #25b66a;
            color: white;
            border-radius: 6px;
            font-weight: 600;
        }}
        """)

    def _icon_button(self, icon, tooltip):
        btn = QToolButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIcon(icon)
        btn.setIconSize(QSize(54, 54))
        btn.setFixedSize(72, 72)
        btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        btn.setAutoRaise(False)
        btn.setToolTip(tooltip)
        return btn


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 12, 24, 18)
        root.setSpacing(10)

        status_strip = QLabel("M002 - FUNCTION DONE")
        status_strip.setAlignment(Qt.AlignCenter)
        status_strip.setObjectName("HomeStatusBanner")
        status_strip.setFixedHeight(24)
        root.addWidget(status_strip)

        form_box = QFrame()
        form_box.setObjectName("HomeForm")
        form_layout = QGridLayout(form_box)
        form_layout.setContentsMargins(18, 10, 18, 12)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(10)

        tray_col = QVBoxLayout()
        tray_col.setSpacing(4)
        tray_col.addWidget(label("Tray Number", bold=True, size=13))
        tray_input_row = QHBoxLayout()
        tray_input_row.setSpacing(6)
        self.trayNumber = QSpinBox()
        self.trayNumber.setRange(0, 9999)
        self.trayNumber.setValue(55)
        self.trayNumber.setFixedHeight(36)
        self.trayNumber.setButtonSymbols(QSpinBox.NoButtons)
        self.trayNumber.setObjectName("TrayNumberInput")
        tray_input_row.addWidget(self.trayNumber, 1)
        help_btn = QPushButton("?")
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.setFixedSize(28, 28)
        help_btn.setObjectName("HelpButton")
        tray_input_row.addWidget(help_btn)
        tray_col.addLayout(tray_input_row)
        form_layout.addLayout(tray_col, 0, 0)

        self.fetchButton = orange_button("Fetch Tray")
        self.fetchButton.setIcon(icon_fetch())
        self.fetchButton.setIconSize(QSize(24, 24))
        self.fetchButton.setFixedSize(118, 60)
        form_layout.addWidget(self.fetchButton, 0, 1, Qt.AlignTop)

        child_col = QVBoxLayout()
        child_col.setSpacing(4)
        child_col.addWidget(label("Child Part", bold=True, size=13))
        self.childPart = QLineEdit()
        self.childPart.setFixedHeight(36)
        child_col.addWidget(self.childPart)
        child_col.addWidget(label("Model", bold=True, size=13))
        self.modelInput = QLineEdit()
        self.modelInput.setFixedHeight(36)
        child_col.addWidget(self.modelInput)
        form_layout.addLayout(child_col, 0, 2)

        self.searchButton = orange_button("Search")
        self.searchButton.setFixedSize(106, 60)
        form_layout.addWidget(self.searchButton, 0, 3, Qt.AlignTop)

        shortcut_row = QHBoxLayout()
        shortcut_row.setSpacing(10)
        self.masterData = orange_button("Master Data")
        self.masterData.setFixedSize(116, 46)
        self.sampleFormat = orange_button("Sample Format")
        self.sampleFormat.setFixedSize(116, 46)
        shortcut_row.addWidget(self.masterData)
        shortcut_row.addWidget(self.sampleFormat)
        shortcut_row.addStretch(1)
        form_layout.addLayout(shortcut_row, 1, 0, 1, 4)

        root.addWidget(form_box)

        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(14)
        self.tiles = {}
        tiles = [
            ("Tray Data", "#d16436"),
            ("Inventory List", "#3b7bdc"),
            ("Material Tracking", "#d6688f"),
            ("Available Space", "#2db16b"),
            ("Call Tray Details", "#1aa196"),
            ("Machine Status", "#a58a3a"),
            ("Tray Configuration", "#d8a540"),
            ("Tray Partition", "#1a3f8f"),
        ]
        for text, color in tiles:
            btn = tile_button(text, color)
            self.tiles[text] = btn
            tiles_row.addWidget(btn)
        tiles_row.addStretch(1)
        root.addLayout(tiles_row)


class MachineStatusPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)
        layout.addWidget(label("Machine Status", bold=True, size=16))

        legend = QHBoxLayout()
        on_lbl = label("ON", bold=True, color=LIGHT)
        off_lbl = label("OFF", bold=True, color=LIGHT)
        on_chip = QFrame(); on_chip.setStyleSheet(f"background:{GREEN}; border-radius:6px;"); on_chip.setFixedSize(48,18)
        off_chip = QFrame(); off_chip.setStyleSheet(f"background:{RED}; border-radius:6px;"); off_chip.setFixedSize(48,18)
        legend.addWidget(on_chip); legend.addWidget(on_lbl); legend.addSpacing(16)
        legend.addWidget(off_chip); legend.addWidget(off_lbl); legend.addStretch(1)
        legw = QFrame(); ll = QHBoxLayout(legw); ll.addLayout(legend)
        layout.addWidget(legw)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14); grid.setVerticalSpacing(10)

        def status_group(title, rows):
            g = QGroupBox(title)
            g.setStyleSheet("QGroupBox{font-weight:600;}")
            v = QVBoxLayout(g)
            lst = QListWidget()
            for r in rows:
                it = QListWidgetItem(r)
                it.setBackground(QBrush(QColor(GREEN)))
                it.setForeground(QBrush(Qt.white))
                lst.addItem(it)
            lst.setFrameShape(QFrame.NoFrame)
            lst.setSpacing(4)
            v.addWidget(lst)
            return g

        grid.addWidget(status_group("Machine Info", ["Number of Cycle: 68212",
                                                     "Lift Motor Running Time: 167h",
                                                     "Door Motor Running Time: 14h"]), 0,0)
        grid.addWidget(status_group("Front Tray Guide", ["Front Tray Sensor: 1/0",
                                                         "Door Open Sensor: 0/1"]), 0,1)
        grid.addWidget(status_group("Rear Tray Guide", ["Rear Tray Sensor: 1/1"]), 0,2)
        grid.addWidget(status_group("Input Status", ["Shelf Center Sensor 1.0",
                                                     "Tray IN PN Sensor 1.8"]), 1,0)
        grid.addWidget(status_group("Output Status", ["Safety Light Output: 1.0",
                                                      "Tray OUT Cylinder: 1.5"]), 1,1)
        grid.addWidget(status_group("Running Status", ["UFR: READY", "EMO: RELEASED"]), 1,2)

        gridw = QWidget(); gridw.setLayout(grid)
        layout.addWidget(gridw, 1)


class ModelTrayConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(32, 24, 32, 24)
        v.setSpacing(20)
        v.addWidget(label("Model Tray Configuration", bold=True, size=16))

        filters = QHBoxLayout()
        filters.setSpacing(12)
        self.txtModel = QLineEdit(); self.txtModel.setPlaceholderText("Model")
        self.spinRows = QSpinBox(); self.spinRows.setRange(1, 99); self.spinRows.setPrefix("Rows: ")
        self.spinCols = QSpinBox(); self.spinCols.setRange(1, 99); self.spinCols.setPrefix("Cols: ")
        btnSearch = orange_button("Search")
        btnClear = gray_button("Clear")
        for w in [self.txtModel, self.spinRows, self.spinCols, btnSearch, btnClear]:
            filters.addWidget(w)
        filters.addStretch(1)
        v.addLayout(filters)

        self.table = QTableWidget(6, 8)
        self.table.setHorizontalHeaderLabels([
            "Site", "Tray No", "Model", "Row Number", "Column No", "Update", "Delete", "⭳"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setFixedHeight(46)
        self.table.verticalHeader().setDefaultSectionSize(44)
        for r in range(self.table.rowCount()):
            self.table.setItem(r, 0, QTableWidgetItem(str(r+1)))
            self.table.setItem(r, 1, QTableWidgetItem(str(100+r)))
            self.table.setItem(r, 2, QTableWidgetItem("XT2_39_BB"))
            self.table.setItem(r, 3, QTableWidgetItem("5"))
            self.table.setItem(r, 4, QTableWidgetItem("24"))
            u = orange_button("Update")
            d = gray_button("Del")
            e = gray_button("View")
            self.table.setCellWidget(r, 5, u)
            self.table.setCellWidget(r, 6, d)
            self.table.setCellWidget(r, 7, e)

        v.addWidget(self.table, 1)

        footer = QHBoxLayout()
        btnExport = orange_button("Export")
        btnDown = gray_button("Down")
        btnUp = gray_button("Up")
        btnNew = orange_button("New")
        btnBack = orange_button("Back")
        for b in [btnExport, btnDown, btnUp, btnNew, btnBack]:
            footer.addWidget(b)
        footer.addStretch(1)
        v.addLayout(footer)


class MaterialIOSearchPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(32, 24, 32, 24)
        v.setSpacing(20)
        v.addWidget(label("Material In & Out Search", bold=True, size=16))
        row = QHBoxLayout()
        row.setSpacing(12)
        for t in ["Child Part", "Period", "AP", "Tray No", "Type", "Part/Code"]:
            row.addWidget(QLineEdit(placeholderText=t))
        row.addWidget(orange_button("Search"))
        row.addWidget(gray_button("Clear"))
        v.addLayout(row)

        tbl = QTableWidget(8, 8)
        tbl.setHorizontalHeaderLabels(["S No", "Date", "Time", "Tray No", "Child Part",
                                       "Product Code", "Serial No", "Qty"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.horizontalHeader().setFixedHeight(46)
        tbl.verticalHeader().setDefaultSectionSize(44)
        for r in range(8):
            for c in range(8):
                tbl.setItem(r, c, QTableWidgetItem("-"))
        v.addWidget(tbl, 1)

        footer = QHBoxLayout()
        footer.addWidget(orange_button("Export"))
        footer.addStretch(1)
        footer.addWidget(gray_button("Down"))
        footer.addWidget(gray_button("Up"))
        v.addLayout(footer)


class TrayPartitionPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(32, 24, 32, 24)
        v.setSpacing(20)
        v.addWidget(label("Tray Partition", bold=True, size=16))
        form = QFormLayout()
        form.setHorizontalSpacing(28)
        form.setVerticalSpacing(16)
        self.editModel = QLineEdit()
        self.fromTray = QSpinBox(); self.fromTray.setRange(0, 9999)
        self.toTray = QSpinBox(); self.toTray.setRange(0, 9999)
        self.rows = QSpinBox(); self.rows.setRange(1, 50)
        self.cols = QSpinBox(); self.cols.setRange(1, 50)
        form.addRow("Model", self.editModel)
        form.addRow("From TrayNo", self.fromTray)
        form.addRow("To TrayNo", self.toTray)
        form.addRow("Rows", self.rows)
        form.addRow("Columns", self.cols)
        w = QWidget(); w.setLayout(form)
        v.addWidget(w)

        actions = QHBoxLayout()
        actions.addWidget(orange_button("Apply"))
        actions.addWidget(gray_button("Clear"))
        actions.addStretch(1)
        actions.addWidget(orange_button("Create Partition"))
        actions.addWidget(gray_button("Delete Partition"))
        actions.addWidget(gray_button("Existing Partition"))
        v.addLayout(actions)


class CallTrayHistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(32, 24, 32, 24)
        v.setSpacing(20)
        v.addWidget(label("Call Tray History", bold=True, size=16))
        filt = QHBoxLayout()
        filt.setSpacing(12)
        for t in ["S No", "Period", "AP", "Tray No", "Type"]:
            filt.addWidget(QLineEdit(placeholderText=t))
        filt.addWidget(orange_button("Search"))
        filt.addWidget(gray_button("Clear"))
        v.addLayout(filt)

        tbl = QTableWidget(7, 8)
        tbl.setHorizontalHeaderLabels(["S No", "Date", "Time", "Tray No", "Slots", "Storage Side", "User", "Access Point"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.horizontalHeader().setFixedHeight(46)
        tbl.verticalHeader().setDefaultSectionSize(44)
        for r in range(7):
            for c in range(8):
                tbl.setItem(r, c, QTableWidgetItem(""))
        v.addWidget(tbl, 1)

        foot = QHBoxLayout()
        foot.addWidget(orange_button("Export"))
        foot.addStretch(1)
        foot.addWidget(gray_button("Down"))
        foot.addWidget(gray_button("Up"))
        v.addLayout(foot)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ABB • VSTORE Replica")
        self.setMinimumSize(1280, 800)
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        self.header = Header()
        root.addWidget(self.header, 0)

        self.topBar = TopActionBar(self._navigate_to)
        root.addWidget(self.topBar, 0)

        self.pages = QStackedWidget()
        self.pages.setObjectName("PageStack")
        self.homePage = HomePage()
        self.modelPage = ModelTrayConfigPage()
        self.ioPage = MaterialIOSearchPage()
        self.partitionPage = TrayPartitionPage()
        self.historyPage = CallTrayHistoryPage()
        self.statusPage = MachineStatusPage()
        self.pages.addWidget(self.homePage)        # 0
        self.pages.addWidget(self.modelPage)       # 1
        self.pages.addWidget(self.ioPage)          # 2
        self.pages.addWidget(self.partitionPage)   # 3
        self.pages.addWidget(self.historyPage)     # 4
        self.pages.addWidget(self.statusPage)      # 5

        contentFrame = QFrame()
        contentFrame.setObjectName("ContentFrame")
        contentLayout = QVBoxLayout(contentFrame)
        contentLayout.setContentsMargins(24, 18, 24, 24)
        contentLayout.addWidget(self.pages)

        root.addWidget(contentFrame, 1)

        self._wire_home_tiles()
        self._navigate_to(0)

        self.setStyleSheet(f"""
        QWidget {{
            background: {GRAY_BG};
            color: {DARK};
            font-family: 'Segoe UI', 'Noto Sans', 'Ubuntu', Arial;
            font-size: 12px;
        }}
        #LeftLegend {{
            background: #e7e9ec;
            border-radius: 6px;
        }}
        #ContentFrame {{
            background: {LIGHT};
            border: 1px solid #e5e7eb;
            border-radius: 18px;
        }}
        #HomeCard {{
            background: #f7f8fb;
            border: 1px solid #e4e7ec;
            border-radius: 18px;
        }}
        #HomeStatusBanner {{
            background: #fbe8d9;
            color: {ORANGE_DARK};
            border-radius: 12px;
            font-weight: 600;
            letter-spacing: 0.6px;
        }}
        QPushButton#HelpButton {{
            background: #f1f1f1;
            border: 1px solid #d1d5db;
            border-radius: 18px;
            font-weight: 700;
            color: {ORANGE_DARK};
        }}
        QPushButton#HelpButton:hover {{
            background: #e6e7ea;
        }}
        QSpinBox#TrayNumberInput {{
            background: #edf5ff;
            border: 1px solid #9cbcf5;
            border-radius: 10px;
            padding: 6px 12px;
            font-weight: 600;
            color: #1d4ed8;
        }}
        #PageStack {{
            background: transparent;
        }}
        QTableWidget {{
            background: {LIGHT};
            border: 1px solid #e5e7eb;
            gridline-color: #e5e7eb;
            selection-background-color: {ORANGE};
            selection-color: white;
            border-radius: 12px;
        }}
        QHeaderView::section {{
            background: #f5f6f8;
            color: {DARK};
            border: 1px solid #dcdfe3;
            padding: 10px 8px;
            font-weight: 600;
        }}
        QPushButton {{
            background: #e5e7eb;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 8px 12px;
        }}
        QPushButton:hover {{ background: #e9ecef; }}
        QPushButton[accent="true"] {{
            background: {ORANGE};
            border-color: {ORANGE_DARK};
            color: {LIGHT};
            font-weight: 600;
        }}
        QPushButton[accent="true"]:hover {{
            background: {ORANGE_DARK};
        }}
        QLineEdit, QSpinBox, QComboBox {{
            background: {LIGHT};
            border: 1px solid #d1d5db;
            border-radius: 6px;
            padding: 6px 8px;
        }}
        QGroupBox {{
            background: {LIGHT};
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            margin-top: 12px;
            padding: 8px;
        }}
        QListWidget {{
            background: transparent;
            border: none;
        }}
        QListWidget::item {{
            margin: 4px 0;
            padding: 6px 8px;
            border-radius: 6px;
        }}
        """)

        self._setup_tray()

    def _wire_home_tiles(self):
        if not hasattr(self, "homePage"):
            return
        mapping = {
            "Tray Configuration": 1,
            "Available Space": 2,
            "Tray Partition": 3,
            "Call Tray Details": 4,
            "Machine Status": 5,
        }
        for title, index in mapping.items():
            btn = self.homePage.tiles.get(title)
            if btn:
                btn.clicked.connect(lambda _, i=index: self._navigate_to(i))

    def _navigate_to(self, index: int):
        if 0 <= index < self.pages.count():
            self.pages.setCurrentIndex(index)

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        if icon.isNull():
            icon = QIcon.fromTheme('computer')
        if icon.isNull():
            pm = QPixmap(32,32); pm.fill(Qt.darkGray); icon = QIcon(pm)
        self.tray.setIcon(icon)

        self.tray.setToolTip("ABB • VSTORE")

        menu = QMenu()

        act_show = QAction("Show Window", self, triggered=self.showNormal)
        act_hide = QAction("Hide Window", self, triggered=self.hide)
        act_quit = QAction("Quit", self, triggered=QApplication.instance().quit)

        act_traycfg = QAction("Model Tray Configuration", self, triggered=lambda: self.pages.setCurrentIndex(1))

        nav = QMenu("Navigate", menu)

        def add_nav(title, idx):
            action = QAction(title, self, triggered=lambda i=idx: self.pages.setCurrentIndex(i))
            nav.addAction(action)

        add_nav("Status", 0)
        add_nav("Model Tray Config", 1)
        add_nav("Material I/O Search", 2)
        add_nav("Tray Partition", 3)
        add_nav("Call Tray History", 4)

        menu.addAction(act_traycfg)
        menu.addMenu(nav)
        menu.addSeparator()
        menu.addAction(act_show)
        menu.addAction(act_hide)
        menu.addSeparator()
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.show()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
