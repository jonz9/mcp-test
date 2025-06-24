from dataclasses import dataclass
import torch
import torch.nn as nn
from huggingface_hub import PyTorchModelHubMixin


@dataclass
class ModelArgs:
    text_vocab_size: int
    audio_vocab_size: int
    audio_num_codebooks: int
    embed_dim: int = 2048         # Default for CSM-1B
    decoder_dim: int = 2048       # Default for CSM-1B


class Model(nn.Module, PyTorchModelHubMixin):
    def __init__(self, config: ModelArgs):
        super().__init__()
        self.config = config

        self.text_embeddings = nn.Embedding(config.text_vocab_size, config.embed_dim)
        self.audio_embeddings = nn.Embedding(config.audio_vocab_size * config.audio_num_codebooks, config.embed_dim)

        self.projection = nn.Linear(config.embed_dim, config.decoder_dim, bias=False)
        self.codebook0_head = nn.Linear(config.embed_dim, config.audio_vocab_size, bias=False)
        self.audio_head = nn.Parameter(torch.empty(config.audio_num_codebooks - 1, config.decoder_dim, config.audio_vocab_size))

    def setup_caches(self, max_batch_size: int):
        pass  # Implement if needed for CSM

    def generate_frame(self, tokens, tokens_mask, input_pos, temperature, topk):
        pass  # Implement if needed for CSM

    def reset_caches(self):
        pass  # Implement if needed for CSM

    def _embed_audio(self, codebook: int, tokens: torch.Tensor) -> torch.Tensor:
        return self.audio_embeddings(tokens + codebook * self.config.audio_vocab_size)

    def _embed_tokens(self, tokens: torch.Tensor) -> torch.Tensor:
        text_embeds = self.text_embeddings(tokens[:, :, -1]).unsqueeze(-2)

        audio_tokens = tokens[:, :, :-1] + (
            self.config.audio_vocab_size * torch.arange(self.config.audio_num_codebooks, device=tokens.device)
        )
        audio_embeds = self.audio_embeddings(audio_tokens.view(-1)).reshape(
            tokens.size(0), tokens.size(1), self.config.audio_num_codebooks, -1
        )

        return torch.cat([audio_embeds, text_embeds], dim=-2)