from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from backend.metrics_calculations import (
    classify_strikes,
    calculate_totals,
    calculate_difference,
    calculate_difference_percent,
    calculate_bid_ask_imbalance,
    calculate_bid_ask_spread,
)
from backend.database import get_db_session  # Assuming you have a DB session provider
from backend.models import OptionChainData, MetricsData  # Assuming ORM models

router = APIRouter()

class MetricsRequest(BaseModel):
    instrument_key: str
    expiry_date: str

@router.post("/calculate_metrics")
async def calculate_metrics(request: MetricsRequest):
    db = get_db_session()
    try:
        # Fetch latest option chain data for given instrument and expiry
        option_chain_data = db.query(OptionChainData).filter(
            OptionChainData.instrument_key == request.instrument_key,
            OptionChainData.expiry_date == request.expiry_date
        ).order_by(OptionChainData.fetched_at.desc()).first()

        if not option_chain_data:
            raise HTTPException(status_code=404, detail="Option chain data not found")

        data = option_chain_data.data  # Assuming JSON field with list of option data dicts
        current_price = option_chain_data.underlying_spot_price

        strikes = [item['strike_price'] for item in data]
        strikes_classification = classify_strikes(current_price, strikes)

        columns = ['oi', 'volume', 'iv', 'bid_qty', 'ask_qty']

        totals = calculate_totals(data, strikes_classification, columns)

        # Fetch baseline metrics from DB or create if not exists
        baseline_metrics = db.query(MetricsData).filter(
            MetricsData.instrument_key == request.instrument_key,
            MetricsData.expiry_date == request.expiry_date,
            MetricsData.is_baseline == True
        ).first()

        if not baseline_metrics:
            # Store current totals as baseline
            baseline_metrics = MetricsData(
                instrument_key=request.instrument_key,
                expiry_date=request.expiry_date,
                is_baseline=True,
                totals=totals
            )
            db.add(baseline_metrics)
            db.commit()
            db.refresh(baseline_metrics)

        difference = calculate_difference(totals, baseline_metrics.totals, columns)
        difference_percent = calculate_difference_percent(difference, totals, columns)
        bid_ask_imbalance = calculate_bid_ask_imbalance(data, strikes_classification)
        bid_ask_spread = calculate_bid_ask_spread(data, strikes_classification)

        # Store calculated metrics in DB
        metrics = MetricsData(
            instrument_key=request.instrument_key,
            expiry_date=request.expiry_date,
            is_baseline=False,
            totals=totals,
            difference=difference,
            difference_percent=difference_percent,
            bid_ask_imbalance=bid_ask_imbalance,
            bid_ask_spread=bid_ask_spread
        )
        db.add(metrics)
        db.commit()
        db.refresh(metrics)

        return {
            "current_price": current_price,
            "totals": totals,
            "difference": difference,
            "difference_percent": difference_percent,
            "bid_ask_imbalance": bid_ask_imbalance,
            "bid_ask_spread": bid_ask_spread
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
