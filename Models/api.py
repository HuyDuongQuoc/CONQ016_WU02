from __future__ import annotations

from datetime import datetime
from dataclasses import asdict

import pandas as pd

from .config import GAConfig
from .data_adapter import normalize_tasks
from .fuzzy import calculate_urgency_score
from .optimizer import run_ga


_PRIORITY_TO_NUM = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


def _attach_urgency_scores(df: pd.DataFrame, config: GAConfig) -> pd.DataFrame:
    df = df.copy()

    if "priority_level" not in df.columns:
        df["priority_level"] = "Medium"

    if "cognitive_load" not in df.columns:
        df["cognitive_load"] = 5.0

    if "urgency_score" not in df.columns and "Urgency_Score" not in df.columns:
        deadlines = pd.to_datetime(df["deadline"], errors="coerce")
        now = config.now or datetime.now()

        priority_nums = (
            df["priority_level"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(_PRIORITY_TO_NUM)
            .fillna(2)
            .astype(int)
        )

        hours_remaining = ((deadlines - now).dt.total_seconds() / 3600.0).fillna(0)

        df["urgency_score"] = [
            calculate_urgency_score(
                hours_remaining=float(h),
                priority_level=int(p),
                cognitive_load=float(c),
                duration_mins=int(d),
            )
            for h, p, c, d in zip(
                hours_remaining,
                priority_nums,
                df["cognitive_load"],
                df["estimated_duration_minutes"],
            )
        ]

    elif "Urgency_Score" in df.columns and "urgency_score" not in df.columns:
        df["urgency_score"] = df["Urgency_Score"]

    return df


def optimize_tasks(data: pd.DataFrame | list[dict], config: GAConfig | None = None) -> dict:
    config = config or GAConfig()

    df = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(list(data))
    df = _attach_urgency_scores(df, config)

    tasks = normalize_tasks(df)
    result = run_ga(tasks, config=config)

    gantt_rows = []
    for item in result["schedule"]:
        gantt_rows.append(
            {
                "task_id": item.task_id,
                "task_name": item.task_name,
                "start": item.start,
                "end": item.end,
                "deadline": item.deadline,
                "status": item.status,
                "priority_level": item.priority_level,
                "urgency_score": item.urgency_score,
                "cognitive_load": item.cognitive_load,
                "description": item.description,
            }
        )

    result["gantt_df"] = pd.DataFrame(gantt_rows).sort_values(by=["start", "deadline"]).reset_index(drop=True)
    result["history_df"] = pd.DataFrame(
        {"generation": list(range(len(result["history"]))), "best_fitness": result["history"]}
    )
    return result