from __future__ import annotations

from pathlib import Path

import pandas as pd


SESSION_COLUMNS = {
    "session_id", "date", "host", "category", "duration_minutes",
    "viewers", "orders", "gmv", "refund_amount",
}
INVENTORY_COLUMNS = {
    "sku", "product_name", "category", "current_stock",
    "avg_daily_sales", "unit_cost",
}


def load_csv(path: Path, required_columns: set[str]) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = required_columns.difference(frame.columns)
    if missing:
        raise ValueError(f"{path.name} 缺少字段：{', '.join(sorted(missing))}")
    return frame


def calculate_session_metrics(sessions: pd.DataFrame) -> pd.DataFrame:
    result = sessions.copy()
    result["date"] = pd.to_datetime(result["date"])
    result["conversion_rate"] = (
        result["orders"].div(result["viewers"].replace(0, pd.NA)).fillna(0) * 100
    ).round(2)
    result["average_order_value"] = (
        result["gmv"].div(result["orders"].replace(0, pd.NA)).fillna(0)
    ).round(2)
    result["net_gmv"] = (result["gmv"] - result["refund_amount"]).round(2)
    result["refund_rate"] = (
        result["refund_amount"].div(result["gmv"].replace(0, pd.NA)).fillna(0) * 100
    ).round(2)
    return result.sort_values(["date", "session_id"])


def calculate_inventory_health(inventory: pd.DataFrame) -> pd.DataFrame:
    result = inventory.copy()
    positive_sales = result["avg_daily_sales"].where(result["avg_daily_sales"] > 0)
    result["sellable_days"] = result["current_stock"].div(positive_sales).round(1)
    result["inventory_value"] = (result["current_stock"].clip(lower=0) * result["unit_cost"]).round(2)

    def classify(row: pd.Series) -> str:
        if row["current_stock"] <= 0:
            return "断货"
        if row["avg_daily_sales"] <= 0 or row["sellable_days"] > 30:
            return "滞销"
        if row["sellable_days"] < 7:
            return "低库存"
        return "健康"

    result["stock_status"] = result.apply(classify, axis=1)
    priority = {"断货": 0, "低库存": 1, "滞销": 2, "健康": 3}
    result["priority"] = result["stock_status"].map(priority)
    return result.sort_values(["priority", "sellable_days"], na_position="last").drop(columns="priority")


def generate_reports(data_dir: Path, report_dir: Path) -> tuple[Path, Path]:
    sessions = load_csv(data_dir / "live_sessions.csv", SESSION_COLUMNS)
    inventory = load_csv(data_dir / "inventory.csv", INVENTORY_COLUMNS)
    session_report = calculate_session_metrics(sessions)
    inventory_report = calculate_inventory_health(inventory)
    report_dir.mkdir(parents=True, exist_ok=True)
    session_path = report_dir / "live_session_report.csv"
    inventory_path = report_dir / "inventory_health_report.csv"
    session_report.to_csv(session_path, index=False, encoding="utf-8-sig")
    inventory_report.to_csv(inventory_path, index=False, encoding="utf-8-sig")
    return session_path, inventory_path
