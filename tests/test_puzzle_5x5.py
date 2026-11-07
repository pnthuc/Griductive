"""Difficulty checks use the same public-KB entailment rules as gameplay."""
import unittest
from pathlib import Path
from dataclasses import replace
from griductive.engine.regions import region_registry
from griductive.engine.clues import clue_registry
from griductive.engine.models import load_puzzle
from griductive.engine.game import GameEngine
from griductive.engine.models import freeze
from griductive.engine.game import LogicAgent
from griductive.engine.cnf import build_knowledge_base

ROOT=Path(__file__).resolve().parents[1]


class Case5x5Test(unittest.TestCase):
    def setUp(self):
        self.registry=clue_registry(region_registry())
        self.puzzle=load_puzzle(ROOT/'puzzles/case-5x5-01.json',self.registry)

    def test_opening_requires_more_than_one_revealed_clue(self):
        state=GameEngine(self.puzzle,self.registry).public_state()
        agent=LogicAgent(self.registry);cell,status=agent.next_verdict(state)
        self.assertIsNotNone(cell)
        for owner,clue in state.clues.items():
            with self.subTest(clue=clue['id']):
                single=replace(state,clues=freeze({owner:clue}))
                kb=build_knowledge_base(single,self.registry)
                opposite=-kb.primary[cell] if status=='CRIMINAL' else kb.primary[cell]
                self.assertEqual(agent.query(kb,(opposite,)).status,'SAT')

    def test_conditionals_and_comparisons_are_essential_to_progress(self):
        def contains(clue,kind):
            return clue['type']==kind or (clue['type']=='CONDITIONAL' and
                (contains(clue['if'],kind) or contains(clue['then'],kind)))
        engine=GameEngine(self.puzzle,self.registry);needed=set()
        agent=LogicAgent(self.registry)
        while not engine.solved and len(needed)<2:
            state=engine.public_state();cell,status=agent.next_verdict(state)
            self.assertIsNotNone(cell)
            for kind in ('CONDITIONAL','COMPARISON'):
                if kind in needed:continue
                reduced=replace(state,clues=freeze({c:s for c,s in state.clues.items() if not contains(s,kind)}))
                kb=build_knowledge_base(reduced,self.registry)
                opposite=-kb.primary[cell] if status=='CRIMINAL' else kb.primary[cell]
                if agent.query(kb,(opposite,)).status=='SAT':needed.add(kind)
            self.assertEqual(engine.submit(cell,status)['result'],'ACCEPTED')
        self.assertEqual(needed,{'CONDITIONAL','COMPARISON'})
