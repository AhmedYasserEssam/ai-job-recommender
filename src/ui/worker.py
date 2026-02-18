import traceback

from PyQt6.QtCore import QThread, pyqtSignal

from cv_parser import extract_cv_data
from scraper import scrape_jobs
from similarity import rank_jobs


class JobSearchWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, job_title: str, cv_path: str):
        super().__init__()
        self.job_title = job_title
        self.cv_path = cv_path

    def run(self):
        try:
            jobs = scrape_jobs(self.job_title, page_limit=2)
            if not jobs:
                self.error.emit("No job listings found. Try a different search term.")
                return

            cv_data = extract_cv_data(self.cv_path)
            ranked = rank_jobs(jobs, cv_data, top_k=4)
            unique = list(
                {job.link: (job, score) for job, score in ranked if job.link != "N/A"}.values()
            )
            self.finished.emit(unique)
        except Exception as e:
            traceback.print_exc()
            self.error.emit(str(e))
