from typing import Set
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.decorators import dag, task
import requests
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import text
from sqlalchemy.types import Text, Float, DateTime, Integer, BigInteger
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
from datetime import datetime
import os

# Setup
DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
FILE_URL = "https://s3.amazonaws.com/ibotta-data-engineer-test/traffic_accidents.csv.zip"
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
    'traffic_accidents',
    default_args=default_args,
    catchup=False, 
    template_searchpath='/opt/airflow/',
    schedule_interval=None
    ) as dag:

    @dag.task
    def dl_unzip_data(url: str):
        """Dowloads and unzips source file to local csv"""
        with requests.get(url, stream=True) as r:
            with ZipFile(BytesIO(r.content)) as z:
                with z.open(z.namelist()[0]) as csv_file:
                    pdf = pd.read_csv(csv_file, encoding="ISO-8859-1")

        return pdf

        
    @dag.task
    def prep_for_load(pdf):
        """Formats pd Dataframe for loading to Postgres"""

        # Append load_date column
        pdf['load_date'] = pd.to_datetime('today').date()
        
        # Drop unused cols
        # pdf.drop([], axis=1, inplace=True)
        
        # Clean up col names
        pdf = pdf.rename(columns=str.lower)

        return pdf


    @dag.task
    def load_to_pg(pdf):
        """Loads pd Dataframe to Postgres"""
        
        # Set up PG cnn
        engine = create_engine(target_db_URI)
        
        # Set sqlalchemy datatypes for Dataframe
        dict_types = {
            'objectid_1': BigInteger(),
            'incident_id': BigInteger(),
            'offense_id': BigInteger(),
            'offense_code': Integer(),
            'offense_code_extension': Integer(),
            'top_traffic_accident_offense': Text(),
            'first_occurrence_date': DateTime(),
            'last_occurrence_date': DateTime(),
            'reported_date': DateTime(),
            'incident_address': Text(),
            'geo_x': Float(),
            'geo_y': Float(),
            'geo_lon': Float(),
            'geo_lat': Float(),
            'district_id': Integer(),
            'precinct_id': Integer(),
            'neighborhood_id': Text(),
            'bicycle_ind': Integer(),
            'pedestrian_ind': Integer(),
            'harmful_event_seq_1': Text(),
            'harmful_event_seq_2': Text(),
            'harmful_event_seq_3': Text(),
            'road_location': Text(),
            'road_description': Text(),
            'road_contour': Text(),
            'road_condition': Text(),
            'light_condition': Text(),
            'tu1_vehicle_type': Text(),
            'tu1_travel_direction': Text(),
            'tu1_vehicle_movement': Text(),
            'tu1_driver_action': Text(),
            'tu1_driver_humancontribfactor': Text(),
            'tu1_pedestrian_action': Text(),
            'tu2_vehicle_type': Text(),
            'tu2_travel_direction': Text(),
            'tu2_vehicle_movement': Text(),
            'tu2_driver_action': Text(),
            'tu2_driver_humancontribfactor': Text(),
            'tu2_pedestrian_action': Text(),
            'seriously_injured': Integer(),
            'fatalities': Integer(),
            'fatality_mode_1': Text(),
            'fatality_mode_2': Text(),
            'seriously_injured_mode_1': Text(),
            'seriously_injured_mode_2': Text(),
        }

        # Load to PG
        pdf.to_sql(
            'traffic_accidents', 
            con=engine, 
            index=False,
            if_exists='append', 
            schema='public',
            dtype=dict_types
        )

    load_to_pg(prep_for_load(dl_unzip_data(FILE_URL)))
