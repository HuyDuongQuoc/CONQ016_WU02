from __future__ import annotations

from collections import defaultdict
from math import ceil

from .config import GAConfig
from .models import Chromosome, Task
from .scheduler import gene_to_schedule, repair_genes


def evaluate(tasks: list[Task], chromosome: Chromosome, config: GAConfig) -> float:
    chromosome.genes = repair_genes(tasks, chromosome.genes, config)
    schedule = gene_to_schedule(tasks, chromosome.genes, config)

    penalties = 0.0
    rewards = 0.0
    by_id = {item.task_id: item for item in schedule}
    task_by_id = {task.task_id: task for task in tasks}
    day_buckets = defaultdict(list)

    for item in schedule:
        day_buckets[item.start.date()].append(item)

        lateness_hours = max(0.0, (item.end - item.deadline).total_seconds() / 3600)
        penalties += lateness_hours * config.lateness_penalty_per_hour

        priority_score = task_by_id[item.task_id].metadata.get("priority_score", 6.0)
        rewards += config.urgency_reward_weight * (item.urgency_score / 10.0)
        rewards += config.priority_reward_weight * (priority_score / 10.0)
        rewards += config.completion_reward_weight

    for task in tasks:
        current = by_id[task.task_id]
        for prereq in task.prerequisites:
            prereq_sched = by_id.get(prereq)
            if prereq_sched and current.start < prereq_sched.end:
                penalties += config.prerequisite_penalty

    for day, items in day_buckets.items():
        items.sort(key=lambda x: x.start)
        for i in range(len(items) - 1):
            a, b = items[i], items[i + 1]
            if a.end > b.start:
                penalties += config.overlap_penalty
            if a.cognitive_load >= 7 and b.cognitive_load >= 7:
                penalties += config.cognitive_overload_penalty
            if a.priority_level != b.priority_level:
                penalties += config.context_switch_penalty
            else:
                rewards += config.focus_bonus_weight

    chromosome.metrics = {
        "late_tasks": sum(1 for item in schedule if item.status == "late"),
        "on_time_tasks": sum(1 for item in schedule if item.status == "on_time"),
        "scheduled_tasks": len(schedule),
        "total_estimated_minutes": sum(task.estimated_duration_minutes for task in tasks),
    }
    chromosome.fitness = rewards - penalties
    return chromosome.fitness
