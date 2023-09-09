import inspect
import importlib
from libcommon.locale import Locale
from libcommon.color import bold, cyan, magenta, yellow, green, red
from libcommon.response.successes import OK, ACCEPTED
from libcommon.response.errors import ProcessingError

def register_all_tasks_from_module(module_name, queue_instance):
    """
    NOTE: STILL NOT WORKING

    Automatically register all tasks defined in a given module.

    Args:
    - module_name (str): The name of the module to register tasks from.
    - queue_instance: The instance of the queue where tasks should be registered.

    Returns:
    None
    """

    # Import the specified module
    tasks_module = importlib.import_module(module_name)

    # Get all functions in the tasks_module
    functions = [f[1] for f in inspect.getmembers(tasks_module, inspect.isfunction)]

    # Register each function as a task
    for func in functions:
        queue_instance.register_task(func)

def register_celery_task(prompt, celery_task):
    """
    Register celery task to task queue.

    """
    task = celery_task.apply_async((prompt,))
    print(f'Celery task registered in queue with id: {task.id}')
    return task

def fetch_worker_results(
        queue,
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
    """
    Common function to fetch results from Celery tasks.
    
    Args:
    - queue (obj): Celery Queue instance
    - task_id (str)
    - lang (str): The language code, e.g. 'en'.
    - locale (Locale): 
    - locale_key_failed (str): Locale key for the failed response.
    - locale_key_unexpected_result (str): Locale key for unexpected results response.
    - locale_key_still_processing (str): Locale key for still processing response.
    - locale_key_success (str): Locale key for successful response.
    - result_keys (list): List of expected keys in the result.
    - additional_response_data (dict): Additional data to be included in the response.
    
    Returns:
        {
            task_id: ,
            {key 1 in results_keys}: ,
            {key 2 in results_keys}: ,
            ..,
            **additional_response_data
        }
    """
    
    # Retrieve result status from Celery Worker
    task = queue.AsyncResult(task_id)
    status = task.status
    print(bold(f"Task Status: {status}"))

    try:
        result = task.get(timeout=10)
        print(cyan(f"Task Result => {result}"))
    except Exception as e:
        return ProcessingError(lang, locale, locale_key=locale_key_failed).http_response()

    # Handle different result scenarios
    if not result:
        response_data = {
            'task_id': task_id,
            **additional_response_data  # Merge additional data into the response
        }
        return ACCEPTED(
            locale.get(locale_key_still_processing, lang),
            response_data
        ).http_response()
    elif not all(key in result for key in result_keys):
        print(red(result))
        return ProcessingError(
            lang, locale, locale_key=locale_key_unexpected_result).http_response()
    else:
        if update_callback:
            response = update_callback(result)
            if isinstance(response, Exception):  # or some other validation to check if the callback returns an error response
                return response

        response_data = {
            'task_id': task.id,
            **additional_response_data  # Merge additional data into the response
        }

        for key in result_keys:
            response_data[key] = result[key]
            print(f"{key.capitalize()} -> {result[key]}")

        # Return success response
        return OK(locale.get(locale_key_success, lang), response_data).http_response()

