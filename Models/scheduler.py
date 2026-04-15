from __future__ import annotations

from datetime import datetime, timedelta
from heapq import heappop, heappush
from math import ceil

from .config import GAConfig
from .models import ScheduledTask, Task


def gene_to_schedule(tasks: list[Task], genes: list[int], config: GAConfig) -> list[ScheduledTask]:
    base = config.now or datetime.now()
    start_anchor = datetime.combine(base.date(), config.day_start)
    slot_delta = timedelta(minutes=config.slot_minutes)
    slots_per_day = int(
        ((config.day_end.hour * 60 + config.day_end.minute) - (config.day_start.hour * 60 + config.day_start.minute))
        / config.slot_minutes
    )

    scheduled: list[ScheduledTask] = []
    for task, gene in zip(tasks, genes):
        day_offset = max(0, gene // slots_per_day)
        slot_offset = gene % slots_per_day
        start = start_anchor + timedelta(days=day_offset) + slot_delta * slot_offset
        duration_slots = max(1, ceil(task.estimated_duration_minutes / config.slot_minutes))
        end = start + slot_delta * duration_slots
        status = "late" if end > task.deadline else "on_time"

        scheduled.append(
            ScheduledTask(
                task_id=task.task_id,
                task_name=task.task_name,
                start=start,
                end=end,
                priority_level=task.priority_level,
                urgency_score=task.urgency_score,
                cognitive_load=task.cognitive_load,
                status=status,
                deadline=task.deadline,
                description=task.description,
            )
        )
    return scheduled


def _task_priority_key(task: Task) -> tuple:
    """
    Key nhỏ hơn sẽ được lấy trước trong heap.
    Ưu tiên:
    1. Deadline sớm hơn
    2. Urgency cao hơn
    3. Priority score cao hơn
    """
    return (
        task.deadline,
        -task.urgency_score,
        -task.metadata.get("priority_score", 6.0),
        task.task_id,
    )


def topological_task_order(tasks: list[Task]) -> list[int]:
    """
    Sắp xếp topo bằng thuật toán Kahn.
    Nếu có nhiều task cùng indegree = 0, dùng deadline / urgency / priority để chọn.
    Nếu đồ thị có chu trình, phần còn lại sẽ được nối vào cuối theo cùng tiêu chí để tránh crash.
    """
    task_map = {task.task_id: idx for idx, task in enumerate(tasks)}
    indegree = [0] * len(tasks)
    graph: dict[int, list[int]] = {i: [] for i in range(len(tasks))}

    for child_idx, task in enumerate(tasks):
        for prereq_id in task.prerequisites:
            parent_idx = task_map.get(prereq_id)
            if parent_idx is None:
                # prerequisite không tồn tại trong data thì bỏ qua
                continue
            graph[parent_idx].append(child_idx)
            indegree[child_idx] += 1

    heap: list[tuple[tuple, int]] = []
    for idx, deg in enumerate(indegree):
        if deg == 0:
            heappush(heap, (_task_priority_key(tasks[idx]), idx))

    order: list[int] = []
    while heap:
        _, current = heappop(heap)
        order.append(current)

        for nxt in graph[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                heappush(heap, (_task_priority_key(tasks[nxt]), nxt))

    # Nếu còn task chưa vào order => có cycle hoặc dữ liệu phụ thuộc lỗi
    if len(order) < len(tasks):
        remaining = [i for i in range(len(tasks)) if i not in set(order)]
        remaining.sort(key=lambda i: _task_priority_key(tasks[i]))
        order.extend(remaining)

    return order


def repair_genes(tasks: list[Task], genes: list[int], config: GAConfig) -> list[int]:
    base = config.now or datetime.now()
    start_anchor = datetime.combine(base.date(), config.day_start)
    _ = start_anchor  # giữ biến nếu sau này cần neo theo ngày

    slot_minutes = config.slot_minutes
    day_minutes = (config.day_end.hour * 60 + config.day_end.minute) - (
        config.day_start.hour * 60 + config.day_start.minute
    )
    slots_per_day = day_minutes // slot_minutes

    task_map = {task.task_id: idx for idx, task in enumerate(tasks)}

    # Thay vì sort thuần theo deadline, dùng topo order
    task_order = topological_task_order(tasks)

    repaired = genes[:]
    occupied: dict[int, list[tuple[int, int]]] = {}

    for idx in task_order:
        task = tasks[idx]
        duration_slots = max(1, ceil(task.estimated_duration_minutes / slot_minutes))
        preferred = max(0, repaired[idx])

        earliest_allowed = 0
        for prereq in task.prerequisites:
            p_idx = task_map.get(prereq)
            if p_idx is None:
                continue
            p_gene = repaired[p_idx]
            p_slots = max(1, ceil(tasks[p_idx].estimated_duration_minutes / slot_minutes))
            earliest_allowed = max(earliest_allowed, p_gene + p_slots)

        candidate = max(preferred, earliest_allowed)
        placed = False
        days_needed = ceil(len(tasks) / max(1, config.max_tasks_per_day)) + 10

        for shift in range(0, slots_per_day * days_needed):
            slot = candidate + shift
            day = slot // slots_per_day
            offset = slot % slots_per_day

            if offset + duration_slots > slots_per_day:
                continue

            intervals = occupied.setdefault(day, [])
            s, e = offset, offset + duration_slots

            if any(not (e <= a or s >= b) for a, b in intervals):
                continue

            if len(intervals) >= config.max_tasks_per_day:
                continue

            intervals.append((s, e))
            intervals.sort()
            repaired[idx] = slot
            placed = True
            break

        if not placed:
            fallback_day = max(occupied.keys(), default=0) + 1
            repaired[idx] = fallback_day * slots_per_day
            occupied.setdefault(fallback_day, []).append((0, duration_slots))

    return repaired