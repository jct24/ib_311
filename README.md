## Data Engineer Take Home Project

 _Josh Templeton_

---

### Core Tasks

1. Download Denver 311 Service request and Traffic Accident data
2. Transform and Load to query store
3. Analyze for patterns / trends

### Proposed solution

1. Docker-based solution
2. Apache Airflow: data acquisition, transformation and loading
3. Postgres db as query store
4. Apache Superset for analysis / reporting

---
<br>

### Usage: __Airflow__
<br>
1. External volume for Postgres

`docker volume create --name postgres-db-volume -d local`

2. Bring up Postgres in background

`docker-compose -f up postgres -d`

3. Initialize Airflow

`docker-compose -f up airflow-init`

4. Bring up all services

`docker-compose -f up`

5. Login to Airflow UI

`http://localhost:8080`

User and Password = `airflow`

Under `DAGs` you will find 2 entries (`service_requests` and `traffic_accidents`) that correspond to the Python files found in `/dags/`

---
<br>

### Usage: __Superset__
<br>

The Superset instance is empty at the outset and requires manual set-up.

1. Either open the CLI to the Superset container through Docker desktop or:

`docker exec -it ib_311-superset-1 /bin/bash`

2. Create admin user

`superset fab create-admin --username superset --firstname Super --lastname Set --email admin@superset.com --password superset`

3. Upgrade the Superset database

`superset db upgrade`

4. Initialize Superset

`superset init`

5. Login to Superset UI

`http://localhost:8088`

6. Add database connection

  Data tab -> Databases -> `+ Database` button:

* Scroll to bottom and choose SQLAlchemy URI option and enter:
 `postgresql+psycopg2://superset:superset@postgres/denver`