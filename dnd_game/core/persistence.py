# core/persistence.py
from typing import List, Dict, Any, Type
from pathlib import Path
import json
from datetime import datetime
from pydantic import BaseModel
from ..models.game_state import GameState, Round
from ..models.character import Character, PersonalityProfile
from ..models.actions import RoundSummary, Intent, DifficultyAssessment
from ..agents.player import PlayerAgent
from ..agents.dm import DMAgent
from ..agents.chronicler import ChroniclerAgent

class GameSave(BaseModel):
    """Structure for saved game data"""
    metadata: Dict[str, Any]
    game_state: Dict[str, Any]
    characters: Dict[str, Dict[str, Any]]
    personalities: Dict[str, Dict[str, Any]]
    agent_configs: Dict[str, Dict[str, Any]]
    dm_config: Dict[str, Any]
    chronicler_config: Dict[str, Any]

class GamePersistence:
    """Handles saving and loading game state"""
    def __init__(self, save_dir: str = "saves"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

    def save_game(
        self,
        game_master: 'GameMaster',
        save_name: str = None
    ) -> str:
        """
        Save the current game state to a file.
        Returns the path to the save file.
        """
        # Generate save name if not provided
        if save_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"game_save_{timestamp}"

        # Ensure .json extension
        if not save_name.endswith('.json'):
            save_name += '.json'

        save_path = self.save_dir / save_name

        # Create save data structure
        save_data = GameSave(
            metadata={
                "timestamp": datetime.now().isoformat(),
                "round_number": game_master.state.current_round.number,
                "player_count": len(game_master.players),
                "version": "1.0"
            },
            game_state=self._serialize_game_state(game_master.state),
            characters={
                name: self._serialize_character(player.character)
                for name, player in game_master.players.items()
            },
            personalities={
                name: self._serialize_personality(player.personality)
                for name, player in game_master.players.items()
            },
            agent_configs={
                name: {
                    "model": player.model,
                    "temperature": player.temperature
                }
                for name, player in game_master.players.items()
            },
            dm_config={
                "model": game_master.dm.model,
                "temperature": game_master.dm.temperature,
                "style": getattr(game_master.dm, 'style', {})
            },
            chronicler_config={
                "model": game_master.chronicler.model,
                "temperature": game_master.chronicler.temperature,
                "memory_length": game_master.chronicler.memory_length
            }
        )

        # Save to file
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data.model_dump(), f, indent=2, ensure_ascii=False)

        return str(save_path)

    @staticmethod
    def _serialize_game_state(state: GameState) -> Dict[str, Any]:
        """Serialize GameState instance to dictionary"""
        return {
            "current_situation": state.current_situation,
            "current_round": {
                "number": state.current_round.number,
                "turns_taken": state.current_round.turns_taken,
                "round_context": state.current_round.round_context
            },
            "last_actions": state.last_actions,
            "last_results": {
                name: {
                    "success": result.success,
                    "roll": result.roll,
                    "action": result.action,
                    "description": result.description,
                    "difficulty": result.difficulty.value if result.difficulty else None,
                    "reasoning": result.reasoning
                }
                for name, result in state.last_results.items()
                if result is not None
            },
            "round_summaries": [
                summary.model_dump() for summary in state.round_summaries
            ],
            "active_context": state.active_context
        }

    @staticmethod
    def _serialize_character(character: Character) -> Dict[str, Any]:
        """Serialize Character instance to dictionary"""
        return {
            "name": character.name,
            "level": character.level,
            "class_name": character.class_name,
            "race": character.race,
            "key_abilities": character.key_abilities,
            "equipment": character.equipment,
            "description": character.description
        }

    @staticmethod
    def _serialize_personality(personality: PersonalityProfile) -> Dict[str, Any]:
        """Serialize PersonalityProfile instance to dictionary"""
        return {
            "traits": personality.traits,
            "ideals": personality.ideals,
            "bonds": personality.bonds,
            "flaws": personality.flaws,
            "quirks": personality.quirks
        }

    def load_game(self, save_path: str) -> tuple['GameMaster', Dict[str, Any]]:
        """
        Load a game from a save file.
        Returns a new GameMaster instance and the save metadata.
        """
        save_path = Path(save_path)
        if not save_path.exists():
            raise FileNotFoundError(f"Save file not found: {save_path}")

        with open(save_path, 'r', encoding='utf-8') as f:
            save_data = GameSave.model_validate(json.load(f))

        # Recreate player agents
        player_agents = []
        for name, char_data in save_data.characters.items():
            character = Character(**char_data)
            personality = PersonalityProfile(**save_data.personalities[name])
            agent_config = save_data.agent_configs[name]

            player_agents.append(
                PlayerAgent(
                    character=character,
                    personality=personality,
                    model=agent_config["model"],
                    temperature=agent_config["temperature"]
                )
            )

        # Recreate DM agent
        dm_agent = DMAgent(
            model=save_data.dm_config["model"],
            temperature=save_data.dm_config["temperature"],
            style_preferences=save_data.dm_config.get("style")
        )

        # Recreate Chronicler agent
        chronicler_agent = ChroniclerAgent(
            model=save_data.chronicler_config["model"],
            temperature=save_data.chronicler_config["temperature"],
            memory_length=save_data.chronicler_config["memory_length"]
        )

        # Create new GameMaster
        from .game_master import GameMaster  # Import here to avoid circular imports
        game_master = GameMaster(
            dm_agent=dm_agent,
            player_agents=player_agents,
            chronicler_agent=chronicler_agent,
            initial_situation=save_data.game_state["current_situation"]
        )

        # Restore game state
        game_master.state.current_round = Round(**save_data.game_state["current_round"])
        game_master.state.last_actions = save_data.game_state["last_actions"]
        game_master.state.last_results = {
            name: ActionResult(**result_data)
            for name, result_data in save_data.game_state["last_results"].items()
        }
        game_master.state.round_summaries = [
            RoundSummary.model_validate(summary_data)
            for summary_data in save_data.game_state["round_summaries"]
        ]
        game_master.state.active_context = save_data.game_state["active_context"]

        return game_master, save_data.metadata

def get_save_files(save_dir: str = "saves") -> List[Dict[str, Any]]:
    """Get information about all available save files"""
    save_dir = Path(save_dir)
    saves = []

    for save_path in save_dir.glob("*.json"):
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
                saves.append({
                    "filename": save_path.name,
                    "path": str(save_path),
                    "timestamp": save_data["metadata"]["timestamp"],
                    "round": save_data["metadata"]["round_number"],
                    "players": save_data["metadata"]["player_count"]
                })
        except Exception as e:
            print(f"Error reading save file {save_path}: {e}")

    return sorted(saves, key=lambda x: x["timestamp"], reverse=True)
