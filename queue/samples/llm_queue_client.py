import time
import sys
# logger
sys.path.append('../../../')
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta, green
# publisher
from libcommon.queue.queue_publisher import QueueConfig, QueuePublisher, QueueConnectionManager
# server
from libcommon.queue.queue_server import Status

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
    request_ids = []
    for i in range(n):
        time.sleep(interval_sec)
        # Publish message
        logger.info(yellow(f'[{i}/{n-1}]'))
        request_id = publisher.publish(str(f'{1*(i+1)} {2*(i+1)} {3*(i+1)} {4*(i+1)}'))
        request_ids.append(request_id)

    # Poll the server for status until the task is finished
    while len(request_ids) > 0:
        time.sleep(0.25)  # Wait for 1 seconds before each poll
        for request_id in request_ids:
            status = publisher.get_status(request_id)
            if status == Status.finished.value:
                logger.info(green(f"Task {request_id} finished."))

                # get result
                result = publisher.get_result(request_id)
                logger.info(cyan(f"Result for Task {request_id}: {result}"))

                # delete status and result
                publisher.delete_result(request_id)
                publisher.delete_status(request_id)

                # remove from id list
                request_ids.remove(request_id)
                break
            elif status == Status.progress.value:
                logger.info(yellow(f"Task {request_id} is still in progress..."))
            elif status == Status.progress.failed:
                logger.info(red(f"Task {request_id} failed!"))
            else:
                logger.info(red(f"Unknown status for Task {request_id}: {status}"))

    logger.info(magenta('all done.'))

finally:
    # Ensure connection is always closed gracefully, even if there's an error
    time.sleep(1)
    connection_manager.close()
    print('Connection closed gracefully.')