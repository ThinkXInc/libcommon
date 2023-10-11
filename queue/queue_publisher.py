import pika
from redis import StrictRedis
import json
import time
import threading
import uuid
from typing import Dict, Any
# logger
import sys
sys.path.append('../../')
from libcommon.logger import Logger
logger = Logger('queue server')
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta, green, light_green
# queue config
from libcommon.queue.queue_config import QueueConfig
# queue server
from libcommon.queue.queue_server import Status, TaskMessage, StatusMessage, ResultMessage

DELIVERY_PERSISTENT = 2

class QueueConnectionManager:

    def __init__(self, config: QueueConfig):
        self.config = config
        self._connection = None
        self._channel = None
        self._closing = False

    @property
    def channel(self):
        return self._channel

    @property
    def connection(self):
        return self._connection

    @property
    def is_connected(self):
        return self._connection and self._connection.is_open

    # Methods

    def start_ioloop(self):
        if self._connection:
            self._connection.ioloop.start()
        else:
            logger.error(red('No connection.'))

    def open_channel(self):
        logger.info('Creating a new channel..')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def connect(self):
        try:
            credentials = pika.PlainCredentials(self.config.user, self.config.password)
            parameters = pika.ConnectionParameters(
                host=self.config.host,
                port=self.config.port,
                blocked_connection_timeout=self.config.blocked_connection_timeout,
                channel_max=self.config.channel_max,
                frame_max=self.config.frame_max,
                virtual_host=self.config.virtual_host,
                heartbeat=self.config.heartbeat,
                ssl_options=self.config.ssl_options,
                connection_attempts=self.config.connection_attempts,
                retry_delay=self.config.retry_delay,
                socket_timeout=self.config.socket_timeout,
                credentials=credentials
                # backpressure_detection was removed in pika code base, so we won't add it.
            )

            logger.info(str(self.config))

            self._connection = pika.SelectConnection(
                parameters=parameters,
                on_open_callback=self.on_connected,
                on_open_error_callback=self.on_connection_open_error,
                on_close_callback=self.on_connection_closed
            )

            # Start the I/O loop to process events
            #self._connection.ioloop.start()
            threading.Thread(target=self.start_ioloop, daemon=True).start()

        except Exception as e:
            logger.error(f"Error during connection: {e}")
            # Depending on your requirements, you might want to retry, raise the exception, or handle it in another way.
            raise e

    def close(self):
        self._closing = True
        # Close channel and connection
        if self._channel:
            self._channel.close()
            self._channel = None
        if self._connection:
            self._connection.close()
            self._connection = None

    def reconnect(self):
        time.sleep(5)  # wait for 5 seconds
        self.connect()

    # Handlers

    def on_connected(self, _unused_connection):
        """Called when we are fully connected to RabbitMQ"""
        logger.info(f'Connected to RabbitMQ on {_unused_connection.params.host}:{_unused_connection.params.port} with virtual host {_unused_connection.params.virtual_host}')
        self.open_channel()

    def on_channel_open(self, channel):
        """Called when our channel has opened"""
        logger.info(green(f'Channel {channel.channel_number} opened on {self.config.host}:{self.config.port}'))
        self._channel = channel
        self._channel.queue_declare(
            queue=self.config.task_queue_name,
            durable=self.config.queue_durable,
            exclusive=self.config.queue_exclusive,
            auto_delete=self.config.queue_auto_delete,
            callback=self.on_queue_declared
        )
        # Additional status queue declaration
        self._channel.queue_declare(
            queue=self.config.status_queue_name,
            durable=self.config.queue_durable,
            exclusive=self.config.queue_exclusive,
            auto_delete=self.config.queue_auto_delete
        )

    def on_connection_closed(self, _unused_connection, reason):
        if self._closing:
            logger.info(f'Connection stop.')
            self._connection.ioloop.stop()
        else:
            logger.warning(f'Connection closed, reconnect necessary: {reason}')
            self.reconnect()

    def on_connection_open_error(self, _unused_connection, err):
        logger.error(f'Connection open failed: {err}')
        self.reconnect()

    def on_queue_declared(self, frame):
        """Called when RabbitMQ has told us our Queue has been declared, frame is the response from RabbitMQ"""
        logger.info(bold(f'Queue {self.config.task_queue_name} declared successfully with message count: {frame.method.message_count}'))
        # Trigger any post-connection actions here. For example:
        self.post_connection_action()

    def post_connection_action(self):
        """A method to handle actions after connection is fully established and queue is declared."""
        # This is just a placeholder. You can expand on this method.
        logger.info(cyan(f'Connection established on {self.config.host}:{self.config.port} {self.config.task_queue_name}'))
        pass


