# This example:

1. Creates a party of three distinct characters:
   - Brussae: The brave Paladin
   - Shadowstep: The cunning Rogue
   - Eldara: The scholarly Wizard

2. Sets up the game with:
   - A DM with specific style preferences
   - A Chronicler for memory management
   - A complex initial situation

3. Demonstrates:
   - Full game loop
   - Round execution
   - State saving
   - Summary generation

To run this example:
1. Ensure your .env file is set up with necessary API keys
2. Install all requirements
3. Run:
```bash
python example_game.py
```


# Directory structure for the complete project:
```plaintext
dnd_game/
├── README.md
├── requirements.txt
├── .env
├── .gitignore
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── base.py         # Enums, exceptions, base model classes
│   ├── character.py    # Character, PersonalityProfile, PlayerCharacter
│   ├── game_state.py   # GameState, Round, ActionResult
│   └── actions.py      # Intent, PlayerFeedback, DifficultyAssessment, RoundSummary
├── agents/
│   ├── __init__.py
│   ├── base.py         # Agent base class and ModelCaller
│   ├── dm.py           # DM-specific agent implementation
│   ├── player.py       # Player agent implementation
│   └── chronicler.py   # Chronicler agent implementation
├── core/
│   ├── __init__.py
│   ├── game_master.py  # Main game orchestration
│   └── tasks.py        # Task definitions and management
├── config/
│   ├── __init__.py
│   └── settings.py     # Game configuration, environment variables
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_agents/
    ├── test_core/
    └── test_models/
