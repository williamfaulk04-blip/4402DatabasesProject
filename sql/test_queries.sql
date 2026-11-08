-- 1. Line items for order 1 (cents).
SELECT oi.order_id, m.name, oi.quantity, oi.unit_price_cents, oi.quantity*oi.unit_price_cents AS line_total_cents
FROM OrderItem oi JOIN MenuItem m USING(menu_item_id) WHERE oi.order_id=1 ORDER BY m.menu_item_id;
-- 2. Daily completed sales (cents).
SELECT date(created_at) AS sale_date, COUNT(*) AS orders, SUM(paid_cents) AS sales_cents
FROM CustomerOrder GROUP BY date(created_at) ORDER BY sale_date;
-- 3. Units sold, including unsold menu items.
SELECT m.name, COALESCE(SUM(oi.quantity),0) AS units_sold FROM MenuItem m
LEFT JOIN OrderItem oi USING(menu_item_id) GROUP BY m.menu_item_id ORDER BY units_sold DESC,m.menu_item_id;
-- 4. Orders handled by each employee, including zero.
SELECT e.name, COUNT(o.order_id) AS orders_handled FROM Employee e
LEFT JOIN CustomerOrder o USING(employee_id) GROUP BY e.employee_id ORDER BY e.employee_id;
-- 5. All enrolled customers' point balances, including zero.
SELECT c.name, COALESCE(SUM(r.points_change),0) AS points_balance FROM Customer c
LEFT JOIN RewardsTransaction r USING(customer_id) GROUP BY c.customer_id ORDER BY c.customer_id;
