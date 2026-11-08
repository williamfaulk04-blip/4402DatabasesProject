"""Local browser sandbox. The source database is opened read-only."""
import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import secrets
import sqlite3
import sys
from urllib.parse import parse_qs, urlencode, urlsplit
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'src'))
from main import DEFAULT_DB, ROOT, checkout


def fresh_copy():
    memory = sqlite3.connect(':memory:')
    source = sqlite3.connect(DEFAULT_DB.as_uri() + '?mode=ro', uri=True)
    try:
        source.backup(memory)
    finally:
        source.close()
    memory.execute('PRAGMA foreign_keys=ON')
    return memory


def money(cents): return f'${cents / 100:,.2f}'
def e(value): return escape(str(value), quote=True)


class App(HTTPServer):
    def __init__(self, address):
        self.db = fresh_copy()
        self.token = secrets.token_urlsafe(32)
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def page(self, message='', values=None, action=''):
        db = self.server.db
        values = values or {}
        def value(name, default='', scope='order'):
            return values.get(name, [str(default)])[0] if action == scope else str(default)
        def selected(name, option, default='', scope='order'):
            return ' selected' if value(name, default, scope) == str(option) else ''
        token = f'<input type="hidden" name="token" value="{self.server.token}">'
        def form(action, content):
            return f'<form method="post" action="/{action}">{token}{content}</form>'
        customers = db.execute('SELECT c.customer_id,c.name,COALESCE(SUM(r.points_change),0) FROM Customer c LEFT JOIN RewardsTransaction r USING(customer_id) GROUP BY c.customer_id ORDER BY c.customer_id').fetchall()
        menu = db.execute('SELECT * FROM MenuItem ORDER BY menu_item_id').fetchall()
        employees = db.execute('SELECT * FROM Employee').fetchall()
        count, sales = db.execute('SELECT COUNT(*),COALESCE(SUM(paid_cents),0) FROM CustomerOrder').fetchone()
        options = '<option value=""' + selected('customer', '') + '>Guest - no rewards</option>' + ''.join(f'<option value="{i}"{selected("customer", i)}>{e(name)} - {points} pts</option>' for i,name,points in customers)
        employee_options = ''.join(f'<option value="{i}"{selected("employee", i, employees[0][0] if employees else "")}>{e(name)}</option>' for i,name in employees)
        cards = ''.join(f'<div class="menu-item"><div><strong>{e(name)}</strong><small>{e(category)} - {money(price)}</small></div><label class="qty">Quantity<input aria-label="Quantity for {e(name)}" type="number" name="item_{i}" min="0" max="100" value="{e(value(f"item_{i}", 0))}"></label></div>' for i,name,category,price,available in menu if available)
        customer_rows = ''.join(f'<tr><td>#{i}</td><td>{e(name)}</td><td><span class="points">{points} pts</span></td></tr>' for i,name,points in customers)
        orders = db.execute("SELECT o.order_id,COALESCE(c.name,'Guest'),o.subtotal_cents,o.discount_cents,o.paid_cents FROM CustomerOrder o LEFT JOIN Customer c USING(customer_id) ORDER BY o.order_id DESC LIMIT 12").fetchall()
        order_rows = ''.join(f'<tr><td>#{i}</td><td>{e(name)}</td><td>{money(sub)}</td><td>{money(discount)}</td><td>{money(paid)}</td></tr>' for i,name,sub,discount,paid in orders)
        history = db.execute('SELECT r.order_id,c.name,r.transaction_type,r.points_change FROM RewardsTransaction r JOIN Customer c USING(customer_id) ORDER BY transaction_id DESC LIMIT 15').fetchall()
        history_rows = ''.join(f'<tr><td>#{i}</td><td>{e(name)}</td><td>{kind}</td><td>{points:+}</td></tr>' for i,name,kind,points in history)
        redeem_checked = ' checked' if action == 'order' and 'redeem' in values else ''
        order_form = form('order', f'<div class="fields"><label>Customer<select name="customer">{options}</select></label><label>Handled by<select name="employee">{employee_options}</select></label></div><div class="menu">{cards}</div><label class="check"><input type="checkbox" name="redeem"{redeem_checked}> Redeem 100 points for $5 off</label><p class="hint">Minimum $5 subtotal. Earn 1 point per whole dollar paid after discounts.</p><button>Place demo order</button>')
        enroll = form('enroll',f'<label>Customer name<input name="name" value="{e(value("name", scope="enroll"))}" required maxlength="80" placeholder="e.g. Alex Demo"></label><button class="secondary">Enroll demo customer</button>')
        reset = form('reset','<button class="secondary">Reset demo</button>')
        def menu_fields(scope, item=None):
            defaults = item or ('', '', '', 1)
            name, category, price, available = defaults
            choices = ''.join(f'<option value="{i}"{selected("available", i, available, scope)}>{label}</option>' for i,label in [(1,'Available'),(0,'Unavailable')])
            return f'<div class="fields"><label>Item name<input name="name" required maxlength="80" value="{e(value("name", name, scope))}"></label><label>Category<input name="category" required maxlength="80" value="{e(value("category", category, scope))}"></label><label>Price (cents)<input type="number" name="price_cents" min="1" step="1" required value="{e(value("price_cents", price, scope))}"></label><label>Availability<select name="available">{choices}</select></label></div>'
        menu_add = form('menu-add', menu_fields('menu-add') + '<button>Add menu item</button>')
        menu_edits = []
        for i,name,category,price,available in menu:
            scope = f'menu-update:{i}'
            fields = f'<input type="hidden" name="item" value="{i}">' + menu_fields(scope, (name,category,price,available))
            update = form('menu-update', fields + f'<button>Save item #{i}</button>')
            delete = form('menu-delete', f'<input type="hidden" name="item" value="{i}"><button class="secondary">Delete item #{i}</button>')
            menu_edits.append(f'<details><summary>#{i} {e(name)} - {money(price)} - {"Available" if available else "Unavailable"}</summary>{update}{delete}</details>')
        menu_management = '<section><h2>Manage menu</h2><p class="hint">Prices are integer cents: 450 means $4.50. Delete only unused items; mark purchased items unavailable to keep order history.</p><h3>Add an item</h3>' + menu_add + '<h3>Edit or delete an item</h3>' + ''.join(menu_edits) + '</section>'
        queries = []
        for number, statement in enumerate((ROOT/'sql/test_queries.sql').read_text().split(';'),1):
            if not statement.strip(): continue
            cur = db.execute(statement)
            head = ''.join(f'<th>{e(col[0])}</th>' for col in cur.description)
            rows = ''.join('<tr>'+''.join(f'<td>{e(v)}</td>' for v in row)+'</tr>' for row in cur)
            queries.append(f'<details><summary>Query {number}</summary><div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div></details>')
        body = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Biscuit Lab - Local demo</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f7f3eb;color:#27291f;font:15px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}header,main{{max-width:1220px;margin:auto;padding:28px}}header{{display:flex;align-items:center;justify-content:space-between;gap:20px}}h1{{font-family:Georgia,serif;font-size:38px;margin:5px 0}}h2{{font-family:Georgia,serif;font-size:25px;margin:0 0 18px}}p{{line-height:1.5}}.eyebrow{{color:#697248;font-size:12px;font-weight:800;letter-spacing:2px}}.banner{{background:#e7eddd;padding:15px 20px;border-radius:12px;margin-bottom:22px;color:#35462a}}.stats{{display:flex;gap:15px;margin-bottom:24px}}.stat{{flex:1;background:#fffdf8;border:1px solid #e4ddcf;border-radius:14px;padding:20px}}.stat strong{{display:block;font-size:27px;margin-top:6px}}.layout{{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:24px}}.layout>div,section{{min-width:0}}section{{background:#fffdf8;border:1px solid #e4ddcf;border-radius:16px;padding:24px;margin-bottom:24px}}label{{display:block;font-weight:600;font-size:13px}}input,select{{display:block;width:100%;padding:11px;border:1px solid #c9c8ba;border-radius:7px;background:white;color:#27291f;margin-top:7px;font:inherit}}.fields{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.menu{{margin:18px 0}}.menu-item{{display:flex;justify-content:space-between;align-items:center;gap:10px;border-bottom:1px solid #ece6da;padding:12px 0}}small{{display:block;color:#6c6c60;margin-top:5px}}.qty{{width:74px;font-size:11px;color:#6c6c60}}.qty input{{padding:7px}}button{{background:#34492e;color:white;border:0;border-radius:8px;padding:12px 18px;font:600 14px inherit;cursor:pointer}}button:hover{{filter:brightness(1.12)}}.secondary{{background:#ece7db;color:#34412d}}.check{{display:flex;gap:10px;align-items:center}}.check input{{width:auto;margin:0}}.hint{{font-size:13px;color:#6c6c60}}.scroll{{overflow:auto}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:11px 8px;text-align:left;border-bottom:1px solid #ece6da;white-space:nowrap}}th{{font-size:11px;color:#6c6c60;text-transform:uppercase}}.points{{color:#426332;font-weight:700}}form>button{{margin-top:12px}}.notice{{background:#fff0c6;border:1px solid #d9be68;padding:16px;border-radius:10px;margin-bottom:22px}}summary{{padding:14px 0;cursor:pointer;font-weight:600}}footer{{padding:0 28px 28px;color:#6c6c60;font-size:12px;max-width:1220px;margin:auto}}@media(max-width:850px){{.layout{{grid-template-columns:1fr}}header,main{{padding:18px}}h1{{font-size:30px}}.fields{{grid-template-columns:1fr}}.stats{{flex-wrap:wrap}}}}
