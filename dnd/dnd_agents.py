# dnd_agents.py
# Flat structure integrating chronicler, dm, player agents and their tasks

from pydantic import BaseModel
from core.agent import Agent, Task

# Defining Tasks and Agents directly in the main script
compress_memory = Task(
    description="Compress multiple round summaries into a consolidated memory",
    prompt_template="""
    Rounds to compress:
    {round_summaries}

    Create a compressed memory that maintains:
    - Critical narrative developments
    - Important tactical information
    - Character development and changes
    - Significant consequences
    - Unresolved plot threads
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

summarize_turn = Task(
    description="Create a summary of a player's turn and its effects",
    prompt_template="""
    Round {round_number}, Character: {character_name}
    
    Initial situation:
    {initial_situation}
    
    Action taken: {action_taken}
    Difficulty: {difficulty}
    Roll: {roll} ({success})
    Result: {action_result}
    
    Previous context:
    {previous_context}
    
    Summarize:
    - How the situation has changed
    - Immediate effects of the action
    - Current state of the environment
    - What the next player needs to know
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

summarize_round = Task(
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
    response_model=None  # Replace with appropriate Pydantic model if needed
)

assess_detail_importance = Task(
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
    response_model=None  # Replace with appropriate Pydantic model if needed
)

retrieve_relevant_context = Task(
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
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__ask_questions = Task(
    description="Ask relevant questions to the Dungeon Master about the current situation",
    prompt_template="""
    {character_name}, this is your turn. Before you act, ask relevant questions to the Dungeon Master about the current situation

    The story so far: {the_story_so_far}
    What the DM just told you: {what_the_dm_just_told_you}
    Your character sheet: {character_sheet}

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
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__declare_intent = Task(
    description="Declare your intended action based on the information gathered",
    prompt_template="""    
    {character_name}, it is your turn. You have just asked a few questions to the DM and received your answer. Now declare what action you're considering taking and why.
    
    The story so far: 
    {the_story_so_far}
    {what_the_dm_just_told_you}
 
    Your questions: {player_questions} 
    The DM's answers: {dm_answers}

    Your character sheet: {character_sheet}
    
    Based on:
    - The information you've gathered
    - Your character's capabilities
    - Your personality and motivations
    - Your relationship with other party members
    - Your goals and objectives
    - What happened in the game so far

    What single action are you considering taking and why? 
    Make it clear this is your intent, not your final decision. 
    State it in a matter-of-fact way, concise and precise such as 'Mabe I should...' or '"I think I will...'. 
    Since you are in a party, it is best if this is an action only you would consider. Be creative!
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__provide_feedback = Task(
    description="Give feedback to another character's intended action",
    prompt_template="""
    {other_character_name}, it is your turn to provide a quick feedback. Provide a single sentence as feedback regarding another character's intended action, as if you were talking to them in-character. You can also provide an action that is guarranteed to succeed and near instantaneous, such as adjusting your glasses, or taking out a sword from its scabard.

    The story so far: 
    {the_story_so_far}
    {what_the_dm_just_told_you}

    Your own character sheet: {other_character_sheet}

    Character planning to act: {acting_character_name}
    Their intended action: {intended_action}

    Consider:
    - Your relationship with this character
    - Your expertise and experience
    - Potential risks you can see
    - How this might affect the party
    - What your character would actually say
    - You do not have to agree with the character's action. Providing honest feedback and diverging opinions can lead to interesting roleplay.

    Remember to offer a quick verbal feedback and/or a quick action like a nod.
    This could be as simple as *Drawing my sword* 'Great idea! More fighting, less talking!'.
    Do not get verbose on this, as this is not your turn to act (and that turn will come soon enough!). 
    Keep it concise and in-character. This quick feedback should be very unique to your character!
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__make_decision = Task(
    description="Make your final decision on what you will attempt, considering party feedback",
    prompt_template="""
    {character_name}, it is your turn. You have proposed an action and received feedback from your party. Now make your final decision on what you will attempt.

    The story so far: 
    {the_story_so_far}
    {what_the_dm_just_told_you}

    Your original proposal:
    {intended_action}

    Party feedback:
    {party_feedback}

    Your character sheet: 
    {character_sheet}

    Based on your character's:
    - Personality and typical behavior
    - Relationship with other party members
    - Assessment of the feedback

    Make your final decision. 
    It can be brief since we already heard your thinking when you stated your intent.
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__describe_initial_situation = Task(
    description="Describe the current situation to the player",
    prompt_template="""
    This is the beginning of {character_name} turn. 
    Progress the story as needed based on what transpire before and describe the situation to {character_name} so they can make their choice.
    Do not be too verbose, the players want to play! Do provide enough information to help them make an informed decision.
    Not need to provide a list of choices to the player: let them decide what they want to do.

    The story so far: 
    {the_story_so_far}
    
    {character_name}'s details: {character_sheet}
    Other party members: {other_characters}
    
    Describe the scene to {character_name}, emphasizing:
    - How the environment has changed and the consequences of the previous actions, if any, from all the characters.
    - Where {character_name} is positioned and what they can see, especially compared to other characters in the Party.
    - What {character_name} was doing immediately prior to their turn.
    - Any obvious threats or opportunities
    - The atmosphere and environment
    - Any ongoing effects or conditions
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__describe_situation = Task(
    description="Describe the current situation to the player in a few lines",
    prompt_template="""
    This is the beginning of {character_name} turn. Your job is to describe the current situation to the player as succinctly as possible.
    Progress the story as needed based on what transpire before and describe the situation to {character_name} so they can make their choice.
    Be succint, the players want to play! Do provide enough information to help them make an informed decision.
    Not need to provide a list of choices to the player: let them decide what they want to do.

    <the_story_so_far>
    {the_story_so_far}
    </the_story_so_far>

    Do not repeat decriptions or facts that appear in the story_so_far since it is fresh in the player's mind.
    
    <{character_name}>
    {character_sheet}
    </{character_name}>
    
    <other_party_members>
    {other_characters}
    </other_party_members>
    
    If it has not been mentioned already, describe:
    - How the environment has changed and the consequences of the previous actions, if any, from all the characters.
    - Where {character_name} is positioned and what they can see, especially compared to other characters in the Party.
    - Any ongoing effects or conditions

    Do remind {character_name} what they were doing immediately prior to their turn.

    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)


class DifficultyAssessment(BaseModel):
    difficulty: str
    reasoning: str
#

task__assess_difficulty = Task(
    description="Assess the difficulty of a character's proposed action",
    prompt_template="""
    Assess the difficulty of {character_name}'s proposed action.

    The story so far:
    {the_story_so_far}
    {what_you_just_told_the_player}

    {character_name}'s proposed action: {proposed_action}
    {character_name}'s character sheet: {character_sheet}

    Assess how difficult this action would be to accomplish for {character_name}. 
    Consider:
    - {character_name}'s capabilities and equipment
    - The situation and environment
    - Any relevant previous actions or consequences
    - Whether this even needs a roll (simple actions might auto-succeed)

    Reply only as a JSON object with the following fields:
    - difficulty: A description of the difficulty taken from [auto_succeed, easy, average, hard, super_hard, auto_fail]
    - reasoning: Explanation of why you chose this difficulty

    """,
    response_model=DifficultyAssessment
)

task__answer_questions = Task(
    description="Answer the character's questions based on the game's progress",
    prompt_template="""
    Answer {character_name}'s questions in context of the game played so far

    The story so far: 
    {the_story_so_far}
    {what_you_just_told_the_player}

    {character_name}'s character sheet: {character_sheet}
    {character_name}'s questions: {questions}

    Answer these questions while considering:
    - Where {character_name} is positioned and what they can see, especially compared to other characters in the Party
    - What {character_name} could reasonably know or perceive at a simple glance
    - Information they've gained through previous actions
    - Maintaining mystery where appropriate
    - Providing useful but not complete information
    - Do not make {character_name} or other characters say or do anything while answering the questions. Only provide information.
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__resolve_action = Task(
    description="Resolve the character's action based on the roll result",
    prompt_template="""
    Describe how {character_name}'s action plays out based on the roll. Be succint.

    The story so far: 
    <the_story_so_far>
    {the_story_so_far}
    {what_you_just_told_the_player}
    </the_story_so_far>

    {character_name}'s character sheet: {character_sheet}
    {character_name}'s proposed action: {proposed_action}

    Your difficulty assessment for this action: {difficulty_assessment}
    Roll result: {roll}. Note: must be smaller than {success_threshold} to succeed.
    Success: {did_roll_succeed}

    Describe how the action plays out for {character_name}, considering:
    - The degree of success or failure (based on roll)
    - {character_name}'s capabilities and approach
    - Environmental factors and circumstances
    - Maintaining forward momentum
    - Creating interesting consequences

    However, do not repeat decriptions or facts that appear in the story_so_far since it is fresh in the player's mind.
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

# Initialize agents in a straightforward manner
chronicler_agent = Agent(
    name="Chronicler",
    model="openai|gpt-4o-mini",
    temperature=0.3,
    system_prompt="""
    You are the Chronicler, keeper of the game's memory and narrative continuity.

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
    - Track ongoing effects and conditions
    """
)

player_agent = Agent(
    name="Player",
    model="openai|gpt-4o-mini",
    temperature=0.7,
    system_prompt="""
    You are playing the role of a D&D character with personality and traits as defined by the game.

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
    - Express your character's emotions and thoughts naturally
    """
)

dm_agent = Agent(
    name="Dungeon Master",
    model="openai|gpt-4o-mini",
    temperature=0.7,
    system_prompt="""
    You are a skilled Dungeon Master who weaves engaging narratives and controls NPCs.

    Your DMing style:
    - Descriptions: vivid and atmospheric
    - Combat: dynamic and tactical
    - Narrative: balanced between story and game mechanics
    - Difficulty: fair but challenging

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
    - Always maintain narrative momentum regardless of success or failure
    """
)



enforcer_agent = Agent(
    name="Roleplay Enforcer",
    model="openai|gpt-4o-mini",
    temperature=0.7,
    system_prompt="""
    You are a roleplay enforcer ensuring fair-play boundaries in DM and Player interactions

    Your role is to censor or edit any player or DM actions that violate the rules of the game or the roleplay boundaries.
    Typical violations include:
    - Players controlling NPCs or other characters
    - Players determining outcomes of significant actions
    - DMs dictating player actions or internal dialogue
    
    You will also ensure a good pace that give players maximum agency and narrative control.
    So the DM should not say: you explore the whole room and move on to the next corridor that you also find empty because it denies agency to all the players.
    In the same way, a player should not say: I find a secret door that leads to the treasure room because it denies the DM the opportunity to create a meaningful narrative
    and it is not up to the player to decide what they find in the world.
    Also a player should not move away from the group without consulting the group or the DM, as it can disrupt the narrative and the game.
    It is okay for a player to say they enter the room, but not to say: I go back to town and buy provision because it disrupts the narrative for the other players.
    
    Your goal is to maintain a balanced and fair roleplay environment where all participants have agency and contribute to the story.
    You will edit out any violations while preserving the narrative flow, dm decisions and player agency.

    Remember that the players are free to say and feel anything but can only attempt action with their own character.

    As much as possible, you will leave the text you are monitoring untouched, only editing when necessary to enforce the rules.
    Just edit silently: you don't need to inform the players or the DM that you are editing their text and your role 
    should be invisible to the players and the DM.
    """
)

# Define the task for enforcing DM behavior
task__enforce_dm = Task(
    description="Ensure the DM does not control player actions or internal dialogue",
    prompt_template="""
        Ensure the DM does not control player actions or internal dialogue

        DM Output:
        {dm_output}

        Review this output to ensure:
        - The DM does not dictate what players think. 
        - The DM does not dictate what a player do unless the player explictly attempted the action.
        
        The DM however is free to describe the environment, the NPCs and the consequences of the player's actions.

        Ideally, you will output the same text as you reviewed. However, if violations are found, 
        revise the output to remove the violations while keeping the narrative flow intact.
        """,
    response_model=None  # Can use a model for structured validation if needed
)

# Define the task for enforcing Player behavior
task__enforce_player = Task(
    description="Ensure players do not control NPCs or determine outcomes of significant actions",
    prompt_template="""
        Ensure players do not control NPCs or determine outcomes of significant actions

        Player Output:
        {player_output}

        Review this output to ensure:
        - The player does not control NPCs or other characters' actions or dialogue.
        - Non-trivial actions do not have pre-determined outcomes unless confirmed by the DM.

        Remember that the players are free to say and feel anything but can only attempt actions with their own character.

        Ideally, you will output the same text as you reviewed. However, if any issues are detected, revise the output to retain the player’s perspective while removing control over outcomes and other characters.
        """,
    response_model=None
)
