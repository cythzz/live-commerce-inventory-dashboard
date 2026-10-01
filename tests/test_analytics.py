from pathlib import Path

import pandas as pd
import pytest

from src.analytics import (
    calculate_inventory_health,
    calculate_session_metrics,
    generate_reports,
    validate_input_rows,
)


def test_calculates_session_conversion_and_order_value():
    frame = pd.DataFrame([{
        "session_id": "S1", "date": "2026-09-01", "host": "主播",
        "category": "美妆", "duration_minutes": 60, "viewers": 100,
        "orders": 5, "gmv": 500, "refund_amount": 50,
    }])
    result = calculate_session_metrics(frame).iloc[0]
    assert result["conversion_rate"] == 5.0
    assert result["average_order_value"] == 100.0
    assert result["net_gmv"] == 450.0


def test_marks_stockout_low_stock_slow_moving_and_healthy():
    frame = pd.DataFrame([
        {"sku": "A", "product_name": "A", "category": "X", "current_stock": 0, "avg_daily_sales": 3, "unit_cost": 1},
        {"sku": "B", "product_name": "B", "category": "X", "current_stock": 6, "avg_daily_sales": 2, "unit_cost": 1},
        {"sku": "C", "product_name": "C", "category": "X", "current_stock": 100, "avg_daily_sales": 2, "unit_cost": 1},
        {"sku": "D", "product_name": "D", "category": "X", "current_stock": 20, "avg_daily_sales": 2, "unit_cost": 1},
    ])
    result = calculate_inventory_health(frame).set_index("sku")
    assert result.loc["A", "stock_status"] == "断货"
    assert result.loc["B", "stock_status"] == "低库存"
    assert result.loc["C", "stock_status"] == "滞销"
    assert result.loc["D", "stock_status"] == "健康"


def test_zero_sales_is_slow_moving():
    frame = pd.DataFrame([{
        "sku": "A", "product_name": "A", "category": "X", "current_stock": 20,
        "avg_daily_sales": 0, "unit_cost": 2,
    }])
    result = calculate_inventory_health(frame).iloc[0]
    assert pd.isna(result["sellable_days"])
    assert result["stock_status"] == "滞销"


def test_generates_two_local_reports(tmp_path: Path):
    data_dir = Path(__file__).parents[1] / "data"
    session_path, inventory_path = generate_reports(data_dir, tmp_path)
    assert session_path.exists()
    assert inventory_path.exists()


def test_rejects_invalid_and_duplicate_input_rows():
    sessions = pd.DataFrame([{
        "session_id": "S1", "date": "2026-09-01", "host": "主播", "category": "美妆",
        "duration_minutes": 60, "viewers": -1, "orders": 5, "gmv": 500, "refund_amount": 0,
    }])
    inventory = pd.DataFrame([{
        "sku": "A", "product_name": "A", "category": "X", "current_stock": 1,
        "avg_daily_sales": 1, "unit_cost": 1,
    }])
    with pytest.raises(ValueError, match="数据校验失败"):
        validate_input_rows(sessions, inventory)
