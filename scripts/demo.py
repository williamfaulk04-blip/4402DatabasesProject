"""Run a repeatable rewards demonstration in a temporary database."""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from main import connect, checkout, balance, ROOT

with tempfile.TemporaryDirectory() as folder:
    db = connect(Path(folder) / 'demo.db')
    db.executescript((ROOT / 'sql/schema.sql').read_text())
    with db:
        db.execute("INSERT INTO Customer VALUES(1, 'Demo Customer')")
        db.execute("INSERT INTO Employee VALUES(1, 'Demo Cashier')")
        db.execute("INSERT INTO MenuItem VALUES(1, 'Demo Biscuit Sandwich', 'Entree', 1000, 1)")
        db.execute("INSERT INTO MenuItem VALUES(2, 'Demo Side', 'Side', 500, 1)")
    print('\nVICIOUS BISCUIT — REWARDS DEMO')
    print('Fictional classroom policy: $1 paid earns 1 point; 100 points saves $5.\n')
    checkout(db, 1, 1, [(1, 12)])
    print(f'1. Prior $120 purchase: customer now has {balance(db, 1)} points.')
    order, paid = checkout(db, 1, 1, [(1, 2), (2, 1)], redeem=True)
    print(f'2. New order #{order}: 2 sandwiches + 1 side = $25.00.')
    print(f'3. Redeem 100 points: $5.00 discount; simulated amount paid = ${paid / 100:.2f}.')
    print(f'4. Earn 20 new points: final balance = {balance(db, 1)} points.\n')
    print('Rewards history:')
    for kind, points in db.execute('SELECT transaction_type, points_change FROM RewardsTransaction ORDER BY transaction_id'):
        print(f'   {kind:8} {points:+} points')
    print('\nTrying another redemption with only 40 points...')
    try:
        checkout(db, 1, 1, [(1, 1)], redeem=True)
    except ValueError as error:
        print(f'Blocked correctly: {error}')
    print(f'Balance remains {balance(db, 1)} points. No incomplete order was saved.')
    print('\nDemo finished. The project database was not changed.\n')
    db.close()
