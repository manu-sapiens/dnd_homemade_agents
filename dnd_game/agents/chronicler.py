# agents/chronicler.py
from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from .base import Agent, Task
from ..models.character import Character
from ..models.game_state import Round
from ..models.actions import RoundSummary


class ChroniclerMemoryTypes(BaseModel):
    """Different types of details the chronicler should track"""
    narrative: List[str] = Field(default_factory=list, description="Story developments and plot points")
    tactical: List[str] = Field(default_factory=list, description="Important information about the environment and threats")
    character: Dict[str, List[str]] = Field(default_factory=dict, description="Character-specific developments")
    consequences: List[str] = Field(default_factory=list, description="Ongoing effects or consequences of actions")

class DetailImportance(BaseModel):
    """Assessment of a detail's importance for future reference"""
    detail: str
    importance: int = Field(ge=1, le=5, description="Importance rating (1-5)")
    reasoning: str = Field(description="Why this detail might be important later")
    relevant_to: List[str] = Field(default_factory=list, description="Which aspects this detail might affect")

class RoundSummary(BaseModel):
    """Model for summarizing a round's main points"""
    key_events: List[str] = Field(default_factory=list)
    party_state: Dict[str, Any] = Field(default_factory=dict)
    environment_changes: List[str] = Field(default_factory=list)
    important_consequences: List[str] = Field(default_factory=list)
    narrative_focus: str = ""

    def __str__(self) -> str:
        return (
            f"Round Summary:\n"
            f"- Key Events: {', '.join(self.key_events) if self.key_events else 'None'}\n"
            f"- Party State: {self.party_state}\n"
            f"- Environment Changes: {', '.join(self.environment_changes) if self.environment_changes else 'None'}\n"
            f"- Important Consequences: {', '.join(self.important_consequences) if self.important_consequences else 'None'}\n"
            f"- Narrative Focus: {self.narrative_focus or 'None'}\n"
        )

