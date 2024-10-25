# core/game_master.py
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import asyncio
import random
from ..agents.dm import DMAgent
from ..agents.player import PlayerAgent
from ..agents.chronicler import ChroniclerAgent
from ..models.game_state import GameState, Round, PartyStatus
from ..models.actions import Intent, DifficultyAssessment
from ..models.character import Character
from .tasks import TaskSequencer, TaskType
from .persistence import GamePersistence

class GameMaster:
    """
    Main game orchestrator that manages the game state and coordinates
    between DM, players, and chronicler.
    """
    def __init__(
        self,
        dm_agent: DMAgent,
        player_agents: List[PlayerAgent],
        chronicler_agent: ChroniclerAgent,
        initial_situation: str,
        party_status: PartyStatus
    ):
        self.dm = dm_agent
        self.players = {
            player.character.name: player for player in player_agents
        }
        self.chronicler = chronicler_agent
        self.task_sequencer = TaskSequencer(dm_agent, chronicler_agent)

        # Initialize game state
        self.state = GameState(
            current_situation=initial_situation,
            current_round=Round(number=1),
            party_status=party_status
        )

        # Initialize persistence for saving and loading game states
        self.persistence = GamePersistence()

    async def save(self, save_name: Optional[str] = None) -> str:
        """
        Save the current game state.
        Returns the path to the save file.
        """
        return self.persistence.save_game(self, save_name)

    @classmethod
    async def load(cls, save_path: str) -> tuple['GameMaster', Dict[str, Any]]:
        """
        Load a game from a save file.
        Returns the GameMaster instance and save metadata.
        """
        persistence = GamePersistence()
        return persistence.load_game(save_path)

    def get_available_saves(self) -> List[Dict[str, Any]]:
        """Get information about available save files"""
        return self.persistence.get_save_files()

    async def execute_player_turn(self, player_name: str) -> None:
        """Execute a complete turn for a single player"""
        player = self.players[player_name]

        try:
            print(f"\n=== {player_name}'s Turn ===")

            # Retrieve the last action in round_context, if any, for continuity
            previous_action = self.state.current_round.round_context[-1] if self.state.current_round.round_context else None

            # 1. DM describes the situation with the previous action for continuity
            situation_description = await self.task_sequencer.execute_task(
                TaskType.DESCRIBE_SITUATION,
                situation=self.state.current_situation,
                character_name=player_name,
                active_character=player.character.to_string(),
                other_characters=self._format_other_characters(player_name),
                context=self.state.get_relevant_context(),
                previous_action=previous_action  # Include the previous action in the context
            )
            print(f"\nDM:")
            print(f"{situation_description}")
            print("")

            # 2. Player asks questions
            questions = await self.task_sequencer.execute_task(
                TaskType.ASK_QUESTIONS,
                agent=player,
                character_name=player_name,
                situation_description=situation_description,
                context=self.state.get_relevant_context()
            )
            print(f"\n{player_name.upper()}:")
            print(f"{questions}")
            print("")

            # 3. DM answers questions
            answers = await self.task_sequencer.execute_task(
                TaskType.ANSWER_QUESTIONS,
                situation=situation_description,
                questions=questions,
                character_name=player_name,
                character_details=player.character.to_string(),
                context=self.state.get_relevant_context()
            )
            print(f"\nDM:")
            print(f"{answers}")
            print("")

            # 4. Player declares intent
            intent = await self.task_sequencer.execute_task(
                TaskType.DECLARE_INTENT,
                agent=player,
                situation_description=situation_description,
                qa_exchange=player.format_qa_exchange(questions, answers),
                context=self.state.get_relevant_context()
            )
            print(f"\n{player_name.upper()}:")
            print(f"{intent}")
            print("")

            # 5. Other players provide feedback
            feedback = []
            for other_name, other_player in self.players.items():
                if other_name != player_name:
                    player_feedback = await self.task_sequencer.execute_task(
                        TaskType.PROVIDE_FEEDBACK,
                        agent=other_player,
                        situation_description=situation_description,
                        character_name=player.character.to_string(),
                        intended_action=intent
                    )
                    feedback.append((other_name, player_feedback))
                    print(f"\n{other_name.upper()}:")
                    print(f"{player_feedback}")
                    print("")

            # 6. Player makes final decision
            final_action = await self.task_sequencer.execute_task(
                TaskType.MAKE_DECISION,
                agent=player,
                situation_description=situation_description,
                intended_action=intent,
                party_feedback=player.format_party_feedback(feedback),
                context=self.state.get_relevant_context()
            )

            print(f"\n{player_name.upper()}:")
            print(f"{final_action}")
            print("")

            # 7. DM assesses difficulty
            print("--- #7 ---  DM assesses difficulty")
            assessment = await self.task_sequencer.execute_task(
                TaskType.ASSESS_DIFFICULTY,
                character_name=player_name,
                character_details=player.character.to_string(),
                situation=situation_description,
                action=final_action,
                context=self.state.get_relevant_context()
            )
            print("DM:")
            print(f"\nDifficulty: {assessment.difficulty.value}")
            print(f"Reasoning: {assessment.reasoning}")

            # 8. Resolve action
            print("--- #8 ---  Resolve action")
            success, roll = self._determine_success(assessment)
            resolution = await self.task_sequencer.execute_task(
                TaskType.RESOLVE_ACTION,
                situation=situation_description,
                character_name=player_name,
                character_details=player.character.to_string(),
                action=final_action,
                difficulty_details=self.dm.format_difficulty_details(assessment),
                roll_result=str(roll),
                success=success,
                context=self.state.get_relevant_context()
            )
            print(f"\nOutcome (Roll: {roll})")
            print(f"{resolution}")
            print("")

            # After resolution, get chronicler to summarize the turn
            turn_summary = await self.task_sequencer.execute_task(
                TaskType.SUMMARIZE_TURN,
                round_number=self.state.current_round.number,
                character_name=player_name,
                initial_situation=self.state.current_situation,
                action_taken=final_action,
                action_result=resolution,
                difficulty=assessment.difficulty.value,
                roll_result=roll,
                success=success,
                previous_context=self.state.get_relevant_context()
            )

            # Update game state
            self.state.last_actions[player_name] = final_action
            self.state.current_round.round_context.append(
                f"{player_name}'s Action:\n"
                f"- Attempted: {final_action}\n"
                f"- Difficulty: {assessment.difficulty.value}\n"
                f"- Roll: {roll} ({'Success' if success else 'Failure'})\n"
                f"- Result: {resolution}"
                f"- Effects: {turn_summary.environment_changes}"
            )
            self.state.current_round.turns_taken.append(player_name)
            
            # Update current situation for next player
            self.state.current_situation = (
                f"{turn_summary.narrative_focus}\n\n"
                f"Current state:\n" +
                "\n".join(turn_summary.environment_changes)
            )

        except Exception as e:
            print(f"Error during {player_name}'s turn: {str(e)}")
            raise

    async def execute_round(self) -> None:
        """Execute a complete round where each player takes a turn"""
        print(f"\n=== Round {self.state.current_round.number} ===")

        # Store initial situation for the round summary
        initial_situation = self.state.current_situation

        # Each player takes their turn
        for player_name in self.players.keys():
            await self.execute_player_turn(player_name)

        # Create an overall round summary
        summary = await self.task_sequencer.execute_task(
            TaskType.SUMMARIZE_ROUND,
            round_number=self.state.current_round.number,
            initial_situation=initial_situation,
            final_situation=self.state.current_situation,
            round_events="\n".join(self.state.current_round.round_context),
            party_members="\n".join(
                player.character.to_string()
                for player in self.players.values()
            ),
            previous_summary=self.state.round_summaries[-1] if self.state.round_summaries else None
        )

        # Update game state for next round
        self.state.round_summaries.append(summary)
        self.state.current_round = Round(
            number=self.state.current_round.number + 1
        )

    async def run_game(self, num_rounds: int) -> None:
        """Run the game for a specified number of rounds"""
        try:
            for _ in range(num_rounds):
                await self.execute_round()
        except Exception as e:
            print(f"Game ended due to error: {str(e)}")
            raise

    def _determine_success(self, assessment: DifficultyAssessment) -> tuple[bool, float]:
        """Determine if an action succeeds based on its difficulty"""
        if assessment.auto_resolve:
            return (assessment.difficulty.value == "always_succeed", 0.0)

        difficulty_chances = {
            "easy": 80,
            "average": 60,
            "hard": 40,
            "super_hard": 20
        }

        roll = random.uniform(0, 100)
        threshold = difficulty_chances.get(assessment.difficulty.value, 0)
        return (roll <= threshold, roll)

    def _format_other_characters(self, active_player: str) -> str:
        """Format the list of other characters in the party"""
        return "\n".join(
            player.character.to_string()
            for name, player in self.players.items()
            if name != active_player
        )

    def get_game_summary(self) -> str:
        """Get a complete summary of the game so far"""
        return "\n\n".join([
            f"=== Game Summary ===",
            f"Rounds completed: {self.state.current_round.number - 1}",
            "Recent developments:",
            *[summary.narrative_focus for summary in self.state.round_summaries[-3:]],
            "\nParty status:",
            *[f"{name}: {self.state.last_actions.get(name, 'No action')}"
              for name in self.players.keys()],
            "\nCurrent situation:",
            self.state.current_situation
        ])
