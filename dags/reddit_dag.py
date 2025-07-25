from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
from decouple import config
from sqlalchemy import create_engine
import pandas as pd
import requests
import os
import pymysql


class RedditETLPipeline:
    def __init__(self):
        self.secret_token = config("SECRET_TOKEN")
        self.client_id = config("CLIENT_ID")
        self.username = config("USERNAME")
        self.password = config("PASSWORD")
        self.user_agent = 'ETL_Airflow/0.0.1'
        self.headers = self.authenticate()

    def authenticate(self):
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.secret_token)
        data = {'grant_type': 'password', 'username': self.username, 'password': self.password}
        headers = {'User-Agent': self.user_agent}
        res = requests.post('https://www.reddit.com/api/v1/access_token', auth=auth, data=data, headers=headers)
        token = res.json()['access_token']
        headers.update({'Authorization': f'bearer {token}'})
        return headers

    def df_from_response(self, data):
        records = []
        for post in data:
            post_data = post['data']
            records.append({
                'subreddit': post_data['subreddit'],
                'title': post_data['title'],
                'selftext': post_data['selftext'],
                'upvote_ratio': post_data['upvote_ratio'],
                'ups': post_data['ups'],
                'downs': post_data['downs'],
                'score': post_data['score'],
                'created_utc': datetime.fromtimestamp(post_data['created_utc']).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'id': post_data['id'],
                'kind': post['kind']
            })
        return pd.DataFrame(records)

    def fetch_data(self):
        all_data = pd.DataFrame()
        params = {'limit': 100}

        for _ in range(10):
            res = requests.get("https://oauth.reddit.com/r/python/new", headers=self.headers, params=params)
            data = res.json()['data']['children']
            df = self.df_from_response(data)

            if df.empty:
                break

            fullname = df.iloc[-1]['kind'] + "_" + df.iloc[-1]['id']
            params['after'] = fullname
            all_data = pd.concat([all_data, df], ignore_index=True)

        all_data.drop_duplicates(subset='id', inplace=True)
        return all_data

    def save_to_csv(self, df, path='/tmp/reddit_data.csv'):
        df.to_csv(path, index=False)
        return path

    def save_to_mysql(self, df):
        db_user = config("DB_USER")
        db_pass = config("DB_PASS")
        db_host = config("DB_HOST")
        db_name = config("DB_NAME")
        engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}")
        df.to_sql(name='reddit_posts', con=engine, if_exists='append', index=False)
        print("Data pushed to MySQL!")


etl = RedditETLPipeline()

def fetch_task_callable(**kwargs):
    df = etl.fetch_data()
    csv_path = etl.save_to_csv(df)
    kwargs['ti'].xcom_push(key='csv_path', value=csv_path)

def store_task_callable(**kwargs):
    csv_path = kwargs['ti'].xcom_pull(key='csv_path')
    df = pd.read_csv(csv_path)
    etl.save_to_mysql(df)


# Airflow DAG
with DAG(
    dag_id='reddit_etl_pipeline',
    default_args={'retries': 1, 'retry_delay': timedelta(minutes=2)},
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['reddit', 'ETL']
) as dag:

    fetch_task = PythonOperator(
        task_id='fetch_reddit_data',
        python_callable=fetch_task_callable,
        provide_context=True
    )

    store_task = PythonOperator(
        task_id='store_to_mysql',
        python_callable=store_task_callable,
        provide_context=True
    )

    fetch_task >> store_task
