# AI Workflow

## Development loop

1. Run targeted unit tests.
2. Fix only the highest-impact failures.
3. Re-run the affected suite.
4. Expand to broader regression checks.

## Expectations

- Prefer deterministic service behavior over heuristic mock-only test coverage.
- Keep the backend and frontend scoped to the delivery requirements.
- Stop only when the verification command is green or the remaining gap is environment-only.
