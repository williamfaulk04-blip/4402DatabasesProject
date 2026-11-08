# CSC4402 submission checklist

This maps the uploaded Project Description requirements to project files. The final report is a separate deliverable and is not generated here.

| Code requirement | Project evidence |
|---|---|
| Database relations and constraints | `data/restaurant.db`, `sql/schema.sql` |
| Populated database and generation script | Included database with 12 customers, 4 employees, 8 menu items, 32 orders, 63 line items, and 27 rewards entries; `scripts/seed.py` reproduces it. |
| Five executable test queries | `sql/test_queries.sql`; execute with `python src/main.py queries`. |
| Application interface source | `src/main.py` for persistent CLI operations; `scripts/local_app.py` for the temporary browser sandbox. |
| Detailed execution instructions | `README.md`, `docs/browser-testing.md`. |
| Test code | `tests/test_rewards.py`, `tests/test_browser_app.py`; run `python -m unittest discover -s tests -v`. |

## Before submitting the code ZIP

- Run all 12 tests and the five queries from the repository root.
- Include the populated `data/restaurant.db` as well as schema and generation source; submitting an empty schema alone is insufficient.
- Include `src`, `scripts`, `sql`, `tests`, `docs`, and `README.md` with their directory structure intact.
- Exclude `.git`, Python cache folders, and personal environment files. GitHub's Download ZIP is suitable after the intended changes have been merged.
- Extract the ZIP into a fresh directory and repeat the README commands.
- Do not use `scripts/seed.py --reset` on a database whose records you want to retain. The checked-in populated database already runs without reseeding.
- Confirm the actual deadline in Gradescope. The assignment's Fall 2026 header and printed 2024 deadline conflict.

## Remaining group-owned information

- Fill `docs/responsibilities.md` with the actual team roster, responsibilities, and contributions. Do not assign credit based on proposed roles alone.
- Prepare the separate report PDF with the enterprise description, E-R diagram, schema explanations, five queries and sample outcomes, interface illustrations and explanations, and participation details.
- Use single-column, single-spaced, Arial 11-point formatting, no more than eight pages, for that separate report.

Design diagrams are in `docs/diagrams`; schema explanations are in `docs/er-diagram.md`; enterprise and business rules are in `docs/scope.md`; baseline query outcomes are in `docs/sample-query-results.txt`.