</style><header><div><span class="eyebrow">VICIOUS BISCUIT - CLASSROOM SANDBOX</span><h1>Biscuit Lab</h1><span>Orders, customers & a little reward.</span></div>{reset}</header><main><div class="banner"><strong>Temporary demo mode.</strong> Changes live only in memory. Your original database stays untouched. Reset or restart to discard experiments.</div>{f'<div class="notice" role="status">{e(message)}</div>' if message else ''}<div class="stats"><div class="stat">Completed orders<strong>{count}</strong></div><div class="stat">Simulated sales<strong>{money(sales)}</strong></div><div class="stat">Rewards members<strong>{len(customers)}</strong></div></div><div class="layout"><div><section><h2>Build an order</h2>{order_form}</section><section><h2>Latest orders</h2><div class="scroll"><table><tr><th>Order</th><th>Customer</th><th>Subtotal</th><th>Discount</th><th>Paid</th></tr>{order_rows}</table></div></section></div><div><section><h2>Rewards members</h2><p class="hint">Start with Demo Customer 1 at 40 points. A $60 purchase earns the remaining 60 points needed to try a redemption.</p><div class="scroll"><table><tr><th>ID</th><th>Customer</th><th>Balance</th></tr>{customer_rows}</table></div><hr style="border:0;border-top:1px solid #ece6da;margin:22px 0">{enroll}</section><section><h2>Rewards activity</h2><div class="scroll"><table><tr><th>Order</th><th>Customer</th><th>Type</th><th>Points</th></tr>{history_rows}</table></div></section></div></div>{menu_management}<section><h2>Explore the five report queries</h2><p class="hint">Results reflect your current demo session. Monetary columns labeled "cents" use integer cents.</p>{''.join(queries)}</section></main><footer>Fictional menu and loyalty policy for CSC4402. No real payments. Local to this computer.</footer></html>'''
        data = body.encode()
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        if urlsplit(self.path).path != '/': self.send_error(404); return
        self.page(parse_qs(urlsplit(self.path).query).get('message',[''])[0])

    def do_POST(self):
        length=int(self.headers.get('Content-Length','0'))
        if length>16384: self.send_error(413); return
        values=parse_qs(self.rfile.read(length).decode())
        if not secrets.compare_digest(values.get('token',[''])[0],self.server.token):
            self.send_error(403); return
        db=self.server.db
        try:
            if self.path=='/reset':
                replacement=fresh_copy(); db.close(); self.server.db=replacement
                message='Demo reset. Original data loaded into a fresh temporary copy.'
            elif self.path=='/enroll':
                name=values.get('name',[''])[0].strip()
                if not name or len(name)>80: raise ValueError('Enter a name of 1-80 characters.')
                with db: db.execute('INSERT INTO Customer(name) VALUES(?)',(name,))
                message=f'{name} enrolled in the demo.'
            elif self.path in ('/menu-add', '/menu-update'):
                name=values.get('name',[''])[0].strip()
                category=values.get('category',[''])[0].strip()
                if not name or len(name)>80 or not category or len(category)>80:
                    raise ValueError('Item name and category must each contain 1-80 characters.')
                price=int(values.get('price_cents',[''])[0])
                available=int(values.get('available',['1'])[0])
                if price<=0 or available not in (0,1):
                    raise ValueError('Price must be positive integer cents; availability must be 0 or 1.')
                with db:
                    if self.path=='/menu-add':
                        item=db.execute('INSERT INTO MenuItem(name,category,price_cents,available) VALUES(?,?,?,?)',(name,category,price,available)).lastrowid
                        message=f'Menu item #{item} added.'
                    else:
                        item=int(values.get('item',[''])[0])
                        result=db.execute('UPDATE MenuItem SET name=?,category=?,price_cents=?,available=? WHERE menu_item_id=?',(name,category,price,available,item))
                        if not result.rowcount: raise ValueError('Menu item does not exist.')
                        message=f'Menu item #{item} updated.'
            elif self.path=='/menu-delete':
                item=int(values.get('item',[''])[0])
                with db:
                    if db.execute('SELECT 1 FROM OrderItem WHERE menu_item_id=?',(item,)).fetchone():
                        raise ValueError('This item has order history. Mark it unavailable instead of deleting it.')
                    result=db.execute('DELETE FROM MenuItem WHERE menu_item_id=?',(item,))
                    if not result.rowcount: raise ValueError('Menu item does not exist.')
                message=f'Menu item #{item} deleted.'
            elif self.path=='/order':
                items=[]
                for key,value in values.items():
                    if key.startswith('item_'):
                        quantity=int(value[0])
                        if quantity<0 or quantity>100: raise ValueError('Quantity must be between 0 and 100.')
                        if quantity: items.append((int(key[5:]),quantity))
                customer=values.get('customer',[''])[0]
                order,paid=checkout(db,int(values['employee'][0]),int(customer) if customer else None,items,'redeem' in values)
                message=f'Demo order #{order} completed. Simulated payment: {money(paid)}. Rewards updated.'
            else: self.send_error(404); return
        except (ValueError,KeyError,sqlite3.Error) as error:
            message=f'Could not complete action: {error}'
            action=self.path.lstrip('/')
            if action=='menu-update': action += ':' + values.get('item',[''])[0]
            self.page(message, values, action)
            return
        self.send_response(303); self.send_header('Location','/?'+urlencode({'message':message})); self.end_headers()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    server=App(('127.0.0.1',args.port))
    print(f'Biscuit Lab running at http://127.0.0.1:{server.server_port}',flush=True)
    print('Original database is read-only. Press Ctrl+C to stop and discard demo changes.',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close(); server.db.close()
