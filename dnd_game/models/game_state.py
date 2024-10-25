# models/game_state.py
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from datetime import datetime
from .base import BaseGameModel, ValidationResult
from .actions import Intent, DifficultyAssessment

@dataclass
class ActionResult:
    """Represents the result of an attempted action"""
    success: bool
    roll: float  # The actual roll value (0-100)
    action: str  # The action attempted
    description: str  # What happened
    difficulty: Optional[DifficultyAssessment] = None  # The difficulty assessment if any
    reasoning: Optional[str] = None  # Reasoning for the outcome
    timestamp: datetime = field(default_factory=datetime.now)

    def to_string(self) -> str:
        """Format the result for prompts"""
        parts = [
            f"Action: {self.action}",
            f"Result: {'Success' if self.success else 'Failure'} (Roll: {self.roll:.1f})",
            f"What happened: {self.description}"
        ]

        if self.difficulty:
            parts.append(f"Difficulty: {self.difficulty.difficulty.value}")
            parts.append(f"Reasoning: {self.difficulty.reasoning}")

        if self.reasoning:
            parts.append(f"Outcome reasoning: {self.reasoning}")

        return "\n".join(parts)

class EnvironmentalEffect(BaseModel):
    """Tracks ongoing environmental conditions or effects"""
    name: str
    description: str
    duration: Optional[int] = None  # Number of rounds, None for permanent
    affected_areas: List[str] = Field(default_factory=list)
    severity: str = "normal"

    def is_active(self, current_round: int, start_round: int) -> bool:
        """Check if the effect is still active"""
        if self.duration is None:
            return True
        return current_round - start_round < self.duration

class PartyStatus(BaseModel):
    """Tracks the overall status of the party"""
    location: str = Field(..., description="Current party location")
    conditions: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Conditions affecting each character"
    )
    group_conditions: List[str] = Field(
        default_factory=list,
        description="Conditions affecting the whole party"
    )
    resources_used: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Resources used by each character"
    )

@dataclass
class Round:
    """Represents a single round of gameplay"""
    number: int
    turns_taken: List[str] = field(default_factory=list)
    round_context: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    environmental_effects: Dict[str, EnvironmentalEffect] = field(default_factory=dict)

    def add_effect(self, effect: EnvironmentalEffect) -> None:
        """Add a new environmental effect"""
        self.environmental_effects[effect.name] = effect
        self.round_context.append(f"New effect: {effect.name} - {effect.description}")

    def remove_effect(self, effect_name: str) -> None:
        """Remove an environmental effect"""
        if effect_name in self.environmental_effects:
            effect = self.environmental_effects.pop(effect_name)
            self.round_context.append(f"Effect ended: {effect.name}")

    def get_active_effects(self, current_round: int) -> List[EnvironmentalEffect]:
        """Get all currently active environmental effects"""
        return [
            effect for effect in self.environmental_effects.values()
            if effect.is_active(current_round, self.number)
        ]

