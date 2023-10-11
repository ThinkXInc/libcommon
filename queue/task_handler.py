import time
from typing import Callable, Any, Dict
import sys
sys.path.append('../../')
# queue
from libcommon.queue.queue_publisher import QueuePublisher
from libcommon.queue.queue_server import Status
# locale
from libcommon.locale import Locale
# response
from libcommon.response.successes import OK, ACCEPTED
from libcommon.response.errors import ProcessingError
# logger
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta, green


def request_llm_inference(publisher, prompt: str, delay_in_sec: int = 0) -> str:
    """
    Schedules a task with the given publisher to be executed after a delay.
    """
    request_id = publisher.publish(prompt, delay_in_sec)
    print(bold(f'Task registered with id: {request_id} [with delay:{delay_in_sec}]'))
    return request_id

def fetch_llm_results(
        queue_publisher: QueuePublisher,
        request_id: str,
        lang: str,
        locale: Locale,
        locale_key_failed: str,
        locale_key_unexpected_result: str,
        locale_key_still_processing: str,
        locale_key_success: str,
        result_keys: list,
        parser_function=None,
        additional_response_data: dict = {},
        update_callback=None):

    # Use the get_status method from the QueuePublisher to fetch the task status
    status = queue_publisher.get_status(request_id)
    print(bold(f"Task Status: {status}"))

    if status == "Not found":
        logger.error(red(f"Error: Task {request_id} not found!"))
        return ProcessingError(lang, locale, locale_key=locale_key_failed).http_response()

    if status != Status.finished.value:
        logger.debug(yellow(f"Task {request_id} still processing..."))
        response_data = {
            'request_id': request_id,
            **additional_response_data
        }
        return ACCEPTED(
            locale.get(locale_key_still_processing, lang),
            response_data
        ).http_response()

    # Use the get_result method from the QueuePublisher to fetch the task result
    try:
        logger.debug(cyan("Fetching task result..."))
        result = queue_publisher.get_result(request_id)
        logger.info(cyan(f"Task Result => {result}"))
    except Exception as e:
        logger.error(red(f"Error fetching result for task {request_id}: {e}"))
        return ProcessingError(lang, locale, locale_key=locale_key_failed).http_response()

    if "error" in result:
        logger.error(red(f"Error found in task result for {request_id}!"))
        return ProcessingError(lang, locale, locale_key=locale_key_failed).http_response()

    # Parse the result using the provided parser_function, if any
    if parser_function:
        logger.debug(green(f"Parsing result for task {request_id} using provided parser function..."))
        result = parser_function(result)

    # Checking if all required keys are present in the result
    if not all(key in result for key in result_keys):
        logger.error(red(f"Unexpected result format for task {request_id}. Missing keys in result."))
        return ProcessingError(lang, locale, locale_key=locale_key_unexpected_result).http_response()

    response_data = {
        'request_id': request_id,
        **additional_response_data,
        **result
    }

    if update_callback:
        logger.debug(blue(f"Executing update callback for task {request_id}..."))
        response = update_callback(result)
        if isinstance(response, Exception):  
            return response

    logger.info(green(f"Task {request_id} processed successfully!"))
    return OK(locale.get(locale_key_success, lang), response_data).http_response()


if __name__ == '__main__':
    # TODO: the below is testing draft
    # Sample values for execution
    queue_publisher = QueuePublisher()  # Some assumed class, needs real initialization
    request_id = "sample_request_id"
    lang = "en"
    from libcommon.locale import Locale
    locale = Locale()  # Some assumed class, needs real initialization
    locale_key_failed = "task_failed"
    locale_key_still_processing = "task_processing"
    locale_key_success = "task_success"

    result = fetch_worker_results(queue_publisher, request_id, lang, locale, locale_key_failed, locale_key_still_processing, locale_key_success, parser_function=parse_title_and_keywords)
    print(result)