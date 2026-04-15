from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from .config import GAConfig
from .data_adapter import normalize_tasks
from .optimizer import run_ga


def optimize_tasks(data: pd.DataFrame | list[dict], config: GAConfig | None = None) -> dict:
    tasks = normalize_tasks(data)
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
