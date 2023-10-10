import time
from typing import Callable, Any, Dict

# Assuming bold, cyan, red, ACCEPTED, OK, and ProcessingError are imported or defined elsewhere in your code

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
        queue_publisher: QueuePublisher,  # replace Celery queue with QueuePublisher
        task_id: str,
        lang: str,
        locale: Locale,
        locale_key_failed: str,
        locale_key_unexpected_result: str,
        locale_key_still_processing: str,
        locale_key_success: str,
        result_keys: list,
        additional_response_data: dict = {},
        update_callback=None):

    # Use the get_status method from the QueuePublisher to fetch the task status
    status = queue_publisher.get_status(task_id)
    print(bold(f"Task Status: {status}"))

    if status == "Not found":
        return ProcessingError(lang, locale, locale_key=locale_key_failed).http_response()

    if status != Status.finished.value:
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
        result = queue_publisher.get_result(task_id)
        print(cyan(f"Task Result => {result}"))
    except Exception as e:
        return ProcessingError(lang, locale, locale_key=locale_key_failed).http_response()

    if "error" in result:
        return ProcessingError(lang, locale, locale_key=locale_key_failed).http_response()
    elif not all(key in result for key in result_keys):
        print(red(result))
        return ProcessingError(
            lang, locale, locale_key=locale_key_unexpected_result).http_response()
    else:
        if update_callback:
            response = update_callback(result)
            if isinstance(response, Exception):  
                return response

        response_data = {
            'task_id': task_id,
            **additional_response_data  
        }

        for key in result_keys:
            response_data[key] = result[key]
            print(f"{key.capitalize()} -> {result[key]}")

        return OK(locale.get(locale_key_success, lang), response_data).http_response()