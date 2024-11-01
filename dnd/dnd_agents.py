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
    <turn_summary>
        <round_number>{round_number}</round_number>
        <character_name>{character_name}</character_name>

        <initial_situation>
            {initial_situation}
        </initial_situation>

        <action_taken>
            {action_taken}
        </action_taken>

        <difficulty>{difficulty}</difficulty>
        <roll>{roll}</roll>
        <success>{success}</success>
        <result>
            {action_result}
        </result>

        <previous_context>
            {previous_context}
        </previous_context>

        <summary_guidelines>
            Use the initial_situation to identify the context before the action.
            Use the action_taken and roll result to describe what changed, considering both immediate and potential impacts.
            Reference the previous_context for any ongoing effects or previously unresolved issues.

            Summarize:
            - How the situation has changed based on action_taken
            - Immediate effects of the action on the environment and characters
            - Any information that will impact the next player's turn
        </summary_guidelines>
    </turn_summary>
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)


summarize_round = Task(
    description="Create a comprehensive summary of the completed round",
    prompt_template="""
    <round_summary>
        <round_number>{round_number}</round_number>

        <initial_situation>
            {initial_situation}
        </initial_situation>

        <round_events>
            {round_events}
        </round_events>

        <party_members>
            {party_members}
        </party_members>

        <previous_summary>
            {previous_summary}
        </previous_summary>

        <summary_guidelines>
            - Use initial_situation to frame the context at the start of the round.
            - Use round_events to highlight important actions and their impacts.
            - Reference party_members to note any character status updates or relationship shifts.
            - Connect with previous_summary to maintain continuity and track unresolved threads.

            Summarize:
            - Key events and their significance
            - Changes in characters or the environment
            - Immediate and potential consequences
            - Primary narrative focus for the next round
        </summary_guidelines>
    </round_summary>
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)


assess_detail_importance = Task(
    description="Evaluate the importance of specific details for future reference",
    prompt_template="""
    <detail_assessment>
        <detail>{detail}</detail>
        <current_context>{current_context}</current_context>
        <recent_history>{recent_history}</recent_history>

        <assessment_guidelines>
            - Evaluate detail in light of current_context for immediate relevance.
            - Refer to recent_history to identify connections with ongoing plot threads or past events.
            - Assess whether this detail impacts character development, tactical choices, or story progression.

            Consider:
            - Potential future relevance of detail
            - Connections to plot or character arcs in recent_history
            - Tactical or narrative importance within current_context
        </assessment_guidelines>
    </detail_assessment>
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)


retrieve_relevant_context = Task(
    description="Retrieve relevant context for the current situation",
    prompt_template="""
    <retrieve_context>
        <current_situation>{current_situation}</current_situation>
        <active_character>{active_character}</active_character>
        <attempted_action>{attempted_action}</attempted_action>
        <memory_store>{memory_store}</memory_store>

        <context_guidelines>
            - Use current_situation to frame the setting and identify immediate information needs.
            - Look at active_character and attempted_action to focus on relevant experiences and tactical knowledge.
            - Search memory_store for similar past events, character actions, or consequences connected to the current situation.

            Retrieve:
            - Related character experiences and tactical information from memory_store
            - Connected narrative elements that may influence current_situation
            - Similar past situations relevant to active_character
        </context_guidelines>
    </retrieve_context>
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__ask_questions = Task(
    description="Ask relevant questions to the Dungeon Master about the current situation",
    prompt_template="""
    <ask_questions>
        <character_name>{character_name}</character_name>

        <turn_instructions>
            It is your turn. Before you act, ask relevant questions to the Dungeon Master about the current situation.
        </turn_instructions>

        <story_so_far>
            {the_story_so_far}
        </story_so_far>

        <dm_info>
            {what_the_dm_just_told_you}
        </dm_info>

        <character_sheet>
            {character_sheet}
        </character_sheet>

        <question_guidelines>
            - Use dm_info to clarify recent changes or details about the immediate environment.
            - Refer to story_so_far to connect your questions with any ongoing plot threads or previous events relevant to your character.
            - Use character_sheet to shape questions based on your character’s motivations, skills, and knowledge.

            Formulate concise questions:
            - About potential risks and opportunities related to dm_info
            - That clarify points your character would naturally wonder about, considering their abilities in character_sheet
            - Limit yourself to 3 questions: one about rules, one about your character, and one about the world.
        </question_guidelines>
    </ask_questions>
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)


