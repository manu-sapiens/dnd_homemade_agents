# core/tasks.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum, auto
from ..agents.dm import DMAgent
from ..agents.player import PlayerAgent
from ..agents.chronicler import ChroniclerAgent
from ..models.game_state import GameState, Round
from ..models.actions import Intent, PlayerFeedback, DifficultyAssessment

class TaskType(Enum):
    """Types of game tasks that can be executed"""
    DESCRIBE_SITUATION = auto()
    ASK_QUESTIONS = auto()
    ANSWER_QUESTIONS = auto()
    DECLARE_INTENT = auto()
    PROVIDE_FEEDBACK = auto()
    MAKE_DECISION = auto()
    ASSESS_DIFFICULTY = auto()
    RESOLVE_ACTION = auto()
    SUMMARIZE_ROUND = auto()
    SUMMARIZE_TURN = auto()

@dataclass
class GameTask:
    """
    Represents a specific task in the game sequence
    """
    task_type: TaskType
    agent_type: str  # "dm", "player", or "chronicler"
    description: str
    required_inputs: List[str]
    optional_inputs: List[str] = None

    def validate_inputs(self, **kwargs) -> Dict[str, Any]:
        """Validate and prepare inputs for task execution"""
        if self.optional_inputs is None:
            self.optional_inputs = []

        # Check for required inputs
        missing = [inp for inp in self.required_inputs if inp not in kwargs]
        if missing:
            raise ValueError(f"Missing required inputs for {self.task_type}: {missing}")

        # Filter to only include relevant inputs
        valid_inputs = {
            k: v for k, v in kwargs.items()
            if k in self.required_inputs + self.optional_inputs
        }

        return valid_inputs

