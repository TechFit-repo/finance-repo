import datetime as dt
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

def notify_report():
    print('Writing in file')
    with open('/Users/greengodfitness/Desktop/TechFit/finance-repo/techfit-finance-repo/log/notification.txt', 'a+', encoding='utf8') as f:
        now = dt.datetime.now()
        t = now.strftime("%Y-%m-%d %H:%M")
        f.write(str(t) + '\n')
        f.write(str('Master Statement Created...') + '\n')
    return 'Master Statement Created...'

default_args = {
    'owner': 'airflow',
    'start_date': dt.datetime(2020, 3, 28, 10, 00, 00),
    'concurrency': 1,
    'retries': 0
}

with DAG('finance_dag',
         default_args=default_args,
         schedule_interval='*/30 * * * *',
         ) as dag:
    opr_finance = BashOperator(task_id='run_report',
                             bash_command='/Users/greengodfitness/Desktop/TechFit/finance-repo/techfit-finance-repo/bin/run-script.sh ')

    opr_notify_report = PythonOperator(task_id='notify_report',
                               python_callable=notify_report)

opr_finance >> opr_notify_report