class GameState(BaseGameModel):
    """
    Maintains the complete state of the game, including:
    - Current situation
    - Round information
    - Character actions and results
    - Environmental effects
    - Game history
    """
    current_situation: str = Field(..., description="Current state of the game world")
    current_round: Round
    party_status: PartyStatus = Field(default_factory=PartyStatus)
    last_actions: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Last action taken by each character"
    )
    last_results: Dict[str, Optional[ActionResult]] = Field(
        default_factory=dict,
        description="Results of the last actions"
    )
    round_summaries: List[Any] = Field(  # Type will be RoundSummary, avoiding circular import
        default_factory=list,
        description="Summaries of completed rounds"
    )
    active_context: List[str] = Field(
        default_factory=list,
        description="Current round's contextual information"
    )

    class Config:
        arbitrary_types_allowed = True

    def add_context(self, event: str) -> None:
        """Add an event to the current context"""
        self.active_context.append(event)
        if len(self.active_context) > 10:  # Keep context manageable
            self.active_context.pop(0)

    def record_action(self, character_name: str, action: str,
                     result: ActionResult) -> None:
        """Record a character's action and its result"""
        self.last_actions[character_name] = action
        self.last_results[character_name] = result
        self.current_round.turns_taken.append(character_name)

        # Add to round context
        self.current_round.round_context.append(result.to_string())

    def start_new_round(self) -> None:
        """Start a new round"""
        new_round_number = self.current_round.number + 1

        # Create new round
        self.current_round = Round(number=new_round_number)

        # Clear per-round state
        self.last_actions.clear()
        self.last_results.clear()
        self.active_context.clear()

    def get_relevant_context(self, lookback: int = 2) -> str:
        """Get formatted context from recent history"""
        context = []

        # Add recent round summaries
        for summary in self.round_summaries[-lookback:]:
            context.append(f"Round {len(self.round_summaries) - self.round_summaries.index(summary)}:")
            context.extend([f"- {event}" for event in summary.key_events])
            context.append("Important consequences:")
            context.extend([f"- {cons}" for cons in summary.important_consequences])
            context.append(f"Narrative focus: {summary.narrative_focus}")
            context.append("")

        # Add current round's events
        if self.active_context:
            context.append("Current round:")
            context.extend(self.active_context)

        # Add active environmental effects
        active_effects = self.current_round.get_active_effects(self.current_round.number)
        if active_effects:
            context.append("\nActive environmental effects:")
            for effect in active_effects:
                context.append(f"- {effect.name}: {effect.description}")

        return "\n".join(context)

    def validate_state(self) -> ValidationResult:
        """Validate the current game state"""
        errors = []
        warnings = []

        # Check round consistency
        if len(self.round_summaries) + 1 != self.current_round.number:
            errors.append("Round number doesn't match number of summaries")

        # Check action/result consistency
        for char_name, action in self.last_actions.items():
            if action and char_name not in self.last_results:
                errors.append(f"Missing result for {char_name}'s action")

        # Check turn order
        if len(set(self.current_round.turns_taken)) != len(self.current_round.turns_taken):
            errors.append("Duplicate turns detected in current round")

        # Check context size
        if len(self.active_context) > 10:
            warnings.append("Active context exceeds recommended size")

        # Validate party status
        for char_name in self.last_actions.keys():
            if char_name not in self.party_status.conditions:
                warnings.append(f"No status tracking for character: {char_name}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def get_character_status(self, character_name: str) -> Dict[str, Any]:
        """Get current status for a specific character"""
        return {
            "conditions": self.party_status.conditions.get(character_name, []),
            "resources_used": self.party_status.resources_used.get(character_name, []),
            "last_action": self.last_actions.get(character_name),
            "last_result": self.last_results.get(character_name),
            "turns_this_round": self.current_round.turns_taken.count(character_name)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to dictionary for serialization"""
        return {
            "current_situation": self.current_situation,
            "current_round": {
                "number": self.current_round.number,
                "turns_taken": self.current_round.turns_taken,
                "round_context": self.current_round.round_context,
                "start_time": self.current_round.start_time.isoformat(),
                "environmental_effects": {
                    name: effect.dict()
                    for name, effect in self.current_round.environmental_effects.items()
                }
            },
            "party_status": self.party_status.dict(),
            "last_actions": self.last_actions,
            "last_results": {
                name: {
                    "success": result.success,
                    "roll": result.roll,
                    "action": result.action,
                    "description": result.description,
                    "difficulty": result.difficulty.dict() if result.difficulty else None,
                    "reasoning": result.reasoning,
                    "timestamp": result.timestamp.isoformat()
                }
                for name, result in self.last_results.items()
            },
            "round_summaries": [
                summary.dict() for summary in self.round_summaries
            ],
            "active_context": self.active_context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """Create game state from dictionary (for deserialization)"""
        # Convert datetime strings back to datetime objects
        if "current_round" in data:
            data["current_round"]["start_time"] = datetime.fromisoformat(
                data["current_round"]["start_time"]
            )

        if "last_results" in data:
            for result in data["last_results"].values():
                if result and "timestamp" in result:
                    result["timestamp"] = datetime.fromisoformat(result["timestamp"])

        return cls(**data)
