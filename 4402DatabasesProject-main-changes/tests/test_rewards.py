import sqlite3
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from main import connect, checkout, balance, ROOT


class RewardsTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(':memory:')
        self.db.executescript((ROOT/'sql/schema.sql').read_text())
        with self.db:
            self.db.executemany('INSERT INTO Customer VALUES(?,?)',[(1,'A'),(2,'B')])
            self.db.execute("INSERT INTO Employee VALUES(1,'Staff')")
            self.db.executemany('INSERT INTO MenuItem VALUES(?,?,?,?,?)',[(1,'Biscuit','Food',1000,1),(2,'Tea','Drink',250,1)])

    def tearDown(self): self.db.close()

    def test_earn_redeem_and_price_history(self):
        checkout(self.db,1,1,[(1,12)])
        self.assertEqual(balance(self.db,1),120)
        order,paid=checkout(self.db,1,1,[(1,2),(2,2)],True)
        self.assertEqual(paid,2000)
        self.assertEqual(balance(self.db,1),40)
        with self.db: self.db.execute('UPDATE MenuItem SET price_cents=2000 WHERE menu_item_id=1')
        self.assertEqual(self.db.execute('SELECT unit_price_cents FROM OrderItem WHERE order_id=? AND menu_item_id=1',(order,)).fetchone()[0],1000)

    def test_insufficient_balance_leaves_no_order(self):
        with self.assertRaises(ValueError): checkout(self.db,1,1,[(1,1)],True)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM CustomerOrder').fetchone()[0],0)
        self.assertEqual(balance(self.db,1),0)

    def test_guest_and_fractional_dollars(self):
        checkout(self.db,1,None,[(1,1)])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM RewardsTransaction').fetchone()[0],0)
        checkout(self.db,1,1,[(2,1)])
        self.assertEqual(balance(self.db,1),2)

    def test_invalid_and_unavailable_items(self):
        for items in [[],[(1,0)],[(99,1)]]:
            with self.assertRaises(ValueError): checkout(self.db,1,1,items)
        with self.db: self.db.execute('UPDATE MenuItem SET available=0 WHERE menu_item_id=1')
        with self.assertRaises(ValueError): checkout(self.db,1,1,[(1,1)])

    def test_constraints_and_transaction_rollback(self):
        order,_=checkout(self.db,1,1,[(1,1)])
        with self.assertRaises(sqlite3.IntegrityError), self.db:
            self.db.execute("INSERT INTO RewardsTransaction(customer_id,order_id,points_change,transaction_type) VALUES(2,?,-100,'redeem')",(order,))
        with self.assertRaises(sqlite3.IntegrityError), self.db:
            self.db.execute("INSERT INTO RewardsTransaction(customer_id,order_id,points_change,transaction_type) VALUES(1,?,10,'earn')",(order,))
        # Inject failure after order insertion to ensure all checkout writes roll back.
        self.db.execute("CREATE TRIGGER fail_reward BEFORE INSERT ON RewardsTransaction BEGIN SELECT RAISE(ABORT,'test failure'); END")
        with self.assertRaises(sqlite3.IntegrityError): checkout(self.db,1,1,[(1,1)])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM CustomerOrder').fetchone()[0],1)
        self.assertEqual(balance(self.db,1),10)


if __name__=='__main__': unittest.main()
