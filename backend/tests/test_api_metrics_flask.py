import unittest
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api_metrics_flask import metrics_bp
from main import app

class TestMetricsAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_missing_parameters(self):
        response = self.app.post('/api/metrics/calculate_metrics', data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing instrument_key or expiry_date', response.get_data(as_text=True))

    def test_invalid_instrument_key(self):
        payload = {
            "instrument_key": "INVALID_KEY",
            "expiry_date": "2025-09-16"
        }
        response = self.app.post('/api/metrics/calculate_metrics', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 404)
        self.assertIn('Option chain data not found', response.get_data(as_text=True))

    # Additional tests for valid data, edge cases, and database integration can be added here

if __name__ == '__main__':
    unittest.main()
