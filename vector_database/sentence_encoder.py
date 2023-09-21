# llm/sentence_encoder.py
#

from typing import Any

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

from libcommon.logger import Logger
logger = Logger('SentenceEncoder')
logger.setLevel(logger.INFO)

class SentenceEncoder:

    def __init__(
            self,
            checkpoint: str,
            embedding_dim: int = 512,
            tokenizer_checkpoint: str = None,
            tokenizer = None,
            device: str = 'cuda:1'
    ):
        """Class that finds an embedding of simple text

        Args:
            checkpoint (str): Path to the saved model and possibly tokenizer.
            tokenizer_checkpoint (str, optional): Path to the saved tokenizer. If none, the tokenizer will be assumed to
                exist at the same path as the model. (Default = None)
            tokenizer (object, optional): If a specific tokenizer is set, this tokenizer is prioritized.
            device (any, optional): Argument to pass to torch.*.to(). (Default = None)
        """
        self.checkpoint = checkpoint
        self.device = device

        # neural encoder model
        logger.info(f'Load model from checkpoint {self.checkpoint} to device {self.device}..')
        self.model = AutoModel.from_pretrained(checkpoint).to(device)

        # if tokenizer check point is not set, use model's
        logger.info(f'Load tokenizer from checkpoint {self.checkpoint}..')
        self.tokenizer = tokenizer or AutoTokenizer.from_pretrained(
            tokenizer_checkpoint or checkpoint)

        self.embedding_dim = embedding_dim

    def sentence_to_vec(self, sentence: str) -> torch.Tensor:
        """Returns the embedding of the provided sentence.

        Args:
            sentence (str): Sentence or paragraph to encode as a single vector.

        Returns:
            sentence_embedding (torch.Tensor): Encoded input.
        """

        def mean_pooling(model_output, attention_mask) -> torch.Tensor:
            """Attention-mask-aware mean pooling."""
            token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            masked_sum = torch.sum(token_embeddings * input_mask_expanded, 1)
            norm = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            return masked_sum / norm


        # Tokenize sentences
        encoded_input = self.tokenizer(sentence, padding=True, truncation=True, return_tensors='pt').to(self.device)
        logger.debug(f'sentence_to_vec():\n{sentence}\n-> {encoded_input}')

        # Compute token embeddings
        with torch.no_grad():
            token_outputs = self.model(**encoded_input)

        # Perform pooling
        sentence_embedding = mean_pooling(token_outputs, encoded_input['attention_mask'])

        # Normalize embeddings
        sentence_embedding = F.normalize(sentence_embedding, p=2, dim=1)

        return sentence_embedding.to('cpu')

    def __call__(self, sentence: str) -> torch.Tensor:
        """Returns the embedding of the provided sentence.

        Args:
            sentence (str): Sentence or paragraph to encode as a single vector.

        Returns:
            sentence_embedding (torch.Tensor): Encoded input.
        """
        return self.sentence_to_vec(sentence)