import os
from pydantic import BaseModel
from pydantic import create_model
from typing import Dict, Type, List, Optional

def check_env():
    from dotenv import load_dotenv
    DOTENV_PATH = '/src/neuravoice-control-center/.env'
    REQUIRED_KEYS = [
        "REDIS_CACHE_HOST",
        "REDIS_CACHE_PORT",
        "REDIS_CACHE_LOGLEVEL",
        "REDIS_CACHE_EXPIRATION_TIME_SEC",
        # "REDIS_CACHE_PASSWORD"   # Uncomment this if you want to include password in the checks
    ]
    if os.path.exists(DOTENV_PATH):
        load_dotenv(DOTENV_PATH)
        # Check for required keys
        missing_keys = [key for key in REQUIRED_KEYS if key not in os.environ]
        if missing_keys:
            raise MissingKeyError(red(f"Missing keys in .env file: {', '.join(missing_keys)}"))
    else:
        print(red('[WARNING] no .env file exists in {}'.format(DOTENV_PATH)))

check_env()

class ResultDataFormat(BaseModel):
    # TODO: enable customization from outside of this file
    text: str
    token_ids: List[int]

class RedisConfig(BaseModel):
    host: str = os.environ.get("REDIS_CACHE_HOST")
    port: int = os.environ.get("REDIS_CACHE_PORT")
    loglevel: str = os.environ.get("REDIS_CACHE_LOGLEVEL")
    expiration_time: int = os.environ.get("REDIS_CACHE_EXPIRATION_TIME_SEC")  # default is 3 minutes in seconds
    #password: str = os.environ.get("REDIS_CACHE_PASSWORD")


class QueueConfig(BaseModel):
    user: str = 'guest'  # Assuming default RabbitMQ credentials. Change if necessary.
    password: str = 'guest'  # Assuming default RabbitMQ credentials. Change if necessary.
    host: str = 'localhost'
    port: int = 5672
    redis_config: RedisConfig = RedisConfig()
    blocked_connection_timeout: int = None
    channel_max: int = 65535
    frame_max: int = 131072
    virtual_host: str = '/'
    heartbeat: int = 0
    ssl_options: dict = None  # Assuming this is a dictionary. Adjust if needed.
    connection_attempts: int = 3
    retry_delay: int = 2
    socket_timeout: float = 0.25  # Float type since it's in fractions of a second
    queue_durable: bool = True
    queue_exclusive: bool = False
    queue_auto_delete: bool = False
    task_queue_name: str = 'task_queue'
    status_queue_name: str = 'status_queue'
    results_queue_name: str = 'results_queue'
    result_store_expire_in_sec: int = 3*60
    result_data_format = ResultDataFormat

    def __str__(self):
        return (
            f"QueueConfig("
            f"user={self.user}, "
            f"host={self.host}, "
            f"port={self.port}, "
            f"blocked_connection_timeout={self.blocked_connection_timeout}, "
            f"channel_max={self.channel_max}, "
            f"frame_max={self.frame_max}, "
            f"virtual_host={self.virtual_host}, "
            f"heartbeat={self.heartbeat}, "
            # Note: For better security, it's common practice not to display SSL options
            f"connection_attempts={self.connection_attempts}, "
            f"retry_delay={self.retry_delay}, "
            f"socket_timeout={self.socket_timeout}, "
            f"task_queue_name={self.task_queue_name}, "
            f"status_queue_name={self.status_queue_name}, "
            f"results_queue_name={self.results_queue_name}, "
            f"queue_durable={self.queue_durable}, "
            f"queue_exclusive={self.queue_exclusive}, "
            f"queue_auto_delete={self.queue_auto_delete},"
            f"result_store_expire_in_sec={self.result_store_expire_in_sec},"
            f"result_data_format={self.result_data_format}"
            f")"
        )

