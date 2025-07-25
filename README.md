# ETL_Pipeline_Airflow_Reddit_API

This project is an end-to-end ETL (Extract, Transform, Load) pipeline built using **Apache Airflow**, **Python**, and **Docker**. It extracts posts from a specified subreddit using the Reddit API, transforms the data using `pandas`, and loads it into a **MySQL** database.

---

## 🔧 Tech Stack

- **Apache Airflow** 2.8.1
- **Docker & Docker Compose**
- **Python 3.10**
- **Reddit API (via `requests`)**
- **MySQL** (for storing transformed data)
- **Pandas** (for transformation)

---

## 📂 Project Structure

```
ETL_Pipeline_Airflow_Reddit_API/
├── dags/
│   └── reddit_dag.py              # Main Airflow DAG file with ETL logic
├── .env                           # Reddit API and MySQL credentials (user-created)
├── requirements.txt               # Required Python packages
├── docker-compose.yml             # Docker services for Airflow and Postgres (metadata DB)
└── README.md
```

---

## 🧾 Step 1: Get Reddit API Credentials

To connect to Reddit's API, you need to register an application:

1. Visit: https://www.reddit.com/prefs/apps
2. Scroll down and click **“create another app…”**
3. Fill out the form:
   - **Name**: Any name like "Airflow ETL"
   - **Type**: Script
   - **Redirect URI**: `http://localhost`
   - Save and note down the following:
     - `client_id` (under the app name)
     - `client_secret` (right after you create)
     - Your Reddit `username` and `password`

Now create a `.env` file in the root directory:

```
SECRET_TOKEN=your_client_secret
CLIENT_ID=your_client_id
USERNAME=your_reddit_username
PASSWORD=your_reddit_password

DB_USER=your_mysql_user
DB_PASS=your_mysql_password
DB_NAME=your_mysql_db_name
DB_HOST=host.docker.internal
```

> Use `host.docker.internal` if your MySQL server is running on your **host OS** and not inside Docker.

---

## 🧾 Step 2: Set up MySQL

### Option A: Use Installed MySQL (e.g., Workbench)

1. Start MySQL on your machine (use Workbench or `mysql.server start`).
2. Create database:

```sql
CREATE DATABASE reddit_etl;
```

3. Create a user and grant privileges (optional):

```sql
CREATE USER 'myuser'@'localhost' IDENTIFIED BY 'mypassword';
GRANT ALL PRIVILEGES ON reddit_etl.* TO 'myuser'@'localhost';
FLUSH PRIVILEGES;
```

Add these values into your `.env`.

---

## 🐳 Step 3: Start the Airflow Environment

```bash
docker compose up --build
```

> This will start the Airflow webserver and scheduler containers.

---

## 🌐 Step 4: Initialize Airflow DB and Create Admin User

Once the containers are running:

### Open a terminal in the `airflow-webserver` container:

```bash
docker exec -it <webserver_container_id> bash
```

Then run:

```bash
airflow db init

airflow users create   --username <preferred username>   --firstname <FirstName>   --lastname <LastName>   --role Admin   --email abc@example.com   --password <preferred password>
```

This sets up the Airflow metadata DB and creates your admin user.

---

## 🎛️ Step 5: Access Airflow

- Navigate to: [http://localhost:8080](http://localhost:8080)
- Login with the credentials created above.

---

## 🚀 Step 6: Trigger the Pipeline

1. Locate the DAG named `reddit_etl_pipeline`.
2. Turn it on using the toggle.
3. Click ▶️ "Trigger DAG" to run the ETL process.

---

## 🧪 Sample SQL Queries

```sql
-- Show tables
SHOW TABLES;

-- Describe schema
DESCRIBE reddit_posts;

-- View latest records
SELECT * FROM reddit_posts ORDER BY created_utc DESC LIMIT 10;

-- Total records
SELECT COUNT(*) FROM reddit_posts;

-- Unique posts (based on Reddit post ID)
SELECT COUNT(DISTINCT id) FROM reddit_posts;
```

---

## ✅ Done!

You now have a working ETL pipeline that pulls fresh Reddit posts, transforms them, and loads them into MySQL using Airflow.
