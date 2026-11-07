"""GUI requests and stale-result protection around the pure Python engine."""
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, Slot
from .engine_worker import EngineWorker, Job


@dataclass
class SessionView:
    state: object
    trace: list

    @property
    def solved(self):
        return len(self.state.statuses) == len(self.state.board.cells)

    def public_state(self):
        return self.state


class GameController(QObject):
    finished = Signal(str, object, object, object)
    failed = Signal(object)
    busy_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = EngineWorker(self)
        self.worker.completed.connect(self.receive)
        self.generation = 0
        self.request_id = 0
        self.current = None
        self.busy = False
        self.view = None
        self.closed = False
        self.worker.start()

    def replace(self, engine):
        if self.closed:
            raise RuntimeError('Game controller is closed')
        self.cancel()
        self.generation += 1
        self.view = SessionView(engine.public_state(), [])
        self.worker.queue.put(Job(self.generation, self.request_id, 'replace', engine))
        return self.view

    def request(self, kind, payload=None):
        if kind not in ('hint', 'step', 'submit'):
            raise ValueError(f'Unknown game request: {kind}')
        if self.closed or self.view is None or self.busy:
            return False
        self.request_id += 1
        self.current = Job(self.generation, self.request_id, kind, payload)
        self.busy = True
        self.busy_changed.emit(True)
        self.worker.queue.put(self.current)
        return True

    def cancel(self):
        if self.current:
            self.current.cancel.set()
        self.current = None
        self.request_id += 1
        self.busy = False
        self.busy_changed.emit(False)

    @Slot(object)
    def receive(self, response):
        job, result, state, trace, metrics, error = response
        if (job.generation, job.request) != (self.generation, self.request_id):
            return
        self.current = None
        self.busy = False
        self.busy_changed.emit(False)
        if error:
            self.failed.emit(error)
            return
        self.view = SessionView(state, trace)
        self.finished.emit(job.kind, result, self.view, metrics)

    def shutdown(self):
        if self.closed:
            return
        self.closed = True
        self.cancel()
        self.worker.queue.put(None)
        self.worker.wait()
