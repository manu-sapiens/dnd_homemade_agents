import os
import asyncio
import uuid
from typing import IO
from io import BytesIO
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment
from pydub.playback import play
from concurrent.futures import ThreadPoolExecutor

# ElevenLabs setup
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Asynchronous queue to hold audio streams
audio_queue = asyncio.Queue()

# Generate a unique run ID and initialize counter
run_id = uuid.uuid4().hex
file_count = 0

async def text_to_speech_stream(text: str, voice_id: str = "pNInz6obpgDQGcFmaJgB") -> IO[bytes]:
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

    audio_stream = BytesIO()
    for chunk in response:
        if chunk:
            audio_stream.write(chunk)
    audio_stream.seek(0)
    return audio_stream

async def play_audio_from_stream(audio_stream: IO[bytes]):
    # Helper function to play audio from a stream in a separate thread
    audio = AudioSegment.from_file(audio_stream, format="mp3")
    with ThreadPoolExecutor() as executor:
        await asyncio.get_running_loop().run_in_executor(executor, play, audio)

async def save_audio_to_disk(audio_stream: IO[bytes], filename: str):
    # Save audio data from BytesIO to a file after playback
    with open(filename, "wb") as f:
        f.write(audio_stream.read())
    print(f"Audio saved to {filename}")

async def enqueue_audio(text: str, voice_id: str = "pNInz6obpgDQGcFmaJgB"):
    global file_count
    
    # Increment count and generate filename
    file_count += 1
    filename = f"{run_id}_{file_count}.mp3"
    
    # Convert text to speech and add to the queue
    audio_stream = await text_to_speech_stream(text, voice_id=voice_id)
    await audio_queue.put((audio_stream, filename))

async def playback_worker():
    while True:
        # Get the next audio stream and filename from the queue
        audio_stream, filename = await audio_queue.get()
        
        if audio_stream:
            # Play audio from the stream, then save to disk afterward
            await play_audio_from_stream(audio_stream)
            audio_stream.seek(0)  # Reset stream position before saving
            await save_audio_to_disk(audio_stream, filename)
        
        audio_queue.task_done()
        await asyncio.sleep(0.1)

# Main entry to start the playback worker
async def tts_initialize():
    # Start the playback worker
    asyncio.create_task(playback_worker())
#