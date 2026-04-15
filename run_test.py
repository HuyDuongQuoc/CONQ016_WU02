import pandas as pd

from Models.api import optimize_tasks
from Models.config import GAConfig


def main():
    df = pd.read_csv("Data/df_500_tasks.csv")

    config = GAConfig(
        population_size=40,
        generations=60,
        mutation_rate=0.18,
        crossover_rate=0.85,
    )

    result = optimize_tasks(df, config=config)

    print("=== BEST FITNESS ===")
    print(result["best_fitness"])
    print()

    print("=== METRICS ===")
    for k, v in result["metrics"].items():
        print(f"{k}: {v}")
    print()

    print("=== TOP 10 SCHEDULED TASKS ===")
    print(result["gantt_df"].head(10).to_string(index=False))

    result["gantt_df"].to_csv("gantt_output.csv", index=False)
    result["history_df"].to_csv("history_output.csv", index=False)

    print()
    print("Saved: gantt_output.csv")
    print("Saved: history_output.csv")


if __name__ == "__main__":
    main()