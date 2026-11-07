"""Run both in-house DPLL configurations on exactly the same six cases."""
import argparse
import csv
import json
from pathlib import Path
from time import perf_counter
from .engine.game import LogicAgent
from griductive.engine.game import check_uniqueness
from .engine.cnf import build_knowledge_base
from .engine.game import GameEngine
from griductive.engine.models import load_puzzle
from .engine.clues import clue_registry
from .engine.regions import region_registry
from .engine.sat import SolverTimeout

ROOT=Path(__file__).resolve().parents[1]


def run_case(path, heuristic, timeout=30.):
    registry=clue_registry(region_registry())
    puzzle=load_puzzle(path,registry)
    engine=GameEngine(puzzle,registry)
    agent=LogicAgent(registry,heuristic=heuristic,timeout=min(10.,timeout))
    start=perf_counter()
    queries=[]
    status='SOLVED'
    try:
        while not engine.solved:
            if perf_counter()-start >= timeout:
                raise SolverTimeout('Case time limit exceeded')
            cell,verdict=agent.next_verdict(engine.public_state())
            if cell is None:
                status=verdict
                break
            # The engine independently verifies each request, using the same
            # configuration as the agent for a fair configuration comparison.
            response=engine.submit(cell,verdict,heuristic=heuristic)
            queries.extend(response['queries'])
            if response['result']!='ACCEPTED':
                status=response['result']
                break
    except SolverTimeout:
        status='TIMEOUT'
    runtime=perf_counter()-start
    queries=agent.queries+queries
    kb=build_knowledge_base(engine.public_state(),registry)
    try:
        unique=check_uniqueness(puzzle,registry,heuristic,min(10.,timeout))
    except SolverTimeout:
        unique='TIMEOUT'
    result={
        'puzzle':puzzle.puzzle_id,'size':puzzle.board.size,'heuristic':heuristic,
        'status':status,'uniqueness':unique,'primary_variables':len(kb.primary),
        'auxiliary_variables':kb.auxiliary_count,'clauses':len(kb.clauses),
        'sat_calls':len(queries),'decisions':sum(q['decisions'] for q in queries),
        'propagations':sum(q['propagations'] for q in queries),
        'backtracks':sum(q['backtracks'] for q in queries),
        'steps':len(engine.trace),'runtime':runtime,
    }
    return result,engine.trace


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'output/experiments')
    parser.add_argument('--timeout',type=float,default=30.)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for path in sorted((ROOT/'puzzles').glob('case-*.json')):
        for heuristic in ('ordered','frequency'):
            result,trace=run_case(path,heuristic,args.timeout)
            rows.append(result)
            (args.output/f'{path.stem}-{heuristic}-trace.json').write_text(
                json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
            print(f"{result['puzzle']} {heuristic}: {result['status']} ({result['runtime']:.3f}s)",flush=True)
    (args.output/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    with (args.output/'results.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__=='__main__':
    main()
