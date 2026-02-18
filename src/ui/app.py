import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                             QFileDialog, QMessageBox, QGraphicsOpacityEffect,
                             QStackedWidget, QFrame, QGridLayout, QScrollArea,
                             QHBoxLayout, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QTimer
from PyQt6.QtGui import QFont, QColor

from models import Job
from ui.styles import STYLESHEET
from ui.widgets import NeonButton, LoadingSpinner
from ui.dialogs import JobDetailDialog
from ui.worker import JobSearchWorker


class CareerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.cv_path = ""
        self._animations = []
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("AI Powered Job Finder")
        self.setFixedSize(500, 750)
        self.setStyleSheet(STYLESHEET)

        self._stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self._stack)
        layout.setContentsMargins(0, 0, 0, 0)

        self._setup_input_page()
        self._setup_loading_page()
        self._setup_results_page()

    # ----- Pages -----

    def _setup_input_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 60, 40, 60)
        layout.setSpacing(20)

        title_top = QLabel("AI POWERED")
        title_top.setFont(QFont("Segoe UI", 14, QFont.Weight.Light))
        title_top.setStyleSheet("color: #bc13fe; letter-spacing: 5px;")

        title_main = QLabel("JOB\nFINDER")
        title_main.setFont(QFont("Segoe UI", 42, QFont.Weight.Bold))
        title_main.setStyleSheet("color: white; line-height: 0.9;")

        input_container = QWidget()
        input_container.setStyleSheet("background: rgba(255,255,255,0.03); border-radius: 20px;")
        ic_layout = QVBoxLayout(input_container)
        ic_layout.setContentsMargins(20, 30, 20, 30)

        self._job_input = QLineEdit()
        self._job_input.setPlaceholderText("Enter your Desired Job Title")

        self._upload_btn = QPushButton("\U0001f4ce UPLOAD CV")
        self._upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._upload_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 2px dashed #636e72;
                color: #b2bec3;
                border-radius: 12px;
                padding: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                border: 2px dashed #00f3ff;
                color: #00f3ff;
                background: rgba(0, 243, 255, 0.05);
            }
        """)
        self._upload_btn.clicked.connect(self._open_file_dialog)

        ic_layout.addWidget(self._job_input)
        ic_layout.addWidget(self._upload_btn)

        submit_btn = NeonButton("FIND BEST JOBS")
        submit_btn.clicked.connect(self._submit)

        layout.addWidget(title_top)
        layout.addWidget(title_main)
        layout.addSpacing(20)
        layout.addWidget(input_container)
        layout.addStretch()
        layout.addWidget(submit_btn)

        self._stack.addWidget(page)

    def _setup_loading_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(30)

        spinner = LoadingSpinner()

        self._load_text = QLabel("ANALYZING YOUR CV...")
        self._load_text.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._load_text.setStyleSheet("color: #00f3ff; letter-spacing: 2px;")
        self._load_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("RANKING JOBS BY SIMILARITY...")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #636e72;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        center = QHBoxLayout()
        center.addStretch()
        center.addWidget(spinner)
        center.addStretch()
        layout.addLayout(center)
        layout.addWidget(self._load_text)
        layout.addWidget(sub)
        layout.addStretch()

        self._stack.addWidget(page)

    def _setup_results_page(self):
        page = QWidget()
        res_layout = QVBoxLayout(page)
        res_layout.setContentsMargins(30, 50, 30, 30)

        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("BEST JOB MATCHES")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: white; border-bottom: 3px solid #bc13fe;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        self._grid_container = QWidget()
        self._grid = QGridLayout(self._grid_container)
        self._grid.setSpacing(20)
        self._grid.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(self._grid_container)

        back_btn = QPushButton("SEARCH AGAIN")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("color: #636e72; background: transparent; border: none; font-weight: bold;")
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))

        res_layout.addWidget(header)
        res_layout.addWidget(scroll)
        res_layout.addWidget(back_btn)

        self._stack.addWidget(page)

    # ----- Slots -----

    def _open_file_dialog(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select CV", "", "PDF (*.pdf)")
        if fname:
            self.cv_path = fname
            self._upload_btn.setText(f"\u2705 {os.path.basename(fname)} ATTACHED")
            self._upload_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 243, 255, 0.1);
                    border: 2px solid #00f3ff;
                    color: #00f3ff;
                    border-radius: 12px;
                    padding: 15px;
                    font-weight: bold;
                }
            """)

    def _submit(self):
        if not self._job_input.text() or not self.cv_path:
            QMessageBox.warning(self, "Input Error", "Data Incomplete. Please provide Job Title and CV.")
            return

        self._stack.setCurrentIndex(1)
        self._load_text.setText("ANALYZING YOUR CV...")

        self._worker = JobSearchWorker(self._job_input.text(), self.cv_path)
        self._worker.finished.connect(self._display_results)
        self._worker.error.connect(self._handle_error)
        self._worker.start()

    def _handle_error(self, message: str):
        self._stack.setCurrentIndex(0)
        QMessageBox.critical(self, "Error", f"Search failed:\n{message}")

    def _display_results(self, results):
        while self._grid.count():
            child = self._grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not results:
            lbl = QLabel("No matches found. Try recalibrating.")
            lbl.setStyleSheet("color: #636e72; font-size: 16px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid.addWidget(lbl, 0, 0)
        else:
            self._animations.clear()
            for i, (job, score) in enumerate(results):
                card = self._create_job_card(job, score)
                card.setVisible(False)
                self._grid.addWidget(card, i // 2, i % 2)

                effect = QGraphicsOpacityEffect(card)
                card.setGraphicsEffect(effect)

                anim = QPropertyAnimation(effect, b"opacity", self)
                anim.setDuration(500)
                anim.setStartValue(0)
                anim.setEndValue(1)
                self._animations.append(anim)

                QTimer.singleShot(
                    i * 150,
                    lambda c=card, a=anim: self._start_card_anim(c, a),
                )

        self._stack.setCurrentIndex(2)

    @staticmethod
    def _start_card_anim(card, anim):
        card.setVisible(True)
        anim.start()

    def _create_job_card(self, job: Job, score: float = 0.0) -> QFrame:
        card = QFrame()
        card.setFixedSize(200, 200)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet("""
            QFrame {
                background-color: #151923;
                border: 1px solid #2d3436;
                border-radius: 16px;
            }
            QFrame:hover {
                background-color: #1a1e29;
                border: 1px solid #00f3ff;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        t = QLabel(job.title)
        t.setWordWrap(True)
        t.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        t.setStyleSheet("color: white; border: none; background: transparent;")

        c = QLabel(job.company)
        c.setStyleSheet("color: #bc13fe; font-size: 11px; border: none; background: transparent;")

        loc = QLabel(job.city)
        loc.setStyleSheet("color: #636e72; font-size: 10px; border: none; background: transparent;")

        score_lbl = QLabel(f"Match: {score:.1f}%")
        score_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        score_lbl.setStyleSheet("color: #00f3ff; border: none; background: transparent;")

        layout.addWidget(t)
        layout.addWidget(c)
        layout.addWidget(loc)
        layout.addStretch()
        layout.addWidget(score_lbl)

        card.mousePressEvent = lambda e: self._show_details(job)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)

        return card

    def _show_details(self, job: Job):
        dialog = JobDetailDialog(job, self)
        dialog.exec()
