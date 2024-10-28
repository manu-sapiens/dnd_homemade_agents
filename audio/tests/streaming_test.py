#streaming_test.py

import torch
from parler_tts import ParlerTTSForConditionalGeneration, ParlerTTSStreamer
from transformers import AutoTokenizer
from threading import Thread
import sounddevice as sd

import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "False"

torch_device = "mps"#"cuda:0" # Use "mps" for Mac 
torch_dtype = torch.bfloat16
model_name = "parler-tts/parler-tts-mini-v1"

# need to set padding max length
max_length = 50

# load model and tokenizer
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name) 
print("loading model")
model = ParlerTTSForConditionalGeneration.from_pretrained(
    model_name,
).to(torch_device, dtype=torch_dtype)

sampling_rate = model.audio_encoder.config.sampling_rate
frame_rate = model.audio_encoder.config.frame_rate

def generate(text, description, play_steps_in_s=0.5):
  print("Generating: ", text)
  print("Using description = ", description)

  play_steps = int(frame_rate * play_steps_in_s)

  print("Streaming with play_steps = ", play_steps)
  streamer = ParlerTTSStreamer(model, device=torch_device, play_steps=play_steps)

  print("Tokenizing id...")
  # tokenization
  inputs = tokenizer(description, return_tensors="pt").to(torch_device)

  print("Tokenizing prompt...")
  prompt = tokenizer(text, return_tensors="pt").to(torch_device)
  # create generation kwargs
  generation_kwargs = dict(
    input_ids=inputs.input_ids,
    prompt_input_ids=prompt.input_ids,
    attention_mask=inputs.attention_mask,
    prompt_attention_mask=prompt.attention_mask,
    streamer=streamer,
    do_sample=True,
    temperature=1.0,
    min_new_tokens=10,
  )
  # initialize Thread
  print("Starting generation thread...")
  thread = Thread(target=model.generate, kwargs=generation_kwargs)
  thread.start()


  # iterate over chunks of audio
  for new_audio in streamer:
    print("# iterate over chunks of audio")
    if new_audio.shape[0] == 0:
      break
    print(f"Sample of length: {round(new_audio.shape[0] / sampling_rate, 4)} seconds")
    yield sampling_rate, new_audio


# now you can do
text = "This is a test of the streamer class"
description = "Jon's talking really fast."

chunk_size_in_s = 0.5

for (sampling_rate, audio_chunk) in generate(text, description, chunk_size_in_s):
  # You can do everything that you need with the chunk now
  # For example: stream it, save it, play it.
  print(audio_chunk.shape) 
    # Play the audio chunk
  sd.play(audio_chunk, samplerate=sampling_rate)
  sd.wait()  # Wait until the chunk finishes playing