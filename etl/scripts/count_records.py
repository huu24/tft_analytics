from pyspark.sql import SparkSession
spark = SparkSession.builder.master('local[1]').appName('count').getOrCreate()

df = spark.read.parquet('s3a://lakehouse-bucket/tft-silver/participants')
c = df.count()
print('SILVER participants:', f'{c:,}')

gold_path = 's3a://lakehouse-bucket/tft-gold/'
fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())
path_obj = spark._jvm.org.apache.hadoop.fs.Path(gold_path)
statuses = fs.listStatus(path_obj)
dirs = [s.getPath().toString() for s in statuses if s.isDirectory()]
latest = sorted(dirs)[-1]
print(f'\nGOLD latest version: {latest.split("/")[-1]}')

tables = fs.listStatus(spark._jvm.org.apache.hadoop.fs.Path(latest))
for t in tables:
    if t.isDirectory():
        tbl = spark.read.parquet(t.getPath().toString())
        cnt = tbl.count()
        print(f'  {t.getPath().getName():35s}: {cnt:>10,} rows')
