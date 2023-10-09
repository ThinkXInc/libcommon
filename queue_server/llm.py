import time
import threading
from pydantic import BaseModel
from typing import List, Optional, Union
from vllm.engine.llm_engine import LLMEngine
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.sampling_params import SamplingParams
from vllm.utils import random_uuid

import sys
sys.path.append('../../')
from libcommon.logger import Logger
logger = Logger('llm')
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta, orange, green

# LLM inference outpu format
class InferenceOutput(BaseModel):
    request_id: str
    prompt: str
    generated_text: str
    generated_token_ids: List[int]
    finished: bool
    finish_reason: Optional[str]

class ResultStore:
    """
    A thread-safe store to manage inference results by request IDs.
    
    Usage Example:
    -------------
    >>> store = ResultStore()
    >>> inference_output = InferenceOutput(
    ...     request_id="1",
    ...     prompt="Hello",
    ...     generated_text="Hello, World!",
    ...     generated_token_ids=[1, 2, 3],
    ...     finished=True,
    ...     finish_reason="Completed"
    ... )
    >>> store.add("1", inference_output)
    >>> print(store.get("1").generated_text)
    Hello, World!
    >>> print(store.is_finished("1"))
    stop
    >>> removed_output = store.pop("1")
    >>> print(removed_output.generated_text)
    Hello, World!
    >>> print(store.get("1"))
    None
    """
    def __init__(self):
        self.store = {}
        self.lock = threading.Lock()

    def add(self, request_id: str, result: InferenceOutput) -> None:
        with self.lock:
            self.store[request_id] = result

    def get(self, request_id: str) -> Optional[InferenceOutput]:
        with self.lock:
            return self.store.get(request_id)

    def pop(self, request_id: str) -> Optional[InferenceOutput]:
        with self.lock:
            result = self.store.get(request_id)
            if result:
                del self.store[request_id]
            return result

    def is_finished(self, request_id: str) -> Union[None, bool, str]:
        with self.lock:
            result = self.store.get(request_id)
            if not result:
                return None
            return result.finish_reason if result.finished else False

results_store = ResultStore()

# Initialize LLMEngine
def llm_engine(engine_args: AsyncEngineArgs) -> LLMEngine:
    """Initialize LLMEngine instance"""
    llm_engine = LLMEngine.from_engine_args(engine_args)
    return llm_engine

# Publisher process - Add inference request to LLMEngine
def add_request(prompt, llm_engine: LLMEngine, sampling_params: SamplingParams) -> str:
    """Add inference request to LLMEngine"""
    print('add request')
    request_id = random_uuid()
    request_dict = {
        "prompt": prompt,
        "request_id": request_id
    }
    logger.info(bold(f'add request: {request_dict}'))
    llm_engine.add_request(request_id, prompt, sampling_params)
    return request_id

# Consumer process - Step inference to get ouputs
def inference_step(llm_engine: LLMEngine) -> List[InferenceOutput]:
    """Step inference"""
    results = llm_engine.step()

    outputs = []

    for i, result in enumerate(results):
        request_id = result.request_id
        prompt = result.prompt
        prompt_token_ids = result.prompt_token_ids
        generated_text = result.prompt + result.outputs[0].text
        generate_token_ids = prompt_token_ids + result.outputs[0].token_ids
        finished = result.finished
        finish_reason = result.outputs[0].finish_reason

        # Log information
        logger.info(f'[{i}]')
        logger.info(yellow(f"request_id: {request_id}"))
        logger.info(cyan(f"prompt: {prompt}"))
        logger.info(bold(f"text: {generated_text}"))
        logger.info(magenta(f"token_ids: {generate_token_ids}"))
        logger.info(f"finished: {finished} reason: {finish_reason}")

        # Append to outputs
        output = InferenceOutput(
            request_id=request_id,
            prompt=prompt,
            generated_text=generated_text,
            generated_token_ids=generate_token_ids,
            finished=finished,
            finish_reason=finish_reason
        )

        outputs.append(output)
        results_store.add(request_id, output)

    return outputs

def run_consumer_server_in_thread(llm_engine: LLMEngine) -> ResultStore:
    """
    Run the inference_step in a sub-thread and return immediately.
    """
    def _inference_step(delay=0):
        logger.info(green('Consumer process started running in a thread.'))
        while True:
            try:
                inference_step(llm_engine)
                if delay: time.sleep(delay)  # You can adjust this sleep time as necessary
            except Exception as e:
                logger.error(f"Error occurred in the consumer thread: {e}")
                break
    
    thread = threading.Thread(target=_inference_step)
    thread.daemon = True  # Ensures the thread exits when the main program does
    thread.start()
    
    logger.info(yellow("Started the consumer process in a separate thread."))
    return results_store

# Default AsyncEngineArgs and SamplingParams

checkpoint = "/src/hfmodels/llama-2-7b-chat"
#checkpoint = "/src/hfmodels/llama-2-13b-chat"

n_gpu = 4
gpu_memory_utilization = 0.80
max_seq_size = 256

engine_args = AsyncEngineArgs(
    model = checkpoint,
    tokenizer = checkpoint,
    tokenizer_mode = 'auto',
    trust_remote_code = False,
    download_dir = None,
    load_format = 'auto',
    dtype = 'auto',
    seed = 0,
    max_model_len = None,
    worker_use_ray = False,
    pipeline_parallel_size = 1,
    tensor_parallel_size = n_gpu,
    block_size = 16,
    swap_space = 4,  # GiB
    gpu_memory_utilization = gpu_memory_utilization,
    max_num_batched_tokens = None,
    max_num_seqs = max_seq_size,
    disable_log_stats = False,
    revision = None,
    quantization = None,

    # AsyncEngineArgs
    engine_use_ray = False,
    disable_log_requests = False,
    max_log_len = None,
)

sampling_params = SamplingParams(
    n = 1,                      # Corresponds to num_return_sequences
    best_of = 1,                # Doesn't have a direct match, but can be inferred from num_return_sequences
    presence_penalty = 0.0,     # Not available in (latest), defaulting to 0
    frequency_penalty = 0.0,    # Not available in (latest), defaulting to 0
    temperature = 0.6,          # Corresponds to temperature
    top_p = 1,                  # Not available in (latest), defaulting to 1
    top_k = 40,                 # Corresponds to top_k
    #use_beam_search = False,    # Inferred from num_beams being absent/default (using sampling instead)
    length_penalty = 1.0,       # Not available in (latest), defaulting to 1.0 (no penalty)
    #early_stopping = True,     # Not available in (latest), defaulting to False
    #stop = [],                  # Not available in (latest), defaulting to empty list
    #stop_token_ids = [],        # Not available in (latest), defaulting to empty list
    #ignore_eos = False,         # Not available in (latest), defaulting to False
    max_tokens = 128,           # Corresponds to max_new_tokens
    logprobs = None,            # Not available in (latest), defaulting to None
    skip_special_tokens = True  # Not available in (latest), defaulting to True
)

if __name__ == "__main__":
    engine = llm_engine(engine_args)
    add_request('12345', engine, sampling_params)
    add_request('98765', engine, sampling_params)