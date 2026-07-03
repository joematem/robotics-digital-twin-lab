from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg://robotics:robotics_password@localhost:5433/robotics_lab"

engine = create_engine(DATABASE_URL)

run = {
    "experiment_name": "stage6_postgres_test",
    "stage": "database_verification",
    "metric": "connection_status",
    "value": 1.0,
    "created_at": datetime.now(timezone.utc),
}

df = pd.DataFrame([run])

with engine.begin() as conn:
    conn.execute(text("SELECT 1"))

df.to_sql("experiment_metrics", engine, if_exists="append", index=False)

with engine.begin() as conn:
    result = conn.execute(
        text("""
            SELECT experiment_name, stage, metric, value, created_at
            FROM experiment_metrics
            ORDER BY created_at DESC
            LIMIT 5
        """)
    )

    for row in result:
        print(dict(row._mapping))

print("PostgreSQL experiment logging OK")
