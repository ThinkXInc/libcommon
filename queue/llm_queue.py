# new_queue.py
import uuid

class LLMQueue:
    def __init__(self, config, llm_engine, results_expire_in_sec=180):
        self.queue_config = config
        self.queue_server = ReconnectingQueueServer(self.queue_config)
        self.consumer_server = LLMConsumer(llm_engine, results_expire_in_sec)
        self.results_store = self.consumer_server.results_store
        
    def start(self):
        self.consumer_server.run()
        self.queue_server.run()

    def register_task(self, func, *args, **kwargs):
        self.queue_server.register_task(func, *args, **kwargs)


def register_task(publisher, prompt):
    publisher.publish(prompt)
    print(bold(f'Task registered in queue with prompt: {prompt}'))

def fetch_worker_results(
        queue,
        task_id,
        lang,
        locale,
        locale_key_failed,
        locale_key_unexpected_result,
        locale_key_still_processing,
        locale_key_success,
        result_keys,
        additional_response_data={},
        update_callback=None):

    status = queue.results_store.get_status(task_id)
    result = queue.results_store.get_result(task_id)

    print(bold(f"Task Status: {status}"))

    if not status or status == 'PENDING':
        response_data = {
            'task_id': task_id,
            **additional_response_data
        }
        return ACCEPTED(locale.get(locale_key_still_processing, lang), response_data).http_response()
    elif not result or not all(key in result for key in result_keys):
        return ProcessingError(lang, locale, locale_key=locale_key_unexpected_result).http_response()
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
