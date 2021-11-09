FROM apache/airflow:latest-python3.8

RUN pip install --no-cache-dir nltk==3.6.5
