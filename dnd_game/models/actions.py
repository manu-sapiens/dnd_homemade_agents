# models/actions.py
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
from .base import BaseGameModel, Difficulty, SupportLevel

class Intent(BaseModel):
    """
    Represents a player's intended action and their reasoning.
    Used when a player declares what they want to do.
    """
    action: str = Field(..., description="Description of the intended action")
    reasoning: str = Field(..., description="Explanation of why this action was chosen")
    target: Optional[str] = Field(
        default=None,
        description="Target of the action, if any"
    )
    using_ability: Optional[str] = Field(
        default=None,
        description="Specific ability being used, if any"
    )
    using_equipment: Optional[str] = Field(
        default=None,
        description="Specific equipment being used, if any"
    )

    def to_string(self) -> str:
        """Format the intent for prompts"""
        parts = [
            f"Intended Action: {self.action}",
            f"Reasoning: {self.reasoning}"
        ]

        if self.target:
            parts.append(f"Target: {self.target}")
        if self.using_ability:
            parts.append(f"Using Ability: {self.using_ability}")
        if self.using_equipment:
            parts.append(f"Using Equipment: {self.using_equipment}")

        return "\n".join(parts)

class PlayerFeedback(BaseModel):
    """
    Represents feedback from one player about another player's intended action.
    """
    support_level: SupportLevel = Field(
        ...,
        description="Level of support for the proposed action"
    )
    reasoning: str = Field(
        ...,
        description="Explanation of the feedback"
    )
    suggestion: Optional[str] = Field(
        default=None,
        description="Alternative suggestion or modification to the plan"
    )
    concerns: List[str] = Field(
        default_factory=list,
        description="Specific concerns about the action"
    )
    character_perspective: str = Field(
        ...,
        description="How this feedback relates to the character's personality and abilities"
    )

    def to_string(self) -> str:
        """Format the feedback for prompts"""
        parts = [
            f"Support Level: {self.support_level.value}",
            f"Reasoning: {self.reasoning}",
            f"Character Perspective: {self.character_perspective}"
        ]

        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")

        if self.concerns:
            parts.append("Concerns:")
            parts.extend(f"- {concern}" for concern in self.concerns)

        return "\n".join(parts)

class DifficultyAssessment(BaseModel):
    """
    Represents the DM's assessment of an action's difficulty.
    """
    difficulty: Difficulty = Field(
        ...,
        description="Assessed difficulty level of the action"
    )
    reasoning: str = Field(
        ...,
        description="Explanation of why this difficulty was chosen"
    )
    key_factors: List[str] = Field(
        ...,
        description="Factors that influenced the difficulty assessment"
    )
    auto_resolve: bool = Field(
        default=False,
        description="Whether this action should auto-succeed/fail without a roll"
    )
    modifiers: Dict[str, int] = Field(
        default_factory=dict,
        description="Any modifiers that affect the difficulty"
    )
    requirements: List[str] = Field(
        default_factory=list,
        description="Any specific requirements for attempting the action"
    )

    def to_string(self) -> str:
        """Format the assessment for prompts"""
        parts = [
            f"Difficulty: {self.difficulty.value}",
            f"Reasoning: {self.reasoning}",
            "\nKey Factors:"
        ]
        parts.extend(f"- {factor}" for factor in self.key_factors)

        if self.auto_resolve:
            parts.append("\nAuto-resolve: Yes")

        if self.modifiers:
            parts.append("\nModifiers:")
            parts.extend(f"- {k}: {v}" for k, v in self.modifiers.items())

        if self.requirements:
            parts.append("\nRequirements:")
            parts.extend(f"- {req}" for req in self.requirements)

        return "\n".join(parts)

class RoundSummary(BaseModel):
    """
    Comprehensive summary of a completed round.
    """
    key_events: List[str] = Field(
        ...,
        description="The most important events that occurred"
    )
    party_state: Dict[str, str] = Field(
        ...,
        description="Brief status of each character"
    )
    environment_changes: List[str] = Field(
        ...,
        description="How the situation/environment has changed"
    )
    important_consequences: List[str] = Field(
        ...,
        description="Consequences that might affect future rounds"
    )
    narrative_focus: str = Field(
        ...,
        description="The main narrative thread to keep in mind"
    )
    unresolved_threads: List[str] = Field(
        default_factory=list,
        description="Plot threads or situations that remain unresolved"
    )
    discovered_information: List[str] = Field(
        default_factory=list,
        description="New information learned during the round"
    )
    relationship_changes: Dict[str, str] = Field(
        default_factory=dict,
        description="Changes in relationships between characters or NPCs"
    )

    def to_string(self) -> str:
        """Format the summary for prompts"""
        parts = [
            "=== Round Summary ===",
            "\nKey Events:"
        ]
        parts.extend(f"- {event}" for event in self.key_events)

        parts.append("\nParty Status:")
        parts.extend(f"- {char}: {status}" for char, status in self.party_state.items())

        parts.append("\nEnvironmental Changes:")
        parts.extend(f"- {change}" for change in self.environment_changes)

        parts.append("\nImportant Consequences:")
        parts.extend(f"- {cons}" for cons in self.important_consequences)

        parts.append(f"\nNarrative Focus: {self.narrative_focus}")

        if self.unresolved_threads:
            parts.append("\nUnresolved Threads:")
            parts.extend(f"- {thread}" for thread in self.unresolved_threads)

        if self.discovered_information:
            parts.append("\nDiscovered Information:")
            parts.extend(f"- {info}" for info in self.discovered_information)

        if self.relationship_changes:
            parts.append("\nRelationship Changes:")
            parts.extend(
                f"- {chars}: {change}"
                for chars, change in self.relationship_changes.items()
            )

        return "\n".join(parts)

    def get_important_elements(self) -> Dict[str, Any]:
        """Extract elements that need to be remembered for future rounds"""
        return {
            "critical_consequences": [
                cons for cons in self.important_consequences
                if any(word in cons.lower()
                      for word in ["must", "requires", "cannot", "permanent"])
            ],
            "active_effects": [
                change for change in self.environment_changes
                if not any(word in change.lower()
                          for word in ["ended", "disappeared", "removed"])
            ],
            "pending_threads": self.unresolved_threads,
            "key_information": self.discovered_information
        }

# Helper function for formatting feedback from multiple players
def format_party_feedback(feedback_list: List[tuple[str, str]]) -> str:
    """Format feedback from multiple players into a single string"""
    sections = []
    for character_name, feedback in feedback_list:
        sections.append(f"=== Feedback from {character_name} ===")
        sections.append(feedback)
    return "\n\n".join(sections)
