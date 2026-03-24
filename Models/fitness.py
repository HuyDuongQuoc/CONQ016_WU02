import random

def evaluate_fitness(chromosome):
    chromosome.fitness = round(random.uniform(0, 100), 2)
    return chromosome.fitness