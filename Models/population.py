from Models.chromosome import Chromosome

class Population:
    def __init__(self, size=10):
        self.size = size
        self.chromosomes = []

    def initialize(self, num_genes=5):
        self.chromosomes = []
        for _ in range(self.size):
            chromosome = Chromosome()
            chromosome.random_initialize(num_genes)
            self.chromosomes.append(chromosome)

    def __repr__(self):
        return f"Population(size={self.size}, chromosomes={self.chromosomes})"