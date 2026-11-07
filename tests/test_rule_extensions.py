import itertools
import unittest
from griductive.engine.clues import Clue,clue_registry
from griductive.engine.regions import Board,region_registry,Region
from griductive.engine.cnf import Encoder
from griductive.engine.clues import clue_parts
from griductive.engine.sat import solve,SolverCancelled


class RuleExtensionTests(unittest.TestCase):
    def test_new_rule_composes_inside_conditional_without_compiler_changes(self):
        regions=region_registry()
        @regions.register('PAIR')
        class Pair(Region):
            def resolve(self, spec, board, regions, depth):
                return {'A1','B1'}

            def describe(self, spec, board, regions):
                return 'hai ô đầu'

        clues=clue_registry(regions)

        @clues.register('ODD_PAIR')
        class OddPair(Clue):
            region_fields = ('region',)

            def evaluate(self, spec, assignment, board, clues):
                return sum(assignment[c] for c in clues.regions.resolve(spec['region'], board)) % 2 == 1

            def expression(self, spec, encoder, clues):
                cells = clues.regions.resolve(spec['region'], encoder.board)
                a, b = [encoder.variables[c] for c in encoder.board.ordered(cells)]
                return encoder.gate('AND', (encoder.gate('OR', (a, b)), encoder.gate('OR', (-a, -b))))

            def describe(self, spec, board, clues):
                return 'Một trong hai người phạm tội.'
        inner={'type':'ODD_PAIR','region':{'type':'PAIR'}}
        spec={'type':'CONDITIONAL','if':inner,'then':{'type':'FACT','person':'C1','status':'INNOCENT'}}
        board=Board(3);encoder=Encoder(board);encoder.add(spec,clues);kb=encoder.finish()
        for bits in itertools.product((False,True),repeat=3):
            assignment=dict.fromkeys(board.cells,False);assignment.update(zip(('A1','B1','C1'),bits))
            fixed=[v if assignment[c] else -v for c,v in kb.primary.items()]
            self.assertEqual(solve(kb.clauses,kb.variable_count,fixed).status=='SAT',clues.evaluate(spec,assignment,board))
        parts={p.key:p for p in clue_parts(spec,board,clues)}
        self.assertEqual(parts['if.region'].cells,{'A1','B1'})
        self.assertTrue(parts['if.region'].is_region)

    def test_cancel_is_not_unknown_or_a_partial_model(self):
        with self.assertRaises(SolverCancelled):solve([(1,2)],cancelled=lambda:True)
