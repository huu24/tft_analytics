import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from elasticsearch import Elasticsearch
from minio import Minio
from pyspark import StorageLevel
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType,
    LongType, BooleanType, ArrayType
)
from pyspark.sql import functions as F
from pyspark.sql.window import Window


MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
ES_HOST = os.environ.get("ES_HOST", "elasticsearch")
ES_PORT = os.environ.get("ES_PORT", "9200")
RAW_PATH = os.environ.get("RAW_PATH", "s3a://lakehouse-bucket/tft-raw/")
SILVER_PATH = os.environ.get("SILVER_PATH", "s3a://lakehouse-bucket/tft-silver")
GOLD_PATH = os.environ.get("GOLD_PATH", "s3a://lakehouse-bucket/tft-gold")
SILVER_FORMAT = os.environ.get("SILVER_FORMAT", "parquet").lower()
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "lakehouse-bucket")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.environ.get("POSTGRES_DB", "airflow")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "airflow")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "airflow")
MAPPINGS_DIR = Path(__file__).resolve().parent.parent / "config" / "es_mappings"

INDEX_NAMES = [
    "player_stats",
    "champion_stats",
    "item_stats",
    "comp_meta",
    "champion_item_combo",
    "champion_trait_combo",
    "player_champion_stats",
    "player_trait_stats",
    "player_item_stats",
]

TRAIT_SCHEMA = StructType([
    StructField("name", StringType(), True),
    StructField("num_units", IntegerType(), True),
    StructField("style", IntegerType(), True),
    StructField("tier_current", IntegerType(), True),
    StructField("tier_total", IntegerType(), True),
])

UNIT_SCHEMA = StructType([
    StructField("character_id", StringType(), True),
    StructField("tier", IntegerType(), True),
    StructField("itemNames", ArrayType(StringType()), True),
    StructField("items", ArrayType(IntegerType()), True),
    StructField("rarity", IntegerType(), True),
])

PARTICIPANT_SCHEMA = StructType([
    StructField("puuid", StringType(), True),
    StructField("placement", IntegerType(), True),
    StructField("level", IntegerType(), True),
    StructField("gold_left", IntegerType(), True),
    StructField("last_round", IntegerType(), True),
    StructField("total_damage_to_players", IntegerType(), True),
    StructField("time_eliminated", DoubleType(), True),
    StructField("augments", ArrayType(StringType()), True),
    StructField("traits", ArrayType(TRAIT_SCHEMA), True),
    StructField("units", ArrayType(UNIT_SCHEMA), True),
])

MATCH_SCHEMA = StructType([
    StructField("metadata", StructType([
        StructField("match_id", StringType(), True),
    ]), True),
    StructField("info", StructType([
        StructField("game_version", StringType(), True),
        StructField("game_datetime", LongType(), True),
        StructField("game_length", DoubleType(), True),
        StructField("queue_id", IntegerType(), True),
        StructField("tft_set_number", IntegerType(), True),
        StructField("participants", ArrayType(PARTICIPANT_SCHEMA), True),
    ]), True),
])


