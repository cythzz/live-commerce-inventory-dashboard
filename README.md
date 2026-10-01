# 直播电商与库存分析看板

一个完全读取本地 CSV 的 Python 数据服务。使用 FastAPI 接收分析任务、Pandas 清洗计算、PostgreSQL 保存任务状态、APScheduler 生成定时报表，并通过 Streamlit 展示交互式看板；不包含网络爬虫或第三方平台接口。

## 功能

- 对比各直播场次的观看人数、订单量、GMV、退款额、转化率和客单价。
- 按品类、主播和日期筛选，并展示 GMV 趋势与场次对比。
- 计算 `可售天数 = 当前库存 / 日均销量`。
- 自动标记 `断货`、`低库存`、`健康`、`滞销` SKU。
- 本地生成 `reports/live_session_report.csv` 与 `reports/inventory_health_report.csv`。
- 页面可直接下载当前筛选后的 CSV 报表。
- FastAPI 上传两类 CSV，后台生成多 Sheet Excel 报表并查询任务进度。
- PostgreSQL 持久化任务状态，处理失败时记录数据校验错误。
- APScheduler 每日生成仓库内模拟数据报表。
- pytest 覆盖指标规则与完整上传/下载流程。

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe generate_reports.py
.\.venv\Scripts\python.exe -m uvicorn src.api:app --reload
.\.venv\Scripts\python.exe -m streamlit run app.py
```

本地直接启动时使用 SQLite，便于开发；作品演示建议用 PostgreSQL 一键启动：

```powershell
docker compose up -d --build
```

- FastAPI / Swagger：本机 `8000/docs`
- Streamlit：本机 `8501`

## 项目结构

```text
data/                  本地模拟直播与库存 CSV
src/analytics.py       可复用 Pandas 指标计算
src/api.py             FastAPI 上传、进度查询和报表下载接口
src/jobs.py            后台分析与定时报表任务
src/models.py          SQLAlchemy 任务模型
app.py                 Streamlit 交互式看板
generate_reports.py    自动报表脚本
tests/                 指标与库存状态测试
```

## API 流程

```text
上传直播场次 CSV + 库存 CSV
  → 创建 PENDING 任务并写入 PostgreSQL
  → 后台任务校验字段并执行 Pandas 分析
  ├─ 成功：生成 Excel → SUCCEEDED → 下载报表
  └─ 失败：记录错误原因 → FAILED
```

主要接口：

- `POST /api/jobs`：表单字段 `sessions`、`inventory`，均为 CSV。
- `GET /api/jobs/{jobId}`：查询任务状态和失败原因。
- `GET /api/jobs/{jobId}/report`：下载生成的 Excel。

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
- 增加 FastAPI 后台任务、PostgreSQL 状态持久化、APScheduler 定时任务和 Excel 导出。
- 增加 Docker Compose、GitHub Actions 和 API 端到端测试。

## 开源说明

本项目引入并保留 `streamlit/demo-uber-nyc-pickups` 的提交历史和 Apache License 2.0。当前业务数据、分析逻辑、测试及中文文档由本仓库维护者重新设计和实现。
