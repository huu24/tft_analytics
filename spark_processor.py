from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, explode
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, ArrayType

# ==========================================
# 1. KHỞI TẠO SPARK SESSION (Bản ổn định 3.5.1)
# ==========================================
print("🚀 Đang khởi động Apache Spark...")
spark = SparkSession.builder \
    .appName("TFT_RealTime_Meta") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Các phần số 2, 3, 4, 5 giữ nguyên như cũ...

# ==========================================
# 2. ĐỊNH NGHĨA SCHEMA (BẢN VẼ DỮ LIỆU)
# ==========================================
# Vì file JSON quá lớn, ta chỉ định nghĩa những cột ta thực sự cần phân tích để Spark chạy nhanh hơn.

# Schema của Tộc/Hệ (Traits)
trait_schema = StructType([
    StructField("name", StringType()),
    StructField("tier_current", IntegerType())
])

# Schema của Tướng (Units)
unit_schema = StructType([
    StructField("character_id", StringType()),
    StructField("tier", IntegerType()), # Số sao
    StructField("itemNames", ArrayType(StringType())) # Mảng trang bị
])

# Schema của Người chơi (Participant)
participant_schema = StructType([
    StructField("puuid", StringType()),
    StructField("placement", IntegerType()),  # Hạng (1-8)
    StructField("level", IntegerType()),      # Cấp độ
    StructField("traits", ArrayType(trait_schema)), # Mảng Tộc hệ
    StructField("units", ArrayType(unit_schema))    # Mảng Tướng
])

# Schema Tổng của toàn bộ cục JSON
tft_schema = StructType([
    StructField("metadata", StructType([
        StructField("match_id", StringType())
    ])),
    StructField("info", StructType([
        StructField("participants", ArrayType(participant_schema))
    ]))
])

# ==========================================
# 3. ĐỌC DỮ LIỆU TỪ KAFKA (STREAMING)
# ==========================================
raw_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "tft-raw-matches") \
    .option("startingOffsets", "latest") \
    .load()

# Dữ liệu từ Kafka mặc định là dạng Byte. Ép kiểu về String.
json_df = raw_df.selectExpr("CAST(value AS STRING) as json_string")

# ==========================================
# 4. XỬ LÝ: ÉP KHUÔN VÀ ĐẬP PHẲNG (EXPLODE)
# ==========================================
# 4.1. Ốp cái Schema vào chuỗi JSON
parsed_df = json_df.select(from_json(col("json_string"), tft_schema).alias("data"))

# 4.2. Lấy match_id và mảng participants ra
matches_df = parsed_df.select(
    col("data.metadata.match_id").alias("match_id"),
    col("data.info.participants").alias("participants")
)

# 4.3. EXPLODE: Đập 1 dòng trận đấu thành 8 dòng người chơi
players_df = matches_df.select(
    col("match_id"),
    explode(col("participants")).alias("player") # <--- PHÉP THUẬT Ở ĐÂY
)

# 4.4. Trích xuất các cột cần thiết cho việc phân tích
final_df = players_df.select(
    col("match_id"),
    col("player.placement").alias("top"),
    col("player.level").alias("level"),
    col("player.puuid").alias("puuid")
)

# ==========================================
# 5. XUẤT KẾT QUẢ RA MÀN HÌNH (SINK)
# ==========================================
print("🎧 Đang lắng nghe luồng dữ liệu và đập phẳng...")
query = final_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

query.awaitTermination()
