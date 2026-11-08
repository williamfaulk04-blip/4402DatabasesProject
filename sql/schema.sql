PRAGMA foreign_keys = ON;
CREATE TABLE Customer (customer_id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(length(trim(name)) > 0));
CREATE TABLE Employee (employee_id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(length(trim(name)) > 0));
CREATE TABLE MenuItem (
 menu_item_id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(length(trim(name)) > 0),
 category TEXT NOT NULL, price_cents INTEGER NOT NULL CHECK(price_cents > 0),
 available INTEGER NOT NULL DEFAULT 1 CHECK(available IN (0,1))
);
CREATE TABLE CustomerOrder (
 order_id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES Customer(customer_id),
 employee_id INTEGER NOT NULL REFERENCES Employee(employee_id),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 subtotal_cents INTEGER NOT NULL CHECK(subtotal_cents > 0),
 discount_cents INTEGER NOT NULL CHECK(discount_cents IN (0,500)),
 paid_cents INTEGER NOT NULL CHECK(paid_cents >= 0 AND paid_cents = subtotal_cents-discount_cents),
 CHECK(discount_cents = 0 OR customer_id IS NOT NULL), UNIQUE(order_id, customer_id)
);
CREATE TABLE OrderItem (
 order_id INTEGER NOT NULL REFERENCES CustomerOrder(order_id),
 menu_item_id INTEGER NOT NULL REFERENCES MenuItem(menu_item_id),
 quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents > 0),
 PRIMARY KEY(order_id,menu_item_id)
);
CREATE TABLE RewardsTransaction (
 transaction_id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES Customer(customer_id),
 order_id INTEGER NOT NULL, points_change INTEGER NOT NULL,
 transaction_type TEXT NOT NULL CHECK(transaction_type IN ('earn','redeem')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CHECK((transaction_type='earn' AND points_change>0) OR (transaction_type='redeem' AND points_change=-100)),
 UNIQUE(order_id,transaction_type),
 FOREIGN KEY(order_id,customer_id) REFERENCES CustomerOrder(order_id,customer_id)
);
