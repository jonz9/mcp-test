import os
import torch
import torchaudio
from huggingface_hub import hf_hub_download
from generator import load_csm_1b
from dataclasses import dataclass
from transformers import CsmForConditionalGeneration, AutoProcessor

os.environ["NO_TORCH_COMPILE"] = "1"

model_id = "sesame/csm-1b"
device = "cuda" if torch.cuda.is_available() else "cpu"

processor = AutoProcessor.from_pretrained(model_id)
model = CsmForConditionalGeneration.from_pretrained(model_id).to(device)

prompt_filepath_conversational_assistant = "/client/jarvis.wav"

SPEAKER_PROMPT = {
    "assistant_a": {
        "text": (
            "You are a helpful AI assistant. Your responses should sound clear, concise, and informative. ",
            "Use a friendly, professional and most importantly human tone.",
            "Speak at a moderate pace, and ensure your pronunciation is clear. ",
            "Sound like JARVIS from Iron Man, with a calm and authoritative voice. ",
            "Always address them as 'Boss'.",
            "Sound a little sassy, but not too much.",

        )
    }
}

def load_prompt_audio(audio_path: str, target_sample_rate: int) -> torch.Tensor:
    audio_tensor, sample_rate = torchaudio.load(audio_path)
    audio_tensor = audio_tensor.squeeze(0)
    audio_tensor = torchaudio.functional.resample(
        audio_tensor, orig_freq=sample_rate, new_freq=target_sample_rate
    )
    return audio_tensor

def prepare_prompt(text: str, speaker: int, audio_path: str, sample_rate: int) -> Segment:
    audio_tensor = load_prompt_audio(audio_path, sample_rate)
    return Segment(text=text, speaker=speaker, audio=audio_tensor)

def generate_audio(response: str) -> None:
    speaker_prompt = SPEAKER_PROMPT["assistant_a"]["text"]

    assistant_prompt = prepare_prompt(
        text=speaker_prompt,
        speaker=0,
        audio_path=prompt_filepath_conversational_assistant,
        sample_rate=24000
    )

    conversation = [{
        "text": response,
        "speaker_id": 0,
    }]

    audio_tensor = generator.generate(
        text=conversation.text,
        speaker=conversation.speaker_id,
        context=assistant_prompt,
        max_audio_length_ms=10000,
    )
    
    torchaudio.save("gemini_response.wav", audio_tensor, sample_rate=24000)

    print("Successfully generated audio response")

generate_audio("Hello! This is your AI assistant speaking.")