from datetime import datetime, timedelta

import pandas as pd

from ga_engine import optimize_tasks
from ga_engine.config import GAConfig
from Data.data_preprocessing import CSVTaskProcessor
now = datetime.now()

processor = CSVTaskProcessor(now=datetime(2026, 3, 25, 8, 0))
df = processor.process_csv("Data/df_500_tasks.csv")

config = GAConfig(now=now, population_size=30, generations=40, mutation_rate=0.15)
result = optimize_tasks(df, config=config)
print(result["metrics"])
print(result["gantt_df"][["task_id", "task_name", "start", "end", "status"]])