class ChroniclerAgent(Agent):
    """
    Chronicler agent implementation.
    Responsible for maintaining and compressing game memory while preserving
    important narrative and tactical information.
    """
    def __init__(
        self,
        model: str,
        temperature: float = 0.3,  # Lower temperature for more consistent summaries
        memory_length: int = 5  # Number of rounds to maintain in detailed memory
    ):
        system_prompt = self._generate_system_prompt()
        super().__init__(
            name="Chronicler",
            system_prompt=system_prompt,
            model=model,
            temperature=temperature
        )

        self.memory_length = memory_length
        self.tasks = self._initialize_tasks()

    def _generate_system_prompt(self) -> str:
        return """You are the Chronicler, keeper of the game's memory and narrative continuity.

Your responsibilities:
- Summarize events while preserving crucial details
- Track cause-and-effect relationships
- Maintain narrative consistency
- Identify potentially important information
- Create concise but comprehensive summaries
- Connect current events to past occurrences
- Track character development and changes

When summarizing:
- Prioritize information that might be relevant later
- Track both immediate and potential long-term consequences
- Maintain separate tracks for narrative, tactical, and character information
- Highlight unresolved plot threads
- Note environmental and situational changes
- Record character decisions and their impacts
- Preserve mystery elements and unrevealed information

Your summaries should:
- Be concise but informative
- Maintain clear chronological order
- Separate different types of information
- Highlight connections between events
- Note both successes and failures
- Track ongoing effects and conditions"""

    def _initialize_tasks(self) -> Dict[str, Task]:
        return {
            "summarize_round": Task(
                description="Create a comprehensive summary of the completed round",
                prompt_template="""
                Round number: {round_number}

                Initial situation:
                {initial_situation}

                Events this round:
                {round_events}

                Party members:
                {party_members}

                Previous round summary (if any):
                {previous_summary}

                Create a structured summary highlighting:
                - Key events and their significance
                - Changes to characters or their status
                - Environmental or situational changes
                - Immediate and potential consequences
                - The main narrative thread

                Required fields:
                - key_events
                - party_state
                - environment_changes
                - important_consequences
                - narrative_focus

                Consider different types of information:
                - Narrative developments
                - Tactical situation
                - Character developments
                - Ongoing effects
                """,
                expected_output="A structured summary of the round's important elements",
                agent=self,
                response_model=RoundSummary
            ),

            "assess_detail_importance": Task(
                description="Evaluate the importance of specific details for future reference",
                prompt_template="""
                Detail to assess:
                {detail}

                Current context:
                {current_context}

                Recent history:
                {recent_history}

                Evaluate this detail's importance considering:
                - Potential future relevance
                - Connection to existing plot threads
                - Impact on character development
                - Tactical significance
                - Narrative implications
                """,
                expected_output="A structured assessment of the detail's importance",
                agent=self,
                response_model=DetailImportance
            ),

            "compress_memory": Task(
                description="Compress multiple round summaries into a consolidated memory",
                prompt_template="""
                Rounds to compress:
                {round_summaries}

                Party members:
                {party_members}

                Create a compressed memory that maintains:
                - Critical narrative developments
                - Important tactical information
                - Character development and changes
                - Significant consequences
                - Unresolved plot threads

                Focus on:
                - Cause-and-effect relationships
                - Pattern recognition
                - Emerging themes
                - Long-term implications
                """,
                expected_output="A structured compilation of important information from multiple rounds",
                agent=self,
                response_model=ChroniclerMemoryTypes
            ),

            "retrieve_relevant_context": Task(
                description="Retrieve relevant context for the current situation",
                prompt_template="""
                Current situation:
                {current_situation}

                Character acting:
                {active_character}

                Attempted action:
                {attempted_action}

                Available memory:
                {memory_store}

                Identify and retrieve:
                - Similar past situations
                - Relevant character experiences
                - Related consequences
                - Applicable tactical information
                - Connected narrative elements
                """,
                expected_output="A curated selection of relevant context from memory",
                agent=self
            ),

            "summarize_turn": Task(
                description="Create a summary of a player's turn and its effects",
                prompt_template="""
                Round {round_number}, Character: {character_name}
                
                Initial situation:
                {initial_situation}
                
                Action taken: {action_taken}
                Difficulty: {difficulty}
                Roll: {roll_result} ({success})
                Result: {action_result}
                
                Previous context:
                {previous_context}
                
                Summarize:
                - How the situation has changed
                - Immediate effects of the action
                - Current state of the environment
                - What the next player needs to know
                """,
                expected_output="A structured summary of the turn's effects",
                agent=self,
                response_model=RoundSummary
            )
        
        }

    async def summarize_round(self, **kwargs) -> RoundSummary:
        """Create a summary of the completed round"""
        return await self._execute_task_with_logging(self.tasks["summarize_round"], **kwargs)

    async def summarize_turn(self, **kwargs) -> RoundSummary:
        """Create a summary of a player's turn and its effects"""
        return await self._execute_task_with_logging(self.tasks["summarize_turn"], **kwargs)
        
    async def assess_detail(self, **kwargs) -> DetailImportance:
        """Assess the importance of a specific detail"""
        return await self._execute_task_with_logging(self.tasks["assess_detail_importance"], **kwargs)

    async def compress_memory(self, **kwargs) -> ChroniclerMemoryTypes:
        """Compress multiple round summaries into consolidated memory"""
        return await self._execute_task_with_logging(self.tasks["compress_memory"], **kwargs)

    async def get_relevant_context(self, **kwargs) -> str:
        """Retrieve context relevant to the current situation"""
        return await self._execute_task_with_logging(self.tasks["retrieve_relevant_context"], **kwargs)

    async def _execute_task_with_logging(self, task: Task, **kwargs):
        """Execute a task with error handling and logging."""
        try:
            response = await self.execute_task(task, **kwargs)
            print("Model response:", response)
            return response
        except ValidationError as e:
            print(f"Validation error in {task.description}: {e}")
            return None

    def format_round_summaries(self, summaries: List[RoundSummary]) -> str:
        """Format multiple round summaries for prompts"""
        formatted = []
        for i, summary in enumerate(summaries, 1):
            formatted.append(f"Round {i}:")
            formatted.extend([f"- {event}" for event in summary.key_events])
            formatted.append("Consequences:")
            formatted.extend([f"- {cons}" for cons in summary.important_consequences])
            formatted.append(f"Focus: {summary.narrative_focus}\n")
        return "\n".join(formatted)

    def format_memory_store(self, memory: ChroniclerMemoryTypes) -> str:
        """Format memory store for prompts"""
        sections = [
            "Narrative Developments:",
            *[f"- {item}" for item in memory.narrative],
            "\nTactical Information:",
            *[f"- {item}" for item in memory.tactical],
            "\nCharacter Developments:"
        ]

        for char, developments in memory.character.items():
            sections.append(f"\n{char}:")
            sections.extend([f"- {dev}" for dev in developments])

        sections.extend([
            "\nOngoing Consequences:",
            *[f"- {cons}" for cons in memory.consequences]
        ])

        return "\n".join(sections)

    def __repr__(self):
        return f"ChroniclerAgent(memory_length={self.memory_length})"
