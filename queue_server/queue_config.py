from pydantic import BaseModel

class QueueConfig(BaseModel):
    user: str = 'guest'  # Assuming default RabbitMQ credentials. Change if necessary.
    password: str = 'guest'  # Assuming default RabbitMQ credentials. Change if necessary.
    host: str = 'localhost'
    port: int = 5672
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
            f"queue_durable={self.queue_durable}, "
            f"queue_exclusive={self.queue_exclusive}, "
            f"queue_auto_delete={self.queue_auto_delete}"
            f")"
        )

