import unittest
from griductive.engine.regions import Board,region_registry
from griductive.engine.clues import clue_registry
from griductive.engine.clues import clue_parts
from griductive.presentation.wording_vi import clue_html
from griductive.ui.themes import THEMES


class PresentationTest(unittest.TestCase):
    def setUp(self):
        self.board=Board(3);self.regions=region_registry();self.clues=clue_registry(self.regions)

    def test_nested_difference_intersection_union_have_independent_parts(self):
        spec={'type':'EXACTLY','k':0,'region':{'type':'DIFFERENCE',
            'left':{'type':'UNION','left':{'type':'ROW','row':1},'right':{'type':'COLUMN','column':'A'}},
            'right':{'type':'INTERSECTION','left':{'type':'CORNERS'},'right':{'type':'ROW','row':1}}}}
        parts={p.key:p for p in clue_parts(spec,self.board,self.clues)}
        self.assertEqual(parts['result'].cells,{'B1','A2','A3'})
        self.assertEqual(parts['region.left'].cells,{'A1','B1','C1','A2','A3'})
        self.assertEqual(parts['region.right'].cells,{'A1','C1'})
        html=clue_html(spec,self.board,self.clues,THEMES['pixel'])
        self.assertIn('href="region.left.right"',html)
        self.assertIn('href="region.right.left"',html)
        self.assertEqual(parts['result'].cells,self.clues.cells(spec,self.board))

    def test_empty_result_remains_empty_while_inspecting_operands(self):
        row={'type':'ROW','row':1}
        spec={'type':'EXACTLY','k':0,'region':{'type':'DIFFERENCE','left':row,'right':row}}
        parts={p.key:p for p in clue_parts(spec,self.board,self.clues)}
        self.assertEqual(parts['result'].cells,set())
        self.assertEqual(len(parts['region.left'].cells),3)

    def test_named_people_have_triggers_but_relation_and_status_stay_neutral(self):
        spec={'type':'DIFFERENT','a':'A1','b':'B2'}
        html=clue_html(spec,self.board,self.clues,THEMES['pixel'])
        self.assertIn('href="a"',html);self.assertIn('href="b"',html)
        self.assertEqual(html.count('<a '),2)
        self.assertTrue(html.endswith(': một người phạm tội, người kia vô tội.'))
        self.assertEqual(clue_parts(spec,self.board,self.clues)[0].cells,{'A1','B2'})

    def test_repeated_person_does_not_create_nested_links(self):
        html=clue_html({'type':'SAME','a':'A1','b':'A1'},self.board,self.clues,THEMES['pixel'])
        self.assertEqual(html.count('<a '),2)
        self.assertEqual(html.count('</a>'),2)
        self.assertTrue(html.endswith('hoặc cùng phạm tội, hoặc cùng vô tội.'))

    def test_region_and_named_anchor_are_colored_but_quantity_and_status_are_not(self):
        spec={'type':'EXACTLY','k':2,'region':{'type':'NEIGHBORS','cell':'B2'}}
        parts={p.key:p for p in clue_parts(spec,self.board,self.clues)}
        self.assertEqual(parts['region.anchor.B2'].cells,{'B2'})
        self.assertNotIn('B2',parts['result'].cells)
        html=clue_html(spec,self.board,self.clues,THEMES['pixel'])
        self.assertIn('href="region"',html)
        self.assertEqual(html.count('<a '),2)
        self.assertIn('href="region.anchor.B2"',html)
        self.assertNotIn(THEMES['pixel'].criminal,html)
        self.assertIn('có đúng 2 Tội phạm.',html)
        self.assertNotIn('text-decoration:underline',html)
        self.assertNotIn('<u>',html)


if __name__=='__main__':unittest.main()
