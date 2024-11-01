# run_game.py
# ----------------------------------------------
import asyncio
import argparse
import sys
from qasync import QEventLoop
from PyQt5.QtWidgets import QInputDialog, QApplication
import logging
# ----------------------------------------------
from dnd.dnd_agents import Agent, player_agent, chronicler_agent, dm_agent, enforcer_agent
from dnd.game_master import GameMaster, PlayerCharacter, CharacterSheet
from audio.tts_elevenlabs import elevenlabs_tts, tts_initialize, flush_audio_queue, playback_worker, audio_queue
from core.job_manager import (
    initialize_workers,
    enqueue_llm_job,
    enqueue_audio_playback_job,
    enqueue_tts_job,
    enqueue_user_input_job,
    get_user_input,
    app
)
# ----------------------------------------------

DM_VOICE = "N2lVS1w4EtoT3dr4eOWO" # Callum's voice
SKIP_INTRO = False
logger = logging.getLogger(__name__)
# ----------------------------------------------
# Example of running the game
async def main(initial_situation, connected_clients):

    logger.info("MAIN")
    logger.info("Starting the game...")
    try:
        logger.info("Inializing workers..")
        await initialize_workers(connected_clients)  # Initialize all job workers


        await tts_initialize()

        # Start playback worker task within active event loop
        playback_task = asyncio.create_task(playback_worker())

        logger.info("Enqueuing user input job..")
        user_input = await get_user_input("What is the name of the DM?")
        logger.info(f"User input: {user_input}")

        # Create player agents -------------------------------------------

        # Create Brussae the Paladin
        brussae = PlayerCharacter(
            character_model="human",
            name="Brussae", 
            character_sheet=CharacterSheet(
                name="Brussae",
                pronouns="he/him",
                level=2,
                class_name="Paladin",
                race="Human",
                key_abilities=["divine magic", "combat", "healing"],
                equipment=["longsword", "shield", "chain mail"],
                description="A warrior of faith, devoted to protecting the innocent",
                traits=["brave", "compassionate", "direct"],
                ideals=["protect the innocent", "uphold justice"],
                bonds=["sworn to defend the weak", "devoted to their deity"],
                flaws=["too trusting", "sees everything as good vs evil"],
                quirks=["always cleans their sword after battle", "prays before every meal"]
            ),
            character_voice="iP95p4xoKVk53GoZ742B" #Chris	
        )

        # Create Shadowstep the Rogue
        shadowstep = PlayerCharacter(
            name = "Shadowstep",
            character_sheet=CharacterSheet(
                name="Shadowstep",
                pronouns="he/him",
                level=3,
                class_name="Rogue",
                race="Elf",
                key_abilities=["stealth", "lockpicking", "acrobatics"],
                equipment=["daggers", "thieves tools", "leather armor"],
                description="A nimble burglar with a heart of gold",
                traits=["cunning", "cautious", "witty"],
                ideals=["freedom", "loyalty to friends"],
                bonds=["protective of street urchins", "owes a debt to a noble"],
                flaws=["greedy", "overconfident in their abilities"],
                quirks=["always checks for traps, even in safe places", "collects small trinkets"]
            ),
            character_voice="JBFqnCBsd6RMkjVDRZzb" # George
        )

        # Create Eldara the Wizard
        eldara = PlayerCharacter(
            name="Eldara", 
            character_sheet= CharacterSheet(
                name="Eldara",
                pronouns="she/her",
                level=2,
                class_name="Wizard",
                race="half-elf",
                key_abilities=["arcane magic", "investigation", "history"],
                equipment=["staff", "spellbook", "component pouch"],
                description="A scholarly mage seeking ancient knowledge",
                traits=["analytical", "curious", "reserved"],
                ideals=["knowledge", "magical preservation"],
                bonds=["ancient magical texts", "wizard academy"],
                flaws=["overthinks simple problems", "dismissive of non-magical solutions"],
                quirks=["takes notes about everything", "speaks in unnecessarily complex terms"]
            ),
            character_voice="Xb7hH8MSUJpSbSDYk0k2" # Alice
        )

        player_characters = [brussae, shadowstep, eldara]

        game_master = GameMaster(
            dm_agent=dm_agent,
            player_characters=player_characters,
            chronicler_agent=chronicler_agent,
            enforcer_agent=enforcer_agent,
            initial_situation=initial_situation,
            dm_voice=DM_VOICE 
        )
        
        if SKIP_INTRO==False: await enqueue_tts_job("Welcome to the game! I am the Dungeon Master. Let's begin.", DM_VOICE)
        if SKIP_INTRO==False: await enqueue_tts_job(initial_situation, DM_VOICE)

        logger.info("Starting the game... v 0.22 \n--------------------\n")
        logger.info(initial_situation)
        logger.info("---------")

        if False:
            the_story_so_far = initial_situation
            for player in player_characters:
                the_story_so_far = await game_master.execute_player_turn(player, the_story_so_far, logger)
                logger.info("-------the story so far -------------\n")
                logger.info(the_story_so_far)
                logger.info("---------and now...-----------\n")        
            # 
            await flush_audio_queue()   

        logger.info("DONE Part 2: main")
        # Signal the playback worker to shut down (only if you want a controlled exit)

         # Ensure playback worker finishes
        await playback_task
        logger.info("Playback worker terminated.")

    except Exception as e:
        logger.info(f"Error in main: {e}")
    finally:
        await audio_queue.put(None)  # Send termination signal to playback worker
        await playback_task  # Ensure playback task completes
        logger.info("Playback worker terminated.")
    #
    logger.info("DONE DONE: main")

#
# ----------------------------------------------

# Run the main event loop with qasync
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the D&D game.")
    parser.add_argument(
        "--story",
        type=str,
        default=(
            "The party stands at the entrance of the Crimson Crypt, an ancient tomb recently "
            "uncovered in the forests north of the city. Local legends speak of powerful "
            "magical artifacts sealed away here centuries ago. The stone doorway bears "
            "mysterious runes, and a cold breeze emanates from within. The sun is setting, "
            "casting long shadows through the trees.\n\n"
            "The party has been hired by the Arcane Academy to investigate the tomb and "
            "retrieve any magical artifacts, especially the rumored Orb of First Light. "
            "However, they're not the only ones interested in the tomb's contents - they've "
            "spotted signs of other adventurers in the area."
        ),
        help="The initial situation for the game session.",
    )

    args = parser.parse_args()
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(main(args.story))
# ----------------------------------------------