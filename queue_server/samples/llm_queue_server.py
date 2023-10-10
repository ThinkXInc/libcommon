import sys
# logger
sys.path.append('../../../')
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta
# llm
from libcommon.queue_server.llm import engine_args, sampling_params, InferenceOutput, llm_engine, add_request, inference_step
# llm consumer
from libcommon.queue_server.llm_consumer import LLMConsumer, QueueConfig

# Initialize LLMEngine instance
engine = llm_engine(engine_args)

# Start running consumer server (in subthread)
consumer_server = LLMConsumer(engine, QueueConfig(), expire_in_sec=60*3)
sampling_params.max_tokens = 24  # for test
consumer_server.register_task(add_request, engine, sampling_params)
consumer_server.run()