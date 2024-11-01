import os
import asyncio
import uuid
import hashlib
import json
import shutil
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment
from pydub.playback import play
from nltk.tokenize import sent_tokenize
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

# Initialize a ThreadPoolExecutor for playback
executor = ThreadPoolExecutor(max_workers=1)

# Initialize logging for error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List to store background tasks
background_tasks = []

# Track task completion
def task_done_callback(task):
    # Remove task from background_tasks when done
    background_tasks.remove(task)
    logger.info(f"Task {task.get_name()} completed successfully")

# ElevenLabs setup
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Directory setup
run_id = uuid.uuid4().hex
file_count = 0
output_dir = f"./audio_out/{run_id}"
common_audio_dir = "./common_audio"
cache_file = "./audio_cache.json"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(common_audio_dir, exist_ok=True)
print(f"Output directory for this session: {output_dir}")

# Load or initialize cache dictionary
if os.path.exists(cache_file):
    with open(cache_file, "r") as f:
        audio_cache = json.load(f)
else:
    audio_cache = {}

# Asynchronous queue to hold audio file paths
audio_queue = asyncio.Queue()

# Generate a unique hash for each text + voice_id combination
def generate_hash(text: str, voice_id: str) -> str:
    return hashlib.sha256(f"{text}_{voice_id}".encode()).hexdigest()

# Convert text to speech or retrieve from cache
async def text_to_speech_stream(text: str, voice_id: str = "pNInz6obpgDQGcFmaJgB") -> str:
    file_hash = generate_hash(text, voice_id)
    print("File hash:", file_hash)
    common_file_path = os.path.join(common_audio_dir, f"{voice_id}_{file_hash}.mp3")
    print("Common_file_path:", common_file_path)

    # Check if file is already cached and in common_audio
    if file_hash in audio_cache:
        cached_path = audio_cache[file_hash]
        
        # If cached file is missing, regenerate
        if not os.path.exists(cached_path):
            print(f"Warning: Cached audio missing for text: '{text}'. Regenerating...")
            del audio_cache[file_hash]  # Remove broken cache entry
        else:
            # If cached file exists but is not in common_audio, move it there
            if cached_path != common_file_path:
                shutil.move(cached_path, common_file_path)
                audio_cache[file_hash] = common_file_path  # Update cache to point to common_audio
                print(f"Moved audio to common_audio for repeated use: '{text}'")

                with open(cache_file, "w") as f:
                    print("Saving audio cache to disk...")
                    json.dump(audio_cache, f)

            else:
                print(f"Using cached audio for text: '{text}'")

            # Copy to session directory if not already there
            session_file_path = os.path.join(output_dir, os.path.basename(common_file_path))
            if not os.path.exists(session_file_path):
                shutil.copy2(common_file_path, session_file_path)

            print(f"Returning path={session_file_path} cached audio for text: '{text}' <--------------")
            return session_file_path

    # Generate new audio if not cached
    global file_count
    file_count += 1
    filename = f"{voice_id}_{file_hash}.mp3"
    session_file_path = os.path.join(output_dir, filename)

    # Convert text to speech
    response = client.text_to_speech.convert(
        voice_id=voice_id,
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )
    
    with open(session_file_path, "wb") as f:
        for chunk in response:
            f.write(chunk)

    # Cache the path for future use
    audio_cache[file_hash] = session_file_path
    
    # Save cache to disk
    with open(cache_file, "w") as f:
        print("Saving audio cache to disk...")
        json.dump(audio_cache, f)
    
    return session_file_path

async def play_audio_file(file_path: str):
    print("Playing audio file:", file_path)
    audio = AudioSegment.from_file(file_path, format="mp3")
    # Run the play function in a separate thread
    await asyncio.get_running_loop().run_in_executor(executor, play, audio)

