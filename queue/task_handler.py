import time
from typing import Callable, Any, Dict
# logger
import sys
sys.path.append('../../')
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta, green

def register_task_with_publisher(publisher, task_name: str, *args, **kwargs) -> str:
    """
    Registers a task with the given publisher.
    """
    task_id = publisher.publish(task_name, args, kwargs)
    print(bold(f'Task registered with id: {task_id}'))
    return task_id

def schedule_task_with_publisher(publisher, task_name: str, delay_sec: int, *args, **kwargs) -> str:
    """
    Schedules a task with the given publisher to be executed after a delay.
    """
    time.sleep(delay_sec)  # Simulating the delay, this might not be an efficient method
    return register_task_with_publisher(publisher, task_name, *args, **kwargs)

def fetch_worker_results(
        queue_publisher: QueuePublisher,
        task_id: str,
        lang: str,
        locale: Locale,
        locale_key_failed: str,
        locale_key_still_processing: str,
        locale_key_success: str,
        parser_function=None,
        additional_response_data: dict = {},
        update_callback=None):

    # Use the get_status method from the QueuePublisher to fetch the task status
    status = queue_publisher.get_status(task_id)
    print(bold(f"Task Status: {status}"))

    if status == "Not found":
        logger.error(red(f"Error: Task {task_id} not found!"))
        return ProcessingError(lang, locale, locale_key=locale_key_failed).http_response()

    if status != Status.finished.value:
        logger.debug(yellow(f"Task {task_id} still processing..."))
        response_data = {
            'task_id': task_id,
            **additional_response_data
        }
        return ACCEPTED(
            locale.get(locale_key_still_processing, lang),
            response_data
        ).http_response()

    # Use the get_result method from the QueuePublisher to fetch the task result
    try:
        logger.debug(cyan("Fetching task result..."))
        result = queue_publisher.get_result(task_id)
        logger.info(cyan(f"Task Result => {result}"))
    except Exception as e:
        logger.error(red(f"Error fetching result for task {task_id}: {e}"))
        return ProcessingError(lang, locale, locale_key=locale_key_failed).http_response()

    if "error" in result:
        logger.error(red(f"Error found in task result for {task_id}!"))
        return ProcessingError(lang, locale, locale_key=locale_key_failed).http_response()

    # Parse the result using the provided parser_function, if any
    if parser_function:
        logger.debug(green(f"Parsing result for task {task_id} using provided parser function..."))
        result = parser_function(result)

    response_data = {
        'task_id': task_id,
        **additional_response_data,
        **result
    }

    if update_callback:
        logger.debug(blue(f"Executing update callback for task {task_id}..."))
        response = update_callback(result)
        if isinstance(response, Exception):  
            return response

    logger.info(green(f"Task {task_id} processed successfully!"))
    return OK(locale.get(locale_key_success, lang), response_data).http_response()


if __name__ == '__main__':
    # TODO: the below is testing draft
    # Sample values for execution
    queue_publisher = QueuePublisher()  # Some assumed class, needs real initialization
    task_id = "sample_task_id"
    lang = "en"
    from libcommon.locale import Locale
    locale = Locale()  # Some assumed class, needs real initialization
    locale_key_failed = "task_failed"
    locale_key_still_processing = "task_processing"
    locale_key_success = "task_success"

    result = fetch_worker_results(queue_publisher, task_id, lang, locale, locale_key_failed, locale_key_still_processing, locale_key_success, parser_function=parse_title_and_keywords)
    print(result)