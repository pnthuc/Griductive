# Current application design

The active interface is Pixel 2D with the selected bright coastal direction.
Ivory cards sit on a powder-blue seaside backdrop. Navy display type, apricot
actions and marine clue outlines provide the hierarchy. Profession scenes sit
below labels and use aspect-preserving fitting. Card sizes remain uniform.

The Python engine owns hidden puzzle data, validates verdicts against public
knowledge, encodes clues automatically and uses its own DPLL implementation.
LogicAgent receives immutable public state only. Both six core clue templates
and the confirmed region/comparison/conditional extensions are supported.

The UI displays the entire board, keeps equal card sizes and scrolls long clue
text inside each card. Highlight parts share semantic keys with clue wording.
The solver panel appears on request and exposes step/start/pause/trace export.
Its journal view lives in `griductive/ui/journal.py`: accepted verdicts appear
as individual entries, with expandable clue and SAT verification details. The
view reads the existing engine trace; JSON export retains every original field.
Closing the journal pauses playback. Wrapped details resize within the scroll
list, and new entries preserve the position of someone reading older steps.
All six cases are available through the Tools menu. No graphics toggle remains.

Pixel art is stored in one 25-row atlas. Each character has seven slots and
transparent padding. Regenerated poses use one common uniform scale per person.

The engine uses six modules: models.py (data and JSON), regions.py (region
definitions), clues.py (clue definitions and references), cnf.py (encoding),
sat.py (DPLL) and game.py (agent, session and uniqueness). Named rule classes
are registered with decorators; metadata supplies validation and highlights.
Optional wording methods receive plain/HTML helpers from presentation without
importing Qt. The compiler uses one auxiliary allocator per KB. Independent
evaluators remain separate. See EXTENDING.md for executable examples.

The GUI controller serializes requests to one worker. Each operation uses an
isolated tentative session; cancellation discards it even if the result was
already calculated but not accepted by the UI. Generation and request IDs reject
stale deliveries. JSON loading/structural validation remains synchronous and
bounded to the small puzzle format; all gameplay SAT calls and KB metrics run
on the worker. The core APIs remain synchronous for CLI/tests/benchmarks.

Gameplay never guesses: a verdict requires the opposite assumption to be UNSAT
under a consistent public KB. Rejected and cancelled requests do not reveal
cards. Full-clue uniqueness checking is an offline operation and blocks only
primary variables; hidden clues are never used by Hint or the gameplay agent.

COMPARISON compares Criminal counts with =, !=, <, <=, > and >=. Overlapping
cells count once in each region. CONDITIONAL is material implication with
arbitrary supported clues on either side. Regions additionally support CORNERS,
UNION, INTERSECTION and DIFFERENCE. All active clues are true regardless of
their owner's status.


## Approved simplification: rule registration

The user approved a smaller engine and easier clue/region registration. Keep
models.py (data and JSON loading), regions.py, clues.py (including semantic
references), cnf.py, sat.py and game.py (agent, session, uniqueness).

Use named rule classes and @register_region / @register_clue decorators.
A definition keeps validation, direct evaluation, expression compilation and
reference metadata together. Registries also accept local decorators so tests
and custom sessions can add rules without changing the default game catalog.
Declared person/region/child fields supply shared validation and highlights.
An optional wording method receives a plain-Python text context and can provide
linked Vietnamese text in the same rule definition, without changing the GUI.

Always preserve: JSON schema and puzzle files, public/private separation,
independent evaluators, deterministic deduction, shared CNF allocation, worker
cancellation, trace export, current Vietnamese wording and visual behavior.
No new runtime dependencies, report/video work, puzzle changes or SAT changes.

Verification: .venv/Scripts/python.exe -B -m unittest discover -s tests;
.venv/Scripts/python.exe -B -m griductive.experiments.
Add meaningful integration coverage registering a new region and clue through
the new API, including conditional composition, CNF/evaluator equivalence,
validation, text/HTML reference keys, isolated catalogs and duplicate errors.
Migrate callers directly and remove old internal modules after checks pass.

## Python web deployment

The user requires web UI source and game logic to be Python. Dash components,
style dictionaries and Python callbacks form the browser UI in web.py; there
are no handwritten HTML, CSS or JavaScript files. Framework-generated browser
code is served by Dash. The existing desktop remains available.

web_game.py reconstructs each request from the puzzle and public move history,
re-verifying every move through GameEngine.submit before revealing its clue.
No process-global mutable sessions, shared player state or trusted browser
verdicts. Browser state holds only accepted moves and selections; bundled
solutions and unrevealed clues stay server-side. A user-uploaded puzzle stays
in that user's tab and is validated through the existing loader.

Vercel runs the Flask server exposed in app.py, with only Dash/Flask runtime
dependencies. Shared desktop/web images live in public/images and are deployed
directly to the CDN; no custom build step or duplicate image files are needed.
Each server operation has a 45-second cooperative deadline inside a 60-second
function. Hint/rejection/timeout preserve progress. Auto Solve requests one
proved move at a time; journal export contains the real reconstructed trace.
Uploaded JSON is limited to 128 KB. Test stateless replay, forged history,
hidden-data boundaries, real Dash callbacks and the existing desktop suite.
