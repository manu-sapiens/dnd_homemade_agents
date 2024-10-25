# agents/player.py
from typing import Optional, Union, List, Dict
from dataclasses import dataclass
from pydantic import BaseModel
from .base import Agent, Task
from ..models.character import Character, PersonalityProfile
from ..models.actions import Intent, PlayerFeedback

class PlayerAgent(Agent):
    """
    Player character agent implementation.
    Responsible for asking questions, planning actions, and providing feedback
    while maintaining consistent character personality and abilities.
    """
    def __init__(
        self,
        character: Character,
        personality: PersonalityProfile,
        model: str,
        temperature: float = 0.7
    ):
        self.character = character
        self.personality = personality

        system_prompt = self._generate_system_prompt()
        super().__init__(
            name=character.name,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature
        )

        # Initialize player-specific tasks
        self.tasks = self._initialize_tasks()

    def _generate_system_prompt(self) -> str:
        """Generate the player's system prompt based on character and personality"""
        return f"""You are playing the role of:

{self.character.to_string()}

Your personality:
{self.personality.to_prompt()}

Core principles when roleplaying this character:
- Stay true to your personality traits, ideals, bonds, and flaws
- Make decisions based on your capabilities and equipment
- Ask questions your character would naturally ask
- Consider your character's knowledge and experience
- Maintain consistent characterization in all interactions
- React authentically to situations based on your personality

Knowledge boundaries:
- You know your abilities, equipment, and background
- You know what your character has experienced in the game
- You don't know things your character hasn't learned
- You don't have meta-knowledge about the game world

Decision making:
- Consider risks based on your character's personality
- Use your character's skills and equipment appropriately
- Factor in your character's goals and motivations
- React to other characters based on your relationships
- Express your character's emotions and thoughts naturally"""

    def _initialize_tasks(self) -> Dict[str, Task]:
        """Initialize all player-specific tasks"""
        return {
            "ask_questions": Task(
                description="Ask relevant questions to the Dungeon Master about the current situation",
                prompt_template="""
                Current situation:
                {situation_description}

                Based on your character's:
                - Current capabilities and equipment
                - Personality and motivations
                - Recent experiences
                - Knowledge and expertise

                What questions would you ask to better understand:
                - Potential risks and opportunities
                - Important details you need to make decisions
                - Aspects relevant to your character's interests

                Regarding the world, only ask questions that would take only an instant to answer, like a quick glance or simple observation.

                Format your questions as a list separated by |
                Only ask questions to clarify the situation, a game rule or something you should know about your character, others, the situation or the world.
                Prioritize: Try to limit yourself to at most 3 questions: one question about rules, one question about your character and one question about the world.
                """,
                expected_output="A list of relevant questions separated by |",
                agent=self
            ),

            "declare_intent": Task(
                description="Declare what action you're considering taking",
                prompt_template="""
                Current situation:
                {situation_description}

                Your questions and the DM's answers:
                {qa_exchange}

                Based on:
                - The information you've gathered
                - Your character's capabilities
                - Your personality and motivations
                - Recent events: {context}

                What single action are you considering taking and why? Make it clear this is your intent, not your final decision. State it in a matter-of-fact way, concise and precise.
                """,
                expected_output="A description of your intended action and reasoning",
                agent=self#,
                #response_model=Intent
            ),

            "provide_feedback": Task(
                description="Provide a quick quip as feedback on another character's intended action, as if you were talking to them in-character. This is a quick, immediate reaction so it should not be too verbose but highlight your personality and your relationship with the acting character.",
                prompt_template="""
                Current situation:
                {situation_description}

                Character planning to act:
                {character_name}

                Their intended action:
                {intended_action}

                Consider:
                - Your relationship with this character
                - Your expertise and experience
                - Potential risks you can see
                - How this might affect the party
                - What your character would actually say
                """,
                expected_output="Quick feedback about the proposed action",
                agent=self
            ),

            "make_decision": Task(
                description="Make your final decision on what you will attempt, considering party feedback",
                prompt_template="""
                Current situation:
                {situation_description}

                Your original intent:
                Action: {intended_action}

                Party feedback:
                {party_feedback}

                Additional context:
                {context}

                Based on your character's:
                - Personality and typical behavior
                - Relationship with other party members
                - Assessment of the feedback

                Make your final decision.
                """,
                expected_output="Your final decided action, potentially modified based on feedback. Make it clear this is what you attempt to do.",
                agent=self
            )
        }

    async def ask_questions(self, **kwargs) -> str:
        """Ask questions about the current situation"""
        return await self.execute_task(self.tasks["ask_questions"], **kwargs)

    async def declare_intent(self, **kwargs) -> str: #Intent:
        """Declare what action you're considering taking"""
        return await self.execute_task(self.tasks["declare_intent"], **kwargs)

    async def provide_feedback(self, **kwargs) -> str:
        """Provide feedback on another character's intended action"""
        return await self.execute_task(self.tasks["provide_feedback"], **kwargs)

    async def make_decision(self, **kwargs) -> str:
        """Make final decision about your action"""
        return await self.execute_task(self.tasks["make_decision"], **kwargs)

    def format_qa_exchange(self, questions: str, answers: str) -> str:
        """Format Q&A exchange for prompts"""
        formatted_questions = [q.strip() for q in questions.split('|')]
        return "\n".join([
            "Questions and Answers:",
            *[f"Q: {q}\nA: {a}" for q, a in zip(
                formatted_questions,
                answers.split('\n')
            )]
        ])

    def format_party_feedback(self, feedback: List[tuple[str, str]]) -> str:
        """Format party feedback for prompts"""
        return "\n\n".join([
            f"Feedback from {name}: {fb}\n"
            for name, fb in feedback
        ])

    def __repr__(self):
        return f"PlayerAgent(character='{self.character.name}', class='{self.character.class_name}')"