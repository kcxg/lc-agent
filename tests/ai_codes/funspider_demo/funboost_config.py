# -*- coding: utf-8 -*-
"""
funspider_demo 专用的 funboost 配置。

funboost 优先读取"启动脚本所在目录"的 funboost_config.py，
这里复制自项目根配置，仅修改 SQLLITE_QUEUES_PATH / TXT_FILE_PATH
指向本 demo 目录，避免 SQLITE_QUEUE 队列文件写到盘根目录。
"""
import logging
from pathlib import Path
from funboost.utils.simple_data_class import DataClassBase
from nb_log import nb_log_config_default
from urllib.parse import quote_plus

DEMO_DIR = Path(__file__).parent


class BrokerConnConfig(DataClassBase):
    MONGO_CONNECT_URL = f'mongodb://127.0.0.1:27017'

    RABBITMQ_USER = 'rabbitmq_user'
    RABBITMQ_PASS = 'rabbitmq_pass'
    RABBITMQ_HOST = '127.0.0.1'
    RABBITMQ_PORT = 5672
    RABBITMQ_VIRTUAL_HOST = '/'
    RABBITMQ_URL = f'amqp://{RABBITMQ_USER}:{quote_plus(RABBITMQ_PASS)}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VIRTUAL_HOST}'

    REDIS_HOST = '127.0.0.1'
    REDIS_USERNAME = ''
    REDIS_PASSWORD = ''
    REDIS_PORT = 6379
    REDIS_DB = 7
    REDIS_DB_FILTER_AND_RPC_RESULT = 8
    REDIS_SSL = False
    REDIS_URL = f'{"rediss" if REDIS_SSL else "redis"}://{REDIS_USERNAME}:{quote_plus(REDIS_PASSWORD)}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    NSQD_TCP_ADDRESSES = ['127.0.0.1:4150']
    NSQD_HTTP_CLIENT_HOST = '127.0.0.1'
    NSQD_HTTP_CLIENT_PORT = 4151

    KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']
    KFFKA_SASL_CONFIG = {
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
        "sasl_plain_username": "",
        "sasl_plain_password": "",
        "sasl_mechanism": "SCRAM-SHA-256",
        "security_protocol": "SASL_PLAINTEXT",
    }

    SQLACHEMY_ENGINE_URL = 'sqlite:////sqlachemy_queues/queues.db'

    MYSQL_HOST = '127.0.0.1'
    MYSQL_PORT = 3306
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '123456'
    MYSQL_DATABASE = 'testdb6'

    # SQLITE_QUEUE / PERSISTQUEUE 队列文件落在 demo 目录下
    SQLLITE_QUEUES_PATH = str(DEMO_DIR / 'sqllite_queues')

    TXT_FILE_PATH = str(DEMO_DIR / 'txt_queues')

    ROCKETMQ_NAMESRV_ADDR = '192.168.199.202:9876'
    ROCKETMQ_ENDPOINTS = '127.0.0.1:8081'
    ROCKETMQ_ACCESS_KEY = ''
    ROCKETMQ_SECRET_KEY = ''

    MQTT_HOST = '127.0.0.1'
    MQTT_TCP_PORT = 1883

    HTTPSQS_HOST = '127.0.0.1'
    HTTPSQS_PORT = 1218
    HTTPSQS_AUTH = '123456'

    NATS_URL = 'nats://192.168.6.134:4222'

    KOMBU_URL = 'redis://127.0.0.1:6379/9'

    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/12'
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/13'

    DRAMATIQ_URL = RABBITMQ_URL

    PULSAR_URL = 'pulsar://192.168.70.128:6650'

    SQS_REGION_NAME = 'us-east-1'
    SQS_AWS_ACCESS_KEY_ID = ''
    SQS_AWS_SECRET_ACCESS_KEY = ''
    SQS_ENDPOINT_URL = ''

    POSTGRES_DSN = 'host=127.0.0.1 port=5432 dbname=funboost user=postgres password=123456'


class FunboostCommonConfig(DataClassBase):
    NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = logging.Formatter(
        f'%(asctime)s-({nb_log_config_default.computer_ip},{nb_log_config_default.computer_name})-[p%(process)d_t%(thread)d] - %(name)s - "%(filename)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(task_id)s - %(message)s',
        "%Y-%m-%d %H:%M:%S",)

    TIMEZONE = 'Asia/Shanghai'

    SHOW_HOW_FUNBOOST_CONFIG_SETTINGS = False  # demo 里屏蔽启动横幅，输出更干净
    FUNBOOST_PROMPT_LOG_LEVEL = logging.WARNING
    KEEPALIVETIMETHREAD_LOG_LEVEL = logging.WARNING
