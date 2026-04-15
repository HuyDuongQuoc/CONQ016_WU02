from __future__ import annotations

import random

from .config import GAConfig
from .models import Chromosome, Task
from .scheduler import repair_genes


def tournament_selection(population: list[Chromosome], k: int = 3) -> Chromosome:
    sampled = random.sample(population, k=min(k, len(population)))
    sampled.sort(key=lambda ch: ch.fitness if ch.fitness is not None else float("-inf"), reverse=True)
    return sampled[0].copy()


def crossover(parent_a: Chromosome, parent_b: Chromosome, tasks: list[Task], config: GAConfig) -> tuple[Chromosome, Chromosome]:
    size = len(parent_a.genes)
    if size < 2 or random.random() > config.crossover_rate:
        return parent_a.copy(), parent_b.copy()

    left = random.randint(0, size - 2)
    right = random.randint(left + 1, size - 1)
    child1_genes = parent_a.genes[:left] + parent_b.genes[left:right] + parent_a.genes[right:]
    child2_genes = parent_b.genes[:left] + parent_a.genes[left:right] + parent_b.genes[right:]

    child1 = Chromosome(genes=repair_genes(tasks, child1_genes, config))
    child2 = Chromosome(genes=repair_genes(tasks, child2_genes, config))
    return child1, child2


def mutate(chromosome: Chromosome, tasks: list[Task], config: GAConfig) -> Chromosome:
    genes = chromosome.genes[:]
    day_slots = ((config.day_end.hour * 60 + config.day_end.minute) - (config.day_start.hour * 60 + config.day_start.minute)) // config.slot_minutes

    for i in range(len(genes)):
        if random.random() < config.mutation_rate:
            shift = random.choice([-4, -2, -1, 1, 2, 4, day_slots])
            genes[i] = max(0, genes[i] + shift)

    if len(genes) >= 2 and random.random() < config.mutation_rate:
        a, b = random.sample(range(len(genes)), 2)
        genes[a], genes[b] = genes[b], genes[a]

    return Chromosome(genes=repair_genes(tasks, genes, config))
