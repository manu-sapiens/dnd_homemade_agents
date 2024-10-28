
from typing import List, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel
from random import Random
random = Random()
import difflib

async def enforce_dm(enforcer_agent, original_text:str) -> str:

    print("DM[*]:")
    edited_text = await enforcer_agent.execute_task(
                task__enforce_dm,
                dm_output=original_text
            )

    color_diff(original_text, edited_text)

    return edited_text
#

async def enforce_player(enforcer_agent, original_text:str, player_name) -> str:
    
    print(f"{player_name.upper()}[*]:")        
    edited_text = await enforcer_agent.execute_task(
                task__enforce_player,
                player_output=original_text
            )

    color_diff(original_text, edited_text)

    return edited_text
#

def color_diff_OLD(original, edited):
    # Define ANSI color codes
    RED = "\033[91m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    # Use difflib's SequenceMatcher to find differences
    diff = difflib.ndiff(original, edited)

    # Process differences and apply color formatting
    result = []
    for item in diff:
        if item.startswith(" "):  # Unchanged text
            result.append(item[2:])
        elif item.startswith("+"):  # Added text in green
            result.append(f"{GREEN}{item[2:]}{RESET}")
        elif item.startswith("-"):  # Removed text in red
            result.append(f"{RED}{item[2:]}{RESET}")

    # Join list into a single string and print to console
    print("".join(result))
#

def color_diff(original, edited):
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
    print(" ".join(result))
#

