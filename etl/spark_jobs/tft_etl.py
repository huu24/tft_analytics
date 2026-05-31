import os
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
    return (
        SparkSession.builder
        .appName("TFT_ETL")
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262,org.elasticsearch:elasticsearch-spark-30_2.12:8.13.0")
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.es.nodes", ES_HOST)
        .config("spark.es.port", ES_PORT)
        .config("spark.es.nodes.wan.only", "true")
        .config("spark.es.batch.size.bytes", "1mb")
        .config("spark.es.batch.size.entries", "500")
        .getOrCreate()
    )


def read_raw_matches(spark):
    return (
        spark.read
        .schema(MATCH_SCHEMA)
        .option("multiLine", "true")
        .json(RAW_PATH)
    )


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
        F.when(F.col("unique_items").isNotNull(), F.col("unique_items") / 9.0).otherwise(0.0)
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
            "match_id", "placement",
            F.col("unit.character_id").alias("character_id")
        )
        .filter(F.col("character_id").isNotNull())
        .dropDuplicates(["match_id", "character_id"])
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
        "character_id", "total_games", "wins", "top4_count", "avg_placement",
        "win_rate", "top4_rate", "pick_rate"
    )


def calc_item_stats(participants_df):
    items_df = (
        participants_df
        .select("match_id", "placement", F.explode("units").alias("unit"))
        .select("match_id", "placement", F.explode(F.col("unit.itemNames")).alias("item_name"))
        .filter(F.col("item_name").isNotNull() & (F.col("item_name") != ""))
        .dropDuplicates(["match_id", "item_name"])
    )

    stats = items_df.groupBy("item_name").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    return stats.select("item_name", "total_games", "wins", "top4_count", "avg_placement")


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
        .agg(F.concat_ws("|", F.collect_list("trait_name")).alias("signature"))
        .filter(F.col("signature") != "")
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

    stats = comp_with_units.groupBy("signature").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
        F.flatten(F.collect_list(F.coalesce(F.col("unit_set"), F.array()))).alias("all_units"),
    )
    stats = stats.withColumn(
        "win_rate",
        F.when(F.col("total_games") > 0, F.col("wins") / F.col("total_games")).otherwise(0.0)
    )
    stats = stats.withColumn(
        "top4_rate",
        F.when(F.col("total_games") > 0, F.col("top4_count") / F.col("total_games")).otherwise(0.0)
    )
    stats = stats.withColumn("core_units", F.array_distinct(F.col("all_units"))).drop("all_units")

    return stats.select(
        "signature", "total_games", "wins", "top4_count", "avg_placement",
        "win_rate", "top4_rate", "core_units"
    )


def calc_champion_item_combo(participants_df):
    combo_df = (
        participants_df
        .select("match_id", "placement", F.explode("units").alias("unit"))
        .select(
            "match_id", "placement",
            F.col("unit.character_id").alias("character_id"),
            F.explode(F.col("unit.itemNames")).alias("item_name")
        )
        .filter(
            F.col("character_id").isNotNull()
            & F.col("item_name").isNotNull()
            & (F.col("item_name") != "")
        )
        .dropDuplicates(["match_id", "character_id", "item_name"])
    )

    stats = combo_df.groupBy("character_id", "item_name").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    return stats.select("character_id", "item_name", "total_games", "wins", "top4_count", "avg_placement")


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
        .dropDuplicates(["match_id", "character_id", "trait_name"])
    )

    stats = combo_df.groupBy("character_id", "trait_name").agg(
        F.count("*").alias("total_games"),
        F.sum(F.when(F.col("placement") == 1, 1).otherwise(0)).alias("wins"),
        F.sum(F.when(F.col("placement") <= 4, 1).otherwise(0)).alias("top4_count"),
        F.avg("placement").alias("avg_placement"),
    )
    return stats.select("character_id", "trait_name", "total_games", "wins", "top4_count", "avg_placement")


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
        "puuid", "character_id", "total_games", "wins", "top4_count", "avg_placement",
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
    return stats.select(
        "puuid", "trait_name", "total_games", "wins", "top4_count", "avg_placement", "win_rate"
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
    return stats.select(
        "puuid", "item_name", "total_games", "wins", "top4_count", "avg_placement", "win_rate"
    )


def write_to_es(df, index_name, id_field=None):
    writer = (
        df.write
        .format("org.elasticsearch.spark.sql")
        .option("es.resource", index_name)
    )
    if id_field:
        writer = writer.option("es.mapping.id", id_field)
    
    writer.mode("append").save()


def main():
    print("🚀 Starting TFT ETL job...")
    spark = create_spark_session()
    print("✅ Spark session created")
    try:
        raw_df = read_raw_matches(spark)
        print(f"📥 Read {raw_df.count()} raw matches from MinIO")
        
        participants_df = explode_participants(raw_df)
        print(f"👥 Exploded to {participants_df.count()} participant records")

        print("📊 Calculating player stats...")
        player_stats = calc_player_stats(participants_df)
        print(f"   ✅ {player_stats.count()} player stats")
        
        print("📊 Calculating champion stats...")
        champion_stats = calc_champion_stats(participants_df)
        print(f"   ✅ {champion_stats.count()} champion stats")
        
        print("📊 Calculating item stats...")
        item_stats = calc_item_stats(participants_df)
        print(f"   ✅ {item_stats.count()} item stats")
        
        print("📊 Calculating comp meta...")
        comp_meta = calc_comp_meta(participants_df)
        print(f"   ✅ {comp_meta.count()} comp meta")
        
        print("📊 Calculating champion-item combos...")
        champion_item_combo = calc_champion_item_combo(participants_df)
        print(f"   ✅ {champion_item_combo.count()} champion-item combos")
        
        print("📊 Calculating champion-trait combos...")
        champion_trait_combo = calc_champion_trait_combo(participants_df)
        print(f"   ✅ {champion_trait_combo.count()} champion-trait combos")
        
        print("📊 Calculating player-champion stats...")
        player_champion_stats = calc_player_champion_stats(participants_df)
        print(f"   ✅ {player_champion_stats.count()} player-champion stats")
        
        print("📊 Calculating player-trait stats...")
        player_trait_stats = calc_player_trait_stats(participants_df)
        print(f"   ✅ {player_trait_stats.count()} player-trait stats")
        
        print("📊 Calculating player-item stats...")
        player_item_stats = calc_player_item_stats(participants_df)
        print(f"   ✅ {player_item_stats.count()} player-item stats")

        print("💾 Writing to Elasticsearch...")
        write_to_es(player_stats, "player_stats", "puuid")
        write_to_es(champion_stats, "champion_stats", "character_id")
        write_to_es(item_stats, "item_stats", "item_name")
        write_to_es(comp_meta, "comp_meta", "signature")
        write_to_es(champion_item_combo, "champion_item_combo")
        write_to_es(champion_trait_combo, "champion_trait_combo")
        
        write_to_es(player_champion_stats, "player_champion_stats")
        write_to_es(player_trait_stats, "player_trait_stats")
        write_to_es(player_item_stats, "player_item_stats")
        print("✅ All data written to Elasticsearch")
    finally:
        spark.stop()
        print("🛑 Spark session stopped")


if __name__ == "__main__":
    main()
