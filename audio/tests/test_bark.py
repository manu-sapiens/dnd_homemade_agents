#test_bark.py
import os

# set env variable SUNO_USE_SMALL_MODELS=True to use smaller models
os.environ["SUNO_USE_SMALL_MODELS"] = "True"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
print("SUNO_USE_SMALL_MODELS:", os.environ["SUNO_USE_SMALL_MODELS"])    

from transformers import AutoProcessor, BarkModel

print("--------------------")
print("loading processor")
processor = AutoProcessor.from_pretrained("suno/bark")

print("--------------------")
print("loading model")
model = BarkModel.from_pretrained("suno/bark")

voice_preset = "v2/en_speaker_6"

print("--------------------")
print("Processing text")
inputs = processor("Hello, my dog is cute", voice_preset=voice_preset)

print("--------------------")
print("Generate audio")
audio_array = model.generate(**inputs)

print("--------------------")
print("Squeeze audio")
audio_array = audio_array.cpu().numpy().squeeze()

print("--------------------")
print("Play audio (1)")
from IPython.display import Audio
sample_rate = model.generation_config.sample_rate
Audio(audio_array, rate=sample_rate)

import scipy
print("SAVE & Play audio (2)")
sample_rate = model.generation_config.sample_rate
scipy.io.wavfile.write("bark_out.wav", rate=sample_rate, data=audio_array)