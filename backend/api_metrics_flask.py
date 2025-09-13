from flask import Blueprint, request, jsonify
from metrics_calculations import (
    classify_strikes,
    calculate_totals,
    calculate_difference,
    calculate_difference_percent,
    calculate_bid_ask_imbalance,
    calculate_bid_ask_spread,
)
from datetime import datetime, timezone
from pymongo import DESCENDING
from database import db, metrics_collection, option_chain_collection

metrics_bp = Blueprint('metrics', __name__)

def calculate_metrics_internal(instrument_key, expiry_date):
    # Internal function to calculate metrics without HTTP context
    # Returns metrics dict or raises Exception
    # Fetch latest option chain data for given instrument and expiry from MongoDB
    option_chain_data_doc = option_chain_collection.find_one(
        {'instrument_key': instrument_key, 'expiry_date': expiry_date},
        sort=[('fetched_at', DESCENDING)]
    )

    if not option_chain_data_doc:
        raise Exception("Option chain data not found")

    data = option_chain_data_doc.get('data', [])
    current_price = option_chain_data_doc.get('underlying_spot_price')

    if current_price is None:
        # If no underlying spot price, but data exists, set current_price to nearest ATM strike or 0
        if data:
            strikes = [item['strike_price'] for item in data]
            current_price = min(strikes, key=lambda x: abs(x - 0))  # fallback to 0
        else:
            # Return empty metrics
            return {
                "current_price": 0,
                "totals": {"call": {}, "put": {}},
                "difference": {"call": {}, "put": {}},
                "difference_percent": {"call": {}, "put": {}},
                "bid_ask_imbalance": {"call": 0.0, "put": 0.0},
                "bid_ask_spread": {"call": {"bid_avg": 0.0, "ask_avg": 0.0}, "put": {"bid_avg": 0.0, "ask_avg": 0.0}}
            }
    if not data:
        # Return empty metrics if data is empty
        return {
            "current_price": current_price,
            "totals": {"call": {}, "put": {}},
            "difference": {"call": {}, "put": {}},
            "difference_percent": {"call": {}, "put": {}},
            "bid_ask_imbalance": {"call": 0.0, "put": 0.0},
            "bid_ask_spread": {"call": {"bid_avg": 0.0, "ask_avg": 0.0}, "put": {"bid_avg": 0.0, "ask_avg": 0.0}}
        }

    strikes = [item['strike_price'] for item in data]
    strikes_classification = classify_strikes(current_price, strikes)

    columns = ['oi', 'volume', 'iv', 'bid_qty', 'ask_qty']

    totals = calculate_totals(data, strikes_classification, columns)

    # Fetch baseline metrics from MongoDB or create if not exists
    baseline_metrics_doc = metrics_collection.find_one({
        'instrument_key': instrument_key,
        'expiry_date': expiry_date,
        'is_baseline': True
    })

    if not baseline_metrics_doc:
        # Store current totals as baseline
        baseline_metrics_doc = {
            'instrument_key': instrument_key,
            'expiry_date': expiry_date,
            'is_baseline': True,
            'totals': totals,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        metrics_collection.insert_one(baseline_metrics_doc)

    difference = calculate_difference(totals, baseline_metrics_doc['totals'], columns)
    difference_percent = calculate_difference_percent(difference, totals, columns)
    bid_ask_imbalance = calculate_bid_ask_imbalance(data, strikes_classification)
    bid_ask_spread = calculate_bid_ask_spread(data, strikes_classification)

    # Store calculated metrics in MongoDB
    metrics_doc = {
        'instrument_key': instrument_key,
        'expiry_date': expiry_date,
        'is_baseline': False,
        'totals': totals,
        'difference': difference,
        'difference_percent': difference_percent,
        'bid_ask_imbalance': bid_ask_imbalance,
        'bid_ask_spread': bid_ask_spread,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc)
    }
    metrics_collection.insert_one(metrics_doc)

    return {
        "current_price": current_price,
        "totals": totals,
        "difference": difference,
        "difference_percent": difference_percent,
        "bid_ask_imbalance": bid_ask_imbalance,
        "bid_ask_spread": bid_ask_spread
    }

@metrics_bp.route("/calculate_metrics", methods=['POST'])
def calculate_metrics():
    try:
        request_data = request.get_json()
        instrument_key = request_data.get('instrument_key')
        expiry_date = request_data.get('expiry_date')

        if not instrument_key or not expiry_date:
            # Try to get from query params as fallback
            instrument_key = instrument_key or request.args.get('instrument_key')
            expiry_date = expiry_date or request.args.get('expiry_date')
            if not instrument_key or not expiry_date:
                return jsonify({"detail": "Missing instrument_key or expiry_date"}), 400

        metrics_result = calculate_metrics_internal(instrument_key, expiry_date)
        return jsonify(metrics_result)
    except Exception as e:
        return jsonify({"detail": str(e)}), 500
