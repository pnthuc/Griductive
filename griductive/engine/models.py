"""Board, public/private puzzle data and JSON loading."""
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType


class PuzzleError(ValueError):
    pass


@dataclass(frozen=True)
class Board:
    size: int

    @property
    def cells(self):
        return tuple(f'{chr(65 + column)}{row + 1}'
                     for row in range(self.size) for column in range(self.size))

    def position(self, cell):
        if not isinstance(cell, str) or cell not in self.cells:
            raise PuzzleError(f'Ô không hợp lệ: {cell!r}')
        return int(cell[1:]) - 1, ord(cell[0]) - 65

    def ordered(self, cells):
        return tuple(cell for cell in self.cells if cell in cells)


def freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class Character:
    cell: str
    name: str
    profession: str
    portrait: int


@dataclass(frozen=True)
class PublicState:
    puzzle_id: str
    title: str
    board: Board
    characters: tuple
    statuses: Mapping
    clues: Mapping


@dataclass(frozen=True)
class PrivatePuzzle:
    puzzle_id: str
    title: str
    board: Board
    characters: tuple
    solution: Mapping
    clues: Mapping
    initially_revealed: tuple


def required_string(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PuzzleError(f'{key} phải là chuỗi không rỗng.')
    return value


def load_puzzle(path, registry):
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError,ValueError) as exc:
        raise PuzzleError(f'Không đọc được JSON: {exc}') from exc
    if not isinstance(data,dict):
        raise PuzzleError('Puzzle phải là một object JSON.')
    if type(data.get('schema_version')) is not int or data['schema_version']!=1:
        raise PuzzleError('schema_version phải là 1.')
    if type(data.get('size')) is not int or data['size'] not in (3,4,5):
        raise PuzzleError('size phải là 3, 4 hoặc 5.')
    board=Board(data['size']); chars=[]
    entries=data.get('characters')
    if not isinstance(entries,list) or len(entries)!=len(board.cells):
        raise PuzzleError('characters phải có đúng một nhân vật cho mỗi ô.')
    for i,entry in enumerate(entries):
        if not isinstance(entry,dict):
            raise PuzzleError(f'characters[{i}] phải là object.')
        cell=required_string(entry,'cell'); board.position(cell)
        portrait=entry.get('portrait',i)
        if type(portrait) is not int or portrait < 0:
            raise PuzzleError(f'characters[{i}].portrait phải là số nguyên không âm.')
        chars.append(Character(cell,required_string(entry,'name'),required_string(entry,'profession'),portrait))
    if {c.cell for c in chars} != set(board.cells):
        raise PuzzleError('characters chứa ô trùng hoặc thiếu ô.')
    chars.sort(key=lambda c:board.cells.index(c.cell))
    names=[c.name.casefold() for c in chars]
    if len(set(names))!=len(names) or names!=sorted(names):
        raise PuzzleError('Tên phải khác nhau và theo alphabet từ trái sang phải, trên xuống dưới.')
    solution=data.get('solution')
    if not isinstance(solution,dict) or set(solution)!=set(board.cells):
        raise PuzzleError('solution phải có đủ mọi ô.')
    if any(s not in ('CRIMINAL','INNOCENT') for s in solution.values()):
        raise PuzzleError('solution chỉ nhận CRIMINAL hoặc INNOCENT.')
    clues=data.get('clues')
    if not isinstance(clues,dict) or set(clues)!=set(board.cells):
        raise PuzzleError('clues phải có đúng một clue cho mỗi ô.')
    ids=set(); assignment={c:s=='CRIMINAL' for c,s in solution.items()}
    for cell,clue in clues.items():
        try:
            if not isinstance(clue,dict):
                raise PuzzleError('Clue phải là object.')
            cid=required_string(clue,'id')
            if cid in ids:
                raise PuzzleError('ID clue bị trùng.')
            ids.add(cid); registry.validate(clue,board)
            if not registry.evaluate(clue,assignment,board):
                raise PuzzleError('Clue sai dưới solution đã cung cấp.')
        except PuzzleError as exc:
            raise PuzzleError(f'clues.{cell}: {exc}') from exc
    opened=data.get('initially_revealed')
    if not isinstance(opened,list) or not opened:
        raise PuzzleError('initially_revealed phải là danh sách không rỗng.')
    for c in opened: board.position(c)
    if len(set(opened))!=len(opened):
        raise PuzzleError('initially_revealed chứa ô trùng.')
    return PrivatePuzzle(required_string(data,'puzzle_id'),required_string(data,'title'),board,
        tuple(chars),freeze(solution),freeze(clues),tuple(opened))


