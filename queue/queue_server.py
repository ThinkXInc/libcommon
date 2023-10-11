import pika
from redis import StrictRedis
import json
from enum import Enum
from pydantic import BaseModel, Field, ValidationError
from typing import Union, Any, Dict
# logger
import sys
sys.path.append('../../')
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta, green, orange
# queue config
from libcommon.queue.queue_config import QueueConfig

# Create a global channel variable to hold our channel object in
channel = None

class Status(str, Enum):
    finished = "finished"
    progress = "progress"
    failed = "failed"


class TaskMessage(BaseModel):
    request_id: str = Field(..., description="Unique identifier for the request/task")
    message: str = Field(..., description="Request text message. e.g. prompt")


class StatusMessage(BaseModel):
    request_id: str = Field(..., description="Unique identifier for the request/task")
    status: str = Field(..., description="Current status of the request/task")


class ResultMessage(BaseModel):
    request_id: str = Field(..., description="Unique identifier for the request/task")
    result: Dict[str, Any] = Field(..., description="Result of the processed task containing text and token ids.")


class QueueServer:
    def __init__(self, config: QueueConfig):  # TODO: config type by pydantic
        self.config = config
        self.redis = StrictRedis(
            host=config.redis_config.host,
            port=config.redis_config.port,
            decode_responses=True  # add this if you want the responses to be str and not bytes
        )
        self.expiration_time = config.redis_config.expiration_time

        self._connection = None
        self._channel = None
        self._should_reconnect = False
        self._closing = False
        self._consuming = False
        self._consumer_tag = None

        self.registered_tasks = {}  # A dictionary to store the registered tasks

    def connect(self):
        """Establish connection to RabbitMQ."""
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

        return pika.SelectConnection(
            parameters=parameters,
            on_open_callback=self.on_connected,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed
        )

    # Handlers

    def on_connected(self, _unused_connection):
        """Called when we are fully connected to RabbitMQ"""
        self.open_channel()

    def on_channel_open(self, channel):
        """Called when our channel has opened"""
        logger.info(green(f'Channel {channel.channel_number} opened on {self.config.host}:{self.config.port}'))
        self._channel = channel
        # Task queue declaration
        self._channel.queue_declare(
            queue=self.config.task_queue_name,
            durable=self.config.queue_durable,
            exclusive=self.config.queue_exclusive,
            auto_delete=self.config.queue_auto_delete,
            callback=self.on_queue_declared
        )
        # Status queue declaration
        self._channel.queue_declare(
            queue=self.config.status_queue_name,
            durable=self.config.queue_durable,
            exclusive=self.config.queue_exclusive,
            auto_delete=self.config.queue_auto_delete
        )
        # Results queue declaration
        self._channel.queue_declare(
            queue=self.config.results_queue_name,
            durable=self.config.queue_durable,
            exclusive=self.config.queue_exclusive,
            auto_delete=self.config.queue_auto_delete
        )


    def on_connection_open_error(self, _unused_connection, err):
        logger.error('Connection open failed: %s', err)
        self.reconnect()

    def on_connection_closed(self, _unused_connection, reason):
        if self._closing:
            logger.info(f'Connection stop.')
            self._connection.ioloop.stop()
        else:
            logger.warning(f'Connection closed, reconnect necessary: {reason}')
            self.reconnect()

    def on_queue_declared(self, frame):
        """Called when RabbitMQ has told us our Queue has been declared, frame is the response from RabbitMQ"""
        logger.info(bold(f'Queue {self.config.task_queue_name} declared successfully with message count: {frame.method.message_count}'))
        self._channel.basic_consume(self.config.task_queue_name, on_message_callback=self.handle_delivery)

    # Methods

    def open_channel(self):
        logger.info('Creating a new channel..')
        logger.info(f'Connected to RabbitMQ on {self.config.host}:{self.config.port} with virtual host {self.config.virtual_host}')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def register_task(self, func, *args, **kwargs):
        """Method to register a task along with its arguments."""
        self.registered_tasks[func.__name__] = (func, args, kwargs)
        logger.info(f"Task registered: {func.__name__} with args {args} and kwargs {kwargs}")

    def handle_delivery(self, channel, method, header, request_body) -> str:
        """Called when we receive a message from RabbitMQ"""
        logger.info(magenta(f'Received message: {request_body}, delivery tag: {method.delivery_tag}, exchange: "{method.exchange}"'))

        data = json.loads(request_body)
        request_id = data["request_id"]
        message = data["message"]

        # Execute all registered tasks with the request_body and their registered arguments
        for task_name, (task_func, args, kwargs) in self.registered_tasks.items():
            try:
                task_func(request_id, message, *args, **kwargs)
                logger.info(green(f"Successfully executed task: {task_name}"))
            except Exception as e:
                logger.error(f"Error executing task {task_name}[{request_id}]: {e}")
                update_status_queue(request_id, Status.failed)

            # Update the status queue
            self.update_status_queue(request_id, Status.progress)

        channel.basic_ack(delivery_tag=method.delivery_tag)

    def update_status_queue(self, request_id: str, status: Status):
        try:
            self.redis.setex(f"status:{request_id}", self.expiration_time, status.value)
            logger.info(green(f"Updated status to '{status}' for request {request_id}"))
        except Exception as e:
            logger.error(f"Error updating status for request {request_id}: {e}")

    def update_results_queue(self, request_id: str, result_data: Dict[str, Any]):
        try:
            validated_data = self.config.result_data_format(**result_data)
            self.redis.setex(f"result:{request_id}", self.expiration_time, ResultMessage(request_id=request_id, result=validated_data.dict()).json())
            logger.info(green(f"Updated result data for request {request_id}"))
        except ValidationError as e:
            logger.error(f"Error validating result data for request {request_id}: {e}")
        except Exception as e:
            logger.error(f"Error updating result data for request {request_id}: {e}")

    def delete_from_results_queue(self, request_id: str):
        try:
            self.redis.delete(f"result:{request_id}")
            logger.info(green(f"Deleted result data for request {request_id}"))
        except Exception as e:
            logger.error(f"Error deleting result for request {request_id}: {e}")

    #def update_status_queue(self, request_id: str, status: Status):
    #    try:
    #        # Note: You need a reference to the channel. You can make the channel an instance variable in LLMConsumer
    #        self._channel.basic_publish(
    #            exchange='',
    #            routing_key=self.config.status_queue_name,
    #            body=StatusMessage(request_id=request_id, status=status.value).json()
    #        )
    #        logger.info(green(f"Updated status to {status} for request {request_id}"))
    #    except Exception as e:
    #        logger.error(f"Error updating status for request {request_id}: {e}")

    #def update_results_queue(self, request_id: str, result_data: Dict[str, Any]):
    #    """Update the results queue with the result data."""
    #    try:
    #        # Ensure that result_data fits the expected format
    #        validated_data = self.config.result_data_format(**result_data)
    #        self._channel.basic_publish(
    #            exchange='',
    #            routing_key=self.config.results_queue_name,
    #            body=ResultMessage(request_id=request_id, result=validated_data.dict()).json()
    #        )
    #        logger.info(green(f"Updated result data for request {request_id}"))
    #    except ValidationError as e:
    #        logger.error(f"Error validating result data for request {request_id}: {e}")
    #    except Exception as e:
    #        logger.error(f"Error updating result data for request {request_id}: {e}")

    #def delete_from_results_queue(self, request_id: str):
    #    """Delete a specific result from the results queue."""
    #    # Note: Deleting a specific message from RabbitMQ is not straightforward.
    #    # We will consume and not ack until we find the right one.
    #    # This is a potentially expensive operation!
    #    for method_frame, header_frame, body in self._channel.consume(queue=self.config.results_queue_name):
    #        data = json.loads(body)
    #        if data["request_id"] == request_id:
    #            self._channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    #            break
    #        self._channel.basic_nack(delivery_tag=method_frame.delivery_tag)
    #    logger.info(green(f"Deleted result data for request {request_id}"))

    # Run/Stop

    def run(self):
        logger.info('QueueServer Start running..')
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        logger.info('Stopping')
        if self._channel:
            self._channel.close()
            self._channel = None

        if self._connection:
            self._connection.close()
            self._connection = None

        logger.info('Stopped')

    def reconnect(self):
        """Attempts to reconnect to the RabbitMQ server."""
        
        # Detailed logging information
        logger.info(f"Attempting to reconnect to RabbitMQ server at {self.config.host}:{self.config.port}.")
        
        # Setting the reconnect flag
        self._should_reconnect = True
        self.stop()

