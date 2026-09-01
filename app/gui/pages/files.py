from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
from app.gui.themes import Theme
from app.core.jobs.manager import JobManager, Job, JobStatus


class FileImportWorker(QThread):
    finished = Signal(str)

    def __init__(self, job_mgr: JobManager, source: str, target: str):
        super().__init__()
        self.job_mgr = job_mgr
        self.source = source
        self.target = target

    def run(self):
        try:
            job = self.job_mgr.create('file_import', 'import')
            job.status = JobStatus.RUNNING
            import shutil
            from pathlib import Path
            src = Path(self.source)
            dst = Path(self.target)
            dst.mkdir(parents=True, exist_ok=True)
            files = [f for f in src.rglob('*') if f.is_file()]
            total = len(files)
            for i, f in enumerate(files):
                if job.is_cancelled():
                    job.status = JobStatus.CANCELLED
                    self.finished.emit('cancelled')
                    return
                rel = f.relative_to(src)
                dest = dst / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
                job.update_progress((i + 1) / total)
            job.status = JobStatus.COMPLETED
            self.finished.emit('success')
        except Exception as exc:
            job.status = JobStatus.FAILED
            self.finished.emit(f'error: {exc}')


class FilesPage(QWidget):
    page_name = 'files'

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state
        self.setObjectName('page')
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        header = QLabel('Files')
        header.setStyleSheet('font-size: 24px; font-weight: bold;')
        layout.addWidget(header)
        toolbar = QHBoxLayout()
        self.upload_btn = QPushButton('Upload')
        self.new_folder_btn = QPushButton('New Folder')
        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self._refresh)
        toolbar.addWidget(self.upload_btn)
        toolbar.addWidget(self.new_folder_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Name', 'Type', 'Size', 'Modified'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

    def _refresh(self):
        self.table.setRowCount(0)
        if not self.state or not self.state.is_initialized:
            return
        projects = self.state.projects.list_projects()
        for p in projects:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(p.name))
            self.table.setItem(row, 1, QTableWidgetItem(p.runtime))
            self.table.setItem(row, 2, QTableWidgetItem(str(p.port)))
            self.table.setItem(row, 3, QTableWidgetItem(p.status))
