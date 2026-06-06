from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
import os


def check_raw_data():
    from minio import Minio
    import os
    
    endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    # Clean the endpoint for Minio library connect
    endpoint_clean = endpoint.replace("http://", "").replace("https://", "")
    access_key = os.getenv("MINIO_ACCESS_KEY", "admin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "password123")
    bucket = os.getenv("MINIO_BUCKET", "lakehouse-bucket")
    
    try:
        print(f"Connecting to MinIO at: {endpoint_clean}")
        client = Minio(
            endpoint_clean,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        
        if not client.bucket_exists(bucket):
            raise Exception(f"Bucket '{bucket}' does not exist")
            
        first_object = next(client.list_objects(bucket, prefix="tft-raw/", recursive=True), None)
        if first_object is None:
            raise Exception(f"No match JSON files found in MinIO bucket '{bucket}' under 'tft-raw/'")
        print(f"Raw match data is available: {first_object.object_name}")
        return True
    except Exception as e:
        raise Exception(f"MinIO raw match check failed: {str(e)}")


def verify_es_indices():
    from elasticsearch import Elasticsearch
    
    es_host = os.environ.get("ES_HOST", "localhost")
    es_port = os.environ.get("ES_PORT", "9200")
    
    # 2. Kết nối động qua mạng Docker (ví dụ: http://elasticsearch:9200)
    es = Elasticsearch([f'http://{es_host}:{es_port}'])
    
    expected_indices = [
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
    
    for index_name in expected_indices:
        alias_name = f"tft_{index_name}"
        if not es.indices.exists_alias(name=alias_name):
            raise Exception(f"Serving alias {alias_name} does not exist")
        
        count = es.count(index=alias_name)['count']
        if count == 0:
            raise Exception(f"Index {index_name} has no documents")
        
        print(f"Alias {alias_name}: {count} documents")
    
    print("All ES indices verified successfully")


def verify_data_quality():
    import psycopg2

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "airflow"),
        user=os.environ.get("POSTGRES_USER", "airflow"),
        password=os.environ.get("POSTGRES_PASSWORD", "airflow"),
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT participant_count, rejected_participant_count
                FROM data_quality_runs
                ORDER BY checked_at DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
        if not row:
            print("No new Silver batch was normalized; using the previous quality report.")
            return
        participant_count, rejected_count = row
        rejected_ratio = rejected_count / participant_count if participant_count else 0
        max_ratio = float(os.environ.get("DQ_MAX_REJECTED_RATIO", "0.02"))
        if rejected_ratio > max_ratio:
            raise Exception(
                f"Rejected participant ratio {rejected_ratio:.4f} exceeds threshold {max_ratio:.4f}"
            )
        print(f"Data quality passed: rejected participant ratio={rejected_ratio:.4f}")
    finally:
        conn.close()


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': int(os.environ.get("ETL_MAX_RETRIES", "3")),
    'retry_delay': timedelta(minutes=int(os.environ.get("ETL_RETRY_DELAY_MINUTES", "5"))),
    'sla': timedelta(minutes=10),
}

with DAG(
    dag_id='tft_analytics_etl',
    default_args=default_args,
    description='TFT Analytics ETL Pipeline',
    schedule_interval=os.environ.get("ETL_SCHEDULE_INTERVAL", "0 * * * *"),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['tft', 'etl'],
) as dag:
    
    check_raw_data = PythonOperator(
        task_id='check_raw_data',
        python_callable=check_raw_data,
    )
    
    run_spark_etl = BashOperator(
        task_id='run_spark_etl',
        bash_command='spark-submit --driver-memory 3g --executor-memory 3g /opt/airflow/etl/spark_jobs/tft_etl.py',
    )
    
    verify_es_indices = PythonOperator(
        task_id='verify_es_indices',
        python_callable=verify_es_indices,
    )

    verify_data_quality = PythonOperator(
        task_id='verify_data_quality',
        python_callable=verify_data_quality,
    )
    
    send_notification = DummyOperator(
        task_id='send_notification',
    )
    
    check_raw_data >> run_spark_etl >> verify_data_quality >> verify_es_indices >> send_notification
