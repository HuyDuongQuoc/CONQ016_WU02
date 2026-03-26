from __future__ import annotations

from datetime import datetime
import ast
from typing import Any, Dict, List, Tuple

import pandas as pd

from Models.fuzzy import build_fuzzy_engine, evaluate_and_sort_tasks



PRIORITY_MAP = {
    "low": 1,
    "medium": 2,
    "high": 3,
    1: 1,
    2: 2,
    3: 3,
}


class CSVTaskProcessor:
    """
    Xử lý CSV task và enrich bằng urgency_score từ fuzzy.

    Pipeline:
    1. load_csv()
    2. normalize_dataframe()
    3. apply_fuzzy()
    4. process_csv()  # all-in-one
    """

    def __init__(self, now: datetime | None = None):
        self.now = now or datetime.now()
        self.fuzzy_engine = build_fuzzy_engine()

    @staticmethod
    def _parse_prerequisites(value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(x) for x in value]

        if pd.isna(value):
            return []

        if isinstance(value, str):
            text = value.strip()
            if text == "" or text == "[]":
                return []
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except (ValueError, SyntaxError):
                pass
            return [text]

        return []

    @staticmethod
    def _normalize_priority(value: Any) -> int:
        if isinstance(value, str):
            value = value.strip().lower()
        return PRIORITY_MAP.get(value, 2)

    def load_csv(self, csv_path: str) -> pd.DataFrame:
        return pd.read_csv(csv_path)

    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        required_columns = [
            "task_id",
            "task_name",
            "estimated_duration_minutes",
            "deadline",
            "priority_level",
            "cognitive_load",
        ]

        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"CSV thiếu cột bắt buộc: {missing}")

        normalized = df.copy()
        normalized["deadline"] = pd.to_datetime(normalized["deadline"], errors="coerce")
        normalized["estimated_duration_minutes"] = pd.to_numeric(
            normalized["estimated_duration_minutes"], errors="coerce"
        ).fillna(0).astype(int)
        normalized["cognitive_load"] = pd.to_numeric(
            normalized["cognitive_load"], errors="coerce"
        ).fillna(5.0).clip(1, 10)
        normalized["priority_level_num"] = normalized["priority_level"].apply(self._normalize_priority)

        if "prerequisites" not in normalized.columns:
            normalized["prerequisites"] = [[] for _ in range(len(normalized))]
        else:
            normalized["prerequisites"] = normalized["prerequisites"].apply(self._parse_prerequisites)

        normalized = normalized.dropna(subset=["deadline"]).reset_index(drop=True)
        return normalized

    def to_fuzzy_tasks(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        task_list: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            hours_remaining = (row["deadline"] - self.now).total_seconds() / 3600.0
            task_list.append(
                {
                    "task_id": row["task_id"],
                    "task_name": row["task_name"],
                    "hours_remaining": round(hours_remaining, 4),
                    "priority_level": int(row["priority_level_num"]),
                    "cognitive_load": float(row["cognitive_load"]),
                    "duration_mins": int(row["estimated_duration_minutes"]),
                }
            )

        return task_list

    def apply_fuzzy(self, df: pd.DataFrame) -> pd.DataFrame:
        fuzzy_tasks = self.to_fuzzy_tasks(df)
        scored_tasks = evaluate_and_sort_tasks(fuzzy_tasks, self.fuzzy_engine)

        urgency_map = {task["task_id"]: float(task["urgency_score"]) for task in scored_tasks}
        rank_map = {task["task_id"]: idx + 1 for idx, task in enumerate(scored_tasks)}
        hours_map = {task["task_id"]: float(task["hours_remaining"]) for task in scored_tasks}

        enriched = df.copy()
        enriched["hours_remaining"] = enriched["task_id"].map(hours_map)
        enriched["urgency_score"] = enriched["task_id"].map(urgency_map).fillna(5.0)
        enriched["fuzzy_rank"] = enriched["task_id"].map(rank_map)

        return enriched.sort_values(by=["fuzzy_rank", "deadline"]).reset_index(drop=True)

    def process_csv(self, csv_path: str) -> pd.DataFrame:
        raw_df = self.load_csv(csv_path)
        normalized_df = self.normalize_dataframe(raw_df)
        enriched_df = self.apply_fuzzy(normalized_df)
        return enriched_df

    def process_and_save(
        self,
        csv_path: str,
        output_path: str = "tasks_with_fuzzy.csv",
    ) -> Tuple[pd.DataFrame, str]:
        enriched_df = self.process_csv(csv_path)
        enriched_df.to_csv(output_path, index=False)
        return enriched_df, output_path

