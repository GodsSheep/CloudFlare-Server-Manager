from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QProgressBar, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QThread
import os
from app.gui.themes import Theme
from app.core.state.machine import ProjectState
from app.core.jobs.manager import JobManager, Job, JobStatus


class ImportWorker(QThread):
    finished = Signal(str, str, str)

    def __init__(self, job_mgr: JobManager, name: str, source: str, target: str):
        super().__init__()
        self.job_mgr = job_mgr
        self.name = name
        self.source = source
        self.target = target

    def run(self):
        try:
            job = self.job_mgr.create('import', 'import')
            job.status = JobStatus.RUNNING
            from app.files.manager import ProjectManager
            from app.runtime.manager import RuntimeManager
            from app.server.port import PortManager
            from app.core.events.bus import EventBus
            from app.database.models import Database
            from pathlib import Path
            import os
            db = Database(str(Path(self.target).resolve().parent.parent / 'data' / 'database' / 'nebulaforge.db'))
            events = EventBus()
            runtime = RuntimeManager()
            port_mgr = PortManager()
            pm = ProjectManager(db, runtime, port_mgr, self.job_mgr, events)
            result = pm.import_folder(job, self.name, self.source, self.target)
            if result:
                self.finished.emit('success', f'Project {self.name} created', str(result.id))
            else:
                self.finished.emit('cancelled', 'Import cancelled', '')
        except Exception as exc:
            self.finished.emit('error', str(exc), '')


class ProjectsPage(QWidget):
    page_name = 'projects'

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state
        self.setObjectName('page')
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        header = QLabel('Live Projects')
        header.setStyleSheet('font-size: 24px; font-weight: bold;')
        layout.addWidget(header)
        toolbar = QHBoxLayout()
        self.new_btn = QPushButton('+ New Project')
        self.new_btn.setObjectName('primary')
        self.import_btn = QPushButton('Import')
        self.import_btn.clicked.connect(self._import)
        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self._refresh)
        toolbar.addWidget(self.new_btn)
        toolbar.addWidget(self.import_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search projects...')
        layout.addWidget(self.search)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        if self.state and self.state.is_initialized:
            self._refresh()

    def _refresh(self):
        self.list_widget.clear()
        if not self.state or not self.state.is_initialized:
            return
        projects = self.state.projects.list_projects()
        for p in projects:
            item = QListWidgetItem(f'{p.name}\n{p.status} | {p.runtime} | {p.host}:{p.port}')
            self.list_widget.addItem(item)

    def _import(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Project Folder')
        if not folder:
            return
        name = os.path.basename(folder)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.worker = ImportWorker(self.state.jobs if self.state else JobManager(), name, folder, folder)
        self.worker.finished.connect(self._import_done)
        self.worker.start()

    def _import_done(self, status, message, project_id):
        self.progress.setVisible(False)
        QMessageBox.information(self, 'Import', message)
        self._refresh()