task__declare_intent = Task(
    description="Declare your intended action based on the information gathered",
    prompt_template="""
    <declare_intent>
        <character_name>{character_name}</character_name>

        <turn_instructions>
            It is your turn. You have just asked a few questions to the DM and received your answers. Now declare what action you're considering taking and why.
        </turn_instructions>

        <story_so_far>
            {the_story_so_far}
        </story_so_far>

        <dm_response>
            {what_the_dm_just_told_you}
        </dm_response>

        <player_questions>
            {player_questions}
        </player_questions>

        <dm_answers>
            {dm_answers}
        </dm_answers>

        <character_sheet>
            {character_sheet}
        </character_sheet>

        <intent_guidelines>
            Based on:
            - The information you've gathered from the dm_answers
            - Your character's capabilities, goals, objectives, personality and motivations as describe in the character_sheet
            - What happened in the game so far and your relationship with other party members as gathered from the_story_so_far

            Describe the action you are considering. Make it clear this is your intent, not your final decision. 
            State it concisely, such as "Maybe I should..." or "I think I will...".
            This action should ideally reflect your unique role in the party.
        </intent_guidelines>
    </declare_intent>
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__provide_feedback = Task(
    description="Give feedback to another character's intended action",
    prompt_template="""
    <provide_feedback>
        <other_character_name>{other_character_name}</other_character_name>

        <turn_instructions>
            It is your turn to provide quick feedback regarding another character's intended action, as if you were talking to them in-character.
        </turn_instructions>

        <story_so_far>
            {the_story_so_far}
        </story_so_far>

        <dm_info>
            {what_the_dm_just_told_you}
        </dm_info>

        <character_sheet>
            {other_character_sheet}
        </character_sheet>

        <acting_character>
            <name>{acting_character_name}</name>
            <intended_action>{intended_action}</intended_action>
        </acting_character>

        <feedback_guidelines>
            - Use story_so_far and dm_info to frame your feedback with relevant background knowledge, especially regarding relationships and current stakes.
            - Tailor feedback based on your character’s personality and expertise in character_sheet, while considering any visible risks in the intended_action.
            - Keep feedback concise and in-character, providing a quick verbal response or minor action (like nodding or drawing a weapon).

            This feedback should be authentic to your character’s view, even if it disagrees with the intended action.
        </feedback_guidelines>
    </provide_feedback>
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

task__describe_initial_situation_chatty = Task(
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

task__describe_initial_situation = Task(
    description="Describe the current situation to the player briefly",
    prompt_template="""
    <describe_initial_situation>
        <character_name>{character_name}</character_name>

        <turn_instructions>
            Provide a succinct description to set up {character_name}'s next turn. Use minimal detail—focus only on key elements that affect immediate decisions.
        </turn_instructions>

        <story_so_far>
            {the_story_so_far}
        </story_so_far>

        <character_sheet>
            {character_sheet}
        </character_sheet>

        <scene_guidelines>
            - Use 2-3 sentences only.
            - Describe the essentials, like major threats, opportunities, and any urgent changes in the environment.
            - Avoid embellishing details or background information unless it's critical.
            - Highlight {character_name}'s immediate options or cues to guide their next action.
        </scene_guidelines>
    </describe_initial_situation>
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
    <difficulty_assessment>
        <character_name>{character_name}</character_name>

        <story_so_far>
            {the_story_so_far}
        </story_so_far>

        <dm_response>
            {what_you_just_told_the_player}
        </dm_response>

        <proposed_action>{proposed_action}</proposed_action>
        <character_sheet>{character_sheet}</character_sheet>

        <assessment_guidelines>
            - Use character_sheet to evaluate capabilities and equipment relevant to proposed_action.
            - Reference story_so_far and dm_response to account for environmental factors or recent consequences.

            Assess and respond in JSON format:
            - difficulty: Describe as auto_succeed, easy, average, hard, super_hard, or auto_fail.
            - reasoning: Explain based on character capabilities, environment, and action complexity.
        </assessment_guidelines>
    </difficulty_assessment>
    """,
    response_model=DifficultyAssessment
)


task__answer_questions = Task(
    description="Answer the character's questions based on the game's progress",
    prompt_template="""
    <answer_questions>
        <character_name>{character_name}</character_name>

        <story_so_far>
            {the_story_so_far}
        </story_so_far>

        <dm_response>
            {what_you_just_told_the_player}
        </dm_response>

        <character_sheet>{character_sheet}</character_sheet>
        <questions>{questions}</questions>

        <answer_guidelines>
            - Use dm_response and story_so_far to answer questions in the context of recent events.
            - Refer to character_sheet to gauge what knowledge or perceptions are reasonable for the character.
            - Maintain a balance between helpful hints and preserving mystery.

            Only provide answers, without assuming any character actions or reactions.
        </answer_guidelines>
    </answer_questions>
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__resolve_action_chatty = Task(
    description="Resolve the character's action based on the roll result",
    prompt_template="""
    <resolve_action>
        <character_name>{character_name}</character_name>

        <story_so_far>
            {the_story_so_far}
        </story_so_far>

        <dm_response>
            {what_you_just_told_the_player}
        </dm_response>

        <character_sheet>{character_sheet}</character_sheet>
        <proposed_action>{proposed_action}</proposed_action>
        <difficulty_assessment>{difficulty_assessment}</difficulty_assessment>
        <roll_result>{roll}</roll_result>
        <success_threshold>{success_threshold}</success_threshold>
        <did_roll_succeed>{did_roll_succeed}</did_roll_succeed>

        <resolution_guidelines>
            - Use character_sheet to tailor the description of success or failure based on capabilities.
            - Refer to story_so_far and dm_response for environmental factors and previous effects.
            - Consider the difficulty_assessment and roll outcome to show the degree of success or failure.

            Resolve in 2-3 sentences, addressing the entire party.
        </resolution_guidelines>
    </resolve_action>
    """,
    response_model=None  # Replace with appropriate Pydantic model if needed
)

task__resolve_action = Task(
    description="Resolve the character's action briefly based on the roll result",
    prompt_template="""
    <resolve_action>
        <character_name>{character_name}</character_name>

        <story_so_far>
            {the_story_so_far}
        </story_so_far>

        <dm_response>
            {what_you_just_told_the_player}
        </dm_response>

        <character_sheet>{character_sheet}</character_sheet>
        <proposed_action>{proposed_action}</proposed_action>
        <difficulty_assessment>{difficulty_assessment}</difficulty_assessment>
        <roll_result>{roll}</roll_result>
        <success_threshold>{success_threshold}</success_threshold>
        <did_roll_succeed>{did_roll_succeed}</did_roll_succeed>

        <resolution_guidelines>
            - Describe the action outcome in 2-3 sentences.
            - Focus on the immediate effect and impact on the party; avoid extra detail.
            - Only describe what’s necessary for the story to progress and create a clear transition to the next player's turn.
        </resolution_guidelines>
    </resolve_action>
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
    - Succint: provide enough detail without overwhelming. You let the players ask for more details if they want. 
    You tell in a couple of sentances what the players see and what they can do.

    Core principles:
    - Never decide for the players, always let them choose what they want to do
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
    - Be succint and to the point, do not get verbose on descriptions or repeating details that are already known to the players.
    """
)

less_chatty_dm = Agent(
    name="Less Chatty Dungeon Master",
    model="openai|gpt-4o-mini",
    temperature=0.5,
    system_prompt="""
    You are a concise Dungeon Master who focuses on brief, impactful descriptions to keep the action moving quickly. 
    Use short, vivid sentences to provide essential details, especially when resolving actions or describing situations mid-story.
    
    Your key principles:
    - Limit responses to 2-3 sentences when brief descriptions are sufficient.
    - Avoid lengthy narratives; instead, focus on advancing the action with minimal detail.
    - Describe outcomes and immediate consequences clearly, but avoid excessive detail.
    - Let players ask for additional information if needed; offer only what’s essential to proceed.

    Exceptions:
    - At the start of a new scene or major event, you can provide a slightly more detailed description.
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
