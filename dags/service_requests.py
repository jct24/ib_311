from typing import Set
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
# from airflow.operators.python_operator import PythonOperator
from airflow.decorators import dag, task
# from airflow.operators.python import task, get_current_context
import requests
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import text
from sqlalchemy.types import Text, Float, Date, DateTime, Integer
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
from datetime import datetime
import os

# Setup
DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
FILE_URL = "https://s3.amazonaws.com/ibotta-data-engineer-test/311_service_requests.csv.zip"
target_db = "denver"

# Defaults arguments for all tasks
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2021, 11, 1),
    'retries': 0,
    # 'retry_delay': timedelta(minutes=1),
}

# Set up PG cnn, adjusting to write to "denver" db
split_uri = PostgresHook(postgres_conn_id='postgres_311').get_uri().split("/")
split_uri[3] = target_db
target_db_URI = "/".join(split_uri)

# Lack of schedule_interval requires manual run
with DAG(
    'service_requests',
    default_args=default_args,
    catchup=False, 
    template_searchpath='/opt/airflow/',
    schedule_interval=None
    ) as dag:

    @dag.task
    def dl_unzip_data(url):
        """Dowloads and unzips source file to local csv"""
        with requests.get(url, stream=True) as r:
            with ZipFile(BytesIO(r.content)) as z:
                with z.open(z.namelist()[0]) as csv_file:
                    pdf = pd.read_csv(csv_file, encoding="ISO-8859-1")
                    # with open(local_csv, 'wb') as f:
                        # shutil.copyfileobj(infile, f)

        return pdf

    @dag.task
    def clean_load_pg(pdf_csv):
        """Converts csv file to pandas and loads to PG"""
        
        # Set up PG cnn
        engine = create_engine(target_db_URI)
        
        # Append load_date column
        pdf_csv['load_date'] = pd.to_datetime('today').date()
        
        # Drop unused cols
        pdf_csv.drop(['Division', 'Major Area', 'Topic'], axis=1, inplace=True)
        
        # Clean up col names
        pdf_csv.rename(columns={
            "Case Summary": "case_summary",
            "Case Status": "case_status",
            "Case Source": "case_source",
            "Case Created Date": "case_created_date",
            "Case Created dttm": "case_created_dttm",
            "Case Closed Date": "case_closed_date",
            "Case Closed dttm": "case_closed_dttm",
            "First Call Resolution": "first_call_resolution",
            "Customer Zip Code": "customer_zip_code",
            "Incident Address 1": "incident_address_1",
            "Incident Address 2": "incident_address_2",
            "Incident Intersection 1": "incident_intersection_1",
            "Incident Intersection 2": "incident_intersection_2",
            "Incident Zip Code": "incident_zip_code",
            "Longitude": "longitude",
            "Latitude": "latitude",
            "Agency": "agency",
            "Type": "svc_type",
            "Council District": "council_district",
            "Police District": "police_district",
            "Neighborhood": "neighborhood"}, inplace=True)
        
        # Set datatypes
        dict_types = {
            "case_summary": Text(),
            "case_status": Text(),
            "case_source": Text(),
            "case_created_date": Date(),
            "case_created_dttm": DateTime(),
            "case_closed_date": Date(),
            "case_closed_dttm": DateTime(),
            "first_call_resolution": Text(),
            "customer_zip_code": Text(),
            "incident_address_1": Text(),
            "incident_address_2": Text(),
            "incident_intersection_1": Text(),
            "incident_intersection_2": Text(),
            "incident_zip_code": Text(),
            "longitude": Float(),
            "latitude": Float(),
            "agency": Text(),
            "svc_type": Text(),
            "council_district": Integer(),
            "police_district": Integer(),
            "neighborhood": Text(),
        }

        # Load to PG
        pdf_csv.to_sql(
            "service_requests", 
            con=engine, 
            index=False,
            if_exists='append', 
            schema='public',
            dtype=dict_types
        )

    clean_load_pg(dl_unzip_data(FILE_URL))
