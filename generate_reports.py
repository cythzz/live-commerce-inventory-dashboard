from pathlib import Path

from src.analytics import generate_reports


if __name__ == "__main__":
    root = Path(__file__).parent
    outputs = generate_reports(root / "data", root / "reports")
    for output in outputs:
        print(f"已生成：{output}")
