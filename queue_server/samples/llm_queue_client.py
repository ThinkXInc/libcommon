import time
import sys
# logger
sys.path.append('../../../')
from libcommon.logger import Logger
logger = Logger('llm')
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta
# publisher
from libcommon.queue_server.queue_publisher import QueueConfig, QueuePublisher, QueueConnectionManager

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
        publisher.publish(str(f'{i}/{n-1}: 123456'))

finally:
    # Ensure connection is always closed gracefully, even if there's an error
    time.sleep(1)
    connection_manager.close()
    print('Connection closed gracefully.')