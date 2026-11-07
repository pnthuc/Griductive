import unittest
from griductive.presentation.wording_vi import clue_text,clue_html
from griductive.engine.regions import Board,region_registry
from griductive.engine.clues import clue_registry
from griductive.ui.themes import THEMES


class WordingTest(unittest.TestCase):
    def test_named_difference_preserves_region_link_keys(self):
        board=Board(3);clues=clue_registry(region_registry())
        spec={'type':'EXACTLY','k':2,'region':{'type':'DIFFERENCE',
            'left':{'type':'NEIGHBORS','cell':'B2'},'right':{'type':'ROW','row':1}}}
        plain=clue_text(spec,board,clues,{'B2':'Eli'})
        self.assertIn('xung quanh Eli',plain);self.assertIn('không ở hàng 1',plain)
        self.assertNotIn('Criminal',plain);self.assertNotIn('B2',plain)
        html=clue_html(spec,board,clues,THEMES['pixel'],{'B2':'Eli'})
        for key in ('region.left','region.right'):
            self.assertIn(f'href="{key}"',html)
        self.assertIn('href="region.left.anchor.B2"',html)

    def test_nested_scope_and_html_names_are_safe(self):
        board=Board(3);clues=clue_registry(region_registry())
        row={'type':'ROW','row':1};col={'type':'COLUMN','column':'A'}
        spec={'type':'EXACTLY','k':1,'region':{'type':'DIFFERENCE','left':row,
            'right':{'type':'UNION','left':row,'right':col}}}
        text=clue_text(spec,board,clues)
        self.assertIn('(ở hàng 1 hoặc ở cột A)',text)
        fact={'type':'FACT','person':'A1','status':'INNOCENT'}
        html=clue_html(fact,board,clues,THEMES['pixel'],{'A1':'<Ada>'})
        self.assertIn('&lt;Ada&gt;',html);self.assertIn('Vô tội',html)

    def test_single_person_comparison_and_condition_read_as_people_not_groups(self):
        board=Board(3);clues=clue_registry(region_registry());names={'B2':'Eli','C2':'Finn','A3':'Gwen'}
        comparison={'type':'COMPARISON','op':'!=',
            'left':{'type':'INTERSECTION','left':{'type':'ROW','row':2},'right':{'type':'COLUMN','column':'C'}},
            'right':{'type':'EXPLICIT','cells':['B2']}}
        self.assertEqual(clue_text(comparison,board,clues,names),
            'Finn và Eli: một người phạm tội, người kia vô tội.')
        conditional={'type':'CONDITIONAL','if':{'type':'EXACTLY','k':0,'region':{'type':'EXPLICIT','cells':['C2']}},
            'then':{'type':'FACT','person':'A3','status':'CRIMINAL'}}
        self.assertEqual(clue_text(conditional,board,clues,names),'Nếu Finn vô tội thì Gwen là Tội phạm.')

    def test_empty_union_is_not_rendered_as_a_mysterious_group(self):
        board=Board(3);clues=clue_registry(region_registry())
        spec={'type':'AT_LEAST','k':1,'region':{'type':'UNION',
            'left':{'type':'ROW','row':2},'right':{'type':'EXPLICIT','cells':[]}}}
        self.assertEqual(clue_text(spec,board,clues),'Ở hàng 2, có ít nhất 1 Tội phạm.')
