from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator


def check_kafka_topic():
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
            
        objects = list(client.list_objects(bucket, prefix="tft-raw/", recursive=True))
        if len(objects) > 0:
            print(f"✅ Success: Found {len(objects)} match JSON files in MinIO bucket '{bucket}' under 'tft-raw/'")
            return True
        else:
            raise Exception(f"No match JSON files found in MinIO bucket '{bucket}' under 'tft-raw/'")
    except Exception as e:
        raise Exception(f"MinIO raw match check failed: {str(e)}")


def verify_es_indices():
    from elasticsearch import Elasticsearch
    
    es = Elasticsearch(['http://localhost:9200'])
    
    expected_indices = [
        'tft-matches',
        'tft-players',
        'tft-augments',
        'tft-traits',
        'tft-units',
        'tft-items'
    ]
    
    for index_name in expected_indices:
        if not es.indices.exists(index=index_name):
            raise Exception(f"Index {index_name} does not exist")
        
        count = es.count(index=index_name)['count']
        if count == 0:
            raise Exception(f"Index {index_name} has no documents")
        
        print(f"Index {index_name}: {count} documents")
    
    print("All ES indices verified successfully")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'sla': timedelta(minutes=10),
}

with DAG(
    dag_id='tft_analytics_etl',
    default_args=default_args,
    description='TFT Analytics ETL Pipeline',
    schedule_interval='0 * * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['tft', 'etl'],
) as dag:
    
    check_kafka_topic = PythonOperator(
        task_id='check_kafka_topic',
        python_callable=check_kafka_topic,
    )
    
    run_spark_etl = BashOperator(
        task_id='run_spark_etl',
        bash_command='spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4,org.elasticsearch:elasticsearch-spark-30_2.12:8.13.0 etl/spark_jobs/tft_etl.py',
    )
    
    verify_es_indices = PythonOperator(
        task_id='verify_es_indices',
        python_callable=verify_es_indices,
    )
    
    send_notification = DummyOperator(
        task_id='send_notification',
    )
    
    check_kafka_topic >> run_spark_etl >> verify_es_indices >> send_notification
