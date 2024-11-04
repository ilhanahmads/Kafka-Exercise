# Kafka Exercise (Docker Kali Linux)

- Iki Adfi Nur M. (5027221033)
- Ilhan Ahmad Syafa (5027221040)

# Konfigurasi

## Requirements

- Docker
- Java (Java 11 recommended)
- Pyspark
- Kafka
- Install Kafka Python dengan `pip install kafka-python`

## 1. Buat file `docker-compose.yaml`. Sesuaikan field sesuai kebutuhan

```
services:
  zookeeper:
    image: 'bitnami/zookeeper:latest'
    container_name: zookeeper
    environment:
      - ALLOW_ANONYMOUS_LOGIN=yes
    ports:
      - '2181:2181'

  kafka:
    image: 'bitnami/kafka:latest'
    container_name: kafka
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - ALLOW_PLAINTEXT_LISTENER=yes
      - KAFKA_LISTENERS=PLAINTEXT://:9092
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
    ports:
      - '9092:9092'
    depends_on:
      - zookeeper
```

## 2. Jalankan docker dan pastikan container untuk masing-masing service berhasil dibuat dan berjalan sempurna

```
docker-compose up -d
docker-compose ps
docker-container ls
```

## 3. Setelah masing-masing service berjalan sempurna, buatlah topic sebagai jalur penghubung antara producer (pengirim data) dan consumer (penerima data). Sesuaikan nama container dan nama topik sesuai kebutuhan

```
docker exec -it <nama_container_kafka> kafka-topics.sh --create --topic <nama-topik> --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

## 4. Kita bisa cek daftar topic yang sudah ada dengan cara berikut

```
docker exec -it kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

## 5. Buat program python yang berperan sebagai producer pada file `producer.py`

```
# Producer

import time
import random
from kafka import KafkaProducer
import json

# Menghubungkan dengan Kafka (Producer)
producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def generate_sensor_data(sensor_id):
    suhu = random.randint(60, 100)
    return {'sensor_id': sensor_id, 'suhu': suhu}

sensor_ids = ['S1', 'S2', 'S3']

try:
    while True:
        for sensor_id in sensor_ids:
            data = generate_sensor_data(sensor_id)
            producer.send('sensor-suhu', data)
            print(f"Mengirim data: {data['sensor_id']} - {data['suhu']}°C")
        time.sleep(1)
except KeyboardInterrupt:
    producer.close()
    print("Producer stopped.")

```

## 6. Buat program python yang berperan sebagai consumer pada file `consumer.py`

```
# Consumer

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
```

## 6. Jalankan kedua program Python tersebut

![hasil](https://github.com/user-attachments/assets/eded89a9-1482-4af0-8950-5c9666a29442)
