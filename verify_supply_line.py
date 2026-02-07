from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark = SparkSession.builder.appName("SchemaCheck").getOrCreate()
path = "gs://macro-engine-warehouse-macroflow-486515/factory/supply_line/latest_state.parquet"

try:
    df = spark.read.parquet(path)
    print("\n" + "="*40)
    print("📋 CURRENT SCHEMA:")
    df.printSchema()
    
    print("📈 LATEST RECORD:")
    df.orderBy(F.col("timestamp").desc()).show(1)
    print("="*40 + "\n")
except Exception as e:
    print(f"❌ Error reading supply line: {e}")
