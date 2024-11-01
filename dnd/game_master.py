# game_master.py
# ----------------------------------------------
from typing import List, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel
from random import Random
import difflib
import uuid
# ----------------------------------------------
from dnd.dnd_agents import (
    Agent, Task, compress_memory, summarize_turn, summarize_round,
    assess_detail_importance, retrieve_relevant_context, task__ask_questions,
    task__declare_intent, task__provide_feedback, task__make_decision, task__describe_situation, task__describe_initial_situation,
    task__assess_difficulty, task__answer_questions, task__resolve_action, task__enforce_dm, task__enforce_player,
    chronicler_agent, dm_agent, enforcer_agent, DifficultyAssessment
)
from audio.tts_elevenlabs import elevenlabs_tts, flush_audio_queue
from core.job_manager import (
    initialize_workers,
    enqueue_llm_job,
    enqueue_audio_playback_job,
    enqueue_tts_job,
    get_user_input,
    app
)# ----------------------------------------------

random = Random()

VERBOSE = False
SKIP = False
TTS_MODEL = "ELEVENSLAB"
logger = None

async def tts(text: str, connected_clients, voice_id: str = "pNInz6obpgDQGcFmaJgB") -> None:
    # ELEVENSLAB TTS
    if TTS_MODEL == "ELEVENSLAB":
        # Schedule enqueue audio to run as a background task
        await elevenlabs_tts(text, connected_clients, voice_id)


async def enforce_dm(enforcer_agent, original_text:str, logger) -> str:

    logger.info("DM[*]:")
    edited_text = await enqueue_llm_job(
                enforcer_agent,
                task__enforce_dm,
                dm_output=original_text
            )

    color_diff(original_text, edited_text, logger)

    return edited_text
#

async def enforce_player(enforcer_agent, original_text:str, player_name, logger) -> str:
    
    logger.info(f"{player_name.upper()}[*]:")        
    edited_text = await enqueue_llm_job(
                enforcer_agent,
                task__enforce_player,
                player_output=original_text
            )

    color_diff(original_text, edited_text, logger)

    return edited_text
#

def color_diff(original, edited, logger):
    # Define ANSI color codes
    RED_STRIKETHROUGH = "\033[91m\033[9m"  # Red with strikethrough
    GREEN = "\033[92m"
    RESET = "\033[0m"

    # Split both strings into words
    original_words = original.split()
    edited_words = edited.split()

    # Use difflib to find differences between word lists
    diff = difflib.ndiff(original_words, edited_words)

    # Process differences and apply color formatting
    result = []
    for item in diff:
        if item.startswith(" "):  # Unchanged words
            result.append(item[2:])
        elif item.startswith("+"):  # Added words in green
            result.append(f"{GREEN}{item[2:]}{RESET}")
        elif item.startswith("-"):  # Removed words in red with strikethrough
            result.append(f"{RED_STRIKETHROUGH}{item[2:]}{RESET}")

    # Join list into a single string with spaces and print to console
    logger.info(" ".join(result))
#

DEFAULT_PLAYERS_MODEL = "openai|gpt-4o-mini"
DEFAULT_PLAYERS_TEMPERATURE = 0.7

# Models and State (placeholder for actual implementations)
@dataclass
class GameState:
    current_situation: str
    current_round: int
    round_summaries: List[Any]
    last_actions: Dict[str, str]
    
    def get_relevant_context(self) -> str:
        return "Relevant context details"

@dataclass
class CharacterSheet:
    name: str
    pronouns: str
    level: int
    class_name: str
    race: str
    key_abilities: List[str]
    equipment: List[str]
    description: str
    traits: List[str]
    ideals: List[str]
    bonds: List[str]
    flaws: List[str]
    quirks: List[str]

    def to_string(self) -> str:
        return f"Character Name: {self.name}, Pronoums: {self.pronouns}, Class: {self.class_name}, Level: {self.level}, Race: {self.race}, Abilities: {', '.join(self.key_abilities)}, Equipment: {', '.join(self.equipment)}, Description: {self.description}, Traits: {', '.join(self.traits)}, Ideals: {', '.join(self.ideals)}, Bonds: {', '.join(self.bonds)}, Flaws: {', '.join(self.flaws)}, Quirks: {', '.join(self.quirks)}"

@dataclass
class PlayerCharacter:
    character_name: str
    character_sheet: CharacterSheet
    character_agent: Agent
    character_voice: str

    def __init__(self, name: str, character_sheet: CharacterSheet, character_voice: str = "pNInz6obpgDQGcFmaJgB", character_model: str = DEFAULT_PLAYERS_MODEL):
   
        PLAYER_SYSTEM_PROMPT = f"You are playing {name}, a character in a D&D game. This is a brief description of your character: {character_sheet.to_string()}."""

        self.character_name = name
        self.character_sheet = character_sheet
        self.character_agent = Agent(name=name, model=character_model, temperature=DEFAULT_PLAYERS_TEMPERATURE, system_prompt=PLAYER_SYSTEM_PROMPT)
        self.character_voice = character_voice
    #
