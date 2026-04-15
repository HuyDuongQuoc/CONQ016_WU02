from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Task:
    task_id: str
    task_name: str
    estimated_duration_minutes: int
    deadline: datetime
    priority_level: str = "Medium"
    cognitive_load: float = 5.0
    urgency_score: float = 5.0
    prerequisites: list[str] = field(default_factory=list)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScheduledTask:
    task_id: str
    task_name: str
    start: datetime
    end: datetime
    priority_level: str
    urgency_score: float
    cognitive_load: float
    status: str
    deadline: datetime
    description: str = ""


@dataclass
class Chromosome:
    genes: list[int]
    fitness: float | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    def copy(self) -> "Chromosome":
        return Chromosome(genes=self.genes[:], fitness=self.fitness, metrics=self.metrics.copy())
