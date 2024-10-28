#test_parler.py
import os
os.environ["TOKENIZERS_PARALLELISM"] = "True"

import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf

device = "cuda:0" if torch.cuda.is_available() else "cpu"

model = ParlerTTSForConditionalGeneration.from_pretrained("parler-tts/parler-tts-mini-v1").to(device)
tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler-tts-mini-v1")

prompt = "Hey, how are you doing today?"
#description = "A female speaker delivers a slightly expressive and animated speech with a moderate speed and pitch. The recording is of very high quality, with the speaker's voice sounding clear and very close up."
description = "Jon's voice is monotone yet slightly fast in delivery, with a very close recording that almost has no background noise."

print("TOKENIZER IDs")
input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)

print("TOKENIZER PROMPT")
prompt_input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)

print("GENERATING")
generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)

print("SQUEEZING")
audio_arr = generation.cpu().numpy().squeeze()

print("WRITING")
sf.write("parler_tts_out.wav", audio_arr, model.config.sampling_rate)

import sounddevice as sd

# Load the audio from the saved file
print("LOADING")
audio_arr, sample_rate = sf.read("parler_tts_out.wav")

# Play the audio
print("PLAYING")
sd.play(audio_arr, samplerate=sample_rate)
sd.wait()  # Wait until the audio finishes playing