from dnd.dnd_agents import (
    Agent, Task, compress_memory, summarize_turn, summarize_round,
    assess_detail_importance, retrieve_relevant_context, task__ask_questions,
    task__declare_intent, task__provide_feedback, task__make_decision, task__describe_situation,
    task__assess_difficulty, task__answer_questions, task__resolve_action, task__enforce_dm, task__enforce_player,
    chronicler_agent, dm_agent, enforcer_agent, DifficultyAssessment
)

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

    def __init__(self, name: str, character_sheet: CharacterSheet):
   
        PLAYER_SYSTEM_PROMPT = f"You are playing {name}, a character in a D&D game. This is a brief description of your character: {character_sheet.to_string()}."""

        self.character_name = name
        self.character_sheet = character_sheet
        self.character_agent = Agent(name=name, model=DEFAULT_PLAYERS_MODEL, temperature=DEFAULT_PLAYERS_TEMPERATURE, system_prompt=PLAYER_SYSTEM_PROMPT)
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
        initial_situation: str):

        self.dm_agent = dm_agent
        self.player_characters = player_characters
        self.chronicler_agent = chronicler_agent
        self.enforcer_agent = enforcer_agent
        self.state = GameState(
            current_situation=initial_situation,
            current_round=1,
            round_summaries=[],
            last_actions={} )
    #

    async def execute_player_turn(self, player: PlayerCharacter, the_story_so_far:str) -> None:
        
        this_turn_narrative = the_story_so_far +"\n"

        character_name = player.character_name
        character_sheet = player.character_sheet.to_string()
        player_agent = player.character_agent
        
        context = self.state.get_relevant_context()
        other_characters = self._format_other_characters(character_name)
        situation = self.state.current_situation

        print(f"\n=== {character_name}'s Turn ===")

        try:
            print("\n# 1. DM describes the situation\n")
            result__situation_description = await self.dm_agent.execute_task(
                task__describe_situation,

                the_story_so_far=the_story_so_far,
                character_name=character_name,
                character_sheet=character_sheet,
                other_characters=other_characters,
            )

            result__situation_description = await enforce_dm(self.enforcer_agent, result__situation_description)

            new_narrative = f"\nDM:\n{result__situation_description}\n"
            #print(new_narrative)
            this_turn_narrative += new_narrative

            print("\n# 2. Player asks questions\n")
            result__questions = await player_agent.execute_task(
                task__ask_questions,

                character_name = character_name,
                the_story_so_far = the_story_so_far,
                what_the_dm_just_told_you = result__situation_description,
                character_sheet=character_sheet,
            )
            
            new_narrative = f"\n{character_name.upper()}:\n{result__questions}\n"
            print(new_narrative)
            this_turn_narrative += new_narrative

            print("\n# 3. DM answers questions\n")
            result__answers = await self.dm_agent.execute_task(
                task__answer_questions,

                character_name = character_name,
                the_story_so_far = the_story_so_far,
                what_you_just_told_the_player = result__situation_description,
                character_sheet = character_sheet,
                questions = result__questions
            )

            result__answers = await enforce_dm(self.enforcer_agent, result__answers)

            new_narrative = f"\nDM:\n{result__answers}\n"
            #print(new_narrative)
            this_turn_narrative += new_narrative

            print("\n# 4. Player declares intent\n")
            result__intent = await player_agent.execute_task(
                task__declare_intent,

                character_name = character_name,
                the_story_so_far = the_story_so_far,
                what_the_dm_just_told_you = result__situation_description,
                character_sheet = character_sheet,
                player_questions = result__questions,
                dm_answers = result__answers,
            )
            new_narrative = f"\n{character_name.upper()}:\n{result__intent}\n"
            print(new_narrative)
            this_turn_narrative += new_narrative

            print("\n# 5. Other players provide feedback\n")
            result__feedbacks = []
            for other_player in self.player_characters:
                other_name = other_player.character_name
                if other_name != character_name:

                    print(f"\n...")
                    result__player_feedback = await other_player.character_agent.execute_task(
                        task__provide_feedback,

                        other_character_name=other_name,
                        the_story_so_far = the_story_so_far,
                        what_the_dm_just_told_you = result__situation_description,
                        other_character_sheet = other_player.character_sheet.to_string(),
                        acting_character_name = character_name,
                        intended_action = result__intent
                    )

                    result__player_feedback = await enforce_player(self.enforcer_agent, result__player_feedback, other_name)
                    result__feedbacks.append((other_name, result__player_feedback))

                    new_narrative = f"\n\n{other_name.upper()}:\n{result__player_feedback}\n\n"
                    #print(new_narrative)
                    this_turn_narrative += new_narrative

            print("\n# 6. Player makes final decision\n")
            result__final_action = await player_agent.execute_task(
                task__make_decision,

                character_name = character_name,
                the_story_so_far = the_story_so_far,
                what_the_dm_just_told_you = result__situation_description,
                character_sheet = character_sheet,
                intended_action = result__intent,
                party_feedback = "\n".join(f"{name}: {fb}" for name, fb in result__feedbacks)
            )

            result__final_action = await enforce_player(self.enforcer_agent, result__final_action, character_name)

            new_narrative = f"\n{character_name.upper()}:\n{result__final_action}\n"
            #print(new_narrative)
            this_turn_narrative += new_narrative

            print("\n# 7. DM assesses difficulty\n")
            result__difficulty_assessment:DifficultyAssessment = await self.dm_agent.execute_task(
                task__assess_difficulty,

                character_name = character_name,
                the_story_so_far = the_story_so_far,
                what_you_just_told_the_player = result__situation_description,
                proposed_action = result__final_action,
                character_sheet = character_sheet
            )
            new_narrative = f"\nDM:\nDifficulty: {result__difficulty_assessment.difficulty}\nReasoning: {result__difficulty_assessment.reasoning}\n"
            print(new_narrative)
            this_turn_narrative += new_narrative

            print("\n# 8. Resolve action\n")
            difficulty_thresholds = {"auto_succeed": 100, "easy": 80, "average": 60, "hard": 40, "super_hard": 20, "auto_fail":0}.get
            success_threshold = difficulty_thresholds(result__difficulty_assessment.difficulty)
            roll = int(random.uniform(0, 100))
            did_roll_succeed = roll <= success_threshold

            new_narrative = f"\nRoll is {roll}. Threshold was {success_threshold}\n"
            print(new_narrative)
            this_turn_narrative += new_narrative

            if did_roll_succeed: 
                new_narrative = f"\n{character_name} succeeds!\n" 
            else: 
                new_narrative = f"\n{character_name} fails!\n"
            #
            print(new_narrative)
            this_turn_narrative += new_narrative

            result__resolution = await self.dm_agent.execute_task(
                task__resolve_action,

                character_name = character_name,
                the_story_so_far = the_story_so_far,
                what_you_just_told_the_player = result__situation_description,
                character_sheet = character_sheet,
                proposed_action = result__final_action,
                difficulty_assessment = result__difficulty_assessment,
                roll = roll,
                success_threshold = success_threshold,
                did_roll_succeed = did_roll_succeed
            )

            result__resolution = await enforce_dm(self.enforcer_agent, result__resolution)

            new_narrative = f"\n{result__resolution}\n"
            #print(new_narrative)
            this_turn_narrative += new_narrative

            # Update game state
            #self.state.last_actions[character_name] = result__final_action
            #self.state.round_summaries.append(f"{character_name}'s Action:\n- Attempted: {result__final_action}\n- Result: {result__resolution}")

            return this_turn_narrative
        
        except Exception as e:
            print(f"Error during {character_name}'s turn: {str(e)}")
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