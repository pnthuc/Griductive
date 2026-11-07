import itertools
import json
from pathlib import Path
import tempfile
import unittest
from griductive.engine.regions import Board, PuzzleError, Region, region_registry
from griductive.engine.clues import clue_registry
from griductive.engine.game import GameEngine
from griductive.engine.models import load_puzzle

ROOT=Path(__file__).resolve().parents[1]


class ContractsTest(unittest.TestCase):
    def setUp(self):
        self.regions=region_registry();self.clues=clue_registry(self.regions);self.board=Board(3)

    def test_invalid_comparison_reports_the_clue_path(self):
        data=json.loads((ROOT/'puzzles/case-3x3-01.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.json'
            for op in ([],{},None,True,42):
                data['clues']['A1']={'id':'A1','type':'COMPARISON','op':op,
                    'left':{'type':'CORNERS'},'right':{'type':'ROW','row':1}}
                path.write_text(json.dumps(data),encoding='utf-8')
                with self.subTest(op=op),self.assertRaisesRegex(PuzzleError,'clues.A1'):
                    load_puzzle(path,self.clues)

    def test_regions_nested_empty_and_anchor(self):
        n={'type':'NEIGHBORS','cell':'B2'}
        self.assertEqual(len(self.regions.resolve(n,self.board)),8)
        self.assertNotIn('B2',self.regions.resolve(n,self.board))
        s={'type':'DIFFERENCE','left':n,'right':{'type':'ROW','row':1}}
        self.assertEqual(self.regions.resolve(s,self.board),{'A2','C2','A3','B3','C3'})
        self.assertEqual(self.regions.anchors(s,self.board),{'B2'})
        empty={'type':'DIFFERENCE','left':n,'right':n}
        self.assertEqual(self.regions.resolve(empty,self.board),set())
        self.assertEqual(self.clues.encode({'type':'EXACTLY','k':0,'region':empty},self.board),[])
        with self.assertRaises(PuzzleError):self.clues.validate({'type':'EXACTLY','k':1,'region':empty},self.board)

    def test_register_new_region_without_changing_clues(self):
        @self.regions.register('CENTER')
        class Center(Region):
            def resolve(self, spec, board, regions, depth):
                return {'B2'}

            def describe(self, spec, board, regions):
                return 'ô giữa'
        clue={'type':'EXACTLY','k':1,'region':{'type':'CENTER'}}
        self.assertEqual(self.clues.encode(clue,self.board),[(5,)])

    def test_invalid_parameters(self):
        for s in [{'type':'ROW','row':True},{'type':'EXPLICIT','cells':['A1','A1']},
                  {'type':'COLUMN','column':'Z'},{'type':'UNKNOWN'},
                  {'type':'NEIGHBORS','cell':'A0'}]:
            with self.subTest(spec=s),self.assertRaises(PuzzleError):self.regions.resolve(s,self.board)
        with self.assertRaises(PuzzleError):self.clues.validate({'type':'AT_MOST','k':True,'region':{'type':'CORNERS'}},self.board)

    def test_semantics_and_cnf_agree_exhaustively(self):
        specs=[{'type':'FACT','person':'A1','status':s} for s in ['CRIMINAL','INNOCENT']]
        specs += [{'type':k,'a':'A1','b':'B2'} for k in ['SAME','DIFFERENT']]
        specs += [{'type':kind,'k':k,'region':{'type':'CORNERS'}}
                  for kind in ['EXACTLY','AT_LEAST','AT_MOST'] for k in range(5)]
        # Also test aliasing the same variable in a binary clue.
        specs += [{'type':k,'a':'A1','b':'A1'} for k in ['SAME','DIFFERENT']]
        for spec in specs:
            clauses=self.clues.encode(spec,self.board)
            for bits in itertools.product([False,True],repeat=9):
                assignment=dict(zip(self.board.cells,bits))
                from griductive.engine.sat import solve
                assumptions=tuple(i+1 if value else -(i+1) for i,value in enumerate(bits))
                satisfies=solve(clauses,assumptions=assumptions).status=='SAT'
                self.assertEqual(satisfies,self.clues.evaluate(spec,assignment,self.board),(spec,bits))

    def test_public_state_does_not_publish_hidden_data(self):
        p=load_puzzle(ROOT/'tests/fixtures/prototype-3x3.json',self.clues)
        public=GameEngine(p).public_state()
        self.assertEqual(set(public.clues),{'A1','B2','C3'})
        self.assertNotIn('B1',public.statuses)
        self.assertFalse(hasattr(public,'solution'))
        with self.assertRaises(TypeError):public.clues['A1']['k']=99

    def test_hidden_changes_do_not_change_public_state(self):
        data=json.loads((ROOT/'tests/fixtures/prototype-3x3.json').read_text(encoding='utf-8'))
        original=GameEngine(load_puzzle(ROOT/'tests/fixtures/prototype-3x3.json',self.clues)).public_state()
        data['clues']['B1']={'id':'B1','type':'FACT','person':'A1','status':'INNOCENT'}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'changed.json';path.write_text(json.dumps(data),encoding='utf-8')
            changed=GameEngine(load_puzzle(path,self.clues)).public_state()
            self.assertEqual(original,changed)

    def test_loader_rejects_false_clue_with_field_path(self):
        data=json.loads((ROOT/'tests/fixtures/prototype-3x3.json').read_text(encoding='utf-8'))
        data['clues']['A1']['k']=4
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.json';path.write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaisesRegex(PuzzleError,'clues.A1'):load_puzzle(path,self.clues)


if __name__=='__main__':unittest.main()
