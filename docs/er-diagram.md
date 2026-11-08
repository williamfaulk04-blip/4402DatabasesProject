# E-R diagram

```mermaid
erDiagram
    CUSTOMER o|--o{ CUSTOMER_ORDER : places
    EMPLOYEE ||--o{ CUSTOMER_ORDER : handles
    CUSTOMER_ORDER ||--|{ ORDER_ITEM : contains
    MENU_ITEM ||--o{ ORDER_ITEM : identifies
    CUSTOMER ||--o{ REWARDS_TRANSACTION : owns
    CUSTOMER_ORDER ||--o{ REWARDS_TRANSACTION : generates
    CUSTOMER {
        integer customer_id PK
        text name
    }
    EMPLOYEE {
        integer employee_id PK
        text name
    }
    MENU_ITEM {
        integer menu_item_id PK
        text name
        text category
        integer price_cents
        integer available
    }
    CUSTOMER_ORDER {
        integer order_id PK
        integer customer_id FK "nullable for guests"
        integer employee_id FK
        text created_at
        integer subtotal_cents
        integer discount_cents
        integer paid_cents
    }
    ORDER_ITEM {
        integer order_id PK,FK
        integer menu_item_id PK,FK
        integer quantity
        integer unit_price_cents
    }
    REWARDS_TRANSACTION {
        integer transaction_id PK
        integer customer_id FK
        integer order_id FK
        integer points_change
        text transaction_type
        text created_at
    }
```

## Relational schema notes
`Customer` stores enrolled members; names need not be unique. `Employee` identifies the staff member responsible for a purchase. `MenuItem` stores the current offering. `CustomerOrder` stores one completed purchase and its totals. `OrderItem` resolves the many-to-many relationship between orders and menu items and preserves historical prices. `RewardsTransaction` stores an append-only history through the checkout function; its signed entries determine balances.

`OrderItem` has composite primary key `(order_id, menu_item_id)`. Rewards have a unique `(order_id, transaction_type)` pair and a composite foreign key `(order_id, customer_id)` to the order, preventing rewards being assigned to a different customer. The schema includes the corresponding unique parent key. The one-or-more item cardinality is enforced by the checkout function.
