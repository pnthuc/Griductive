"""Stateless web sessions: every claimed move is proved again by the engine.

Only the public move history lives in browser storage. No mutable game is
shared between visitors or assumed to survive a Vercel function invocation.
"""
import base64
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

from .engine import (
    GameEngine, PuzzleError, SolverCancelled, SolverTimeout,
    clue_registry, load_puzzle, region_registry,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUZZLE = 'case-3x3-01'
MAX_UPLOAD = 128_000


@lru_cache(maxsize=1)
def puzzle_paths():
    return {path.stem: path for path in sorted((ROOT / 'puzzles').glob('case-*.json'))}


@lru_cache(maxsize=8)
def bundled_puzzle(identifier):
    if identifier not in puzzle_paths():
        raise PuzzleError('Không tìm thấy màn chơi.')
    return load_puzzle(puzzle_paths()[identifier], clue_registry(region_registry()))


def puzzle_options():
    return [{'label': f'{p.board.size}×{p.board.size} — {p.title}', 'value': key}
            for key in puzzle_paths() for p in (bundled_puzzle(key),)]


def read_upload(contents, registry):
    if not isinstance(contents, str) or len(contents) > MAX_UPLOAD * 2:
        raise PuzzleError('Tệp JSON tối đa 128 KB.')
    try:
        raw = base64.b64decode(contents.split(',', 1)[1], validate=True)
        if len(raw) > MAX_UPLOAD:
            raise PuzzleError('Tệp JSON tối đa 128 KB.')
        text = raw.decode('utf-8-sig')
    except (ValueError, IndexError, UnicodeError) as exc:
        raise PuzzleError('Không đọc được tệp JSON đã chọn.') from exc
    with TemporaryDirectory(prefix='griductive-') as folder:
        path = Path(folder) / 'puzzle.json'
        path.write_text(text, encoding='utf-8')
        return load_puzzle(path, registry)


def new_session(puzzle=DEFAULT_PUZZLE, custom=None):
    return {'puzzle': puzzle, 'custom': custom, 'history': [],
            'selected': None, 'focus': None, 'running': False,
            'notice': 'Chọn một nhân vật hoặc lời khai để bắt đầu.'}


def restore(session, cancelled=lambda: False):
    if not isinstance(session, dict):
        raise PuzzleError('Phiên chơi không hợp lệ. Hãy chọn lại màn.')
    registry = clue_registry(region_registry())
    if session.get('custom') is not None:
        puzzle = read_upload(session['custom'], registry)
    else:
        identifier = session.get('puzzle')
        if not isinstance(identifier, str):
            raise PuzzleError('Mã màn không hợp lệ.')
        puzzle = bundled_puzzle(identifier)
    if any(not 0 <= person.portrait < 25 for person in puzzle.characters):
        raise PuzzleError('Màn chơi tham chiếu sprite không có trong bộ ảnh hiện tại.')
    engine = GameEngine(puzzle, registry)
    history = session.get('history', [])
    if not isinstance(history, list) or len(history) > len(puzzle.board.cells):
        raise PuzzleError('Lịch sử phiên không hợp lệ.')
    for move in history:
        if not isinstance(move, dict):
            raise PuzzleError('Lịch sử phiên không hợp lệ.')
        result = engine.submit(move.get('cell'), move.get('verdict'), cancelled=cancelled)
        if result['result'] != 'ACCEPTED':
            raise PuzzleError('Lịch sử chứa phán quyết chưa được chứng minh. Hãy làm lại màn.')
    return engine


MESSAGES = {
    'NOT_PROVABLE': 'NOT_PROVABLE — Chưa đủ dữ kiện để xác định người này.',
    'CONTRADICTED': 'CONTRADICTED — Dữ kiện chứng minh trạng thái ngược lại.',
    'UNKNOWN': 'UNKNOWN — Chưa có phán quyết tiếp theo có thể chứng minh.',
    'INCONSISTENT': 'INCONSISTENT — Các dữ kiện hiện có mâu thuẫn.',
    'ALREADY_REVEALED': 'Nhân vật này đã được xác định.',
}


def transition(session, action=None, payload=None):
    """Perform one UI action; return updated public history and its engine."""
    deadline = monotonic() + 45
    cancelled = lambda: monotonic() >= deadline
    state = deepcopy(session)
    if action == 'load':
        state = new_session(payload)
    elif action == 'upload':
        state = new_session('custom', payload)
    elif action == 'restart':
        state = new_session(state.get('puzzle', DEFAULT_PUZZLE), state.get('custom'))
    try:
        engine = restore(state, cancelled)
        public = engine.public_state()
        names = {person.cell: person.name for person in public.characters}
        if action not in (None, 'tick', 'auto'):
            state['running'] = False
        if action == 'select':
            public.board.position(payload)
            state.update(selected=payload, focus=None,
                         notice=f'Đang chọn {names[payload]} ({payload}).')
        elif action == 'clear':
            state.update(selected=None, focus=None)
        elif action == 'focus':
            from .engine import clue_parts
            owner = state.get('selected')
            if owner not in public.clues:
                raise PuzzleError('Hãy chọn một lời khai đã mở.')
            keys = {part.key for part in clue_parts(public.clues[owner], public.board, engine.registry)}
            if payload not in keys:
                raise PuzzleError('Vùng được chọn không hợp lệ.')
            state['focus'] = None if payload == state.get('focus') else payload
        elif action == 'hint':
            cell, verdict = engine.hint(cancelled=cancelled)
            if cell:
                state.update(selected=cell, focus=None,
                    notice=f'Có thể chứng minh trạng thái của {names[cell]} ({cell}) từ các lời khai đã mở.')
            else:
                state['notice'] = MESSAGES.get(verdict, 'Đã xác định tất cả nhân vật.')
        elif action == 'auto':
            state['running'] = not bool(state.get('running')) and not engine.solved
            state['notice'] = 'Đang tự động giải từng bước…' if state['running'] else 'Đã tạm dừng.'
        elif action in ('step', 'verdict') or (action == 'tick' and state.get('running')):
            if action == 'verdict':
                cell = state.get('selected')
                if cell is None:
                    raise PuzzleError('Hãy chọn một nhân vật trước.')
                result = engine.submit(cell, payload, cancelled=cancelled)
            else:
                result = engine.step(cancelled=cancelled) if not engine.solved else {'result': 'SOLVED'}
            if result['result'] == 'ACCEPTED':
                cell, verdict = result['cell'], result['verdict']
                state['history'].append({'cell': cell, 'verdict': verdict})
                label = 'Tội phạm' if verdict == 'CRIMINAL' else 'Vô tội'
                state.update(selected=cell, focus=None,
                             notice=f'Đã chứng minh {names[cell]} ({cell}): {label}.')
            else:
                state['running'] = False
                state['notice'] = MESSAGES.get(result['result'], 'Đã xác định tất cả nhân vật.')
        if engine.solved:
            state.update(running=False, notice='Hoàn thành! Đã chứng minh trạng thái của tất cả nhân vật.')
        return state, engine
    except SolverCancelled as exc:
        raise SolverTimeout('Hết thời gian suy luận. Tiến độ trước đó được giữ nguyên.') from exc
