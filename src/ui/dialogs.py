import webbrowser

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models import Job
from ui.widgets import NeonButton


class JobDetailDialog(QDialog):
    def __init__(self, job: Job, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Job details")
        self.setFixedSize(450, 550)
        self.setStyleSheet("""
            QDialog { background-color: #0b0e14; border: 2px solid #bc13fe; border-radius: 10px; }
            QLabel { color: #ecf0f1; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel(job.title)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #00f3ff;")
        title.setWordWrap(True)

        company = QLabel(f"\U0001f3e2 {job.company} | \U0001f4cd {job.city}, {job.country}")
        company.setStyleSheet("color: #bc13fe; font-size: 14px; font-weight: bold;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)

        skills_text = ", ".join(job.skills) if job.skills else "Not specified"
        body = QLabel(f"""
        <style>b {{ color: #00f3ff; }}</style>
        <p style="line-height: 1.6; font-size: 14px;">
        <b>Type:</b> {job.job_type}<br>
        <b>Salary:</b> {job.salary}<br>
        <b>Experience:</b> {job.experience_needed} years<br>
        <b>Level:</b> {job.career_level}<br><br>
        <b>Skills Detected:</b><br>{skills_text}<br><br>
        <b>System Requirements:</b><br>{job.requirements}
        </p>
        """)
        body.setWordWrap(True)
        body.setTextFormat(Qt.TextFormat.RichText)
        info_layout.addWidget(body)
        scroll.setWidget(info_widget)

        apply_btn = NeonButton("APPLY NOW", "#bc13fe", "#00f3ff")
        apply_btn.clicked.connect(lambda: webbrowser.open(job.link))

        layout.addWidget(title)
        layout.addWidget(company)
        layout.addWidget(scroll)
        layout.addWidget(apply_btn)
