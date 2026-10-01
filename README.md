# 直播电商与库存分析看板

一个完全读取本地模拟 CSV 的 Python Demo。使用 Pandas 完成直播多场次指标对比、库存可售天数计算、滞销/低库存/断货 SKU 标记，并通过 Streamlit 输出交互式看板和可下载报表；不包含网络爬虫或第三方平台接口。

## 功能

- 对比各直播场次的观看人数、订单量、GMV、退款额、转化率和客单价。
- 按品类、主播和日期筛选，并展示 GMV 趋势与场次对比。
- 计算 `可售天数 = 当前库存 / 日均销量`。
- 自动标记 `断货`、`低库存`、`健康`、`滞销` SKU。
- 本地生成 `reports/live_session_report.csv` 与 `reports/inventory_health_report.csv`。
- 页面可直接下载当前筛选后的 CSV 报表。

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe generate_reports.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 项目结构

```text
data/                  本地模拟直播与库存 CSV
src/analytics.py       可复用 Pandas 指标计算
app.py                 Streamlit 交互式看板
generate_reports.py    自动报表脚本
tests/                 指标与库存状态测试
```

## 状态规则

| 状态 | 规则 |
| --- | --- |
| 断货 | 当前库存小于等于 0 |
| 滞销 | 日均销量为 0，或可售天数大于 30 天 |
| 低库存 | 可售天数小于 7 天 |
| 健康 | 其余情况 |

## 本人改造内容

- 将上游通用 Streamlit 数据可视化示例改造成直播电商业务场景。
- 移除网络数据下载，改为仓库内本地模拟 CSV。
- 抽离可单元测试的 Pandas 指标层。
- 增加多场次经营指标、库存可售天数和风险 SKU 规则。
- 增加自动报表脚本、交互筛选、图表和 CSV 下载。

## 开源说明

本项目引入并保留 `streamlit/demo-uber-nyc-pickups` 的提交历史和 Apache License 2.0。当前业务数据、分析逻辑、测试及中文文档由本仓库维护者重新设计和实现。
