"""Public clue inspection metadata; no Qt or private puzzle dependencies."""
from html import escape
from dataclasses import dataclass

@dataclass(frozen=True)
class RuleText:
    """Plain/HTML helpers passed to a rule's optional wording method.

    region(spec, key, role) and person(cell, key, role) retain highlight keys;
    token(key, value) escapes ordinary text when rendering HTML.
    child(spec, field) formats a nested clue with its reference prefix.
    """
    board: object
    clues: object
    names: dict
    theme: object
    prefix: str
    embedded: bool
    token: object
    person: object
    region: object
    location: object
    child: object


STATUS_TEXT={'CRIMINAL':'Tội phạm','INNOCENT':'Vô tội'}


def clue_text(spec,board,clues,names=None,theme=None,_prefix="",_embedded=False):
    """One wording tree for plain text and rich text; links retain semantic keys."""
    names=names or {}
    def token(key,text,role='result',colored=False):
        if theme is None:return text
        if not colored:return escape(text)
        key = _prefix + key
        color={'result':theme.gold,'a':theme.operand_a,'b':theme.operand_b,'anchor':theme.anchor}[role]
        return f'<a href="{key}" style="color:{color};text-decoration:none;font-weight:700;">{escape(text)}</a>'
    def person(cell,key,role):return token(key,names.get(cell,cell),role,True)
    def joined(values,conjunction='và'):
        if not values:return 'không có ai'
        return values[0] if len(values)==1 else ', '.join(values[:-1])+' '+conjunction+' '+values[-1]
    def member(s,key,role):
        kind=s['type']
        if kind in ('UNION','INTERSECTION','DIFFERENCE'):
            left=member(s['left'],key+'.left','a');right=member(s['right'],key+'.right','b')
            if s['left']['type'] in ('UNION','INTERSECTION','DIFFERENCE'):left='('+left+')'
            if s['right']['type'] in ('UNION','INTERSECTION','DIFFERENCE'):right='('+right+')'
            if kind=='DIFFERENCE':
                if s['right']['type']=='EXPLICIT':
                    right='không phải '+token(key+'.right',joined([names.get(c,c) for c in board.ordered(s['right']['cells'])],'hay'),'b',True)
                else:right='không '+right
            return left+{'UNION':' hoặc ','INTERSECTION':' và ','DIFFERENCE':' nhưng '}[kind]+right
        if kind=='NEIGHBORS':
            return token(key,'ở xung quanh ',role,True)+person(s['cell'],key+'.anchor.'+s['cell'],'anchor')
        if kind=='EXPLICIT':return 'là '+token(key,joined([names.get(c,c) for c in board.ordered(s['cells'])],'hoặc'),role,True)
        return 'ở '+region(s,key,role)
    def region(s,key='region',role='result'):
        custom=clues.regions.handler(s).wording(s,text,key,role)
        if custom is not None:return custom
        kind=s['type']
        if kind in ('UNION','INTERSECTION','DIFFERENCE'):
            if kind=='UNION':
                if not clues.regions.resolve(s['right'],board):return region(s['left'],key+'.left','a')
                if not clues.regions.resolve(s['left'],board):return region(s['right'],key+'.right','b')
            return 'những người '+member(s,key,role)
        if kind=='NEIGHBORS':
            return token(key,'những người xung quanh ',role,True)+person(s['cell'],key+'.anchor.'+s['cell'],'anchor')
        if kind=='EXPLICIT':
            people=[names.get(c,c) for c in board.ordered(s['cells'])]
            label='danh sách trống' if not people else 'riêng '+people[0] if len(people)==1 else 'nhóm gồm '+joined(people)
            return token(key,label,role,True)
        return token(key,{'ROW':lambda:'hàng '+str(s['row']),
                         'COLUMN':lambda:'cột '+s['column'],
                         'CORNERS':lambda:'bốn ô góc'}.get(kind,lambda:clues.regions.describe(s,board))(),role,True)
    def among(s,description):
        if s['type']=='UNION':
            if not clues.regions.resolve(s['right'],board):return among(s['left'],description)
            if not clues.regions.resolve(s['left'],board):return among(s['right'],description)
        if s['type'] in ('ROW','COLUMN','CORNERS'):return 'ở '+description
        return ('trong ' if s['type']=='EXPLICIT' else 'trong số ')+description
    def capitalize(text):
        index=text.index('>')+1 if text.startswith('<a ') else 0
        return text[:index]+text[index:index+1].upper()+text[index+1:]
    def location(s,key='region',role='result'):
        if s['type']=='NEIGHBORS':
            return token(key,'quanh ',role,True)+person(s['cell'],key+'.anchor.'+s['cell'],'anchor')
        return among(s,region(s,key,role))
    kind=spec['type']
    def render_comparison():
        left=clues.regions.resolve(spec['left'],board);right=clues.regions.resolve(spec['right'],board)
        if len(left)==len(right)==1 and spec['op'] in ('=','!='):
            a=person(next(iter(left)),'left','a');b=person(next(iter(right)),'right','b')
            return a+' và '+b+(' hoặc cùng phạm tội, hoặc cùng vô tội.' if spec['op']=='=' else ': một người phạm tội, người kia vô tội.')
        words = {'=':'bằng', '!=':'khác', '<':'ít hơn', '<=':'không nhiều hơn',
                 '>':'nhiều hơn', '>=':'không ít hơn'}
        left=location(spec['left'],'left','a');right=location(spec['right'],'right','b')
        if spec['op'] in ('=','!='):
            return 'Số Tội phạm '+left+' và '+right+' '+('bằng nhau.' if spec['op']=='=' else 'khác nhau.')
        if spec['op'] in ('<','>'):
            return capitalize(left)+' có '+('ít' if spec['op']=='<' else 'nhiều')+' Tội phạm hơn '+right+'.'
        return 'Số Tội phạm '+left+' '+words[spec['op']]+' con số '+right+'.'
    def render_conditional():
        first = clue_text(spec['if'],board,clues,names,theme,_prefix+'if.',True).rstrip('.')
        second = clue_text(spec['then'],board,clues,names,theme,_prefix+'then.',True).rstrip('.')
        def lower_clause(text):
            for word in ('Trong','Không','Số','Tính','Nếu'):
                if text.startswith(word+' '):return word.lower()+text[len(word):]
            if text.startswith('<a '):
                i=text.index('>')+1
                if any(text[i:].startswith(word+' ') for word in ('Hàng','Cột','Những','Nhóm','Bốn','Riêng')):
                    return text[:i]+text[i].lower()+text[i+1:]
            return text
        if spec['if']['type']=='CONDITIONAL':first='('+first+')'
        if spec['then']['type']=='CONDITIONAL':second='('+second+')'
        return 'Nếu '+lower_clause(first)+' thì '+lower_clause(second)+'.'
    def render_fact():
        return person(spec['person'],'person','a')+' là '+token('result',STATUS_TEXT[spec['status']],spec['status'])+'.'
    def render_binary():
        return person(spec['a'],'a','a')+' và '+person(spec['b'],'b','b')+(' hoặc cùng phạm tội, hoặc cùng vô tội.' if kind=='SAME' else ': một người phạm tội, người kia vô tội.')
    def render_count():
        quant={'EXACTLY':'đúng','AT_LEAST':'ít nhất','AT_MOST':'nhiều nhất'}[kind]
        amount='có '+quant+' '+token('result',str(spec['k']),'value')+' '+token('result','Tội phạm','CRIMINAL')
        s=spec['region']
        if s['type']=='EXPLICIT' and len(s['cells'])==1:
            criminal=(kind in ('EXACTLY','AT_LEAST') and spec['k']==1)
            innocent=(kind in ('EXACTLY','AT_MOST') and spec['k']==0)
            if criminal or innocent:
                return token('region',names.get(s['cells'][0],s['cells'][0]),'result',True)+(' là Tội phạm.' if criminal else ' vô tội.')
        if spec['k']==0 and kind in ('EXACTLY','AT_MOST'):
            return 'Không có Tội phạm '+location(s)+'.'
        if _embedded:return location(s)+' '+amount+'.'
        if s['type']=='UNION' and clues.regions.resolve(s['left'],board) and clues.regions.resolve(s['right'],board):
            left=region(s['left'],'region.left','a');right=region(s['right'],'region.right','b')
            return 'Tính cả '+left+' lẫn '+right+', '+amount+'.'
        return capitalize(location(s))+', '+amount+'.'
    text=RuleText(board,clues,names,theme,_prefix,_embedded,token,person,region,location,
        lambda child,field:clue_text(child,board,clues,names,theme,_prefix+field+'.',True))
    custom=clues.handler(spec).wording(spec,text)
    if custom is not None:
        return custom
    renderer={'COMPARISON':render_comparison,'CONDITIONAL':render_conditional,
        'FACT':render_fact,'SAME':render_binary,'DIFFERENT':render_binary,
        'EXACTLY':render_count,'AT_LEAST':render_count,'AT_MOST':render_count}.get(kind)
    if renderer:
        return renderer()
    # Third-party registered clue types retain their own description.
    plain=clues.describe(spec,board)
    return escape(plain) if theme else plain


def clue_html(spec,board,clues,theme,names=None):
    return clue_text(spec,board,clues,names,theme)



from ..engine.clues import CluePart, clue_parts
