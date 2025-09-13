import unittest
import json
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api_metrics_flask import metrics_bp
from main import app
from backend.database import metrics_collection, option_chain_collection

class TestMetricsAPIExtended(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Clear test data in MongoDB collections
        metrics_collection.delete_many({})
        option_chain_collection.delete_many({})

        # Insert sample option chain data
        self.instrument_key = "TEST_INSTRUMENT"
        self.expiry_date = "2025-09-16"
        self.underlying_spot_price = 100.0
        self.option_chain_data = [
            {
                'strike_price': 95,
                'call_options': {'market_data': {'oi': 10, 'volume': 100, 'iv': 0.2, 'bid_qty': 5, 'ask_qty': 3, 'bid_price': 1, 'ask_price': 2}},
                'put_options': {'market_data': {'oi': 20, 'volume': 200, 'iv': 0.3, 'bid_qty': 7, 'ask_qty': 4, 'bid_price': 1.5, 'ask_price': 2.5}}
            },
            {
                'strike_price': 100,
                'call_options': {'market_data': {'oi': 15, 'volume': 150, 'iv': 0.25, 'bid_qty': 6, 'ask_qty': 2, 'bid_price': 1.1, 'ask_price': 2.1}},
                'put_options': {'market_data': {'oi': 25, 'volume': 250, 'iv': 0.35, 'bid_qty': 8, 'ask_qty': 5, 'bid_price': 1.6, 'ask_price': 2.6}}
            },
            {
                'strike_price': 105,
                'call_options': {'market_data': {'oi': 20, 'volume': 200, 'iv': 0.3, 'bid_qty': 7, 'ask_qty': 3, 'bid_price': 1.2, 'ask_price': 2.2}},
                'put_options': {'market_data': {'oi': 30, 'volume': 300, 'iv': 0.4, 'bid_qty': 9, 'ask_qty': 6, 'bid_price': 1.7, 'ask_price': 2.7}}
            }
        ]

        option_chain_collection.insert_one({
            'instrument_key': self.instrument_key,
            'expiry_date': self.expiry_date,
            'underlying_spot_price': self.underlying_spot_price,
            'data': self.option_chain_data,
            'fetched_at': datetime.now(timezone.utc)
        })

    def test_valid_metrics_calculation(self):
        payload = {
            "instrument_key": self.instrument_key,
            "expiry_date": self.expiry_date
        }
        response = self.app.post('/api/metrics/calculate_metrics', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn('current_price', data)
        self.assertIn('totals', data)
        self.assertIn('difference', data)
        self.assertIn('difference_percent', data)
        self.assertIn('bid_ask_imbalance', data)
        self.assertIn('bid_ask_spread', data)

    def test_edge_case_empty_option_chain(self):
        # Insert empty option chain data for a new instrument
        option_chain_collection.insert_one({
            'instrument_key': 'EMPTY_INSTRUMENT',
            'expiry_date': '2025-09-16',
            'underlying_spot_price': 100.0,
            'data': [],
            'fetched_at': datetime.now(timezone.utc)
        })
        payload = {
            "instrument_key": "EMPTY_INSTRUMENT",
            "expiry_date": "2025-09-16"
        }
        response = self.app.post('/api/metrics/calculate_metrics', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        # Totals and other metrics should be zero or empty
        self.assertEqual(data['totals']['call'], {})
        self.assertEqual(data['totals']['put'], {})

    def test_missing_underlying_spot_price(self):
        # Insert option chain data without underlying_spot_price
        option_chain_collection.insert_one({
            'instrument_key': 'NO_SPOT_PRICE',
            'expiry_date': '2025-09-16',
            'data': self.option_chain_data,
            'fetched_at': datetime.now(timezone.utc)
        })
        payload = {
            "instrument_key": "NO_SPOT_PRICE",
            "expiry_date": "2025-09-16"
        }
        response = self.app.post('/api/metrics/calculate_metrics', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