#

# Initialize GameMaster
class GameMaster:
    def __init__(
        self,
        dm_agent: Agent,
        player_characters: List[PlayerCharacter],
        chronicler_agent: Agent,
        enforcer_agent: Agent,
        dm_voice: str,
        initial_situation: str):

        self.dm_voice = dm_voice
        self.agent__dm = dm_agent
        self.player_characters = player_characters
        self.agent__chronicler = chronicler_agent
        self.agent__enforcer = enforcer_agent
        self.state = GameState(
            current_situation=initial_situation,
            current_round=1,
            round_summaries=[],
            last_actions={} )

        self.very_first_time = True
    #

    
    async def execute_player_turn(self, player: PlayerCharacter, the_story_so_far:str, console_logger, connected_clients) -> None:
        
        logger = console_logger
        print("LOGGER = %s", logger)

        this_turn_narrative = the_story_so_far +"\n"

        character_name = player.character_name
        character_sheet = player.character_sheet.to_string()
        agent__player = player.character_agent
        character_voice = player.character_voice
        is_human = agent__player.model.lower() == "human"
        
        context = self.state.get_relevant_context()
        other_characters = self._format_other_characters(character_name)
        situation = self.state.current_situation

        logger.info(f"\n=== {character_name}'s Turn ===")

        try:
            generated__situation_description = ""
            if self.very_first_time:
                logger.info("\n# 1. DM describes the situation FOR THE FIRST TIME\n")
                generated__situation_description = await enqueue_llm_job(
                    self.agent__dm,
                    task__describe_situation,

                    the_story_so_far=the_story_so_far,
                    character_name=character_name,
                    character_sheet=character_sheet,
                    other_characters=other_characters,
                )
                generated__situation_description = await enforce_dm(self.agent__enforcer, generated__situation_description, logger)
                await tts(generated__situation_description, connected_clients, self.dm_voice)
            #


            new_narrative = f"\nDM:\n{generated__situation_description}\n"
            #logger.info(new_narrative)
            this_turn_narrative += new_narrative
            self.very_first_time = False

            try:
                logger.info("\n# 2. Player asks questions\n")
                # let's list the clients
                for client in connected_clients:
                    print(f"Client: {client}")
                #   
                            
                if VERBOSE: await tts(f"{character_name}, do you have any questions?", connected_clients, self.dm_voice)

                generated__questions = ""
                if False: #is_human:
                    generated__questions = await get_user_input(f"{character_name}, do you have any questions?")
                else:
                    generated__questions = await enqueue_llm_job(
                            agent__player,
                            task__ask_questions,

                            character_name=character_name,
                            the_story_so_far=the_story_so_far,
                            what_the_dm_just_told_you=generated__situation_description,
                            character_sheet=character_sheet,
                        )
                
                new_narrative = f"\n{character_name.upper()}:\n{generated__questions}\n"
                if VERBOSE: await tts(generated__questions, connected_clients, character_voice)

                logger.info(new_narrative)
                this_turn_narrative += new_narrative
            except Exception as e:
                logger.info(f"Error during {character_name}'s question asking: {str(e)}")
                # halt the game here
                raise e
            #

            try:
                logger.info("\n# 3. DM answers questions\n")
                generated__answers = await enqueue_llm_job(
                    self.agent__dm,
                    task__answer_questions,

                    character_name=character_name,
                    the_story_so_far=the_story_so_far,
                    what_you_just_told_the_player=generated__situation_description,
                    character_sheet=character_sheet,
                    questions=generated__questions,
                )

                generated__answers = await enforce_dm(self.agent__enforcer, generated__answers, logger)
                if VERBOSE: await tts(generated__answers, connected_clients, self.dm_voice)

                new_narrative = f"\nDM:\n{generated__answers}\n"
                #logger.info(new_narrative)
                this_turn_narrative += new_narrative
            except Exception as e:
                logger.info(f"Error during {character_name}'s question answering: {str(e)}")
                # halt the game here
                raise e
            #

            logger.info("\n# 4. Player declares intent\n")
            generated__intent = await enqueue_llm_job(
                agent__player,
                task__declare_intent,

                character_name = character_name,
                the_story_so_far = the_story_so_far,
                what_the_dm_just_told_you = generated__situation_description,
                character_sheet = character_sheet,
                player_questions = generated__questions,
                dm_answers = generated__answers,
            )
            await tts(generated__intent, connected_clients, character_voice)
            new_narrative = f"\n{character_name.upper()}:\n{generated__intent}\n"
            logger.info(new_narrative)
            this_turn_narrative += new_narrative

            logger.info("\n# 5. Other players provide feedback\n")
            generated__feedbacks = []
            for other_player in self.player_characters:
                other_name = other_player.character_name
                other_voice = other_player.character_voice
                other_agent = other_player.character_agent
                other_sheet = other_player.character_sheet.to_string()


                if other_name != character_name:

                    logger.info(f"\n...")
                    await tts(f"{other_name}?", connected_clients, character_voice)
                    generated__player_feedback = await enqueue_llm_job(
                        other_agent,
                        task__provide_feedback,

                        other_character_name=other_name,
                        the_story_so_far = the_story_so_far,
                        what_the_dm_just_told_you = generated__situation_description,
                        other_character_sheet = other_sheet,
                        acting_character_name = character_name,
                        intended_action = generated__intent
                    )

                    generated__player_feedback = await enforce_player(self.agent__enforcer, generated__player_feedback, other_name, logger)
                    await tts(generated__player_feedback, connected_clients, other_voice)

                    generated__feedbacks.append((other_name, generated__player_feedback))

                    new_narrative = f"\n\n{other_name.upper()}:\n{generated__player_feedback}\n\n"
                    #logger.info(new_narrative)
                    this_turn_narrative += new_narrative

            logger.info("\n# 6. Player makes final decision\n")
            generated__final_action = await enqueue_llm_job(
                agent__player,
                task__make_decision,

                character_name = character_name,
                the_story_so_far = the_story_so_far,
                what_the_dm_just_told_you = generated__situation_description,
                character_sheet = character_sheet,
                intended_action = generated__intent,
                party_feedback = "\n".join(f"{name}: {fb}" for name, fb in generated__feedbacks)
            )

            generated__final_action = await enforce_player(self.agent__enforcer, generated__final_action, character_name, logger)
            await tts(generated__final_action, connected_clients, character_voice)

            new_narrative = f"\n{character_name.upper()}:\n{generated__final_action}\n"
            #logger.info(new_narrative)
            this_turn_narrative += new_narrative

            logger.info("\n# 7. DM assesses difficulty\n")
            generated__difficulty_assessment:DifficultyAssessment = await enqueue_llm_job(
                self.agent__dm,
                task__assess_difficulty,

                character_name = character_name,
                the_story_so_far = the_story_so_far,
                what_you_just_told_the_player = generated__situation_description,
                proposed_action = generated__final_action,
                character_sheet = character_sheet
            )
            
            new_narrative = f"\nDM:\nDifficulty: {generated__difficulty_assessment.difficulty}\nReasoning: {generated__difficulty_assessment.reasoning}\n"
            logger.info(new_narrative)
            this_turn_narrative += new_narrative

            logger.info("\n# 8. Resolve action\n")
            difficulty_thresholds = {"auto_succeed": 100, "easy": 80, "average": 60, "hard": 40, "super_hard": 20, "auto_fail":0}.get
            success_threshold = difficulty_thresholds(generated__difficulty_assessment.difficulty)
            roll = int(random.uniform(0, 100))
            did_roll_succeed = roll <= success_threshold

            new_narrative = f"\nRoll is {roll}. Threshold was {success_threshold}\n"
            logger.info(new_narrative)
            this_turn_narrative += new_narrative

            if did_roll_succeed: 
                new_narrative = f"\n{character_name} succeeds!\n" 
            else: 
                new_narrative = f"\n{character_name} fails!\n"
            #
            logger.info(new_narrative)
            await tts(new_narrative, connected_clients, self.dm_voice)

            this_turn_narrative += new_narrative

            generated__resolution = await enqueue_llm_job(
                self.agent__dm,
                task__resolve_action,

                character_name = character_name,
                the_story_so_far = the_story_so_far,
                what_you_just_told_the_player = generated__situation_description,
                character_sheet = character_sheet,
                proposed_action = generated__final_action,
                difficulty_assessment = generated__difficulty_assessment,
                roll = roll,
                success_threshold = success_threshold,
                did_roll_succeed = did_roll_succeed
            )

            generated__resolution = await enforce_dm(self.agent__enforcer, generated__resolution, logger)
            await tts(generated__resolution, connected_clients, self.dm_voice)

            new_narrative = f"\n{generated__resolution}\n"
            #logger.info(new_narrative)
            this_turn_narrative += new_narrative

            # Update game state
            #self.state.last_actions[character_name] = generated__final_action
            #self.state.round_summaries.append(f"{character_name}'s Action:\n- Attempted: {generated__final_action}\n- Result: {generated__resolution}")

            return this_turn_narrative
        
        except Exception as e:
            logger.info(f"Error during {character_name}'s turn: {str(e)}")
            # halt the game here
            raise e

        return this_turn_narrative
    #

    def _format_other_characters(self, active_player_name: str) -> str:

        other_characters_description = ""
        for character in self.player_characters:
            if character.character_name != active_player_name:
                other_characters_description += character.character_sheet.to_string() + "\n"
            #
        #

        return other_characters_description
    #