from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import (
    INVENTORY_COLUMNS,
    SESSION_COLUMNS,
    calculate_inventory_health,
    calculate_session_metrics,
    generate_reports,
    load_csv,
)


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"

st.set_page_config(page_title="直播电商库存看板", page_icon="📦", layout="wide")
st.title("📦 直播电商场次与库存分析看板")
st.caption("数据仅来自仓库内本地模拟 CSV，不调用爬虫或外部接口。")

sessions = calculate_session_metrics(load_csv(DATA_DIR / "live_sessions.csv", SESSION_COLUMNS))
inventory = calculate_inventory_health(load_csv(DATA_DIR / "inventory.csv", INVENTORY_COLUMNS))
generate_reports(DATA_DIR, REPORT_DIR)

with st.sidebar:
    st.header("筛选条件")
    selected_hosts = st.multiselect("主播", sorted(sessions["host"].unique()), default=sorted(sessions["host"].unique()))
    selected_categories = st.multiselect(
        "品类", sorted(sessions["category"].unique()), default=sorted(sessions["category"].unique())
    )
    status_options = ["断货", "低库存", "滞销", "健康"]
    selected_statuses = st.multiselect("库存状态", status_options, default=status_options)

filtered_sessions = sessions[
    sessions["host"].isin(selected_hosts) & sessions["category"].isin(selected_categories)
]
filtered_inventory = inventory[inventory["stock_status"].isin(selected_statuses)]

total_gmv = filtered_sessions["gmv"].sum()
total_orders = int(filtered_sessions["orders"].sum())
total_viewers = int(filtered_sessions["viewers"].sum())
conversion = total_orders / total_viewers * 100 if total_viewers else 0
stock_risks = int(filtered_inventory["stock_status"].isin(["断货", "低库存", "滞销"]).sum())

cols = st.columns(5)
cols[0].metric("场次", len(filtered_sessions))
cols[1].metric("GMV", f"¥{total_gmv:,.0f}")
cols[2].metric("订单", f"{total_orders:,}")
cols[3].metric("综合转化率", f"{conversion:.2f}%")
cols[4].metric("风险 SKU", stock_risks)

st.subheader("直播场次指标对比")
left, right = st.columns(2)
left.plotly_chart(
    px.bar(filtered_sessions, x="session_id", y="gmv", color="host", hover_data=["orders", "conversion_rate"], title="各场次 GMV"),
    use_container_width=True,
)
right.plotly_chart(
    px.line(filtered_sessions, x="date", y="conversion_rate", color="host", markers=True, title="转化率趋势（%）"),
    use_container_width=True,
)
st.dataframe(
    filtered_sessions[["session_id", "date", "host", "category", "viewers", "orders", "gmv", "conversion_rate", "average_order_value", "refund_rate"]],
    use_container_width=True,
    hide_index=True,
)
st.download_button(
    "下载场次报表",
    filtered_sessions.to_csv(index=False).encode("utf-8-sig"),
    "live_session_report.csv",
    "text/csv",
)

st.subheader("库存健康度")
status_colors = {"断货": "#d62728", "低库存": "#ff7f0e", "滞销": "#9467bd", "健康": "#2ca02c"}
st.plotly_chart(
    px.bar(filtered_inventory, x="sku", y="sellable_days", color="stock_status", color_discrete_map=status_colors,
           hover_data=["product_name", "current_stock", "avg_daily_sales"], title="SKU 可售天数"),
    use_container_width=True,
)

display_inventory = filtered_inventory.copy()
display_inventory["sellable_days"] = display_inventory["sellable_days"].map(
    lambda value: "无销量" if pd.isna(value) else value
)
st.dataframe(display_inventory, use_container_width=True, hide_index=True)
st.download_button(
    "下载库存报表",
    filtered_inventory.to_csv(index=False).encode("utf-8-sig"),
    "inventory_health_report.csv",
    "text/csv",
)
