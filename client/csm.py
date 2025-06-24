import os
import torch
import torchaudio
from huggingface_hub import hf_hub_download
from generator import load_csm_1b

os.environ["NO_TORCH_COMPILE"] = "1"

model_id = "sesame/csm-1b"
device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
generator = load_csm_1b(device)
edium
def generate_audio(response: str, output_path: str = "gemini_response.wav") -> None:
    audio_tensor = generator.generate(
        text=response,
        speaker=0,
        context=[],
        max_audio_length_ms=10000,
    )
    torchaudio.save(output_path, audio_tensor.unsqueeze(0).cpu(), 24000)
    print(f"Successfully generated audio response: {output_path}")

if __name__ == "__main__":
    generate_audio("Hello! This is your AI assistant speaking.")