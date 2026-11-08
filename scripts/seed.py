"""Build deterministic, entirely synthetic demonstration records."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from main import ROOT, DEFAULT_DB, connect, checkout


def initialize(path):
    db=connect(path)
    db.executescript((ROOT/'sql/schema.sql').read_text())
    with db:
        db.executemany('INSERT INTO Customer(name) VALUES(?)',[(f'Demo Customer {i}',) for i in range(1,13)])
        db.executemany('INSERT INTO Employee(name) VALUES(?)',[(f'Demo Employee {i}',) for i in range(1,5)])
        db.executemany('INSERT INTO MenuItem(name,category,price_cents) VALUES(?,?,?)',[
            ('Demo Biscuit Sandwich','Entree',1000),('Demo Breakfast Plate','Entree',1500),
            ('Demo Coffee','Drink',300),('Demo Tea','Drink',250),('Demo Side Potatoes','Side',400),
            ('Demo Fruit Cup','Side',500),('Demo Sweet Biscuit','Dessert',600),('Demo Juice','Drink',350)])
    # Member 1 earns 120, redeems 100 on a $25 purchase, then earns 20.
    checkout(db,1,1,[(1,12)],timestamp='2026-11-01 09:00:00')
    checkout(db,2,1,[(1,1),(2,1)],True,timestamp='2026-11-02 09:00:00')
    for i in range(30):
        checkout(db,1+i%3,None if i%5==0 else 2+i%10,
                 [(1+i%7,1+i%3),(8,1)],timestamp=f'2026-11-{3+i%5:02d} 10:00:00')
    return db


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reset',action='store_true',help='Delete and rebuild the demonstration database')
    args=parser.parse_args()
    if DEFAULT_DB.exists():
        if not args.reset: parser.error('Database already exists; use --reset only to discard it')
        DEFAULT_DB.unlink()
    DEFAULT_DB.parent.mkdir(exist_ok=True)
    db=initialize(DEFAULT_DB)
    db.close()
    print(f'Created {DEFAULT_DB} with 32 completed orders.')
