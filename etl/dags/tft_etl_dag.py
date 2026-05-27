from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator


def check_kafka_topic():
    from kafka import KafkaConsumer
    import socket
    
    bootstrap_servers = 'localhost:9092'
    topic = 'tft-raw-matches'
    
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            consumer_timeout_ms=5000,
            auto_offset_reset='earliest'
        )
        
        messages = list(consumer)
        consumer.close()
        
        if len(messages) > 0:
            print(f"Found {len(messages)} messages in topic {topic}")
            return True
        else:
            raise Exception(f"No messages found in topic {topic}")
    except Exception as e:
        raise Exception(f"Kafka topic check failed: {str(e)}")


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
        bash_command='spark-submit etl/spark_jobs/tft_etl.py',
    )
    
    verify_es_indices = PythonOperator(
        task_id='verify_es_indices',
        python_callable=verify_es_indices,
    )
    
    send_notification = DummyOperator(
        task_id='send_notification',
    )
    
    check_kafka_topic >> run_spark_etl >> verify_es_indices >> send_notification
