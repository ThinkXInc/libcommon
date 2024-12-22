# llm/sentence_encoder.py
#

from typing import Any

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

from libcommon.logger import Logger
logger = Logger('SentenceEncoder')
logger.setLevel(logger.INFO)
#logger.setLevel(logger.DEBUG)
from libcommon.color import *

class SentenceEncoder:

    def __init__(
            self,
            checkpoint: str,
            embedding_dim: int,
            max_context_length: int,
            device: str
    ):
        """Class that finds an embedding of simple text

        Args:
            checkpoint (str): Path to the saved model and possibly tokenizer.
            tokenizer (object): If a specific tokenizer is set, this tokenizer is prioritized.
            device (any): Argument to pass to torch.*.to(). (Default = None)
        """
        self.checkpoint = checkpoint
        self.device = device

        # neural encoder model
        logger.info(f'Load model from checkpoint {self.checkpoint} to device {self.device}..')
        self.model = AutoModel.from_pretrained(checkpoint).to(device)

        self.max_context_length = max_context_length
        self.embedding_dim = embedding_dim

        embedding_size = self.model.get_input_embeddings().num_embeddings

        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint)
        vocab_size = len(self.tokenizer.vocab)
        logger.info(f"Model embedding size: {embedding_size} vocab size: {vocab_size}")
        if vocab_size > embedding_size:
            logger.error(red(f"Tokenizer vocab size {vocab_size} exceeds model's embedding capacity {embedding_size}."))
            raise ValueError("Tokenizer's vocabulary size exceeds model's embedding capacity.")

    def sentence_to_vec(self, sentence: str) -> torch.Tensor:
        """Returns the embedding of the provided sentence.

        Args:
            sentence (str): Sentence or paragraph to encode as a single vector.

        Returns:
            sentence_embedding (torch.Tensor): Encoded input.
        """
        logger.debug(green(f"Tokenizing sentence: {sentence}"))
        #encoded_input = self.tokenizer(sentence, padding=True, truncation=True, return_tensors='pt').to(self.device)
        encoded_input = self.tokenizer(sentence, padding=True, truncation=True, max_length=self.max_context_length, return_tensors='pt').to(self.device)
        logger.debug(cyan(f'Encoded => sentence_to_vec():\n{sentence}\n-> {encoded_input}'))
        logger.debug(f"Tensor shape: {encoded_input['input_ids'].shape}")
        logger.debug(f"Attention mask shape: {encoded_input['attention_mask'].shape}")

        max_vocab_size = self.tokenizer.vocab_size  # Make sure this property matches your tokenizer's attribute
        logger.debug(f'tokenizer.vocab_size {max_vocab_size}')
        if torch.any(encoded_input['input_ids'] >= max_vocab_size):
            logger.error("Token ID exceeds vocabulary size")
        # Check which tokens are out of range
        invalid_tokens = encoded_input['input_ids'][encoded_input['input_ids'] >= max_vocab_size]
        for token_id in invalid_tokens.unique():
            token = self.tokenizer.convert_ids_to_tokens(token_id.item())
            logger.debug(f"Invalid token ID {token_id.item()}: {token}")

        # Compute token embeddings with no gradient computation
        with torch.no_grad():
            model_output = self.model(**encoded_input)
            logger.debug(cyan(f"Model output received."))

        # Perform pooling
        sentence_embedding = self.mean_pooling(model_output, encoded_input['attention_mask'])
        logger.debug(green(f"Pooled sentence embedding computed."))

        # Normalize embeddings
        sentence_embedding = F.normalize(sentence_embedding, p=2, dim=1)
        logger.debug(bold(f"Normalized sentence embedding ready."))

        return sentence_embedding.to('cpu')

    def mean_pooling(self, model_output, attention_mask) -> torch.Tensor:
        """Attention-mask-aware mean pooling."""
        token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        masked_sum = torch.sum(token_embeddings * input_mask_expanded, 1)
        norm = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        logger.debug(yellow(f"Mean pooling completed."))
        return masked_sum / norm

    def __call__(self, sentence: str) -> torch.Tensor:
        """Returns the embedding of the provided sentence.

        Args:
            sentence (str): Sentence or paragraph to encode as a single vector.

        Returns:
            sentence_embedding (torch.Tensor): Encoded input.
        """
        logger.info(bold(f"Generating embedding for: \"{sentence}\""))
        return self.sentence_to_vec(sentence)