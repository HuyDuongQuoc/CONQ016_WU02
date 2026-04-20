from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from .config import GAConfig
from .models import Chromosome, Task
from .scheduler import gene_to_schedule, repair_genes


def _allowed_day_end(moment: datetime, config: GAConfig) -> datetime:
    return datetime.combine(moment.date(), config.day_end)


def evaluate(tasks: list[Task], chromosome: Chromosome, config: GAConfig) -> float:
    if config.use_repair:
        chromosome.genes = repair_genes(tasks, chromosome.genes, config)

    schedule = gene_to_schedule(tasks, chromosome.genes, config)

    penalties = 0.0
    rewards = 0.0
    by_id = {item.task_id: item for item in schedule}
    task_by_id = {task.task_id: task for task in tasks}
    day_buckets = defaultdict(list)

    total_lateness_hours = 0.0
    prerequisite_violations = 0
    overlap_violations = 0
    cognitive_overload_violations = 0
    context_switches = 0
    window_violations = 0
    total_window_overflow_hours = 0.0

    for item in schedule:
        day_buckets[item.start.date()].append(item)

        lateness_hours = max(0.0, (item.end - item.deadline).total_seconds() / 3600)
        total_lateness_hours += lateness_hours
        penalties += lateness_hours * config.lateness_penalty_per_hour

        day_end = _allowed_day_end(item.start, config)
        overflow_hours = max(0.0, (item.end - day_end).total_seconds() / 3600)
        if overflow_hours > 0:
            window_violations += 1
            total_window_overflow_hours += overflow_hours
            penalties += overflow_hours * config.window_violation_penalty_per_hour

        priority_score = task_by_id[item.task_id].metadata.get("priority_score", 6.0)
        rewards += config.completion_reward_weight
        rewards += config.urgency_reward_weight * (item.urgency_score / 10.0)
        rewards += config.priority_reward_weight * (priority_score / 10.0)

    for task in tasks:
        current = by_id[task.task_id]
        for prereq in task.prerequisites:
            prereq_sched = by_id.get(prereq)
            if prereq_sched and current.start < prereq_sched.end:
                prerequisite_violations += 1
                penalties += config.prerequisite_penalty

    for _, items in day_buckets.items():
        items.sort(key=lambda x: x.start)
        for i in range(len(items) - 1):
            a, b = items[i], items[i + 1]
            if a.end > b.start:
                overlap_violations += 1
                penalties += config.overlap_penalty
            if a.cognitive_load >= 7 and b.cognitive_load >= 7:
                cognitive_overload_violations += 1
                penalties += config.cognitive_overload_penalty
            if a.priority_level != b.priority_level:
                context_switches += 1
                penalties += config.context_switch_penalty
            else:
                rewards += config.focus_bonus_weight

    chromosome.metrics = {
        "late_tasks": sum(1 for item in schedule if item.status == "late"),
        "on_time_tasks": sum(1 for item in schedule if item.status == "on_time"),
        "scheduled_tasks": len(schedule),
        "total_estimated_minutes": sum(task.estimated_duration_minutes for task in tasks),
        "total_lateness_hours": round(total_lateness_hours, 4),
        "prerequisite_violations": prerequisite_violations,
        "overlap_violations": overlap_violations,
        "cognitive_overload_violations": cognitive_overload_violations,
        "context_switches": context_switches,
        "window_violations": window_violations,
        "total_window_overflow_hours": round(total_window_overflow_hours, 4),
    }
    chromosome.fitness = rewards - penalties
    return chromosome.fitness