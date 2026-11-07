import itertools
import unittest
from pathlib import Path
from griductive.engine.regions import Board, region_registry, PuzzleError
from griductive.engine.clues import clue_registry
from griductive.engine.cnf import Encoder, build_knowledge_base
from griductive.engine.sat import solve
from griductive.engine.game import LogicAgent
from griductive.engine.game import check_uniqueness
from griductive.engine.game import GameEngine
from griductive.engine.models import PublicState, freeze
from griductive.engine.models import load_puzzle

ROOT = Path(__file__).resolve().parents[1]


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.board = Board(3)
        self.registry = clue_registry(region_registry())

    def _conditional_pairs(self,board,clue,state=None,owner=None):
        """Possible (premise, consequence) pairs before adding this clue."""
        encoder=Encoder(board)
        if state is not None:
            for c,s in state.clues.items():
                if c!=owner:encoder.add(s,self.registry)
            for c,status in state.statuses.items():
                v=encoder.variables[c]
                encoder.clauses.append((v if status=='CRIMINAL' else -v,))
        a=encoder.expression(clue['if'],self.registry)
        b=encoder.expression(clue['then'],self.registry)
        kb=encoder.finish();pairs=set()
        for x,y in itertools.product((False,True),repeat=2):
            assumptions=[];impossible=False
            for expr,value in ((a,x),(b,y)):
                if type(expr) is bool:
                    if expr!=value:impossible=True
                else:assumptions.append(expr if value else -expr)
            if not impossible and solve(kb.clauses,kb.variable_count,tuple(assumptions)).status=='SAT':pairs.add((x,y))
        return pairs

    def test_dpll_complete_model_and_unsat(self):
        for heuristic in ('ordered', 'frequency'):
            sat = solve([(1,2),(-1,2)],4,heuristic=heuristic)
            self.assertEqual(sat.status,'SAT')
            self.assertEqual(set(sat.model),{1,2,3,4})
            self.assertTrue(sat.model[2])
            self.assertEqual(solve([(1,),(-1,)]).status,'UNSAT')
            self.assertEqual(solve([()]).status,'UNSAT')
            self.assertEqual(solve([],2).model,{1:False,2:False})
            self.assertEqual(solve([(1,2),(-1,2)],assumptions=(-2,)).status,'UNSAT')
            # Both branches fail, exercising backtracking.
            result=solve([(1,2),(-1,2),(1,-2),(-1,-2)],heuristic=heuristic)
            self.assertEqual(result.status,'UNSAT')
            self.assertGreater(result.stats.decisions,0)
            self.assertGreater(result.stats.backtracks,0)

    def test_reified_semantics_and_overlapping_comparisons(self):
        a={'type':'EXPLICIT','cells':['A1','B1']}
        b={'type':'EXPLICIT','cells':['B1','C1']}
        specs=[{'type':'COMPARISON','left':a,'right':b,'op':op}
               for op in ('=','!=','<','<=','>','>=')]
        specs += [{'type':kind,'region':a,'k':k} for kind in
                  ('EXACTLY','AT_LEAST','AT_MOST') for k in range(3)]
        specs += [{'type':'SAME','a':'A1','b':'B1'},{'type':'DIFFERENT','a':'A1','b':'A1'}]
        specs += [{'type':'CONDITIONAL','if':{'type':'FACT','person':'A1','status':'CRIMINAL'},
                   'then':{'type':'CONDITIONAL','if':specs[0],'then':specs[1]}}]
        for spec in specs:
            encoder=Encoder(self.board)
            encoder.add(spec,self.registry)
            kb=encoder.finish()
            for bits in itertools.product((False,True),repeat=3):
                assignment={c:False for c in self.board.cells}
                assignment.update(zip(('A1','B1','C1'),bits))
                assumptions=[v if assignment[c] else -v for c,v in kb.primary.items()]
                result=solve(kb.clauses,kb.variable_count,assumptions)
                self.assertEqual(result.status=='SAT',self.registry.evaluate(spec,assignment,self.board),(spec,bits))

    def test_shared_auxiliary_namespace_and_polynomial_size(self):
        board=Board(5)
        encoder=Encoder(board)
        region={'type':'EXPLICIT','cells':list(board.cells)}
        encoder.add({'type':'EXACTLY','k':12,'region':region},self.registry)
        encoder.add({'type':'AT_MOST','k':11,'region':region},self.registry)
        kb=encoder.finish()
        self.assertLess(len(kb.clauses),5000)
        self.assertEqual(solve(kb.clauses,kb.variable_count).status,'UNSAT')

    def test_model_is_not_entailment_and_inconsistency(self):
        state=PublicState('x','x',self.board,(),freeze({}),freeze({
            'A1':{'id':'x','type':'AT_LEAST','k':1,'region':{'type':'EXPLICIT','cells':['A1','B1']}}}))
        result=LogicAgent(self.registry).classify(state)
        self.assertTrue(all(v=='UNKNOWN' for v in result.values()))
        state=PublicState('x','x',self.board,(),freeze({'A1':'INNOCENT'}),freeze({
            'A1':{'id':'x','type':'FACT','person':'A1','status':'CRIMINAL'}}))
        self.assertTrue(all(v=='INCONSISTENT' for v in LogicAgent(self.registry).classify(state).values()))

    def test_rejection_is_atomic_and_acceptance_is_repeatable(self):
        p=load_puzzle(ROOT/'puzzles/case-3x3-01.json',self.registry)
        engine=GameEngine(p,self.registry)
        before=engine.public_state()
        agent=LogicAgent(self.registry)
        cell,status=agent.next_verdict(before)
        opposite='INNOCENT' if status=='CRIMINAL' else 'CRIMINAL'
        self.assertEqual(engine.submit(cell,opposite)['result'],'CONTRADICTED')
        self.assertEqual(engine.public_state(),before)
        unknown=next(c for c,v in LogicAgent(self.registry).classify(before).items() if v=='UNKNOWN')
        self.assertEqual(engine.submit(unknown,'CRIMINAL')['result'],'NOT_PROVABLE')
        self.assertEqual(engine.public_state(),before)
        self.assertEqual(engine.submit(cell,status)['result'],'ACCEPTED')
        after=engine.public_state()
        self.assertEqual(engine.submit(cell,status)['result'],'ALREADY_REVEALED')
        self.assertEqual(engine.public_state(),after)
        self.assertEqual(len(engine.trace),1)

    def test_six_cases_unique_and_progressively_solvable(self):
        paths=sorted((ROOT/'puzzles').glob('case-*.json'))
        self.assertEqual(len(paths),6)
        for path in paths:
            with self.subTest(path=path.name):
                puzzle=load_puzzle(path,self.registry)
                self.assertEqual(check_uniqueness(puzzle,self.registry),'UNIQUE')
                engine=GameEngine(puzzle,self.registry)
                agent=LogicAgent(self.registry)
                four=set(itertools.product((False,True),repeat=2));reverse={(False,False),(True,False)}
                modes=[]
                for owner,clue in puzzle.clues.items():
                    if clue['type']=='CONDITIONAL':
                        self.assertEqual(self._conditional_pairs(puzzle.board,clue),four,
                            f'{owner}: implication must not collapse to one of its sides')
                for owner,clue in engine.public_state().clues.items():
                    if clue['type']=='CONDITIONAL':
                        pairs=self._conditional_pairs(puzzle.board,clue,engine.public_state(),owner)
                        self.assertEqual(pairs,four,f'{owner}: opening needs two genuinely unresolved sides')
                        modes.append(pairs)
                while not engine.solved:
                    cell,status=agent.next_verdict(engine.public_state())
                    self.assertIsNotNone(cell)
                    self.assertEqual(engine.submit(cell,status)['result'],'ACCEPTED')
                    state=engine.public_state();clue=state.clues[cell]
                    if clue['type']=='CONDITIONAL':
                        pairs=self._conditional_pairs(puzzle.board,clue,state,cell)
                        self.assertIn(pairs,(four,reverse),f'{cell}: premise was already decided at reveal')
                        modes.append(pairs)
                self.assertEqual(len(engine.trace),len(puzzle.board.cells)-len(puzzle.initially_revealed))
                self.assertTrue(all(e['queries'][-1]['result']=='UNSAT' for e in engine.trace))
                self.assertIn(reverse,modes,'Case needs at least one actual contraposition opportunity')

    def test_invalid_and_recursive_extensions(self):
        for bad in (
            {'type':'COMPARISON','op':'approx','left':{'type':'CORNERS'},'right':{'type':'CORNERS'}},
            {'type':'CONDITIONAL','if':None,'then':{'type':'FACT','person':'A1','status':'INNOCENT'}}):
            with self.assertRaises(PuzzleError):
                self.registry.validate(bad,self.board)
        clue={'type':'FACT','person':'A1','status':'INNOCENT'}
        for _ in range(14):
            clue={'type':'CONDITIONAL','if':clue,'then':{'type':'FACT','person':'A1','status':'INNOCENT'}}
        with self.assertRaises(PuzzleError):
            self.registry.validate(clue,self.board)
