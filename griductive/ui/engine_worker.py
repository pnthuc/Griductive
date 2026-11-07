"""One sequential owner for the mutable engine; widgets never run SAT."""
import json
from dataclasses import dataclass, field
from queue import Queue
from threading import Event
from PySide6.QtCore import QThread, Signal
from ..engine.cnf import build_knowledge_base
from ..engine.sat import SolverCancelled


@dataclass
class Job:
    generation: int
    request: int
    kind: str
    payload: object = None
    cancel: Event = field(default_factory=Event)


class EngineWorker(QThread):
    completed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.queue = Queue()
        self.engine = None

    def run(self):
        actions = {'hint': self.hint, 'step': self.step, 'submit': self.submit}
        pending = None
        while True:
            job = self.queue.get()
            if pending is not None:
                previous, candidate, original = pending
                self.engine = original if previous.cancel.is_set() else candidate
                pending = None
            if job is None:
                return
            if job.kind == 'replace':
                self.engine = job.payload
                continue
            if job.cancel.is_set():
                continue
            try:
                original = self.engine
                self.engine = original.fork()
                pending = (job, self.engine, original)
                result = actions[job.kind](job)
                state = self.engine.public_state()
                kb = build_knowledge_base(state, self.engine.registry)
                if not job.cancel.is_set():
                    self.completed.emit((job, result, state,
                        json.loads(json.dumps(self.engine.trace)),
                        (len(kb.primary), kb.auxiliary_count, len(kb.clauses)), None))
            except SolverCancelled:
                pass
            except Exception as exc:
                job.cancel.set()
                self.completed.emit((job, None, None, None, None, exc))

    def hint(self, job):
        cell, verdict = self.engine.hint(cancelled=job.cancel.is_set)
        return {'cell': cell, 'result': verdict}

    def step(self, job):
        return self.engine.step(cancelled=job.cancel.is_set)

    def submit(self, job):
        cell, verdict = job.payload
        return self.engine.submit(cell, verdict, cancelled=job.cancel.is_set)
