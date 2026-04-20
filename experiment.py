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

STANDARD_NAME = "Standard GA"
CUSTOM_NAME = "Custom GA"


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


def run_one_match(seed: int, use_repair: bool, df: pd.DataFrame, now: datetime) -> dict:
    config = GAConfig(
        now=now,
        population_size=40,
        generations=60,
        mutation_rate=0.18,
        crossover_rate=0.85,
        random_seed=seed,
        is_standard_ga=not use_repair,
        use_repair=use_repair,
    )

    result = optimize_tasks(df, config=config)
    metrics = result.get("metrics", {})

    return {
        "best_fitness": float(result.get("best_fitness", float("-inf"))),
        "late_tasks": int(metrics.get("late_tasks", 0)),
        "on_time_tasks": int(metrics.get("on_time_tasks", 0)),
        "scheduled_tasks": int(metrics.get("scheduled_tasks", 0)),
        "total_lateness_hours": float(metrics.get("total_lateness_hours", 0.0)),
        "prerequisite_violations": int(metrics.get("prerequisite_violations", 0)),
        "overlap_violations": int(metrics.get("overlap_violations", 0)),
        "window_violations": int(metrics.get("window_violations", 0)),
        "runtime_seconds": float(metrics.get("runtime_seconds", 0.0)),
    }


def _comparison_key(result: dict) -> tuple:
    """
    Key nhỏ hơn là tốt hơn.
    So sánh công bằng bằng metric chung trước, fitness để cuối.
    """
    return (
        result["late_tasks"],
        result["prerequisite_violations"],
        result["overlap_violations"],
        result["window_violations"],
        round(result["total_lateness_hours"], 6),
        -result["on_time_tasks"],
        -round(result["best_fitness"], 6),
    )


def decide_winner(standard: dict, custom: dict) -> str:
    standard_key = _comparison_key(standard)
    custom_key = _comparison_key(custom)

    if standard_key < custom_key:
        return STANDARD_NAME
    if custom_key < standard_key:
        return CUSTOM_NAME
    return "Draw"


def main() -> None:
    now = datetime.now()
    df = load_input_dataframe(now)

    rows: list[dict] = []
    score = {STANDARD_NAME: 0, CUSTOM_NAME: 0, "Draw": 0}

    for seed in SEEDS:
        standard_result = run_one_match(seed=seed, use_repair=False, df=df, now=now)
        custom_result = run_one_match(seed=seed, use_repair=True, df=df, now=now)

        winner = decide_winner(standard_result, custom_result)
        score[winner] += 1

        rows.append(
            {
                "seed": seed,
                "standard_best_fitness": standard_result["best_fitness"],
                "standard_late_tasks": standard_result["late_tasks"],
                "standard_prereq_violations": standard_result["prerequisite_violations"],
                "standard_overlap_violations": standard_result["overlap_violations"],
                "standard_window_violations": standard_result["window_violations"],
                "standard_total_lateness_hours": standard_result["total_lateness_hours"],
                "custom_best_fitness": custom_result["best_fitness"],
                "custom_late_tasks": custom_result["late_tasks"],
                "custom_prereq_violations": custom_result["prerequisite_violations"],
                "custom_overlap_violations": custom_result["overlap_violations"],
                "custom_window_violations": custom_result["window_violations"],
                "custom_total_lateness_hours": custom_result["total_lateness_hours"],
                "winner": winner,
            }
        )

    result_df = pd.DataFrame(rows)
    scoreboard_df = pd.DataFrame(
        {
            "algorithm": [STANDARD_NAME, CUSTOM_NAME, "Draw"],
            "wins": [score[STANDARD_NAME], score[CUSTOM_NAME], score["Draw"]],
        }
    )

    print("\n=== DATAFRAME VIEW ===")
    print(result_df)

    print("\n=== SCOREBOARD ===")
    print(scoreboard_df)

    print("\n=== AVERAGE METRICS ===")
    average_df = pd.DataFrame(
        {
            "algorithm": [STANDARD_NAME, CUSTOM_NAME],
            "avg_late_tasks": [
                result_df["standard_late_tasks"].mean(),
                result_df["custom_late_tasks"].mean(),
            ],
            "avg_prereq_violations": [
                result_df["standard_prereq_violations"].mean(),
                result_df["custom_prereq_violations"].mean(),
            ],
            "avg_overlap_violations": [
                result_df["standard_overlap_violations"].mean(),
                result_df["custom_overlap_violations"].mean(),
            ],
            "avg_window_violations": [
                result_df["standard_window_violations"].mean(),
                result_df["custom_window_violations"].mean(),
            ],
            "avg_total_lateness_hours": [
                result_df["standard_total_lateness_hours"].mean(),
                result_df["custom_total_lateness_hours"].mean(),
            ],
            "avg_best_fitness": [
                result_df["standard_best_fitness"].mean(),
                result_df["custom_best_fitness"].mean(),
            ],
        }
    )
    print(average_df)


if __name__ == "__main__":
    main()