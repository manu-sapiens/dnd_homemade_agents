import os
import time
import uuid
import asyncio
import torch
import soundfile as sf
import sounddevice as sd
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
from queue import SimpleQueue

# Set up environment and device
os.environ["TOKENIZERS_PARALLELISM"] = "True"
device = "cuda:0" if torch.cuda.is_available() else "cpu"

# Initialize global playback queue, state, and counters
audio_queue = SimpleQueue()
is_playing = False
generation_count = 0
unique_id = None  # Will be set during model initialization
output_dir = "./audio_out"  # Base directory for audio files

def initialize_model():
    """Loads the Parler TTS model, tokenizer, generates a unique ID, creates output directories, and displays the time taken."""
    global unique_id, output_dir
    start_time = time.time()
    
    # Generate a unique ID for this initialization
    unique_id = str(uuid.uuid4())
    session_dir = os.path.join(output_dir, unique_id)
    
    # Create the output directory and session directory if they don't exist
    os.makedirs(session_dir, exist_ok=True)
    print(f"Output directory for this session: {session_dir}")
    
    # Load model and tokenizer
    model = ParlerTTSForConditionalGeneration.from_pretrained("parler-tts/parler-tts-mini-v1").to(device)
    tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler-tts-mini-v1")
    
    elapsed_time = time.time() - start_time
    print(f"Model initialization took {elapsed_time:.2f} seconds.")
    
    return model, tokenizer, session_dir

async def generate_and_enqueue_audio(model, tokenizer, prompt, description, session_dir):
    """Generates audio, saves it to a unique file in the session directory, enqueues the filename, and displays the time taken."""
    global is_playing, generation_count
    start_time = time.time()
    
    # Increment the generation counter
    generation_count += 1
    
    # Tokenize the input prompt and description
    input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
    inputs = tokenizer(prompt, return_tensors="pt")
    attention_mask = inputs.attention_mask
    prompt_input_ids = inputs.input_ids.to(device)
    #prompt_input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    #print(prompt_input_ids)
    
    # Generate the audio tensor
    generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)#,attention_mask=attention_mask)#,pad_token_id=tokenizer.eos_token_id)
    audio_arr = generation.cpu().numpy().squeeze()
    
    # Save to a unique file in the session directory
    filename = os.path.join(session_dir, f"{unique_id}_{generation_count}.wav")
    sf.write(filename, audio_arr, model.config.sampling_rate)


    print(f"Saved audio to {filename}")
    
    # Enqueue the filename for playback
    audio_queue.put(filename)
    
    # Display the time taken
    elapsed_time = time.time() - start_time
    print(f"Audio generation and saving took {elapsed_time:.2f} seconds.")
    
    # If nothing is currently playing, start playback
    if not is_playing:
        await play_audio_from_queue()

async def play_audio_from_queue():
    """Plays audio files from the queue, one at a time, and displays the time taken."""
    global is_playing
    is_playing = True

    while not audio_queue.empty():
        start_time = time.time()
        
        filename = audio_queue.get()
        audio_arr, sample_rate = sf.read(filename)
        
        # Play audio
        sd.play(audio_arr, samplerate=sample_rate)
        print(f"Playing audio from {filename}")
        sd.wait()  # Wait until the audio finishes playing
        
        # Display the time taken for playback
        elapsed_time = time.time() - start_time
        print(f"Audio playback took {elapsed_time:.2f} seconds.")
    
    is_playing = False

# Main code to initialize model and process a request
if __name__ == "__main__":
    # Initialize model and tokenizer, and get the session directory
    model, tokenizer, session_dir = initialize_model()

    # Define prompt and description
    prompt = "Hey, how are you doing today?"
    description = "Jon, a male speaker delivers a slightly expressive and animated speech with a moderate speed and pitch. The recording is of very high quality, with the speaker's voice sounding clear and very close up."

    # Run the async function to generate and play audio
    asyncio.run(generate_and_enqueue_audio(model, tokenizer, "Hey, how are you doing today?", description, session_dir))
    asyncio.run(generate_and_enqueue_audio(model, tokenizer, "Because everything is peachy here, you know?", description, session_dir))
    asyncio.run(generate_and_enqueue_audio(model, tokenizer, "<sigh> Lah Lah Lah Because everything is peachy here, you know!", description, session_dir))
    asyncio.run(generate_and_enqueue_audio(model, tokenizer, "<Hey> Hey Hey Hey Because everything is peachy here, you know!", description, session_dir))
