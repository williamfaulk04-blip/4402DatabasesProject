# Scope and business rules

## Enterprise
This project models ordering and loyalty rewards at a single Vicious Biscuit restaurant in Gonzales, Louisiana. A relational database connects menu items, staff, customers, purchases, and rewards, replacing disconnected records and supporting consistent totals and sales reporting. This is an educational model with synthetic data and a proposed rewards policy.

## Users and workflows
Staff enroll customers, view balances, create completed purchases, and redeem rewards. A manager adds, edits, or deletes unused menu items and runs reports. These are workflow descriptions, not implemented authentication roles. The terminal commands are intended for local classroom use and have no access controls.

## Boundaries
Included: menu management, optional customer enrollment, completed purchases, employee attribution, reward earning/redemption, and five reporting queries.
Excluded: payment processing, tax/tips, pending orders, refunds/cancellations, inventory, payroll, delivery, reward expiration, tiers, and authentication. The recorded paid amount is a simulated subtotal after rewards, not a processed payment.

## Rules
- An order has one employee, zero or one customer, and at least one item (enforced by checkout).
- Customers in this model are loyalty members. Guest orders have no customer and no reward transactions.
- Each item appears once per order; repeated input quantities are combined.
- Prices and monetary amounts are integer cents. Order items preserve the price at purchase.
- Each completed dollar paid after discount earns one point: paid_cents // 100.
- A member may redeem exactly 100 points for a 500-cent discount once per order, only if their balance is sufficient and subtotal is at least 500 cents.
- Earned points from the current order cannot fund that order's redemption.
- Points have no expiration. Balance is the sum of the member's reward transactions.
- Checkout inserts the order, line items, redemption, and earnings atomically. A write lock serializes balance checking and redemption.
- Reward entries are linked to the same customer as their order. Each order can have at most one earn and one redeem entry. Orders with zero earned points omit the earn entry.
- Purchased menu items cannot be deleted. Set availability to false to retire them.

## Five reporting questions
1. What are the line items and line totals for order 1?
2. What are the completed order totals by date?
3. Which menu items sold the most units?
4. How many orders did each employee handle?
5. What is each member's rewards balance?

## Enforcement boundary
Foreign keys, uniqueness, and checks enforce row-level integrity. The checkout function enforces a nonempty order, subtotal calculations, sufficient reward balance, availability, and reward eligibility. Direct SQL writes can bypass checkout rules; use the CLI for purchases. A production version would need stronger access controls and additional safeguards.
