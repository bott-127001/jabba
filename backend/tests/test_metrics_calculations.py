import unittest
from backend.metrics_calculations import (
    classify_strikes,
    calculate_totals,
    calculate_difference,
    calculate_difference_percent,
    calculate_bid_ask_imbalance,
    calculate_bid_ask_spread,
)

class TestMetricsCalculations(unittest.TestCase):

    def setUp(self):
        self.sample_data = [
            {
                'strike_price': 100,
                'call_options': {
                    'market_data': {'oi': 10, 'volume': 100, 'iv': 0.2, 'bid_qty': 5, 'ask_qty': 3, 'bid_price': 1, 'ask_price': 2},
                },
                'put_options': {
                    'market_data': {'oi': 20, 'volume': 200, 'iv': 0.3, 'bid_qty': 7, 'ask_qty': 4, 'bid_price': 1.5, 'ask_price': 2.5},
                }
            },
            {
                'strike_price': 105,
                'call_options': {
                    'market_data': {'oi': 15, 'volume': 150, 'iv': 0.25, 'bid_qty': 6, 'ask_qty': 2, 'bid_price': 1.1, 'ask_price': 2.1},
                },
                'put_options': {
                    'market_data': {'oi': 25, 'volume': 250, 'iv': 0.35, 'bid_qty': 8, 'ask_qty': 5, 'bid_price': 1.6, 'ask_price': 2.6},
                }
            }
        ]
        self.strikes_classification = {
            'atm': 100,
            'call_itm': [],
            'call_otm': [105],
            'put_itm': [105],
            'put_otm': []
        }
        self.columns = ['oi', 'volume', 'iv', 'bid_qty', 'ask_qty']

    def test_classify_strikes(self):
        strikes = [100, 105, 110]
        current_price = 102
        classification = classify_strikes(current_price, strikes)
        self.assertEqual(classification['atm'], 100)
        self.assertIn(110, classification['call_otm'])
        self.assertIn(110, classification['put_itm'])

    def test_calculate_totals(self):
        totals = calculate_totals(self.sample_data, self.strikes_classification, self.columns)
        self.assertAlmostEqual(totals['call']['oi'], 25)
        self.assertAlmostEqual(totals['put']['oi'], 45)

    def test_calculate_difference(self):
        current_totals = {'call': {'oi': 30}, 'put': {'oi': 50}}
        baseline_totals = {'call': {'oi': 20}, 'put': {'oi': 40}}
        diff = calculate_difference(current_totals, baseline_totals, ['oi'])
        self.assertEqual(diff['call']['oi'], 10)
        self.assertEqual(diff['put']['oi'], 10)

    def test_calculate_difference_percent(self):
        difference = {'call': {'oi': 10}, 'put': {'oi': 10}}
        totals = {'call': {'oi': 20}, 'put': {'oi': 40}}
        diff_percent = calculate_difference_percent(difference, totals, ['oi'])
        self.assertAlmostEqual(diff_percent['call']['oi'], 50.0)
        self.assertAlmostEqual(diff_percent['put']['oi'], 25.0)

    def test_calculate_bid_ask_imbalance(self):
        imbalance = calculate_bid_ask_imbalance(self.sample_data, self.strikes_classification)
        self.assertTrue('call' in imbalance)
        self.assertTrue('put' in imbalance)

    def test_calculate_bid_ask_spread(self):
        spread = calculate_bid_ask_spread(self.sample_data, self.strikes_classification)
        self.assertTrue('call' in spread)
        self.assertTrue('put' in spread)

if __name__ == '__main__':
    unittest.main()
