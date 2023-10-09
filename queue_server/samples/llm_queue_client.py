import time
import sys
# logger
sys.path.append('../../../')
from libcommon.logger import Logger
logger = Logger()
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

    n = 30
    interval_sec = 0
    for i in range(n):
        time.sleep(interval_sec)
        # Publish message
        logger.info(yellow(f'[{i}/{n-1}]'))
        request_id = publisher.publish(str(f'{1*(i+1)} {2*(i+1)} {3*(i+1)} {4*(i+1)}'))

finally:
    # Ensure connection is always closed gracefully, even if there's an error
    time.sleep(1)
    connection_manager.close()
    print('Connection closed gracefully.')