class QueuePublisher:

    def __init__(self, config, connection_manager: QueueConnectionManager):
        self.config = config
        self.redis = StrictRedis(
            host=config.redis_config.host,
            port=config.redis_config.port,
            decode_responses=True  # add this if you want the responses to be str and not bytes
        )
        self._connection_manager = connection_manager
        self._channel = self._connection_manager.channel
        logger.info(f'Publisher initialized on {self.config.host}:{self.config.host} queue:{self.config.task_queue_name}.')

    def publish(self, message: str, delivery_mode=DELIVERY_PERSISTENT, mandatory=True) -> str:
        # Ensure thread safety if this is used in multi-threaded environments

        if not self._connection_manager.is_connected:
            raise Exception("Connection not open. Ensure you're connected first.")

        if not self._channel:
            raise Exception("Channel not opened. Ensure you're connected first.")
        
        try:
            request_id = self.random_id()
            self._channel.basic_publish(
                exchange='',
                routing_key=self.config.task_queue_name,
                body=TaskMessage(request_id=request_id, message=message).json(),
                properties=pika.BasicProperties(delivery_mode=delivery_mode),
                mandatory=mandatory
            )
        except Exception as e:
            logger.error(f"Error during publishing: {e}")
            # Depending on your requirements, you might want to retry, raise the exception, or handle it in another way.
            raise e

        logger.info(yellow(f'sent message: {message}'))
        return request_id

    def get_status(self, request_id: str) -> str:
        """Fetch status from Redis."""
        logger.info(f'trying to get status from Redis by request_id: {request_id}')

        try:
            # Fetch status from Redis
            status = self.redis.get(f"status:{request_id}")
            if status:
                logger.info(yellow(f'status retrieved: {status}'))
                return status
            else:
                logger.warning(yellow(f'status for {request_id} not found in Redis'))
                return "Not found"
        except Exception as e:
            logger.error(f"Error fetching status from Redis for request {request_id}: {e}")
            raise

    def get_result(self, request_id: str) -> Dict[str, Any]:
        """Fetch result data from Redis."""
        logger.info(f'trying to get result from Redis by request_id: {request_id}')

        try:
            # Fetch result from Redis
            result_json = self.redis.get(f"result:{request_id}")
            if result_json:
                result_message = ResultMessage.parse_raw(result_json)
                logger.info(yellow(f'result data retrieved: {result_message.result}'))
                return result_message.result
            else:
                logger.warning(yellow(f'result for {request_id} not found in Redis'))
                return {"error": "Result not found"}
        except Exception as e:
            logger.error(f"Error fetching result data from Redis for request {request_id}: {e}")
            raise

    def delete_status(self, request_id: str) -> bool:
        """Delete status from Redis."""
        logger.debug(f'trying to delete status from Redis by request_id: {request_id}')

        try:
            # Delete status from Redis
            result = self.redis.delete(f"status:{request_id}")
            if result:
                logger.info(light_green(f'status for {request_id} deleted from Redis'))
                return True
            else:
                logger.warning(yellow(f'status for {request_id} not found in Redis'))
                return False
        except Exception as e:
            logger.error(red(f"Error deleting status from Redis for request {request_id}: {e}"))
            raise

    def delete_result(self, request_id: str) -> bool:
        """Delete result data from Redis."""
        logger.debug(f'trying to delete result from Redis by request_id: {request_id}')

        try:
            # Delete result from Redis
            result = self.redis.delete(f"result:{request_id}")
            if result:
                logger.info(light_green(f'result for {request_id} deleted from Redis'))
                return True
            else:
                logger.warning(yellow(f'result for {request_id} not found in Redis'))
                return False
        except Exception as e:
            logger.error(red(f"Error deleting result data from Redis for request {request_id}: {e}"))
            raise

    def random_id(self) -> str:
        return str(uuid.uuid4().hex)



if __name__ == '__main__':
    # Usage example
    try:
        queue_config = QueueConfig()
        connection_manager = QueueConnectionManager(queue_config)

        ## Start the I/O loop in a separate thread
        connection_manager.connect()

        time.sleep(1)

        # Initialize Publisher
        publisher = QueuePublisher(queue_config, connection_manager)

        n = 5
        for i in range(n):
            time.sleep(1)
            # Publish message
            logger.info(yellow(f'[{i}/{n-1}]'))
            publisher.publish(str(f'{i}/{n-1}'))

    finally:
        # Ensure connection is always closed gracefully, even if there's an error
        time.sleep(1)
        connection_manager.close()
        print('Connection closed gracefully.')