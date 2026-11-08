# Vicious Biscuit restaurant database — CSC4402

A SQLite database project modeling a simplified restaurant in Gonzales, Louisiana. Menu items, customers, employees, and loyalty rules are fictional classroom examples. Deadline: December 1; confirm the submission time in Gradescope.

## Requirements
Python 3.10+ with SQLite support. No third-party Python packages are required. Run the commands below from the repository root in your IDE terminal or system terminal.

## Getting started
The populated `data/restaurant.db` is included. Explore it with:

```sh
python3 src/main.py menu
python3 src/main.py customers
python3 src/main.py employees
python3 src/main.py balance 1
python3 src/main.py queries
```

For a repeatable rewards demonstration using a temporary database:

```sh
python3 scripts/demo.py
```

To run the automated checks:

```sh
python3 -m unittest discover -s tests -v
```

## Updating records
These commands change the selected database. Back up your working copy before experimenting if you need to preserve it.

```sh
python3 src/main.py enroll "New Customer"
python3 src/main.py order --employee 1 --customer 1 --item 1:2
python3 src/main.py menu-add "Sample Side" "Side" 400
python3 src/main.py menu-update 1 --available 0
```

Use `python3 src/main.py --help` for commands. Specify another database with `python3 src/main.py --db /path/to/copy.db menu`. `menu-delete ID` deletes an unused menu item; referenced items must instead be marked unavailable. Prices and totals are integer cents.

An order completes immediately. Omit `--customer` for a guest purchase. Repeat `--item ID:QUANTITY` for multiple items. Add `--redeem` to exchange 100 existing points for a $5 discount on a subtotal of at least $5. Earn one point per whole dollar paid after discounts. The seeded customer 1 starts with 40 points, so must earn more before redeeming.

## Database setup and connections
Run `python3 scripts/seed.py` only if the database is missing. To deliberately discard current records and rebuild the deterministic sample dataset, run `python3 scripts/seed.py --reset`.

Teammates can open `data/restaurant.db` with any SQLite-compatible tool. Enable `PRAGMA foreign_keys = ON` on every connection. The DDL lives in `sql/schema.sql`; five executable reporting queries live in `sql/test_queries.sql`. The seed includes 32 completed orders.

Use `src/main.py`'s `checkout` function when recording purchases in Python: it validates quantities, availability, and reward eligibility and commits the purchase and rewards together. Direct SQL writes must preserve these same rules. See `docs/scope.md` for the enforcement boundary.

## Project structure
- `data/restaurant.db`: populated SQLite database.
- `sql/`: table definitions, constraints, and five reporting queries.
- `src/main.py`: database operations and terminal commands.
- `scripts/seed.py`: reproducible synthetic data generation.
- `scripts/demo.py`: temporary rewards demonstration.
- `tests/`: automated rewards and integrity checks.
- `docs/`: scope, E-R diagram, team responsibilities, and seeded query results.

## Team coordination
Review `docs/scope.md` and `docs/er-diagram.md` together before changing the schema. Replace the placeholders in `docs/responsibilities.md` with actual assignments and contributions. Run the checks before merging changes. Coordinate changes to the binary database file; prefer sharing schema and seed changes that teammates can reproduce.

The project still needs the group's final report, review of the course submission requirements, and completed participation details. The report limit is eight pages, single column, single-spaced, Arial 11 pt.

## Report diagrams
PNG images and editable SVG copies are in `docs/diagrams/`: `entity-relationship` and `relational-schema`. The E-R drawing uses compact entity boxes with attributes and relationship diamonds; participation counts are explained in its legend. The relational drawing follows `sql/schema.sql`, including the composite rewards foreign key.

The optional `scripts/draw_diagrams.py` renderer requires Pillow and Arial TrueType fonts (paths are set for macOS). These are only needed to regenerate the images, not to use the database or terminal commands.

## Biscuit Lab: local browser sandbox
Run from the repository root:

```sh
python3 scripts/local_app.py
```

Open http://127.0.0.1:8765 in your browser. The interface lets you browse menu items, customers, recent orders, rewards history, and the five reporting queries. You can enroll demo customers, place orders, and redeem points.

The source database is opened read-only and copied into memory. All browser changes affect only that temporary copy. **Reset demo** reloads the original data. Stopping the server with Ctrl+C discards all experiments. Tabs connected to the same server share one temporary session.

To try rewards, select Demo Customer 1 and buy six $10 sandwiches to raise the starting 40 points to 100. Then place another order with the redemption checkbox enabled.

No extra packages are required. If port 8765 is occupied, run `python3 scripts/local_app.py --port 8766` and open http://127.0.0.1:8766 instead. The server listens only on this computer.
