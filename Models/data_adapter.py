from __future__ import annotations

import ast
from typing import Iterable

import pandas as pd

from .models import Task


PRIORITY_MAP = {"low": 3.0, "medium": 6.0, "high": 9.0}


def _parse_prerequisites(value) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []

    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "[]"}:
        return []

    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                return [str(v) for v in parsed if str(v).strip()]
        except Exception:
            pass

    return [item.strip() for item in text.split(",") if item.strip()]


def _normalize_deadline_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")

    if df["deadline"].isna().any():
        bad = df[df["deadline"].isna()]["task_id"].astype(str).tolist()
        raise ValueError(f"Invalid deadline format for tasks: {bad}")

    # Nếu giờ đang là 00:00:00 thì coi deadline là cuối ngày 23:59
    midnight_mask = (
        (df["deadline"].dt.hour == 0) &
        (df["deadline"].dt.minute == 0) &
        (df["deadline"].dt.second == 0)
    )
    df.loc[midnight_mask, "deadline"] = df.loc[midnight_mask, "deadline"] + pd.Timedelta(hours=23, minutes=59)

    return df


def normalize_tasks(data: pd.DataFrame | Iterable[dict]) -> list[Task]:
    df = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(list(data))

    required = {"task_id", "task_name", "estimated_duration_minutes", "deadline"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if "priority_level" not in df.columns:
        df["priority_level"] = "Medium"

    if "cognitive_load" not in df.columns:
        df["cognitive_load"] = 5.0

    if "urgency_score" not in df.columns:
        if "Urgency_Score" in df.columns:
            df["urgency_score"] = df["Urgency_Score"]
        else:
            df["urgency_score"] = 5.0

    if "prerequisites" not in df.columns:
        df["prerequisites"] = [[] for _ in range(len(df))]

    if "description" not in df.columns:
        df["description"] = ""

    df = _normalize_deadline_column(df)

    tasks: list[Task] = []
    for _, row in df.iterrows():
        priority = str(row.get("priority_level", "Medium") or "Medium").strip()

        task = Task(
            task_id=str(row["task_id"]),
            task_name=str(row["task_name"]),
            estimated_duration_minutes=max(30, int(row["estimated_duration_minutes"])),
            deadline=row["deadline"].to_pydatetime() if hasattr(row["deadline"], "to_pydatetime") else row["deadline"],
            priority_level=priority,
            cognitive_load=float(row.get("cognitive_load", 5.0) or 5.0),
            urgency_score=float(row.get("urgency_score", row.get("Urgency_Score", 5.0)) or 5.0),
            prerequisites=_parse_prerequisites(row.get("prerequisites", [])),
            description=str(row.get("description", "") or ""),
            metadata={
                "priority_score": PRIORITY_MAP.get(priority.lower(), 6.0),
            },
        )
        tasks.append(task)

    return tasks