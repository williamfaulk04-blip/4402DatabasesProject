"""Local classroom CLI. All monetary values are integer cents."""
import argparse
from collections import Counter
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / 'data/restaurant.db'


def connect(path=DEFAULT_DB):
    db = sqlite3.connect(path)
    db.execute('PRAGMA foreign_keys=ON')
    return db


def balance(db, customer):
    if not db.execute('SELECT 1 FROM Customer WHERE customer_id=?', (customer,)).fetchone():
        raise ValueError('Customer does not exist')
    return db.execute('SELECT COALESCE(SUM(points_change),0) FROM RewardsTransaction WHERE customer_id=?', (customer,)).fetchone()[0]


def checkout(db, employee, customer, items, redeem=False, timestamp=None):
    quantities = Counter()
    for item, quantity in items:
        if quantity <= 0:
            raise ValueError('Quantities must be positive')
        quantities[item] += quantity
    if not quantities:
        raise ValueError('An order needs at least one item')
    db.execute('BEGIN IMMEDIATE')
    try:
        if not db.execute('SELECT 1 FROM Employee WHERE employee_id=?', (employee,)).fetchone():
            raise ValueError('Employee does not exist')
        points = balance(db, customer) if customer is not None else 0
        lines = []
        for item, quantity in quantities.items():
            row = db.execute('SELECT price_cents FROM MenuItem WHERE menu_item_id=? AND available=1', (item,)).fetchone()
            if row is None:
                raise ValueError(f'Menu item {item} is missing or unavailable')
            lines.append((item, quantity, row[0]))
        subtotal = sum(qty * price for _, qty, price in lines)
        if redeem and (customer is None or points < 100 or subtotal < 500):
            raise ValueError('Redemption requires a member with 100 points and a subtotal of at least $5')
        discount = 500 if redeem else 0
        paid = subtotal - discount
        order = db.execute('INSERT INTO CustomerOrder(customer_id,employee_id,created_at,subtotal_cents,discount_cents,paid_cents) VALUES(?,?,COALESCE(?,CURRENT_TIMESTAMP),?,?,?)', (customer,employee,timestamp,subtotal,discount,paid)).lastrowid
        db.executemany('INSERT INTO OrderItem VALUES(?,?,?,?)', [(order,*line) for line in lines])
        if customer is not None:
            for kind, change in [('redeem',-100 if redeem else 0), ('earn',paid//100)]:
                if change:
                    db.execute('INSERT INTO RewardsTransaction(customer_id,order_id,points_change,transaction_type,created_at) VALUES(?,?,?,?,COALESCE(?,CURRENT_TIMESTAMP))', (customer,order,change,kind,timestamp))
        db.commit()
        return order, paid
    except Exception:
        db.rollback()
        raise


def print_rows(cursor):
    print(' | '.join(col[0] for col in cursor.description))
    for row in cursor:
        print(' | '.join(str(value) for value in row))


def queries(db):
    for i, statement in enumerate((ROOT/'sql/test_queries.sql').read_text().split(';')):
        if statement.strip():
            print(f'Query {i+1}')
            print_rows(db.execute(statement))
            print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['menu','customers','employees','queries']:
        sub.add_parser(name)
    sub.add_parser('enroll').add_argument('name')
    sub.add_parser('balance').add_argument('customer',type=int)
    add = sub.add_parser('menu-add')
    add.add_argument('name'); add.add_argument('category'); add.add_argument('price_cents',type=int)
    update = sub.add_parser('menu-update')
    update.add_argument('item',type=int); update.add_argument('--price-cents',type=int)
    update.add_argument('--available',type=int,choices=[0,1])
    sub.add_parser('menu-delete').add_argument('item',type=int)
    order = sub.add_parser('order')
    order.add_argument('--employee',type=int,required=True)
    order.add_argument('--customer',type=int)
    order.add_argument('--item',action='append',required=True,help='ID:QUANTITY; repeat for more items')
    order.add_argument('--redeem',action='store_true')
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error('Database not found. Run python3 scripts/seed.py first.')
    db = connect(args.db)
    try:
        with db:
            if args.command in ['menu','customers','employees']:
                table = {'menu':'MenuItem','customers':'Customer','employees':'Employee'}[args.command]
                print_rows(db.execute(f'SELECT * FROM {table} ORDER BY 1'))
            elif args.command == 'enroll':
                result = db.execute('INSERT INTO Customer(name) VALUES(?)',(args.name,))
                print(f'Enrolled customer {result.lastrowid}')
            elif args.command == 'balance':
                print(f'{balance(db,args.customer)} points')
            elif args.command == 'menu-add':
                result = db.execute('INSERT INTO MenuItem(name,category,price_cents) VALUES(?,?,?)',(args.name,args.category,args.price_cents))
                print(f'Created menu item {result.lastrowid}')
            elif args.command == 'menu-update':
                if args.price_cents is None and args.available is None:
                    raise ValueError('Provide --price-cents or --available')
                result = db.execute('UPDATE MenuItem SET price_cents=COALESCE(?,price_cents),available=COALESCE(?,available) WHERE menu_item_id=?',(args.price_cents,args.available,args.item))
                if not result.rowcount: raise ValueError('Menu item does not exist')
                print('Menu item updated')
            elif args.command == 'menu-delete':
                result = db.execute('DELETE FROM MenuItem WHERE menu_item_id=?',(args.item,))
                if not result.rowcount: raise ValueError('Menu item does not exist')
                print('Menu item deleted')
            elif args.command == 'queries':
                queries(db)
            elif args.command == 'order':
                try:
                    items = [tuple(map(int, value.split(':'))) for value in args.item]
                    if any(len(pair)!=2 for pair in items): raise ValueError()
                except ValueError:
                    raise ValueError('Each --item must be ID:QUANTITY using integers')
                order_id, paid = checkout(db,args.employee,args.customer,items,args.redeem)
                print(f'Order {order_id} completed; paid ${paid/100:.2f}')
    except (ValueError,sqlite3.Error) as error:
        parser.exit(1,f'Error: {error}\n')
    finally:
        db.close()


if __name__ == '__main__':
    main()
