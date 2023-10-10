# llm_consumer.py
import threading
import time
from typing import Optional, Union, List
from pydantic import BaseModel, Field
from vllm.engine.llm_engine import LLMEngine

import sys
sys.path.append('../../')
# llm
from libcommon.queue_server.llm import inference_step, InferenceOutput, ResultStore
# queue server
from libcommon.queue_server.queue_server import ReconnectingQueueServer, QueueConfig, Status
# logger
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta, orange, green

class ResultData(BaseModel):
    text: str = Field(..., description="Generated text from the model.")
    token_ids: List[int] = Field(..., description="Token ids corresponding to the generated text.")

class LLMConsumer:
    def __init__(self, llm_engine: LLMEngine, queue_config: QueueConfig, expire_in_sec: int = 0):
        self.llm_engine = llm_engine
        self.results_store = ResultStore(expire_in_sec=expire_in_sec)
        self.queue_server = ReconnectingQueueServer(queue_config)

    def run(self) -> None:
        """
        Run the inference_step in a sub-thread and return immediately.
        """
        def _inference_step(delay=0):
            logger.info(green('Consumer process started running in a thread.'))
            while True:
                try:
                    outputs = inference_step(self.llm_engine, self.results_store)
                    if delay: time.sleep(delay)  # You can adjust this sleep time as necessary

                    # update status and result
                    for inference_output in outputs:

                        result_data = ResultData(text=inference_output.text, token_ids=inference_output.token_ids)
                        self.update_result(inference_output.request_id, result_data)

                        if inference_output.finished:
                            self.update_status(inference_output.request_id, Status.finished)

                except Exception as e:
                    logger.error(red(f"Error occurred in the consumer thread: {e}"))
                    break
        
        thread = threading.Thread(target=_inference_step)
        thread.daemon = True  # Ensures the thread exits when the main program does
        thread.start()
        
        logger.info(yellow("Started the consumer process in a separate thread."))

        # Start the queue server
        self.queue_server.run()

    def register_task(self, func, *args, **kwargs):
        """Wrapper function to register a task with the queue server."""
        self.queue_server.register_task(func, *args, **kwargs)

    def update_status(self, request_id: str, status: Status):
        return self.queue_server.update_status_queue(request_id, status)

    def update_result(self, request_id: str, result_data: ResultData) -> None:
        """Update the result in the results queue."""
        # Adjusted the method to take the ResultData model directly as a parameter, rather than individual fields
        self.queue_server.update_results_queue(request_id, result_data.dict())  # Converting ResultData model to dict

if __name__ == "__main__":
    from libcommon.queue_server.llm import llm_engine, engine_args

    engine = llm_engine(engine_args)
    consumer_server = LLMConsumer(engine)
    consumer_server.run()

    # Keep the main thread alive while sub-thread(s) are running
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        pass
