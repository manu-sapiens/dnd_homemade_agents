# job_manager.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtWidgets import QInputDialog, QApplication
from typing import Callable
import sys
# ----------------------------------------------
from audio.tts_elevenlabs import play_audio_file, text_to_speech_stream


user_input_event = asyncio.Event()
user_input_value = "<nothing>"

# Ensure QApplication is created only once
app = QApplication.instance() or QApplication(sys.argv)

# Define queues for each job type
llm_queue = asyncio.Queue()
audio_playback_queue = asyncio.Queue()
tts_queue = asyncio.Queue()
user_input_queue = asyncio.Queue()

# Define executors
audio_executor = ThreadPoolExecutor(max_workers=2)  # Dedicated executor for audio
main_thread_executor = ThreadPoolExecutor(max_workers=1)  # For GUI operations (e.g., user input)

# Function to initialize all workers
async def initialize_workers():
    asyncio.create_task(llm_worker())
    asyncio.create_task(audio_playback_worker())
    asyncio.create_task(tts_worker())
    asyncio.create_task(user_input_worker())

# LLM Worker
async def llm_worker():
    while True:
        agent, job, kwargs, result_list = await llm_queue.get()
        try:
            result = await agent.execute_task(job, **kwargs)
            result_list.append(result)
        except Exception as e:
            print(f"Error in LLM Worker: {e}")
        finally:
            llm_queue.task_done()

# Audio Playback Worker
async def audio_playback_worker():
    while True:
        print("Audio Playback Worker started.")
        file_path = await audio_playback_queue.get()
        try:
            await asyncio.get_running_loop().run_in_executor(audio_executor, play_audio_file, file_path)
        except Exception as e:
            print(f"Error in Audio Playback Worker: {e}")
        finally:
            audio_playback_queue.task_done()
        # wait 1s
        await asyncio.sleep(1)

# TTS Worker
async def tts_worker():
    while True:
        text, voice_id = await tts_queue.get()
        try:
            await text_to_speech_stream(text, voice_id)
        except Exception as e:
            print(f"Error in TTS Worker: {e}")
        finally:
            tts_queue.task_done()

# User Input Worker
async def user_input_worker():
    while True:
        prompt_text, user_name, result_future = await user_input_queue.get()
        try:
            user_input, ok = await asyncio.get_running_loop().run_in_executor(
                main_thread_executor,
                lambda: QInputDialog.getText(None, user_name, prompt_text)
            )
            result_future.set_result(user_input if ok else None)
        except Exception as e:
            result_future.set_exception(e)
        finally:
            user_input_queue.task_done()

# Functions to enqueue jobs
async def enqueue_llm_job(agent, job, **kwargs):
    result_list = []
    await llm_queue.put((agent, job, kwargs, result_list))
    await llm_queue.join()  # Wait until job is processed
    return result_list[0]

async def enqueue_audio_playback_job(file_path: str):
    await audio_playback_queue.put(file_path)

async def enqueue_tts_job(text: str, voice_id: str):
    await tts_queue.put((text, voice_id))

async def enqueue_user_input_job(received_value: str):
    global user_input_event, user_input_value
    user_input_value=received_value
    user_input_event.set()  # Signal that input has been received

#

async def get_user_input(prompt):
    global user_input_event, user_input_value
    print(prompt)
    user_input_event.clear()  # Reset the event
    await user_input_event.wait()  # Wait until input is received
    return user_input_value  # Return the stored input