class ReconnectingQueueServer:

    def __init__(self, config):
        self._reconnect_delay = 0
        self.config = config
        self._queue_server = QueueServer(config)

    def run(self):
        while True:
            try:
                self._queue_server.run()
            except KeyboardInterrupt:
                self._queue_server.stop()
                break
            self._maybe_reconnect()

    def _maybe_reconnect(self):
        if self._queue_server._should_reconnect:
            self._queue_server.stop()
            reconnect_delay = self._get_reconnect_delay()
            logger.info(f'Reconnecting after {reconnect_delay} seconds')
            time.sleep(reconnect_delay)
            self._queue_server = QueueServer(self.config)

    def _get_reconnect_delay(self):
        self._reconnect_delay += 1
        if self._reconnect_delay > 30:
            self._reconnect_delay = 30
        return self._reconnect_delay

    def register_task(self, func, *args, **kwargs):
        self._queue_server.register_task(func, *args, **kwargs)

    def update_status_queue(self, request_id: str, status: Status):
        self._queue_server.update_status_queue(request_id, status)

    def update_results_queue(self, request_id: str, result_data: Dict[str, Any]):
        self._queue_server.update_results_queue(request_id, result_data)

    def delete_from_results_queue(self, request_id: str):
        self._queue_server.delete_from_results_queue(request_id, result_data)

if __name__ == '__main__':
    # Usage example
    server = ReconnectingQueueServer(QueueConfig())
    def echo(body):
        print(f'>>>>>>>>>>>>>>>> {body}')
    server.register_task(echo)
    server.run()