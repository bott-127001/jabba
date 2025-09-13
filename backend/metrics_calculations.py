import typing
from collections import defaultdict

def classify_strikes(current_price: float, strikes: typing.List[float]) -> typing.Dict[str, typing.List[float]]:
    """
    Classify strikes into ATM, ITM, OTM for call and put sides based on current price.
    Returns dict with keys:
    - 'atm': float
    - 'call_itm': list of floats
    - 'call_otm': list of floats
    - 'put_itm': list of floats
    - 'put_otm': list of floats
    """
    # Find nearest strike to current price as ATM
    atm = min(strikes, key=lambda x: abs(x - current_price))
    call_itm = [s for s in strikes if s < atm]
    call_otm = [s for s in strikes if s > atm]
    put_itm = [s for s in strikes if s > atm]
    put_otm = [s for s in strikes if s < atm]
    return {
        'atm': atm,
        'call_itm': call_itm,
        'call_otm': call_otm,
        'put_itm': put_itm,
        'put_otm': put_otm,
    }

def calculate_totals(data: typing.List[dict], strikes_classification: dict, columns: typing.List[str]) -> dict:
    """
    Calculate totals for specified columns summing over 5 ITM + ATM + 10 OTM strikes.
    data: list of option chain data dicts with strike_price and call_options/put_options market_data.
    Returns dict with totals for call and put sides.
    """
    totals = {
        'call': defaultdict(float),
        'put': defaultdict(float),
    }
    # Select strikes: 5 ITM + ATM + 10 OTM for each side
    def select_strikes(itm, atm, otm):
        selected = sorted(itm, reverse=True)[:5] + [atm] + sorted(otm)[:10]
        return set(selected)

    call_strikes = select_strikes(strikes_classification['call_itm'], strikes_classification['atm'], strikes_classification['call_otm'])
    put_strikes = select_strikes(strikes_classification['put_itm'], strikes_classification['atm'], strikes_classification['put_otm'])

    for item in data:
        strike = item['strike_price']
        if strike in call_strikes:
            for col in columns:
                val = item['call_options']['market_data'].get(col, 0)
                totals['call'][col] += val
        if strike in put_strikes:
            for col in columns:
                val = item['put_options']['market_data'].get(col, 0)
                totals['put'][col] += val
    return totals

def calculate_difference(current_totals: dict, baseline_totals: dict, columns: typing.List[str]) -> dict:
    """
    Calculate difference = current - baseline for each column and side.
    """
    difference = {
        'call': {},
        'put': {},
    }
    for side in ['call', 'put']:
        for col in columns:
            difference[side][col] = current_totals[side].get(col, 0) - baseline_totals[side].get(col, 0)
    return difference

def calculate_difference_percent(difference: dict, totals: dict, columns: typing.List[str]) -> dict:
    """
    Calculate difference in % terms = (difference / totals) * 100
    """
    diff_percent = {
        'call': {},
        'put': {},
    }
    for side in ['call', 'put']:
        for col in columns:
            total_val = totals[side].get(col, 0)
            diff_val = difference[side].get(col, 0)
            if total_val != 0:
                diff_percent[side][col] = (diff_val / total_val) * 100
            else:
                diff_percent[side][col] = 0.0
    return diff_percent

def calculate_bid_ask_imbalance(data: typing.List[dict], strikes_classification: dict) -> dict:
    """
    Calculate bid-ask imbalance for 16 strikes (5 ITM + ATM + 10 OTM).
    imbalance(per strike) = (bid_qty - ask_qty) / (bid_qty + ask_qty) * 0.2
    Sum over all 16 strikes for call and put sides.
    """
    imbalance = {
        'call': 0.0,
        'put': 0.0,
    }
    def select_strikes(itm, atm, otm):
        selected = sorted(itm, reverse=True)[:5] + [atm] + sorted(otm)[:10]
        return set(selected)

    call_strikes = select_strikes(strikes_classification['call_itm'], strikes_classification['atm'], strikes_classification['call_otm'])
    put_strikes = select_strikes(strikes_classification['put_itm'], strikes_classification['atm'], strikes_classification['put_otm'])

    for item in data:
        strike = item['strike_price']
        if strike in call_strikes:
            bid_qty = item['call_options']['market_data'].get('bid_qty', 0)
            ask_qty = item['call_options']['market_data'].get('ask_qty', 0)
            denom = bid_qty + ask_qty
            if denom != 0:
                imbalance['call'] += ((bid_qty - ask_qty) / denom) * 0.2
        if strike in put_strikes:
            bid_qty = item['put_options']['market_data'].get('bid_qty', 0)
            ask_qty = item['put_options']['market_data'].get('ask_qty', 0)
            denom = bid_qty + ask_qty
            if denom != 0:
                imbalance['put'] += ((bid_qty - ask_qty) / denom) * 0.2
    return imbalance

def calculate_bid_ask_spread(data: typing.List[dict], strikes_classification: dict) -> dict:
    """
    Calculate bid-ask spread for 5 strikes (2 ITM + ATM + 2 OTM).
    Average bid price and ask price over these strikes for call and put sides.
    """
    spread = {
        'call': {'bid_avg': 0.0, 'ask_avg': 0.0},
        'put': {'bid_avg': 0.0, 'ask_avg': 0.0},
    }
    def select_strikes(itm, atm, otm):
        selected = sorted(itm, reverse=True)[:2] + [atm] + sorted(otm)[:2]
        return set(selected)

    call_strikes = select_strikes(strikes_classification['call_itm'], strikes_classification['atm'], strikes_classification['call_otm'])
    put_strikes = select_strikes(strikes_classification['put_itm'], strikes_classification['atm'], strikes_classification['put_otm'])

    call_bid_sum = 0.0
    call_ask_sum = 0.0
    call_count = 0
    put_bid_sum = 0.0
    put_ask_sum = 0.0
    put_count = 0

    for item in data:
        strike = item['strike_price']
        if strike in call_strikes:
            call_bid_sum += item['call_options']['market_data'].get('bid_price', 0)
            call_ask_sum += item['call_options']['market_data'].get('ask_price', 0)
            call_count += 1
        if strike in put_strikes:
            put_bid_sum += item['put_options']['market_data'].get('bid_price', 0)
            put_ask_sum += item['put_options']['market_data'].get('ask_price', 0)
            put_count += 1

    if call_count > 0:
        spread['call']['bid_avg'] = call_bid_sum / call_count
        spread['call']['ask_avg'] = call_ask_sum / call_count
    if put_count > 0:
        spread['put']['bid_avg'] = put_bid_sum / put_count
        spread['put']['ask_avg'] = put_ask_sum / put_count

    return spread
