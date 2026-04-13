from dataclasses import dataclass
from datetime import datetime, time

@dataclass
class GAConfig:
    population_size: int = 40
    generations: int = 60
    mutation_rate: float = 0.18
    crossover_rate: float = 0.85
    elite_size: int = 4
    random_seed: int = 42
    day_start: time = time(8, 0)
    day_end: time = time(22, 0)
    slot_minutes: int = 30
    max_tasks_per_day: int = 8
    lateness_penalty_per_hour: float = 8.0
    overlap_penalty: float = 1000.0
    prerequisite_penalty: float = 200.0
    unassigned_penalty: float = 300.0
    cognitive_overload_penalty: float = 18.0
    context_switch_penalty: float = 1.5
    completion_reward_weight: float = 12.0
    urgency_reward_weight: float = 10.0
    priority_reward_weight: float = 7.0
    focus_bonus_weight: float = 2.0
    is_standard_ga: bool = False
    now: datetime | None = None
    
    
