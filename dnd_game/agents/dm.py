# agents/dm.py
from typing import Optional, Union, List, Dict
from pydantic import BaseModel
from .base import Agent, Task
from ..models.actions import DifficultyAssessment, Intent
from ..models.game_state import ActionResult
from ..models.character import Character

class DMAgent(Agent):
    """
    Dungeon Master agent implementation.
    Responsible for describing situations, answering questions,
    assessing difficulties, and resolving actions.
    """
    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        style_preferences: Optional[Dict[str, str]] = None
    ):
        # Default DM style preferences
        self.style = {
            "description_style": "vivid and atmospheric",
            "combat_style": "dynamic and tactical",
            "narrative_style": "balanced between story and game mechanics",
            "difficulty_style": "fair but challenging",
            **(style_preferences or {})
        }

        system_prompt = self._generate_system_prompt()
        super().__init__(
            name="Dungeon Master",
            system_prompt=system_prompt,
            model=model,
            temperature=temperature
        )

        # Initialize DM-specific tasks
        self.tasks = self._initialize_tasks()

    def _generate_system_prompt(self) -> str:
        """Generate the DM's system prompt based on style preferences"""
        return f"""You are a skilled Dungeon Master who weaves engaging narratives and controls NPCs.

        Your DMing style:
        - Descriptions: {self.style['description_style']}
        - Combat: {self.style['combat_style']}
        - Narrative: {self.style['narrative_style']}
        - Difficulty: {self.style['difficulty_style']}

        Core principles:
        - Never decide for the players, always ask what they want to do
        - Keep the game balanced and interesting
        - Maintain consistency in the world and NPCs
        - Provide clear information for decision-making
        - Keep the story moving forward, even after failed rolls
        - Consider character abilities and limitations
        - Create meaningful consequences for actions

        When resolving actions:
        - On success, describe how they accomplish their goal, possibly with minor complications
        - On failure, describe how they fall short, but keep the story moving forward
        - Always maintain narrative momentum regardless of success or failure"""

    def _initialize_tasks(self) -> Dict[str, Task]:
        """Initialize all DM-specific tasks"""
        return {
            "describe_situation": Task(
                description="{character_name}'s turn. Describe the current situation to the player: {character_name}",
                prompt_template="""
                Current situation: {situation}
                Active character: {character_name}
                Active character details: {active_character}
                Other party members: {other_characters}
                Recent events:
                {context}

                Previous action from the Party (if any):
                {previous_action}

                Describe the scene to {character_name}, emphasizing:
                - What {character_name} character can perceive
                - Any obvious threats or opportunities
                - The atmosphere and environment
                - Recent changes or consequences of previous actions, from this character, other characters in the Party or the world
                """,
                expected_output="A concise description of the current situation",
                agent=self
            ),

            "assess_difficulty": Task(
                description="Assess the difficulty of a proposed action for {character_name}",
                prompt_template="""
                Character attempting the action:
                {character_name}'s details: {character_details}

                Current situation:
                {situation}

                Proposed {character_name}'s action:
                {action}

                Recent context:
                {context}

                Assess how difficult this action would be to accomplish for {character_name}. Consider:
                - {character_name}'s capabilities and equipment
                - The situation and environment
                - Any relevant previous actions or consequences
                - Whether this even needs a roll (simple actions might auto-succeed)
                """,
                expected_output="A structured assessment of the action's difficulty with reasoning",
                agent=self,
                response_model=DifficultyAssessment
            ),

            "answer_questions": Task(
                description="Answer {character_name}'s questions about the situation. Be precise and concise. Do not reveal hidden information. Only answers question that can be answered with a quick glance or simple observation - if a question requires a longer investigation, suggest to the player that they can make that invistigation their next action.",
                prompt_template="""
                Current situation:
                {situation}

                Active character: {character_name}
                Active character details:
                {character_details}

                Questions:
                {questions}

                Recent context:
                {context}

                Answer these questions while considering:
                - Where {character_name} is positioned and what they can see, especially compared to other characters in the Party
                - What {character_name} could reasonably know or perceive at a simple glance
                - Information they've gained through previous actions
                - Maintaining mystery where appropriate
                - Providing useful but not complete information
                - Do not make {character_name} or other characters say or do anything while answering the questions. Only provide information.
                """,
                expected_output="Clear, concise and helpful answers to each question, without revealing information the character couldn't know.",
                agent=self
            ),

            "resolve_action": Task(
                description="Describe how {character_name}'s action plays out based on the roll",
                prompt_template="""
                Current situation:
                {situation}

                Active character: {character_name}
                Active character details:
                {character_details}

                Attempted action:
                {action}

                Difficulty assessment:
                {difficulty_details}

                Roll result: {roll_result}
                Success: {success}

                Recent context:
                {context}

                Describe how the action plays out for {character_name}, considering:
                - The degree of success or failure (based on roll)
                - {character_name}'s capabilities and approach
                - Environmental factors and circumstances
                - Maintaining forward momentum
                - Creating interesting consequences
                """,
                expected_output="A detailed description of how the action plays out, consistent with the roll result",
                agent=self
            )
        }

    async def describe_situation(self, **kwargs) -> str:
        """Describe the current situation to the players"""
        return await self.execute_task(self.tasks["describe_situation"], **kwargs)

    async def assess_action_difficulty(self, **kwargs) -> DifficultyAssessment:
        """Assess the difficulty of a proposed action"""
        return await self.execute_task(self.tasks["assess_difficulty"], **kwargs)

    async def answer_player_questions(self, **kwargs) -> str:
        """Answer questions from a player about the current situation"""
        return await self.execute_task(self.tasks["answer_questions"], **kwargs)

    async def resolve_action_result(self, **kwargs) -> str:
        """Describe the outcome of an action based on the roll result"""
        return await self.execute_task(self.tasks["resolve_action"], **kwargs)

    def format_difficulty_details(self, assessment: DifficultyAssessment) -> str:
        """Format difficulty assessment for prompts"""
        return f"""Difficulty: {assessment.difficulty.value}
Reasoning: {assessment.reasoning}
Key factors:
{chr(10).join(f'- {factor}' for factor in assessment.key_factors)}"""
