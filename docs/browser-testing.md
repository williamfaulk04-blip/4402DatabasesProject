# Browser walkthrough

Start `python scripts/local_app.py` from the repository root on Windows (`python3` on macOS/Linux). Open http://127.0.0.1:8765. All changes affect the in-memory demo only. Reset before beginning.

| Action | Expected result |
|---|---|
| Open the app | 32 completed orders, $663.50 sales, 12 members; Demo Customer 1 has 40 points. |
| Enroll a named demo customer | Member count becomes 13; new customer has zero points. |
| Select Demo Customer 1 and employee 2, enter 2 sandwiches, check redemption, submit | Insufficient points error; no new order; customer, employee, quantity, and checkbox stay selected. |
| Uncheck redemption, change sandwiches to 6, submit | $60 purchase; customer 1 reaches 100 points; order count increases by one. |
| Select customer 1, enter 1 sandwich, check redemption, submit | $5 paid after discount; balance becomes 5 points. |
| Submit with all quantities zero | Empty-order error; no order or rewards saved. |
| Choose Guest, enter 1 tea, leave redemption unchecked, submit | $2.50 purchase; member balances unchanged. |
| In Manage menu add QA Side, category Side, price 450, Available | New item appears at $4.50 in both menu management and ordering. |
| Expand QA Side; change price to 650 and availability to Unavailable; save | Menu entry shows $6.50 and Unavailable; item disappears from ordering. |
| Expand QA Side and delete it before purchasing it | Item is removed. |
| Expand seeded sandwich and attempt deletion | Clear message directs you to mark it unavailable; purchase history remains. |
| Edit seeded sandwich price | Existing order line prices do not change; new purchases use the new price. |
| Expand Query 1 through Query 5 | Tables render; sales, quantity, employee, and rewards reports reflect the current demo session. |
| Click Reset demo | Original 32 orders, $663.50 sales, 12 members, menu prices, and 40-point customer 1 balance return. |

For an invalid price or missing required field, the browser may block submission before a request is sent. Server-side validation is also covered by `tests/test_browser_app.py`.

## Automated verification

```sh
python -m unittest discover -s tests -v
python src/main.py queries
python scripts/demo.py
```

The suite contains 12 tests. Five cover checkout and database integrity; seven cover the actual HTTP sandbox. Compare query output against `docs/sample-query-results.txt` using the original seeded database.

## Interfaces and user tasks

Staff use customer enrollment and checkout, including optional rewards redemption. Managers use menu maintenance and reporting. These are task groupings; the local sandbox does not implement login or enforce separate user roles. CLI menu commands are an alternative interface that writes to the chosen on-disk database. Browser operations remain temporary.
