# llm_consumer.py
import threading
import time
from typing import Optional, Union
from vllm.engine.llm_engine import LLMEngine

import sys
sys.path.append('../../')
# llm
from libcommon.queue_server.llm import inference_step, InferenceOutput, ResultStore
# logger
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta, orange, green

class LLMConsumer:
    def __init__(self, llm_engine: LLMEngine, expire_in_sec: int = 0):
        self.llm_engine = llm_engine
        self.results_store = ResultStore(expire_in_sec=expire_in_sec)

    def run(self) -> None:
        """
        Run the inference_step in a sub-thread and return immediately.
        """
        def _inference_step(delay=0):
            logger.info(green('Consumer process started running in a thread.'))
            while True:
                try:
                    inference_step(self.llm_engine, self.results_store)
                    if delay: time.sleep(delay)  # You can adjust this sleep time as necessary
                except Exception as e:
                    logger.error(f"Error occurred in the consumer thread: {e}")
                    break
        
        thread = threading.Thread(target=_inference_step)
        thread.daemon = True  # Ensures the thread exits when the main program does
        thread.start()
        
        logger.info(yellow("Started the consumer process in a separate thread."))

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