# Enqueue audio with error tracking
async def enqueue_audio(text: str, connected_clients, voice_id: str = "pNInz6obpgDQGcFmaJgB"):
    try:
        # Generate the audio file
        file_path = await text_to_speech_stream(text, voice_id=voice_id)
        print(f"enqueue_audio!!! ===> Enqueued audio for text: '{text}' with voice_id: '{voice_id}'") # Debug info
        await handle_audio_file(text, voice_id, file_path, connected_clients)

        if False:
            # Move file to static/audio directory with a unique name
            file_name = f"{uuid.uuid4()}.mp3"  # Generate a unique name for each file
            static_path = os.path.join("static/audio", file_name)
            # copy2 instead of move to keep the original file
            shutil.copy2(file_path, static_path)
            #os.rename(file_path, static_path)

            print(f"Copied audio file to: {static_path}")
            
            # Construct the URL for the client to access the audio file
            audio_url = f"http://localhost:8000/static/audio/{file_name}"
            print(f"Audio URL: {audio_url}")

            # Send the audio URL to all connected WebSocket clients
            for client in connected_clients:
                print("sending audio URL to client.")
                await client.send_text(f"AUDIO:{audio_url}")
                print("Sent audio URL to client.")
            #
        #else:
        #    print("!!! HOW DID WE GET HERE? !!!")
        #

    except Exception as e:
        logger.error(f"Error in enqueue audio for text: '{text}' with voice_id: '{voice_id}'. Exception: {e}")
        print(f"Error in enqueue audio for text: '{text}' with voice_id: '{voice_id}'. Exception: {e}")
    #
#

async def elevenlabs_tts(text: str, connected_clients, voice_id: str = "pNInz6obpgDQGcFmaJgB") -> None:
    # Schedule enqueue audio as a background task with error tracking
    task = asyncio.create_task(enqueue_audio(text, connected_clients, voice_id))
    task.set_name(f"tts_task_{len(background_tasks) + 1}")
    task.add_done_callback(task_done_callback)  # Callback to remove task upon completion
    background_tasks.append(task)

# Function to check if all background tasks are complete
async def await_all_tasks_complete():
    if background_tasks:
        logger.info("Waiting for all background tasks to complete...")
        await asyncio.gather(*background_tasks)
        logger.info("All background tasks have completed.")
    else:
        logger.info("No background tasks to wait for.")

async def playback_worker():
    
    print("Playback worker started.")
    while True:
        print("Inside the playback worker loop.")
        try:
            file_path = await audio_queue.get()
            print(f"Playback worker processing file: {file_path}")
            
            # Check if this is the termination signal
            if file_path is None:
                print("Playback worker received termination signal.")
                audio_queue.task_done()
                break
            
            # Process the audio file
            try:
                await play_audio_file(file_path)
            except Exception as e:
                print(f"Error processing audio file at {file_path}: {e}")
            
            # Mark the task as done
            audio_queue.task_done()
        
        except Exception as e:
            print(f"Unexpected error in playback_worker: {e}")

        # wait 1s
        print("Playback worker sleeping...")
        await asyncio.sleep(1)

async def flush_audio_queue():
    await await_all_tasks_complete()
    print("Flushing audio queue...")
    worker = asyncio.create_task(playback_worker())
    await audio_queue.join()
    await audio_queue.put(None)
    await worker
    print("All audio flushed and worker has completed.")


def test_nltk_punkt():
    try:
        # Attempt to tokenize without downloading 'punkt'
        sample_text = "Hello! This is a test to see if punkt is available. Let's check."
        sentences = sent_tokenize(sample_text)
        print("Tokenization successful:", sentences)
        return True  # No download necessary
    except LookupError:
        print("NLTK 'punkt' resource not found. Downloading now...")
        nltk.download('punkt')
        return False  # Download was necessary

# Main entry to start the playback worker
async def tts_initialize():
    test_nltk_punkt()

    # Start the playback worker
    # asyncio.create_task(playback_worker())
#

async def handle_audio_file(text:str, voice_id:str, file_path: str, connected_clients):
    print(f"Enqueuing audio for text: '{text}' with voice_id: '{voice_id}'")

    file_path = await text_to_speech_stream(text, voice_id)
    print(f"Generated audio file: {file_path}")

    # Save file to static/audio directory with a unique name
    file_name = f"{uuid.uuid4()}.mp3"
    static_path = os.path.join("static/audio", file_name)
    shutil.copy2(file_path, static_path)
    print(f"Copied audio file to: {static_path}")

    # Construct the accessible audio URL
    audio_url = f"http://localhost:8000/static/audio/{file_name}"
    print(f"Audio URL: {audio_url}")

    # Send the audio URL to all connected WebSocket clients
    print(f"Connected clients: {connected_clients}")
    for client in connected_clients:
        try:
            print("Sending audio URL to client.")
            await client.send_text(f"AUDIO:{audio_url}")
            print("Sent audio URL to client.")
        except Exception as e:
            print(f"Failed to send audio to client: {e}")
            connected_clients.remove(client)  # Remove client on error



