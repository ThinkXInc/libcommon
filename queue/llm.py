import time
import threading
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Optional, Union
from vllm.engine.llm_engine import LLMEngine
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.sampling_params import SamplingParams

import sys
sys.path.append('../../')
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta, orange, green

# LLM inference outpu format
class InferenceOutput(BaseModel):
    request_id: str
    prompt: str
    text: str
    token_ids: List[int]
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
    ...     text="Hello, World!",
    ...     token_ids=[1, 2, 3],
    ...     finished=True,
    ...     finish_reason="Completed"
    ... )
    >>> store.add("1", inference_output)
    >>> print(store.get("1").text)
    Hello, World!
    >>> print(store.is_finished("1"))
    stop
    >>> removed_output = store.pop("1")
    >>> print(removed_output.text)
    Hello, World!
    >>> print(store.get("1"))
    None
    """
    def __init__(self, expire_in_sec: int = 0):
        self.store = {}
        self.expiration_times = {}  # This dictionary will hold expiration times
        self.expire_in_sec = expire_in_sec
        self.lock = threading.Lock()

    def _remove_expired_entries(self):
        """Remove entries that have expired."""
        current_time = datetime.now()
        expired_keys = [k for k, v in self.expiration_times.items() if v <= current_time]

        for key in expired_keys:
            logger.debug(f'{key} in ResultStore is expired. remove it.')
            self.store.pop(key, None)
            self.expiration_times.pop(key, None)

    def add(self, request_id: str, result: InferenceOutput) -> None:
        with self.lock:
            self._remove_expired_entries()
            self.store[request_id] = result
            # Set the expiration time for this request_id
            self.expiration_times[request_id] = datetime.now() + timedelta(seconds=self.expire_in_sec)

    def get(self, request_id: str) -> Optional[InferenceOutput]:
        with self.lock:
            self._remove_expired_entries()
            return self.store.get(request_id)

    def pop(self, request_id: str) -> Optional[InferenceOutput]:
        with self.lock:
            self._remove_expired_entries()
            result = self.store.get(request_id)
            if result:
                del self.store[request_id]
            return result

    def is_finished(self, request_id: str) -> Union[None, bool, str]:
        with self.lock:
            self._remove_expired_entries()
            result = self.store.get(request_id)
            if not result:
                return None
            return result.finish_reason if result.finished else False

# Initialize LLMEngine
def llm_engine(engine_args: AsyncEngineArgs) -> LLMEngine:
    """Initialize LLMEngine instance"""
    llm_engine = LLMEngine.from_engine_args(engine_args)
    return llm_engine

# Generate task request_id
def random_uuid() -> str:
    return str(uuid.uuid4().hex)

# Publisher process - Add inference request to LLMEngine
def add_request(request_id: str, prompt, llm_engine: LLMEngine, sampling_params: SamplingParams) -> str:
    """Add inference request to LLMEngine"""
    print('add request')

    request_dict = {
        "prompt": prompt,
        "request_id": request_id
    }
    logger.info(bold(f'add request: {request_dict}'))
    llm_engine.add_request(request_id, prompt, sampling_params)
    return request_id

# Consumer process - Step inference to get ouputs
def inference_step(llm_engine: LLMEngine, results_store: ResultStore) -> List[InferenceOutput]:
    """Step inference"""
    results = llm_engine.step()  # if no results, [] is out

    outputs = []

    request_ids = []
    prompts = []
    texts = []
    token_ids_list = []
    finished_list = []
    reason_list = []

    for result in results:
        request_id = result.request_id
        prompt = result.prompt
        prompt_token_ids = result.prompt_token_ids
        text = result.prompt + result.outputs[0].text
        token_ids = prompt_token_ids + result.outputs[0].token_ids
        finished = result.finished
        finish_reason = result.outputs[0].finish_reason

        # Append data to lists
        request_ids.append(request_id)
        prompts.append(prompt)
        texts.append(text)
        token_ids_list.append(token_ids)
        finished_list.append(finished)
        reason_list.append(finish_reason)

        # Append to outputs
        output = InferenceOutput(
            request_id=request_id,
            prompt=prompt,
            text=text,
            token_ids=token_ids,
            finished=finished,
            finish_reason=finish_reason
        )
        outputs.append(output)
        results_store.add(request_id, output)

    # Now, log information
    if len(outputs) > 0:
        logger.info(magenta(f"\n{len(outputs)} outputs" + "-"*50))
        logger.info("[request_id]")
        for rid in request_ids: logger.info(f"request_id: {rid}")
        logger.info("[prompt]")
        for p in prompts: logger.info(yellow(f"prompt: {p}"))
        logger.info("[text]")
        for t in texts: logger.info(cyan(f"text: {t}"))
        logger.info("[token_ids]")
        for tids in token_ids_list: logger.info(f"token_ids: {tids}")
        logger.info("[finished]")
        for f, r in zip(finished_list, reason_list):
            if r:
                logger.info(green(f"finished: {f} reason: {r}"))
            else:
                logger.info(f"finished: {f} reason: {r}")

    return outputs


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