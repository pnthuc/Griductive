"""Puzzle rules, CNF encoding, SAT solving and public deduction sessions."""
from .models import Board, Character, PrivatePuzzle, PublicState, PuzzleError, load_puzzle
from .regions import Region, RegionRegistry, region_registry, register_region
from .clues import Clue, ClueRegistry, clue_registry, register_clue, clue_parts
from .game import GameEngine, LogicAgent, check_uniqueness
from .cnf import Encoder, build_knowledge_base
from .sat import solve, SolverCancelled, SolverTimeout