def create_spark_session():
    spark = (
        SparkSession.builder
        .appName("TFT_ETL")
        .master(os.environ.get("SPARK_MASTER", "local[4]"))
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262,org.elasticsearch:elasticsearch-spark-30_2.12:8.13.0")
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .config("spark.sql.catalog.lakehouse", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.lakehouse.type", "hadoop")
        .config("spark.sql.catalog.lakehouse.warehouse", f"{SILVER_PATH}/iceberg-warehouse")
        .config("spark.es.nodes", ES_HOST)
        .config("spark.es.port", ES_PORT)
        .config("spark.es.nodes.wan.only", "true")
        .config("spark.es.batch.size.bytes", "1mb")
        .config("spark.es.batch.size.entries", "500")
        .config("spark.es.http.timeout", os.environ.get("ES_HTTP_TIMEOUT", "10m"))
        .config("spark.es.http.retries", os.environ.get("ES_HTTP_RETRIES", "5"))
        .config("spark.es.batch.write.retry.count", os.environ.get("ES_BATCH_RETRY_COUNT", "5"))
        .config("spark.es.batch.write.retry.wait", os.environ.get("ES_BATCH_RETRY_WAIT", "30s"))
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(os.environ.get("SPARK_LOG_LEVEL", "ERROR"))
    return spark


def read_raw_matches(spark, raw_objects=None):
    paths = (
        [f"s3a://{MINIO_BUCKET}/{obj.object_name}" for obj in raw_objects]
        if raw_objects is not None else RAW_PATH
    )
    return (
        spark.read
        .schema(MATCH_SCHEMA)
        .option("multiLine", "true")
        .json(paths)
    )


def read_silver_participants(spark):
    if SILVER_FORMAT == "iceberg":
        return spark.table("lakehouse.silver.participants")
    return spark.read.parquet(f"{SILVER_PATH}/participants")


def write_silver_frame(spark, frame, table_name):
    if SILVER_FORMAT == "iceberg":
        spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.silver")
        qualified_name = f"lakehouse.silver.{table_name}"
        if spark.catalog.tableExists(qualified_name):
            frame.writeTo(qualified_name).append()
        else:
            frame.writeTo(qualified_name).partitionedBy("silver_batch_id").create()
        return
    frame.write.mode("append").partitionBy("silver_batch_id").parquet(f"{SILVER_PATH}/{table_name}")


def explode_participants(matches_df):
    exploded = (
        matches_df
        .select(
            F.col("metadata.match_id"),
            F.col("info.game_version"),
            F.col("info.game_datetime"),
            F.col("info.game_length"),
            F.col("info.queue_id"),
            F.col("info.tft_set_number"),
            F.explode(F.coalesce(F.col("info.participants"), F.array())).alias("p")
        )
        .select(
            "match_id", "game_version", "game_datetime", "game_length",
            "queue_id", "tft_set_number",
            F.col("p.puuid"),
            F.col("p.placement"),
            F.col("p.level"),
            F.col("p.gold_left"),
            F.col("p.last_round"),
            F.col("p.total_damage_to_players"),
            F.col("p.time_eliminated"),
            F.coalesce(F.col("p.augments"), F.array().cast(ArrayType(StringType()))).alias("augments"),
            F.coalesce(F.col("p.traits"), F.array().cast(ArrayType(TRAIT_SCHEMA))).alias("traits"),
            F.coalesce(F.col("p.units"), F.array().cast(ArrayType(UNIT_SCHEMA))).alias("units"),
        )
    )
    return exploded


def calc_player_stats(participants_df):
    base = participants_df.groupBy("puuid").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    base = base.withColumn(
        "win_rate",
        F.when(F.col("total_games") > 0, F.col("wins") / F.col("total_games")).otherwise(0.0)
    )
    base = base.withColumn(
        "top4_rate",
        F.when(F.col("total_games") > 0, F.col("top4_count") / F.col("total_games")).otherwise(0.0)
    )
    base = base.withColumn(
        "meta_score",
        F.when(F.col("avg_placement") > 0,
            0.4 * F.col("win_rate")
            + 0.3 * F.col("top4_rate")
            + 0.2 * (1.0 / F.col("avg_placement"))
            + 0.1 * F.col("win_rate")
        ).otherwise(0.0)
    )

    trait_counts = (
        participants_df
        .select("puuid", "match_id", F.explode("traits").alias("trait"))
        .select("puuid", "match_id", F.col("trait.name").alias("trait_name"))
        .groupBy("puuid", "trait_name")
        .count()
        .groupBy("puuid")
        .agg(F.max("count").alias("max_trait_count"), F.sum("count").alias("total_trait_games"))
    )
    base = base.join(trait_counts, on="puuid", how="left")
    base = base.withColumn(
        "flex_score",
        F.when(
            (F.col("total_trait_games").isNotNull()) & (F.col("total_games") > 0),
            1.0 - (F.col("max_trait_count") / F.col("total_games"))
        ).otherwise(0.0)
    )

    item_counts = (
        participants_df
        .select("puuid", F.explode("units").alias("unit"))
        .select("puuid", F.explode(F.col("unit.itemNames")).alias("item_name"))
        .filter(F.col("item_name").isNotNull() & (F.col("item_name") != ""))
        .groupBy("puuid")
        .agg(F.countDistinct("item_name").alias("unique_items"))
    )
    base = base.join(item_counts, on="puuid", how="left")
    base = base.withColumn(
        "item_accuracy",
        F.when(F.col("unique_items").isNotNull(), F.least(F.col("unique_items") / 9.0, F.lit(1.0))).otherwise(0.0)
    )

    return base.select(
        "puuid", "total_games", "wins", "top4_count", "avg_placement",
        "win_rate", "top4_rate", "meta_score", "flex_score", "item_accuracy"
    )


def calc_champion_stats(participants_df):
    units_df = (
        participants_df
        .select("puuid", "match_id", "placement", F.explode("units").alias("unit"))
        .select(
            "match_id", "puuid", "placement",
            F.col("unit.character_id").alias("character_id")
        )
        .filter(F.col("character_id").isNotNull())
        .dropDuplicates(["match_id", "puuid", "character_id"])
    )

    total_matches = participants_df.select("match_id").distinct().count()

    stats = units_df.groupBy("character_id").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    stats = stats.withColumn(
        "win_rate",
        F.when(F.col("total_games") > 0, F.col("wins") / F.col("total_games")).otherwise(0.0)
    )
    stats = stats.withColumn(
        "top4_rate",
        F.when(F.col("total_games") > 0, F.col("top4_count") / F.col("total_games")).otherwise(0.0)
    )
    stats = stats.withColumn(
        "pick_rate",
        F.when(F.lit(total_matches) > 0, F.col("total_games") / F.lit(total_matches)).otherwise(0.0)
    )
    return stats.select(
        F.col("character_id").alias("champion_id"), "total_games", "wins", "top4_count", "avg_placement",
        "win_rate", "top4_rate", "pick_rate"
    )


def calc_item_stats(participants_df):
    items_df = (
        participants_df
        .select("match_id", "puuid", "placement", F.explode("units").alias("unit"))
        .select("match_id", "puuid", "placement", F.explode(F.col("unit.itemNames")).alias("item_name"))
        .filter(F.col("item_name").isNotNull() & (F.col("item_name") != ""))
        .dropDuplicates(["match_id", "puuid", "item_name"])
    )

    stats = items_df.groupBy("item_name").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    stats = stats.withColumn(
        "win_rate",
        F.when(F.col("total_games") > 0, F.col("wins") / F.col("total_games")).otherwise(0.0)
    )
    stats = stats.withColumn(
        "top4_rate",
        F.when(F.col("total_games") > 0, F.col("top4_count") / F.col("total_games")).otherwise(0.0)
    )
    return stats.select("item_name", "total_games", "wins", "top4_count", "avg_placement", "win_rate", "top4_rate")


def calc_comp_meta(participants_df):
    active_traits_df = (
        participants_df
        .select("match_id", "placement", "puuid", F.explode("traits").alias("trait"))
        .filter(F.col("trait.style") >= 1)
        .select("match_id", "placement", "puuid", F.col("trait.name").alias("trait_name"))
        .orderBy("trait_name")
    )

    comp_df = (
        active_traits_df
        .groupBy("match_id", "placement", "puuid")
        .agg(F.concat_ws("|", F.sort_array(F.collect_set("trait_name"))).alias("comp_signature"))
        .filter(F.col("comp_signature") != "")
    )

    core_units_df = (
        participants_df
        .select("match_id", "puuid", F.explode("units").alias("unit"))
        .select("match_id", "puuid", F.col("unit.character_id").alias("character_id"))
        .filter(F.col("character_id").isNotNull())
        .groupBy("match_id", "puuid")
        .agg(F.collect_set("character_id").alias("unit_set"))
    )

    comp_with_units = comp_df.join(core_units_df, on=["match_id", "puuid"], how="left")

    stats = comp_with_units.groupBy("comp_signature").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    unit_frequency = (
        comp_with_units
        .select(
            "comp_signature",
            F.explode(F.coalesce(F.col("unit_set"), F.array().cast(ArrayType(StringType())))).alias("champion_id"),
        )
        .groupBy("comp_signature", "champion_id")
        .count()
        .withColumn(
            "unit_rank",
            F.row_number().over(Window.partitionBy("comp_signature").orderBy(F.desc("count"), F.asc("champion_id")))
        )
        .filter(F.col("unit_rank") <= 8)
        .groupBy("comp_signature")
        .agg(F.collect_list("champion_id").alias("core_units"))
    )
    stats = stats.join(unit_frequency, on="comp_signature", how="left")
    stats = stats.withColumn(
        "win_rate",
        F.when(F.col("total_games") > 0, F.col("wins") / F.col("total_games")).otherwise(0.0)
    )
    stats = stats.withColumn(
        "top4_rate",
        F.when(F.col("total_games") > 0, F.col("top4_count") / F.col("total_games")).otherwise(0.0)
    )
    stats = stats.withColumn(
        "core_units",
        F.coalesce(F.col("core_units"), F.array().cast(ArrayType(StringType()))),
    )

    return stats.select(
        "comp_signature", "total_games", "wins", "top4_count", "avg_placement",
        "win_rate", "top4_rate", "core_units"
    )


def calc_champion_item_combo(participants_df):
    combo_df = (
        participants_df
        .select("match_id", "puuid", "placement", F.explode("units").alias("unit"))
        .select(
            "match_id", "puuid", "placement",
            F.col("unit.character_id").alias("character_id"),
            F.explode(F.col("unit.itemNames")).alias("item_name")
        )
        .filter(
            F.col("character_id").isNotNull()
            & F.col("item_name").isNotNull()
            & (F.col("item_name") != "")
        )
        .dropDuplicates(["match_id", "puuid", "character_id", "item_name"])
    )

    stats = combo_df.groupBy("character_id", "item_name").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    return stats.select(F.col("character_id").alias("champion_id"), "item_name", "total_games", "wins", "top4_count", "avg_placement")


def calc_champion_trait_combo(participants_df):
    units_df = (
        participants_df
        .select("match_id", "placement", "puuid", F.explode("units").alias("unit"))
        .select("match_id", "placement", "puuid", F.col("unit.character_id").alias("character_id"))
        .filter(F.col("character_id").isNotNull())
        .dropDuplicates(["match_id", "puuid", "character_id"])
    )

    traits_df = (
        participants_df
        .select("match_id", "puuid", F.explode("traits").alias("trait"))
        .filter(F.col("trait.style") >= 1)
        .select("match_id", "puuid", F.col("trait.name").alias("trait_name"))
        .dropDuplicates(["match_id", "puuid", "trait_name"])
    )

    combo_df = (
        units_df.join(traits_df, on=["match_id", "puuid"], how="inner")
        .dropDuplicates(["match_id", "puuid", "character_id", "trait_name"])
    )

    stats = combo_df.groupBy("character_id", "trait_name").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    return stats.select(F.col("character_id").alias("champion_id"), "trait_name", "total_games", "wins", "top4_count", "avg_placement")


def calc_player_champion_stats(participants_df):
    units_df = (
        participants_df
        .select("puuid", "match_id", "placement", F.explode("units").alias("unit"))
        .select(
            "puuid", "match_id", "placement",
            F.col("unit.character_id").alias("character_id")
        )
        .filter(F.col("character_id").isNotNull())
        .dropDuplicates(["puuid", "match_id", "character_id"])
    )
    stats = units_df.groupBy("puuid", "character_id").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    stats = stats.withColumn(
        "win_rate",
        F.when(F.col("total_games") > 0, F.col("wins") / F.col("total_games")).otherwise(0.0)
    )
    stats = stats.withColumn(
        "top4_rate",
        F.when(F.col("total_games") > 0, F.col("top4_count") / F.col("total_games")).otherwise(0.0)
    )
    return stats.select(
        "puuid", F.col("character_id").alias("champion_id"), "total_games", "wins", "top4_count", "avg_placement",
        "win_rate", "top4_rate"
    )


def calc_player_trait_stats(participants_df):
    traits_df = (
        participants_df
        .select("puuid", "match_id", "placement", F.explode("traits").alias("trait"))
        .filter(F.col("trait.style") >= 1)
        .select(
            "puuid", "match_id", "placement",
            F.col("trait.name").alias("trait_name")
        )
        .dropDuplicates(["puuid", "match_id", "trait_name"])
    )
    stats = traits_df.groupBy("puuid", "trait_name").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    stats = stats.withColumn(
        "win_rate",
        F.when(F.col("total_games") > 0, F.col("wins") / F.col("total_games")).otherwise(0.0)
    )
    stats = stats.withColumn(
        "top4_rate",
        F.when(F.col("total_games") > 0, F.col("top4_count") / F.col("total_games")).otherwise(0.0)
    )
    return stats.select(
        "puuid", "trait_name", "total_games", "wins", "top4_count", "avg_placement", "win_rate", "top4_rate"
    )


def calc_player_item_stats(participants_df):
    items_df = (
        participants_df
        .select("puuid", "match_id", "placement", F.explode("units").alias("unit"))
        .select(
            "puuid", "match_id", "placement",
            F.explode(F.col("unit.itemNames")).alias("item_name")
        )
        .filter(F.col("item_name").isNotNull() & (F.col("item_name") != ""))
        .dropDuplicates(["puuid", "match_id", "item_name"])
    )
    stats = items_df.groupBy("puuid", "item_name").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    stats = stats.withColumn(
        "win_rate",
        F.when(F.col("total_games") > 0, F.col("wins") / F.col("total_games")).otherwise(0.0)
    )
    stats = stats.withColumn(
        "top4_rate",
        F.when(F.col("total_games") > 0, F.col("top4_count") / F.col("total_games")).otherwise(0.0)
    )
    return stats.select(
        "puuid", "item_name", "total_games", "wins", "top4_count", "avg_placement", "win_rate", "top4_rate"
    )


def get_postgres_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def ensure_metadata_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS etl_runs (
                run_id UUID PRIMARY KEY,
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ,
                status VARCHAR(32) NOT NULL,
                raw_object_count INTEGER NOT NULL DEFAULT 0,
                new_object_count INTEGER NOT NULL DEFAULT 0,
                data_version VARCHAR(64),
                error_message TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS processed_raw_objects (
                object_name TEXT PRIMARY KEY,
                etag TEXT,
                size BIGINT NOT NULL,
                processed_at TIMESTAMPTZ NOT NULL,
                data_version VARCHAR(64) NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS data_versions (
                data_version VARCHAR(64) PRIMARY KEY,
                published_at TIMESTAMPTZ NOT NULL,
                raw_object_count INTEGER NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crawler_players (
                puuid TEXT PRIMARY KEY,
                player_name TEXT,
                region VARCHAR(16),
                tier VARCHAR(32),
                last_crawled_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("ALTER TABLE crawler_players ADD COLUMN IF NOT EXISTS player_name TEXT")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crawler_matches (
                match_id TEXT PRIMARY KEY,
                object_name TEXT NOT NULL,
                crawled_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS processed_silver_objects (
                object_name TEXT PRIMARY KEY,
                etag TEXT,
                size BIGINT NOT NULL,
                normalized_at TIMESTAMPTZ NOT NULL,
                silver_batch_id VARCHAR(64) NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS data_quality_runs (
                run_id UUID PRIMARY KEY REFERENCES etl_runs(run_id),
                checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                raw_match_count INTEGER NOT NULL,
                participant_count INTEGER NOT NULL,
                valid_participant_count INTEGER NOT NULL,
                rejected_participant_count INTEGER NOT NULL,
                duplicate_participant_count INTEGER NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_state (
                state_key VARCHAR(64) PRIMARY KEY,
                state_value TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
    conn.commit()


def get_minio_client():
    endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
    return Minio(
        endpoint,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_ENDPOINT.startswith("https://"),
    )


def list_raw_objects():
    client = get_minio_client()
    return list(client.list_objects(MINIO_BUCKET, prefix="tft-raw/", recursive=True))


def get_new_objects(conn, raw_objects, table_name="processed_raw_objects"):
    if table_name not in {"processed_raw_objects", "processed_silver_objects"}:
        raise ValueError(f"Unsupported watermark table: {table_name}")
    with conn.cursor() as cur:
        cur.execute(f"SELECT object_name, etag FROM {table_name}")
        processed = dict(cur.fetchall())
    return [
        obj for obj in raw_objects
        if processed.get(obj.object_name) != obj.etag
    ]


def set_pipeline_state(conn, key, value):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pipeline_state (state_key, state_value, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (state_key) DO UPDATE
            SET state_value = EXCLUDED.state_value,
                updated_at = EXCLUDED.updated_at
            """,
            (key, str(value)),
        )
    conn.commit()


def get_pipeline_state(conn, key, default=None):
    with conn.cursor() as cur:
        cur.execute("SELECT state_value FROM pipeline_state WHERE state_key = %s", (key,))
        row = cur.fetchone()
    return row[0] if row else default


def record_silver_objects(conn, silver_batch_id, raw_objects):
    normalized_at = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO processed_silver_objects (
                object_name, etag, size, normalized_at, silver_batch_id
            ) VALUES %s
            ON CONFLICT (object_name) DO UPDATE
            SET etag = EXCLUDED.etag,
                size = EXCLUDED.size,
                normalized_at = EXCLUDED.normalized_at,
                silver_batch_id = EXCLUDED.silver_batch_id
            """,
            [(obj.object_name, obj.etag, obj.size, normalized_at, silver_batch_id) for obj in raw_objects],
            template="(%s, %s, %s, %s, %s)",
            page_size=1000,
        )
    conn.commit()


def record_data_quality(
    conn, run_id, raw_match_count, participant_count, valid_count, rejected_count, duplicate_count
):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO data_quality_runs (
                run_id, raw_match_count, participant_count, valid_participant_count,
                rejected_participant_count, duplicate_participant_count
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id) DO UPDATE
            SET raw_match_count = EXCLUDED.raw_match_count,
                participant_count = EXCLUDED.participant_count,
                valid_participant_count = EXCLUDED.valid_participant_count,
                rejected_participant_count = EXCLUDED.rejected_participant_count,
                duplicate_participant_count = EXCLUDED.duplicate_participant_count
            """,
            (str(run_id), raw_match_count, participant_count, valid_count, rejected_count, duplicate_count),
        )
    conn.commit()


def normalize_to_silver(spark, conn, run_id, silver_batch_id, raw_objects, total_raw_object_count):
    print(f"🥈 Normalizing {len(raw_objects)} Raw objects into Silver batch {silver_batch_id}...")
    raw_df = (
        read_raw_matches(spark, raw_objects)
        .withColumn("_match_id", F.col("metadata.match_id"))
        .filter(F.col("_match_id").isNotNull())
        .dropDuplicates(["_match_id"])
        .drop("_match_id")
        .persist(StorageLevel.DISK_ONLY)
    )
    raw_match_count = raw_df.count()
    participants = explode_participants(raw_df).persist(StorageLevel.DISK_ONLY)
    participant_count = participants.count()
    valid_condition = (
        F.col("match_id").isNotNull()
        & F.col("puuid").isNotNull()
        & F.col("placement").between(1, 8)
    )
    valid = participants.filter(valid_condition)
    duplicate_count = valid.count() - valid.dropDuplicates(["match_id", "puuid"]).count()
    valid = (
        valid.dropDuplicates(["match_id", "puuid"])
        .withColumn("silver_batch_id", F.lit(silver_batch_id))
        .persist(StorageLevel.DISK_ONLY)
    )
    valid_count = valid.count()
    rejected = (
        participants.filter(~valid_condition)
        .withColumn(
            "rejection_reason",
            F.when(F.col("match_id").isNull(), "missing_match_id")
            .when(F.col("puuid").isNull(), "missing_puuid")
            .otherwise("placement_out_of_range"),
        )
        .withColumn("silver_batch_id", F.lit(silver_batch_id))
    )
    rejected_count = rejected.count()
    write_silver_frame(spark, valid, "participants")
    if rejected_count:
        write_silver_frame(spark, rejected, "quarantine")
    record_data_quality(
        conn, run_id, raw_match_count, participant_count, valid_count, rejected_count, duplicate_count
    )
    record_silver_objects(conn, silver_batch_id, raw_objects)
    set_pipeline_state(conn, "silver_last_batch_id", silver_batch_id)
    set_pipeline_state(conn, "silver_object_count", total_raw_object_count)
    valid.unpersist()
    participants.unpersist()
    raw_df.unpersist()
    print(
        f"✅ Silver batch: {valid_count} valid participants, "
        f"{rejected_count} rejected, {duplicate_count} duplicates removed"
    )


def write_gold_snapshot(snapshot_frames, data_version):
    if os.environ.get("ENABLE_GOLD_PARQUET", "true").lower() != "true":
        return
    for logical_name, (frame, _) in snapshot_frames.items():
        (
            frame.drop("_document_id")
            .write.mode("overwrite")
            .parquet(f"{GOLD_PATH}/data_version={data_version}/{logical_name}")
        )


def start_run(conn, run_id, raw_count, new_count, data_version):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO etl_runs (
                run_id, started_at, status, raw_object_count, new_object_count, data_version
            ) VALUES (%s, NOW(), 'running', %s, %s, %s)
            """,
            (str(run_id), raw_count, new_count, data_version),
        )
    conn.commit()


def finish_run(conn, run_id, status, error_message=None):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE etl_runs
            SET status = %s, error_message = %s, finished_at = NOW()
            WHERE run_id = %s
            """,
            (status, error_message, str(run_id)),
        )
    conn.commit()


def add_snapshot_metadata(df, data_version, raw_match_count):
    return (
        df.withColumn("data_version", F.lit(data_version))
        .withColumn("raw_match_count", F.lit(raw_match_count))
        .withColumn("last_updated", F.current_timestamp())
    )


def add_document_id(df, *columns):
    return df.withColumn("_document_id", F.sha2(F.concat_ws("|", *[F.col(c) for c in columns]), 256))


def write_to_es(df, index_name, id_field):
    writer = (
        df.write
        .format("org.elasticsearch.spark.sql")
        .option("es.resource", index_name)
    )
    writer = writer.option("es.mapping.id", id_field)
    writer.mode("append").save()


def load_mapping(index_name):
    with open(MAPPINGS_DIR / f"{index_name}.json", "r") as f:
        return json.load(f)


def create_version_indices(es, data_version):
    concrete_indices = {}
    for logical_name in INDEX_NAMES:
        concrete_name = f"{logical_name}_{data_version}"
        es_admin_call(es.indices.create, index=concrete_name, body=load_mapping(logical_name))
        concrete_indices[logical_name] = concrete_name
    return concrete_indices


def es_admin_call(func, **kwargs):
    timeout = int(os.environ.get("ES_ADMIN_TIMEOUT", "900"))
    attempts = int(os.environ.get("ES_ADMIN_RETRIES", "5"))
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            return func(request_timeout=timeout, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt == attempts:
                break
            wait_seconds = min(60, 5 * attempt)
            print(
                f"⚠️ Elasticsearch admin call failed on attempt {attempt}/{attempts}: {exc}. "
                f"Retrying in {wait_seconds}s..."
            )
            time.sleep(wait_seconds)
    raise last_exc


def wait_for_es_admin(es):
    timeout = int(os.environ.get("ES_ADMIN_TIMEOUT", "900"))
    try:
        es.cluster.health(
            wait_for_no_initializing_shards=True,
            wait_for_events="languid",
            timeout=f"{timeout}s",
            request_timeout=timeout,
        )
    except Exception as exc:
        print(f"⚠️ Elasticsearch health wait did not complete before alias publish: {exc}")


def publish_aliases(es, concrete_indices):
    wait_for_es_admin(es)
    actions = []
    for logical_name, concrete_name in concrete_indices.items():
        alias = f"tft_{logical_name}"
        if es_admin_call(es.indices.exists_alias, name=alias):
            actions.append({"remove": {"index": "*", "alias": alias}})
        actions.append({"add": {"index": concrete_name, "alias": alias}})
    es_admin_call(es.indices.update_aliases, body={"actions": actions})


def delete_indices(es, concrete_indices):
    for index_name in concrete_indices.values():
        if es_admin_call(es.indices.exists, index=index_name):
            es_admin_call(es.indices.delete, index=index_name)


def cleanup_old_snapshots(es, active_indices):
    retention = max(int(os.environ.get("ES_SNAPSHOT_RETENTION", "2")), 1)
    active = set(active_indices.values())
    for logical_name in INDEX_NAMES:
        try:
            indices = es_admin_call(
                es.indices.get,
                index=f"{logical_name}_v*",
                allow_no_indices=True,
            )
        except Exception as exc:
            print(f"⚠️ Could not list old snapshots for {logical_name}: {exc}")
            continue
        old_indices = sorted(set(indices) - active, reverse=True)
        for index_name in old_indices[retention - 1:]:
            try:
                es_admin_call(es.indices.delete, index=index_name)
            except Exception as exc:
                print(f"⚠️ Could not delete old snapshot {index_name}: {exc}")


def validate_snapshot(es, concrete_indices, raw_match_count):
    required = ["player_stats", "champion_stats", "item_stats", "comp_meta"]
    for logical_name in required:
        count = es_admin_call(es.count, index=concrete_indices[logical_name])["count"]
        if count == 0:
            raise RuntimeError(f"Snapshot validation failed: {logical_name} is empty")
    if raw_match_count <= 0:
        raise RuntimeError("Snapshot validation failed: MinIO raw object count is zero")


def record_published_snapshot(conn, data_version, raw_objects):
    processed_at = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute("UPDATE data_versions SET is_active = FALSE WHERE is_active = TRUE")
        cur.execute(
            """
            INSERT INTO data_versions (data_version, published_at, raw_object_count, is_active)
            VALUES (%s, NOW(), %s, TRUE)
            """,
            (data_version, len(raw_objects)),
        )
        execute_values(
            cur,
            """
            INSERT INTO processed_raw_objects (object_name, etag, size, processed_at, data_version)
            VALUES %s
            ON CONFLICT (object_name) DO UPDATE
            SET etag = EXCLUDED.etag,
                size = EXCLUDED.size,
                processed_at = EXCLUDED.processed_at,
                data_version = EXCLUDED.data_version
            """,
            [(obj.object_name, obj.etag, obj.size, processed_at, data_version) for obj in raw_objects],
            template="(%s, %s, %s, %s, %s)",
            page_size=1000,
        )
    conn.commit()


def get_run_publish_context(conn, data_version):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                r.run_id,
                r.raw_object_count,
                COALESCE(q.raw_match_count, 1) AS raw_match_count
            FROM etl_runs r
            LEFT JOIN data_quality_runs q ON q.run_id = r.run_id
            WHERE r.data_version = %s
            ORDER BY r.started_at DESC
            LIMIT 1
            """,
            (data_version,),
        )
        row = cur.fetchone()
    if not row:
        raise RuntimeError(f"No ETL run metadata found for {data_version}")
    raw_object_count = int(row[1] or 0)
    quality_match_count = int(row[2] or 1)
    # data_quality_runs stores only the latest Silver delta for incremental runs.
    # Republish needs a snapshot-level denominator for UI rates, so fall back to
    # the published raw object count when the quality count is clearly a delta.
    raw_match_count = quality_match_count
    if raw_object_count and quality_match_count < raw_object_count * 0.5:
        raw_match_count = raw_object_count
    return row[0], raw_object_count, raw_match_count


def record_republished_snapshot(conn, data_version, raw_object_count):
    with conn.cursor() as cur:
        cur.execute("UPDATE data_versions SET is_active = FALSE WHERE is_active = TRUE")
        cur.execute(
            """
            INSERT INTO data_versions (data_version, published_at, raw_object_count, is_active)
            VALUES (%s, NOW(), %s, TRUE)
            ON CONFLICT (data_version) DO UPDATE SET
                published_at = EXCLUDED.published_at,
                raw_object_count = EXCLUDED.raw_object_count,
                is_active = TRUE
            """,
            (data_version, raw_object_count),
        )
        cur.execute(
            """
            INSERT INTO processed_raw_objects (object_name, etag, size, processed_at, data_version)
            SELECT object_name, etag, size, NOW(), %s
            FROM processed_silver_objects
            ON CONFLICT (object_name) DO UPDATE SET
                etag = EXCLUDED.etag,
                size = EXCLUDED.size,
                processed_at = EXCLUDED.processed_at,
                data_version = EXCLUDED.data_version
            """,
            (data_version,),
        )
        cur.execute(
            """
            UPDATE etl_runs
            SET status = 'published', finished_at = NOW(), error_message = NULL
            WHERE data_version = %s
            """,
            (data_version,),
        )
    conn.commit()


def read_gold_snapshot(spark, data_version):
    frames = {}
    for logical_name in INDEX_NAMES:
        path = f"{GOLD_PATH}/data_version={data_version}/{logical_name}"
        frames[logical_name] = spark.read.parquet(path)

    def with_document_id(logical_name, *columns):
        frame = frames[logical_name]
        if "_document_id" in frame.columns:
            return frame
        return add_document_id(frame, *columns)

    return {
        "player_stats": (frames["player_stats"], "puuid"),
        "champion_stats": (frames["champion_stats"], "champion_id"),
        "item_stats": (frames["item_stats"], "item_name"),
        "comp_meta": (frames["comp_meta"], "comp_signature"),
        "champion_item_combo": (
            with_document_id("champion_item_combo", "champion_id", "item_name"),
            "_document_id",
        ),
        "champion_trait_combo": (
            with_document_id("champion_trait_combo", "champion_id", "trait_name"),
            "_document_id",
        ),
        "player_champion_stats": (
            with_document_id("player_champion_stats", "puuid", "champion_id"),
            "_document_id",
        ),
        "player_trait_stats": (
            with_document_id("player_trait_stats", "puuid", "trait_name"),
            "_document_id",
        ),
        "player_item_stats": (
            with_document_id("player_item_stats", "puuid", "item_name"),
            "_document_id",
        ),
    }


def republish_gold_snapshot():
    data_version = os.environ.get("REPUBLISH_DATA_VERSION")
    if not data_version:
        return False

    print(f"♻️ Republishing Gold Parquet snapshot {data_version} to Elasticsearch...")
    conn = get_postgres_connection()
    ensure_metadata_tables(conn)
    _, raw_object_count, raw_match_count = get_run_publish_context(conn, data_version)
    es = Elasticsearch(
        [f"http://{ES_HOST}:{ES_PORT}"],
        request_timeout=int(os.environ.get("ES_CLIENT_TIMEOUT", "300")),
        retry_on_timeout=True,
        max_retries=int(os.environ.get("ES_CLIENT_MAX_RETRIES", "5")),
    )
    spark = create_spark_session()
    concrete_indices = {}
    aliases_published = False
    try:
        snapshot_frames = read_gold_snapshot(spark, data_version)
        concrete_indices = create_version_indices(es, data_version)
        for logical_name, (frame, id_field) in snapshot_frames.items():
            print(f"   ↪ Writing {logical_name} to {concrete_indices[logical_name]}...")
            write_to_es(
                add_snapshot_metadata(frame, data_version, raw_match_count),
                concrete_indices[logical_name],
                id_field,
            )
        validate_snapshot(es, concrete_indices, raw_match_count)
        publish_aliases(es, concrete_indices)
        aliases_published = True
        record_republished_snapshot(conn, data_version, raw_object_count)
        set_pipeline_state(conn, "gold_last_data_version", data_version)
        set_pipeline_state(conn, "gold_last_silver_batch_id", data_version)
        cleanup_old_snapshots(es, concrete_indices)
        print(f"✅ Republished {data_version} and swapped aliases")
    except Exception:
        if concrete_indices and not aliases_published:
            delete_indices(es, concrete_indices)
        raise
    finally:
        spark.stop()
        conn.close()
        print("🛑 Spark session stopped")
    return True


def main():
    if republish_gold_snapshot():
        return

    print("🚀 Starting TFT ETL job...")
    conn = get_postgres_connection()
    ensure_metadata_tables(conn)
    raw_objects = list_raw_objects()
    new_objects = get_new_objects(conn, raw_objects)
    silver_objects = get_new_objects(conn, raw_objects, "processed_silver_objects")
    run_id = uuid.uuid4()
    data_version = datetime.now(timezone.utc).strftime("v%Y%m%d%H%M%S%f")
    silver_batch_id = data_version
    silver_last_batch = get_pipeline_state(conn, "silver_last_batch_id")
    gold_last_silver_batch = get_pipeline_state(conn, "gold_last_silver_batch_id")
    start_run(conn, run_id, len(raw_objects), len(silver_objects), data_version)
    if not silver_objects and not new_objects and silver_last_batch == gold_last_silver_batch:
        print("✅ No new MinIO objects. Silver and Gold layers are already current.")
        finish_run(conn, run_id, "skipped")
        conn.close()
        return

    es = Elasticsearch(
        [f"http://{ES_HOST}:{ES_PORT}"],
        request_timeout=int(os.environ.get("ES_CLIENT_TIMEOUT", "300")),
        retry_on_timeout=True,
        max_retries=int(os.environ.get("ES_CLIENT_MAX_RETRIES", "5")),
    )
    concrete_indices = {}
    aliases_published = False
    spark = create_spark_session()
    print("✅ Spark session created")
    try:
        if silver_objects:
            normalize_to_silver(spark, conn, run_id, silver_batch_id, silver_objects, len(raw_objects))
            silver_last_batch = silver_batch_id

        # Parquet is already the durable cache. Persisting this nested frame can
        # exhaust the driver heap while Spark builds cached column batches.
        participants_df = read_silver_participants(spark)
        raw_match_count = participants_df.select("match_id").distinct().count()
        print(f"📥 Read {raw_match_count} distinct matches from Silver")
        print(f"👥 Loaded {participants_df.count()} valid Silver participant records")

        print("📊 Calculating player stats...")
        player_stats = calc_player_stats(participants_df).persist(StorageLevel.MEMORY_AND_DISK)
        print(f"   ✅ {player_stats.count()} player stats")
        
        print("📊 Calculating champion stats...")
        champion_stats = calc_champion_stats(participants_df).persist(StorageLevel.MEMORY_AND_DISK)
        print(f"   ✅ {champion_stats.count()} champion stats")
        
        print("📊 Calculating item stats...")
        item_stats = calc_item_stats(participants_df).persist(StorageLevel.MEMORY_AND_DISK)
        print(f"   ✅ {item_stats.count()} item stats")
        
        print("📊 Calculating comp meta...")
        comp_meta = calc_comp_meta(participants_df).persist(StorageLevel.MEMORY_AND_DISK)
        print(f"   ✅ {comp_meta.count()} comp meta")
        
        print("📊 Calculating champion-item combos...")
        champion_item_combo = calc_champion_item_combo(participants_df).persist(StorageLevel.MEMORY_AND_DISK)
        print(f"   ✅ {champion_item_combo.count()} champion-item combos")
        
        print("📊 Calculating champion-trait combos...")
        champion_trait_combo = calc_champion_trait_combo(participants_df).persist(StorageLevel.MEMORY_AND_DISK)
        print(f"   ✅ {champion_trait_combo.count()} champion-trait combos")
        
        print("📊 Calculating player-champion stats...")
        player_champion_stats = calc_player_champion_stats(participants_df).persist(StorageLevel.MEMORY_AND_DISK)
        print(f"   ✅ {player_champion_stats.count()} player-champion stats")
        
        print("📊 Calculating player-trait stats...")
        player_trait_stats = calc_player_trait_stats(participants_df).persist(StorageLevel.MEMORY_AND_DISK)
        print(f"   ✅ {player_trait_stats.count()} player-trait stats")
        
        print("📊 Calculating player-item stats...")
        player_item_stats = calc_player_item_stats(participants_df).persist(StorageLevel.MEMORY_AND_DISK)
        print(f"   ✅ {player_item_stats.count()} player-item stats")

        print(f"💾 Publishing Elasticsearch snapshot {data_version}...")
        concrete_indices = create_version_indices(es, data_version)
        snapshot_frames = {
            "player_stats": (player_stats, "puuid"),
            "champion_stats": (champion_stats, "champion_id"),
            "item_stats": (item_stats, "item_name"),
            "comp_meta": (comp_meta, "comp_signature"),
            "champion_item_combo": (add_document_id(champion_item_combo, "champion_id", "item_name"), "_document_id"),
            "champion_trait_combo": (add_document_id(champion_trait_combo, "champion_id", "trait_name"), "_document_id"),
            "player_champion_stats": (add_document_id(player_champion_stats, "puuid", "champion_id"), "_document_id"),
            "player_trait_stats": (add_document_id(player_trait_stats, "puuid", "trait_name"), "_document_id"),
            "player_item_stats": (add_document_id(player_item_stats, "puuid", "item_name"), "_document_id"),
        }
        print(f"🏅 Writing Gold Parquet snapshot {data_version}...")
        write_gold_snapshot(snapshot_frames, data_version)
        for logical_name, (frame, id_field) in snapshot_frames.items():
            write_to_es(
                add_snapshot_metadata(frame, data_version, raw_match_count),
                concrete_indices[logical_name],
                id_field,
            )
        validate_snapshot(es, concrete_indices, raw_match_count)
        publish_aliases(es, concrete_indices)
        aliases_published = True
        record_published_snapshot(conn, data_version, raw_objects)
        set_pipeline_state(conn, "gold_last_silver_batch_id", silver_last_batch or "")
        set_pipeline_state(conn, "gold_last_data_version", data_version)
        cleanup_old_snapshots(es, concrete_indices)
        finish_run(conn, run_id, "published")
        print("✅ Snapshot validated and aliases published")
    except Exception as exc:
        finish_run(conn, run_id, "failed", str(exc))
        if concrete_indices and not aliases_published:
            delete_indices(es, concrete_indices)
        raise
    finally:
        spark.stop()
        conn.close()
        print("🛑 Spark session stopped")


if __name__ == "__main__":
    main()