class TaskSequencer:
    """
    Manages the sequence of tasks in the game
    """
    def __init__(self, dm: DMAgent, chronicler: ChroniclerAgent):
        self.dm = dm
        self.chronicler = chronicler
        self.tasks = self._initialize_tasks()

    def _initialize_tasks(self) -> Dict[TaskType, GameTask]:
        """Initialize all available game tasks"""
        tasks = {
            TaskType.DESCRIBE_SITUATION: GameTask(
                task_type=TaskType.DESCRIBE_SITUATION,
                agent_type="dm",
                description="Describe the current situation to players",
                required_inputs=["situation", "active_character", "character_name"],
                optional_inputs=["other_characters", "context", "previous_action"]
            ),

            TaskType.ASK_QUESTIONS: GameTask(
                task_type=TaskType.ASK_QUESTIONS,
                agent_type="player",
                description="Ask questions about the current situation",
                required_inputs=["situation_description"],
                optional_inputs=["context"]
            ),

            TaskType.ANSWER_QUESTIONS: GameTask(
                task_type=TaskType.ANSWER_QUESTIONS,
                agent_type="dm",
                description="Answer player questions",
                required_inputs=["situation", "questions", "character_details","character_name"],
                optional_inputs=["context"]
            ),

            TaskType.DECLARE_INTENT: GameTask(
                task_type=TaskType.DECLARE_INTENT,
                agent_type="player",
                description="Declare intended action",
                required_inputs=["situation_description", "qa_exchange"],
                optional_inputs=["context"]
            ),

            TaskType.PROVIDE_FEEDBACK: GameTask(
                task_type=TaskType.PROVIDE_FEEDBACK,
                agent_type="player",
                description="Provide feedback on another player's intended action",
                required_inputs=[
                    "situation_description",
                    "character_name",
                    "intended_action"
                ]
            ),

            TaskType.MAKE_DECISION: GameTask(
                task_type=TaskType.MAKE_DECISION,
                agent_type="player",
                description="Make final decision about action",
                required_inputs=[
                    "situation_description",
                    "intended_action",
                    "party_feedback"
                ],
                optional_inputs=["context"]
            ),

            TaskType.ASSESS_DIFFICULTY: GameTask(
                task_type=TaskType.ASSESS_DIFFICULTY,
                agent_type="dm",
                description="Assess action difficulty",
                required_inputs=[
                    "character_details",
                    "situation",
                    "action",
                    "character_name"
                ],
                optional_inputs=["context"]
            ),

            TaskType.RESOLVE_ACTION: GameTask(
                task_type=TaskType.RESOLVE_ACTION,
                agent_type="dm",
                description="Resolve action outcome",
                required_inputs=[
                    "situation",
                    "character_details",
                    "character_name",
                    "action",
                    "difficulty_details",
                    "roll_result",
                    "success"
                ],
                optional_inputs=["context"]
            ),

            TaskType.SUMMARIZE_ROUND: GameTask(
                task_type=TaskType.SUMMARIZE_ROUND,
                agent_type="chronicler",
                description="Summarize the round's events",
                required_inputs=[
                    "round_number",
                    "initial_situation",
                    "round_events",
                    "party_members"
                ],
                optional_inputs=["previous_summary"]
            ),

            TaskType.SUMMARIZE_TURN: GameTask(
                task_type=TaskType.SUMMARIZE_TURN,
                agent_type="chronicler",
                description="Summarize the effects and changes from a player's turn",
                required_inputs=[
                    "round_number",
                    "character_name",
                    "initial_situation",
                    "action_taken",
                    "action_result",
                    "difficulty",
                    "roll_result",
                    "success",
                    "previous_context"
                ]
            )
        }
        return tasks
    

    async def execute_task(
        self,
        task_type: TaskType,
        agent: Optional[PlayerAgent] = None,
        **kwargs
    ) -> Any:
        """
        Execute a specific task with the appropriate agent
        """
        task = self.tasks[task_type]
        inputs = task.validate_inputs(**kwargs)

        if task.agent_type == "dm":
            if task_type == TaskType.DESCRIBE_SITUATION:
                return await self.dm.describe_situation(**inputs)
            elif task_type == TaskType.ANSWER_QUESTIONS:
                return await self.dm.answer_player_questions(**inputs)
            elif task_type == TaskType.ASSESS_DIFFICULTY:
                return await self.dm.assess_action_difficulty(**inputs)
            elif task_type == TaskType.RESOLVE_ACTION:
                return await self.dm.resolve_action_result(**inputs)

        elif task.agent_type == "player":
            if not agent:
                raise ValueError(f"Player agent required for task {task_type}")

            if task_type == TaskType.ASK_QUESTIONS:
                return await agent.ask_questions(**inputs)
            elif task_type == TaskType.DECLARE_INTENT:
                return await agent.declare_intent(**inputs)
            elif task_type == TaskType.PROVIDE_FEEDBACK:
                return await agent.provide_feedback(**inputs)
            elif task_type == TaskType.MAKE_DECISION:
                return await agent.make_decision(**inputs)

        elif task.agent_type == "chronicler":
            if task_type == TaskType.SUMMARIZE_ROUND:
                return await self.chronicler.summarize_round(**inputs)
            elif task_type == TaskType.SUMMARIZE_TURN:
                return await self.chronicler.summarize_turn(**inputs)

        raise ValueError(f"Unknown task type: {task_type}")

    def get_task_sequence(self, task_type: TaskType) -> List[TaskType]:
        """
        Get the sequence of tasks that should follow a given task
        """
        sequences = {
            TaskType.DESCRIBE_SITUATION: [TaskType.ASK_QUESTIONS],
            TaskType.ASK_QUESTIONS: [TaskType.ANSWER_QUESTIONS],
            TaskType.ANSWER_QUESTIONS: [TaskType.DECLARE_INTENT],
            TaskType.DECLARE_INTENT: [TaskType.PROVIDE_FEEDBACK],
            TaskType.PROVIDE_FEEDBACK: [TaskType.MAKE_DECISION],
            TaskType.MAKE_DECISION: [TaskType.ASSESS_DIFFICULTY],
            TaskType.ASSESS_DIFFICULTY: [TaskType.RESOLVE_ACTION],
            TaskType.RESOLVE_ACTION: [TaskType.SUMMARIZE_ROUND],
            TaskType.SUMMARIZE_ROUND: [TaskType.DESCRIBE_SITUATION]  # Back to start for next turn
        }

        return sequences.get(task_type, [])
