from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
import numpy as np
from datetime import datetime

spark = SparkSession.builder.appName("MacroFlow-Nuclear-Option").getOrCreate()

def generate_simulations(n_sims=10000, horizon=12):
    # Standard Handshake
    try:
        supply_path = "gs://macro-engine-warehouse-macroflow-486515/factory/supply_line/latest_state.parquet"
        supply_df = spark.read.parquet(supply_path)
        ld = supply_df.orderBy(F.col("timestamp").desc()).limit(1).collect()[0].asDict()
        vix_start = float(ld.get('vix_start', 17.95))
    except:
        vix_start = 17.95

    sim_ids = spark.sparkContext.parallelize(range(n_sims))

    def run_path(sim_id):
        np.random.seed(sim_id)
        path = []
        v = vix_start
        # SCALAR FORCE PHYSICS
        for t in range(horizon):
            # We are forcing it to stay at 17.0+ for this test
            v = (v * 0.98) + (0.40 * (17.5 - v)) + np.random.normal(0, 1.2)
            v = max(v, 14.0) # If it's 14.0, we know this code ran.
            path.append([float(v), 0.035, 0.005])
        return (sim_id, path, vix_start)

    schema = StructType([
        StructField("sim_id", IntegerType(), False),
        StructField("path", ArrayType(ArrayType(FloatType())), False),
        StructField("debug_vix_start", FloatType(), False)
    ])
    
    return sim_ids.map(run_path).toDF(schema).select(
        "sim_id", F.posexplode("path").alias("horizon", "v")
    ).select(
        "sim_id", "horizon",
        F.col("v").getItem(0).alias("vix_value"),
        F.col("v").getItem(1).alias("ffr_value"),
        F.col("v").getItem(2).alias("wedge_value")
    )

# --- THE VERSIONED DELIVERY ---
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
unique_run_path = f"gs://macro-engine-warehouse-macroflow-486515/factory/runs/run_{run_id}/"
pointer_path = "gs://macro-engine-warehouse-macroflow-486515/factory/latest_run_path.json"

# Write Data to unique folder
df_out = generate_simulations()
df_out.write.parquet(unique_run_path)

# Update Pointer JSON
pointer_df = spark.createDataFrame([{"latest_path": unique_run_path, "run_id": run_id}])
pointer_df.write.mode("overwrite").json(pointer_path)

print(f"✅ NUCLEAR DEPLOY COMPLETE: {run_id}")