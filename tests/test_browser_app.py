"""HTTP integration checks for the browser sandbox; source data stays read-only."""
import hashlib
from html.parser import HTMLParser
import http.client
from pathlib import Path
import subprocess
import sys
import unittest
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]


class Forms(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.forms = []
        self.current = None
        self.select = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            self.current = {'action': a['action'], 'values': {}}
            self.forms.append(self.current)
        elif self.current is not None and tag == 'input' and 'name' in a:
            if a.get('type') != 'checkbox' or 'checked' in a:
                self.current['values'][a['name']] = a.get('value', 'on')
        elif self.current is not None and tag == 'select':
            self.select = a['name']
        elif self.select is not None and tag == 'option':
            v = self.current['values']
            if self.select not in v or 'selected' in a:
                v[self.select] = a.get('value', '')

    def handle_endtag(self, tag):
        if tag == 'form': self.current = None
        if tag == 'select': self.select = None

    def form(self, action, item=None):
        return next(f['values'] for f in self.forms if f['action'] == action
                    and (item is None or f['values'].get('item') == str(item)))


class BrowserAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = hashlib.sha256((ROOT/'data/restaurant.db').read_bytes()).digest()
        cls.process = subprocess.Popen(
            [sys.executable, '-u', str(ROOT/'scripts/local_app.py'), '--port', '0'],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        line = cls.process.stdout.readline()
        if 'http://127.0.0.1:' not in line:
            cls.process.terminate()
            raise RuntimeError('Browser sandbox failed to start: ' + line)
        cls.port = int(line.strip().rsplit(':', 1)[1])

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.communicate(timeout=10)
        assert hashlib.sha256((ROOT/'data/restaurant.db').read_bytes()).digest() == cls.original

    def request(self, path='/', values=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        connection.request('POST' if values is not None else 'GET', path,
                           urlencode(values) if values is not None else None, headers)
        response = connection.getresponse()
        status, location = response.status, response.getheader('Location')
        body = response.read().decode()
        connection.close()
        if status == 303:
            return self.request(location)
        return status, body

    def setUp(self):
        _, body = self.request()
        self.token = Forms(body).form('/reset')['token']
        self.post('/reset')

    def post(self, action, **values):
        status, body = self.request(action, {'token': self.token, **values})
        self.assertEqual(status, 200)
        return body

    def test_menu_create_update_delete(self):
        body = self.post('/menu-add', name='QA Side', category='Side', price_cents='450', available='1')
        self.assertIn('Menu item #9 added.', body)
        body = self.post('/menu-update', item='9', name='Updated Side', category='Special', price_cents='650', available='0')
        values = Forms(body).form('/menu-update', 9)
        self.assertEqual((values['name'], values['price_cents'], values['available']), ('Updated Side', '650', '0'))
        self.assertNotIn('Quantity for Updated Side', body)
        body = self.post('/menu-delete', item='9')
        self.assertIn('Menu item #9 deleted.', body)
        self.assertNotIn('Updated Side', body)

    def test_order_error_keeps_inputs_and_does_not_insert(self):
        body = self.post('/order', employee='2', customer='1', item_1='2', redeem='on')
        self.assertIn('Could not complete action: Redemption requires', body)
        values = Forms(body).form('/order')
        self.assertEqual((values['employee'], values['customer'], values['item_1'], values['redeem']), ('2','1','2','on'))
        self.assertIn('Completed orders<strong>32</strong>', body)

    def test_rewards_and_guest(self):
        body = self.post('/order', employee='1', customer='1', item_1='6')
        self.assertIn('Demo Customer 1 - 100 pts', body)
        body = self.post('/order', employee='1', customer='1', item_1='1', redeem='on')
        self.assertIn('Simulated payment: $5.00', body)
        self.assertIn('Demo Customer 1 - 5 pts', body)
        body = self.post('/order', employee='1', customer='', item_4='1')
        self.assertIn('Simulated payment: $2.50', body)
        self.assertIn('Demo Customer 1 - 5 pts', body)

    def test_history_protects_purchased_items(self):
        body = self.post('/menu-delete', item='1')
        self.assertIn('Mark it unavailable instead of deleting it.', body)
        body = self.post('/menu-update', item='1', name='Demo Biscuit Sandwich', category='Entree', price_cents='2000', available='1')
        # Query 1 preserves the price of order 1 despite the new menu price.
        self.assertIn('<td>1000</td><td>12000</td>', body)

    def test_validation_and_form_escaping(self):
        body = self.post('/menu-add', name='<QA & Side>', category='Side', price_cents='0', available='1')
        self.assertIn('Price must be positive integer cents', body)
        self.assertEqual(Forms(body).form('/menu-add')['name'], '<QA & Side>')
        self.assertNotIn('value="<QA & Side>"', body)
        body = self.post('/order', employee='1', item_1='-1')
        self.assertIn('Quantity must be between 0 and 100.', body)
        body = self.post('/order', employee='1')
        self.assertIn('An order needs at least one item', body)

    def test_enroll_reports_and_reset(self):
        body = self.post('/enroll', name='QA Customer')
        self.assertIn('QA Customer enrolled', body)
        self.assertIn('Rewards members<strong>13</strong>', body)
        for i in range(1,6): self.assertIn(f'<summary>Query {i}</summary>', body)
        body = self.post('/reset')
        self.assertNotIn('QA Customer', body)
        self.assertIn('Rewards members<strong>12</strong>', body)

    def test_missing_token_rejected(self):
        status, _ = self.request('/enroll', {'name':'Unauthorized QA'})
        self.assertEqual(status, 403)
        _, body = self.request()
        self.assertNotIn('Unauthorized QA', body)


if __name__ == '__main__':
    unittest.main()
