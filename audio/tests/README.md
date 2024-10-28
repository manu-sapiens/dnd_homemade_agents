# BARK INSTALLATION

# from root of the project:
'''
git clone https://github.com/suno-ai/bark
cd bark && pip install . 
pip install git+https://github.com/huggingface/transformers.git
'''

# PARLER INSTALLATION (see: https://github.com/huggingface/parler-tts/tree/main)
Installation
Parler-TTS has light-weight dependencies and can be installed in one line:
'''
pip install git+https://github.com/huggingface/parler-tts.git
'''

Apple Silicon users will need to run a follow-up command to make use the nightly PyTorch (2.4) build for bfloat16 support:

'''
pip3 install --pre torch torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu
'''

Usage
You can directly try it out in an interactive demo here!
Using Parler-TTS is as simple as "bonjour". Simply install the library once:

'''
pip install git+https://github.com/huggingface/parler-tts.git
'''


ALSO:
pip install sounddevice