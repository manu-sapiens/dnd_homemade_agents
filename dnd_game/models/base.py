# models/base.py
from enum import Enum, auto
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ModelProvider(Enum):
    """Available model providers"""
    OPENAI = auto()
    OLLAMA = auto()

class Difficulty(Enum):
    """Difficulty levels for action resolution"""
    ALWAYS_SUCCEED = "always_succeed"
    EASY = "easy"          # 80% chance
    AVERAGE = "average"    # 60% chance
    HARD = "hard"         # 40% chance
    SUPER_HARD = "super_hard"  # 20% chance
    ALWAYS_FAIL = "always_fail"

class SupportLevel(Enum):
    """Levels of support for player actions"""
    STRONG_SUPPORT = "strong_support"
    SUPPORT = "support"
    NEUTRAL = "neutral"
    CONCERN = "concern"
    STRONG_CONCERN = "strong_concern"

class GameError(Exception):
    """Base exception for game-related errors"""
    pass

class ConfigurationError(GameError):
    """Raised when there's a configuration issue"""
    pass

class ModelError(GameError):
    """Raised when there's an error with model interactions"""
    pass

class ValidationError(GameError):
    """Raised when there's a validation error"""
    pass

class StateError(GameError):
    """Raised when there's an invalid state transition"""
    pass

class BaseGameModel(BaseModel):
    """Base model with common functionality for all game models"""

    def to_prompt(self) -> str:
        """Convert model to prompt format"""
        return str(self)

    @classmethod
    def from_prompt(cls, prompt: str) -> 'BaseGameModel':
        """Create model instance from prompt format"""
        raise NotImplementedError("Subclasses must implement from_prompt")

class ModelResponse(BaseModel):
    """Base model for structured responses from language models"""
    raw_response: str = Field(description="The original response from the model")
    parsed_response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parsed structured data when available"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if parsing failed"
    )

    @property
    def is_valid(self) -> bool:
        """Check if the response was successfully parsed"""
        return self.error is None and self.parsed_response is not None

class Action(BaseGameModel):
    """Base model for any action in the game"""
    actor: str = Field(description="Name of the character performing the action")
    action_type: str = Field(description="Type of action being performed")
    description: str = Field(description="Description of the action")
    targets: Optional[List[str]] = Field(
        default=None,
        description="Targets of the action, if any"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional action-specific metadata"
    )

class Event(BaseGameModel):
    """Base model for game events"""
    event_type: str = Field(description="Type of event")
    description: str = Field(description="Description of what happened")
    actors: List[str] = Field(description="Characters involved in the event")
    timestamp: str = Field(description="When the event occurred (round/turn)")
    consequences: Optional[List[str]] = Field(
        default=None,
        description="Resulting effects or consequences"
    )

class ValidationResult(BaseModel):
    """Result of a validation check"""
    is_valid: bool = Field(description="Whether the validation passed")
    errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of validation warnings"
    )

    def __bool__(self) -> bool:
        return self.is_valid

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

def validate_model_string(model_string: str) -> ValidationResult:
    """Validate a model string is in the correct format"""
    try:
        provider, model = model_string.lower().split('|')
        if provider not in [m.name.lower() for m in ModelProvider]:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown provider: {provider}"]
            )
        return ValidationResult(is_valid=True)
    except ValueError:
        return ValidationResult(
            is_valid=False,
            errors=[f"Invalid model string format: {model_string}. Expected 'provider|model'"]
        )

def validate_game_state(state: 'GameState') -> ValidationResult:
    """Validate game state consistency"""
    errors = []
    warnings = []

    # Check for required fields
    if not state.current_situation:
        errors.append("Missing current situation")

    if not state.current_round:
        errors.append("Missing current round")

    # Check for consistency
    if len(state.round_summaries) + 1 != state.current_round.number:
        warnings.append("Round number doesn't match number of summaries")

    # Check for invalid state combinations
    if state.current_round.turns_taken and not state.last_actions:
        warnings.append("Turns taken but no last actions recorded")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )

# Type aliases for better code readability
ModelString = str  # provider|model format
RoundNumber = int
CharacterName = str