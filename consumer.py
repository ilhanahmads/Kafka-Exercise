from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, concat, lit
from pyspark.sql.types import StructType, StringType, IntegerType

spark = SparkSession.builder \
    .appName("SensorDataProcessor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0") \
    .getOrCreate()

# Konfig Kafka Stream
sensor_data = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "sensor-suhu") \
    .load()

# Define Skema Data Suhu
schema = StructType() \
    .add("sensor_id", StringType()) \
    .add("suhu", IntegerType())

# Convert Value dari Kafka ke JSON
sensor_df = sensor_data \
    .selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), schema).alias("data")) \
    .select("data.sensor_id", "data.suhu")

sensor_df_with_unit = sensor_df.withColumn("suhu", concat(col("suhu"), lit("°C")))

# Filter Suhu > 80°C
alert_df = sensor_df_with_unit.filter(sensor_df.suhu > 80)

# Menampilkan Alert
query = alert_df \
    .select("sensor_id", "suhu") \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()