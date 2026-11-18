"""Run a repeatable rewards demonstration in a temporary database."""
from contextlib import closing

from seed import initialize
from main import balance, checkout


with closing(initialize(':memory:')) as db:
    customer_id = 12
    print('\nVICIOUS BISCUIT — REWARDS DEMO')
    print('Fictional classroom policy: $1 paid earns 1 point; 100 points saves $5.\n')
    checkout(db, 1, customer_id, [(1, 12)])
    print(f'1. Prior $120 purchase: customer now has {balance(db, customer_id)} points.')
    order, paid = checkout(db, 1, customer_id, [(1, 2), (6, 1)], redeem=True)
    print(f'2. New order #{order}: 2 sandwiches + 1 side = $25.00.')
    print(f'3. Redeem 100 points: $5.00 discount; simulated amount paid = ${paid / 100:.2f}.')
    print(f'4. Earn 20 new points: final balance = {balance(db, customer_id)} points.\n')
    print('Rewards history:')
    for kind, points in db.execute(
        '''SELECT transaction_type, points_change
           FROM RewardsTransaction WHERE customer_id = ? ORDER BY transaction_id''',
        (customer_id,),
    ):
        print(f'   {kind:8} {points:+} points')
    print('\nTrying another redemption with only 40 points...')
    try:
        checkout(db, 1, customer_id, [(1, 1)], redeem=True)
    except ValueError as error:
        print(f'Blocked correctly: {error}')
    print(f'Balance remains {balance(db, customer_id)} points. No incomplete order was saved.')
    print('\nDemo finished. The project database was not changed.\n')
