# models/character.py
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from .base import BaseGameModel, ValidationResult

class CharacterClass(Enum):
    """Standard D&D character classes"""
    BARBARIAN = "barbarian"
    BARD = "bard"
    CLERIC = "cleric"
    DRUID = "druid"
    FIGHTER = "fighter"
    MONK = "monk"
    PALADIN = "paladin"
    RANGER = "ranger"
    ROGUE = "rogue"
    SORCERER = "sorcerer"
    WARLOCK = "warlock"
    WIZARD = "wizard"

class Race(Enum):
    """Standard D&D races"""
    HUMAN = "human"
    ELF = "elf"
    DWARF = "dwarf"
    HALFLING = "halfling"
    GNOME = "gnome"
    HALF_ELF = "half-elf"
    HALF_ORC = "half-orc"
    TIEFLING = "tiefling"
    DRAGONBORN = "dragonborn"

class Ability(BaseModel):
    """Represents a character ability or skill"""
    name: str = Field(..., description="Name of the ability")
    description: str = Field(..., description="What the ability does")
    usage_frequency: Optional[str] = Field(
        default=None,
        description="How often the ability can be used (e.g., 'at will', 'once per day')"
    )
    requirements: Optional[List[str]] = Field(
        default_factory=list,
        description="Any requirements for using this ability"
    )

class Equipment(BaseModel):
    """Represents a piece of equipment"""
    name: str = Field(..., description="Name of the item")
    type: str = Field(..., description="Type of equipment (weapon, armor, tool, etc.)")
    description: Optional[str] = None
    properties: List[str] = Field(default_factory=list)
    quantity: int = Field(default=1, ge=1)

class PersonalityProfile(BaseGameModel):
    """
    Represents a character's personality traits, ideals, bonds, and flaws.
    Used to guide roleplay and decision-making.
    """
    traits: List[str] = Field(
        ...,
        min_items=1,
        description="Distinctive personality traits that define the character"
    )
    ideals: List[str] = Field(
        ...,
        min_items=1,
        description="Principles and beliefs the character lives by"
    )
    bonds: List[str] = Field(
        ...,
        min_items=1,
        description="Connections to people, places, or things"
    )
    flaws: List[str] = Field(
        ...,
        min_items=1,
        description="Character weaknesses or imperfections"
    )
    quirks: List[str] = Field(
        default_factory=list,
        description="Optional distinctive behaviors or habits"
    )

    def to_prompt(self) -> str:
        """Format personality for use in prompts"""
        sections = [
            "Personality Profile:",
            "\nTraits:",
            *[f"- {trait}" for trait in self.traits],
            "\nIdeals:",
            *[f"- {ideal}" for ideal in self.ideals],
            "\nBonds:",
            *[f"- {bond}" for bond in self.bonds],
            "\nFlaws:",
            *[f"- {flaw}" for flaw in self.flaws]
        ]

        if self.quirks:
            sections.extend([
                "\nQuirks:",
                *[f"- {quirk}" for quirk in self.quirks]
            ])

        return "\n".join(sections)

    def get_roleplay_guidance(self) -> Dict[str, List[str]]:
        """Get structured guidance for roleplaying this personality"""
        return {
            "core_behaviors": self.traits,
            "motivations": self.ideals,
            "relationships": self.bonds,
            "weaknesses": self.flaws,
            "distinguishing_features": self.quirks
        }

class Character(BaseGameModel):
    """
    Represents a player character with both mechanical and roleplaying attributes.
    """
    name: str = Field(..., description="Character's name")
    level: int = Field(..., ge=1, le=20, description="Character level")
    class_name: str = Field(
        ...,
        description="Character class (e.g., 'Paladin', 'Wizard')"
    )
    race: str = Field(
        ...,
        description="Character race (e.g., 'Human', 'Elf')"
    )
    key_abilities: List[str] = Field(
        ...,
        min_items=1,
        description="Primary abilities and skills"
    )
    equipment: List[str] = Field(
        ...,
        description="Current equipment and items"
    )
    description: str = Field(
        default="",
        description="Physical description and background"
    )
    abilities: List[Ability] = Field(
        default_factory=list,
        description="Special abilities and features"
    )
    inventory: List[Equipment] = Field(
        default_factory=list,
        description="Detailed equipment records"
    )
    status: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current status effects or conditions"
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Additional character notes"
    )

    @validator('class_name')
    def validate_class(cls, v: str) -> str:
        """Validate and normalize class name"""
        try:
            return CharacterClass[v.upper()].value
        except KeyError:
            if v.lower() not in [c.value for c in CharacterClass]:
                raise ValueError(f"Invalid character class: {v}")
            return v.lower()

    @validator('race')
    def validate_race(cls, v: str) -> str:
        """Validate and normalize race"""
        try:
            return Race[v.upper()].value
        except KeyError:
            if v.lower() not in [r.value for r in Race]:
                raise ValueError(f"Invalid race: {v}")
            return v.lower()

    def to_string(self) -> str:
        """Format character details for prompts"""
        base_info = [
            f"Name: {self.name}",
            f"Level {self.level} {self.race.title()} {self.class_name.title()}",
            f"Key abilities: {', '.join(self.key_abilities)}",
            f"Equipment: {', '.join(self.equipment)}"
        ]

        if self.description:
            base_info.append(f"Description: {self.description}")

        if self.status:
            status_lines = [f"Status:"]
            status_lines.extend(f"- {k}: {v}" for k, v in self.status.items())
            base_info.extend(status_lines)

        return "\n".join(base_info)

    def validate_state(self) -> ValidationResult:
        """Validate character state consistency"""
        errors = []
        warnings = []

        # Check equipment consistency
        inventory_items = {item.name.lower() for item in self.inventory}
        for item in self.equipment:
            if item.lower() not in inventory_items:
                warnings.append(f"Equipment '{item}' not found in detailed inventory")

        # Check ability consistency
        ability_names = {ability.name.lower() for ability in self.abilities}
        for ability in self.key_abilities:
            if ability.lower() not in ability_names:
                warnings.append(f"Key ability '{ability}' not found in detailed abilities")

        # Check for invalid status conditions
        for status, value in self.status.items():
            if not isinstance(value, (str, int, float, bool)):
                errors.append(f"Invalid status value type for '{status}'")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def update_status(self, status: Dict[str, Any]) -> None:
        """Update character status conditions"""
        self.status.update(status)

        # Clean up resolved conditions
        self.status = {
            k: v for k, v in self.status.items()
            if v is not None and v != False
        }

    def add_equipment(self, equipment: Equipment) -> None:
        """Add new equipment to inventory"""
        self.inventory.append(equipment)
        if equipment.name not in self.equipment:
            self.equipment.append(equipment.name)

    def remove_equipment(self, equipment_name: str) -> None:
        """Remove equipment from inventory"""
        self.inventory = [
            item for item in self.inventory
            if item.name.lower() != equipment_name.lower()
        ]
        self.equipment = [
            item for item in self.equipment
            if item.lower() != equipment_name.lower()
        ]

    def get_combat_capabilities(self) -> Dict[str, Any]:
        """Get combat-relevant abilities and equipment"""
        combat_equipment = [
            item for item in self.inventory
            if item.type in ['weapon', 'armor', 'shield']
        ]

        combat_abilities = [
            ability for ability in self.abilities
            if any(combat_term in ability.description.lower()
                  for combat_term in ['attack', 'damage', 'defense', 'combat'])
        ]

        return {
            "equipment": combat_equipment,
            "abilities": combat_abilities,
            "status_effects": self.status
        }
