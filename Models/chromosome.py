import random

class Chromosome:
    def __init__(self, genes=None):
        self.genes = genes if genes is not None else []
        self.fitness = None

    def random_initialize(self, num_genes=5):
        self.genes = [random.randint(0, 100) for _ in range(num_genes)]

    def __repr__(self):
        return f"Chromosome(genes={self.genes}, fitness={self.fitness})"