import sys
# logger
sys.path.append('../../../')
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.DEBUG)
from libcommon.color import red, yellow, cyan, blue, bold, magenta
# queue server
from libcommon.queue_server.queue_server import QueueConfig, QueueServer, ReconnectingQueueServer
# llm
from libcommon.queue_server.llm import engine_args, sampling_params, InferenceOutput, llm_engine, add_request, inference_step
# llm consumer
from libcommon.queue_server.llm_consumer import LLMConsumer

# Initialize LLMEngine instance
engine = llm_engine(engine_args)

# Start running consumer server (in subthread)
consumer_server = LLMConsumer(engine, expire_in_sec=0.1)
consumer_server.run()

# Start runnning queue server (in mainthread)
queue_server = ReconnectingQueueServer(QueueConfig())
sampling_params.max_tokens = 24  # for test
queue_server.register_task(add_request, engine, sampling_params)
queue_server.run()