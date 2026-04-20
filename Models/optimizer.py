from __future__ import annotations

import random
import time
from datetime import datetime
from math import ceil

from .config import GAConfig
from .fitness import evaluate
from .models import Chromosome, Task
from .operators import crossover, mutate, tournament_selection
from .scheduler import gene_to_schedule, repair_genes


def _make_random_chromosome(tasks: list[Task], config: GAConfig) -> Chromosome:
    random_genes = []
    slots_per_day = (
        ((config.day_end.hour * 60 + config.day_end.minute) - (config.day_start.hour * 60 + config.day_start.minute))
        // config.slot_minutes
    )
    horizon_days = max(7, ceil(len(tasks) / max(1, config.max_tasks_per_day)) + 10)
    for _ in tasks:
        random_genes.append(random.randint(0, slots_per_day * horizon_days - 1))

    genes = repair_genes(tasks, random_genes, config) if config.use_repair else random_genes
    return Chromosome(genes=genes)


def run_ga(tasks: list[Task], config: GAConfig | None = None) -> dict:
    config = config or GAConfig()
    random.seed(config.random_seed)
    if config.now is None:
        config.now = datetime.now()

    started = time.perf_counter()
    population = [_make_random_chromosome(tasks, config) for _ in range(config.population_size)]
    for individual in population:
        evaluate(tasks, individual, config)

    best = max(population, key=lambda ch: ch.fitness if ch.fitness is not None else float("-inf")).copy()
    history: list[float] = [best.fitness or 0.0]

    for _ in range(config.generations):
        population.sort(key=lambda ch: ch.fitness if ch.fitness is not None else float("-inf"), reverse=True)
        next_generation = [population[i].copy() for i in range(min(config.elite_size, len(population)))]

        while len(next_generation) < config.population_size:
            parent_a = tournament_selection(population)
            parent_b = tournament_selection(population)
            child1, child2 = crossover(parent_a, parent_b, tasks, config)
            child1 = mutate(child1, tasks, config)
            child2 = mutate(child2, tasks, config)
            evaluate(tasks, child1, config)
            evaluate(tasks, child2, config)
            next_generation.append(child1)
            if len(next_generation) < config.population_size:
                next_generation.append(child2)

        population = next_generation
        generation_best = max(population, key=lambda ch: ch.fitness if ch.fitness is not None else float("-inf"))
        if (generation_best.fitness or float("-inf")) > (best.fitness or float("-inf")):
            best = generation_best.copy()
        history.append(best.fitness or 0.0)

    schedule = gene_to_schedule(tasks, best.genes, config)
    runtime_seconds = time.perf_counter() - started

    return {
        "best_fitness": best.fitness,
        "schedule": schedule,
        "history": history,
        "metrics": {
            **best.metrics,
            "runtime_seconds": round(runtime_seconds, 4),
            "population_size": config.population_size,
            "generations": config.generations,
            "mutation_rate": config.mutation_rate,
            "use_repair": config.use_repair,
        },
    }