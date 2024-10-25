# example_game.py
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import List
from dnd_game import (
    Character,
    PersonalityProfile,
    DMAgent,
    PlayerAgent,
    ChroniclerAgent,
    GameMaster,
    PartyStatus
)
from dnd_game.config import get_settings

# Load environment variables
#load_dotenv()

import os
# first list the content of the save directory
print("---------")
print(os.listdir('./dnd_game/'))
print("---------")

settings = get_settings()

async def create_characters():
    """Create our party of adventurers"""

    # Create Brussae the Paladin
    brussae = Character(
        name="Brussae",
        level=2,
        class_name="Paladin",
        race="Human",
        key_abilities=["divine magic", "combat", "healing"],
        equipment=["longsword", "shield", "chain mail"],
        description="A warrior of faith, devoted to protecting the innocent"
    )

    brussae_personality = PersonalityProfile(
        traits=["brave", "compassionate", "direct"],
        ideals=["protect the innocent", "uphold justice"],
        bonds=["sworn to defend the weak", "devoted to their deity"],
        flaws=["too trusting", "sees everything as good vs evil"],
        quirks=["always cleans their sword after battle", "prays before every meal"]
    )

    # Create Shadowstep the Rogue
    shadowstep = Character(
        name="Shadowstep",
        level=3,
        class_name="Rogue",
        race="Elf",
        key_abilities=["stealth", "lockpicking", "acrobatics"],
        equipment=["daggers", "thieves tools", "leather armor"],
        description="A nimble burglar with a heart of gold"
    )

    shadowstep_personality = PersonalityProfile(
        traits=["cunning", "cautious", "witty"],
        ideals=["freedom", "loyalty to friends"],
        bonds=["protective of street urchins", "owes a debt to a noble"],
        flaws=["greedy", "overconfident in their abilities"],
        quirks=["always checks for traps, even in safe places", "collects small trinkets"]
    )

    # Create Eldara the Wizard
    eldara = Character(
        name="Eldara",
        level=2,
        class_name="Wizard",
        race="half-elf",
        key_abilities=["arcane magic", "investigation", "history"],
        equipment=["staff", "spellbook", "component pouch"],
        description="A scholarly mage seeking ancient knowledge"
    )

    eldara_personality = PersonalityProfile(
        traits=["analytical", "curious", "reserved"],
        ideals=["knowledge", "magical preservation"],
        bonds=["ancient magical texts", "wizard academy"],
        flaws=["overthinks simple problems", "dismissive of non-magical solutions"],
        quirks=["takes notes about everything", "speaks in unnecessarily complex terms"]
    )

    return [
        (brussae, brussae_personality),
        (shadowstep, shadowstep_personality),
        (eldara, eldara_personality)
    ]

async def setup_game():
    """Initialize the game with all agents"""

    # Create the DM agent
    dm = DMAgent(
        model=settings.default_dm_model,
        temperature=settings.default_dm_temperature,
        style_preferences={
            "description_style": "vivid and atmospheric",
            "combat_style": "dynamic and tactical",
            "narrative_style": "balanced between story and game mechanics",
            "difficulty_style": "fair but challenging"
        }
    )

    # Create the Chronicler
    chronicler = ChroniclerAgent(
        model=settings.default_chronicler_model,
        temperature=settings.default_chronicler_temperature,
        memory_length=5
    )

    # Create player agents
    characters = await create_characters()
    player_agents = []

    for character, personality in characters:
        player_agent = PlayerAgent(
            character=character,
            personality=personality,
            model=settings.default_player_model,
            temperature=settings.default_player_temperature
        )
        player_agents.append(player_agent)


    party_status = PartyStatus(
        location="The entrance of the Crimson Crypt",
        conditions={},  # You can populate with actual conditions
        group_conditions=[],
        resources_used={}
    )
    # Create the game with initial situation
    game = GameMaster(
        dm_agent=dm,
        player_agents=player_agents,
        chronicler_agent=chronicler,
        initial_situation="""
        The party stands at the entrance of the Crimson Crypt, an ancient tomb recently
        uncovered in the forests north of the city. Local legends speak of powerful
        magical artifacts sealed away here centuries ago. The stone doorway bears
        mysterious runes, and a cold breeze emanates from within. The sun is setting,
        casting long shadows through the trees.

        The party has been hired by the Arcane Academy to investigate the tomb and
        retrieve any magical artifacts, especially the rumored Orb of First Light.
        However, they're not the only ones interested in the tomb's contents - they've
        spotted signs of other adventurers in the area.
        """,
        party_status=party_status
    )

    return game

async def main():
    try:
        # Setup the game
        print("Setting up the game...")
        game = await setup_game()

        # Create saves directory if it doesn't exist
        Path("saves").mkdir(exist_ok=True)

        # Run for 3 rounds
        print("\nStarting the game...")
        for round_num in range(3):
            print(f"\n{'='*20} Round {round_num + 1} {'='*20}")

            # Execute the round
            await game.execute_round()

            # Save after each round
            save_path = await game.save(f"game_round_{round_num + 1}")
            print(f"\nGame saved to: {save_path}")

            # Optional: Print round summary
            if game.state.round_summaries:
                latest_summary = game.state.round_summaries[-1]
                print("\nRound Summary:")
                print(latest_summary)

        # Print final game summary
        print("\nFinal Game Summary:")
        print(game.get_game_summary())

    except Exception as e:
        print(f"Error during game: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())