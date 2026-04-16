from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from Models.api import optimize_tasks
from Models.config import GAConfig
from Data.data_preprocessing import CSVTaskProcessor


SEEDS = [42, 100, 999, 2024, 777]
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_CANDIDATES = [
    PROJECT_ROOT / "Data" / "df_500_tasks.csv",
    PROJECT_ROOT / "df_500_tasks.csv",
]


def load_input_dataframe(now: datetime) -> pd.DataFrame:
    """
    Ưu tiên chạy đúng pipeline của project:
    CSV -> CSVTaskProcessor -> DataFrame đã được enrich urgency_score.
    Nếu không xử lý được thì fallback đọc trực tiếp CSV.
    """
    csv_path = next((p for p in DATA_CANDIDATES if p.exists()), None)
    if csv_path is None:
        searched = "\n".join(f"- {p}" for p in DATA_CANDIDATES)
        raise FileNotFoundError(
            "Không tìm thấy file dữ liệu df_500_tasks.csv. Đã tìm tại:\n" + searched
        )

    try:
        processor = CSVTaskProcessor(now=now)
        return processor.process_csv(str(csv_path))
    except Exception as exc:
        print(f"[WARN] CSVTaskProcessor lỗi, fallback sang pd.read_csv: {exc}")
        return pd.read_csv(csv_path)


def run_one_match(seed: int, is_standard_ga: bool, df: pd.DataFrame, now: datetime) -> dict:
    config = GAConfig(
        now=now,
        population_size=40,
        generations=60,
        mutation_rate=0.18,
        crossover_rate=0.85,
        random_seed=seed,
        is_standard_ga=is_standard_ga,
    )

    result = optimize_tasks(df, config=config)
    metrics = result.get("metrics", {})

    return {
        "best_fitness": float(result.get("best_fitness", float("-inf"))),
        "late_tasks": int(metrics.get("late_tasks", 0)),
        "on_time_tasks": int(metrics.get("on_time_tasks", 0)),
        "scheduled_tasks": int(metrics.get("scheduled_tasks", 0)),
        "runtime_seconds": float(metrics.get("runtime_seconds", 0.0)),
    }


def decide_winner(standard: dict, advanced: dict) -> str:
    """
    Luật so sánh theo yêu cầu:
    1. Fitness cao hơn thì thắng
    2. Nếu hòa fitness, bên ít late_tasks hơn thắng
    3. Nếu vẫn hòa thì Draw
    """
    if standard["best_fitness"] > advanced["best_fitness"]:
        return "Standard GA"
    if standard["best_fitness"] < advanced["best_fitness"]:
        return "Advanced GA"

    if standard["late_tasks"] < advanced["late_tasks"]:
        return "Standard GA"
    if standard["late_tasks"] > advanced["late_tasks"]:
        return "Advanced GA"

    return "Draw"


def main() -> None:
    now = datetime.now()
    df = load_input_dataframe(now)

    rows: list[dict] = []
    score = {"Standard GA": 0, "Advanced GA": 0, "Draw": 0}

    for seed in SEEDS:
        standard_result = run_one_match(seed=seed, is_standard_ga=True, df=df, now=now)
        advanced_result = run_one_match(seed=seed, is_standard_ga=False, df=df, now=now)

        winner = decide_winner(standard_result, advanced_result)
        score[winner] += 1

        rows.append(
            {
                "seed": seed,
                "standard_best_fitness": standard_result["best_fitness"],
                "standard_late_tasks": standard_result["late_tasks"],
                "advanced_best_fitness": advanced_result["best_fitness"],
                "advanced_late_tasks": advanced_result["late_tasks"],
                "winner": winner,
            }
        )

    result_df = pd.DataFrame(rows)
    scoreboard_df = pd.DataFrame(
        {
            "algorithm": ["Standard GA", "Advanced GA", "Draw"],
            "wins": [score["Standard GA"], score["Advanced GA"], score["Draw"]],
        }
    )

    print("\n=== DATAFRAME VIEW ===")
    print(result_df)

    print("\n=== SCOREBOARD ===")
    print(scoreboard_df)


if __name__ == "__main__":
    main()
