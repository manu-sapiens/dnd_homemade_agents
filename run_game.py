# run_game.py
import asyncio
from dnd.dnd_agents import Agent, player_agent, chronicler_agent, dm_agent, enforcer_agent
from dnd.game_master import GameMaster, PlayerCharacter, CharacterSheet


# Example of running the game
async def main():

    # Create player agents -------------------------------------------

    # Create Brussae the Paladin
    brussae = PlayerCharacter(
        name="Brussae", 
        character_sheet=CharacterSheet(
            name="Brussae",
            pronouns="he/him",
            level=2,
            class_name="Paladin",
            race="Human",
            key_abilities=["divine magic", "combat", "healing"],
            equipment=["longsword", "shield", "chain mail"],
            description="A warrior of faith, devoted to protecting the innocent",
            traits=["brave", "compassionate", "direct"],
            ideals=["protect the innocent", "uphold justice"],
            bonds=["sworn to defend the weak", "devoted to their deity"],
            flaws=["too trusting", "sees everything as good vs evil"],
            quirks=["always cleans their sword after battle", "prays before every meal"]
        )
    )

    # Create Shadowstep the Rogue
    shadowstep = PlayerCharacter(
        name = "Shadowstep",
        character_sheet=CharacterSheet(
            name="Shadowstep",
            pronouns="he/him",
            level=3,
            class_name="Rogue",
            race="Elf",
            key_abilities=["stealth", "lockpicking", "acrobatics"],
            equipment=["daggers", "thieves tools", "leather armor"],
            description="A nimble burglar with a heart of gold",
            traits=["cunning", "cautious", "witty"],
            ideals=["freedom", "loyalty to friends"],
            bonds=["protective of street urchins", "owes a debt to a noble"],
            flaws=["greedy", "overconfident in their abilities"],
            quirks=["always checks for traps, even in safe places", "collects small trinkets"]
        )
    )

    # Create Eldara the Wizard
    eldara = PlayerCharacter(
        name="Eldara", 
        character_sheet= CharacterSheet(
            name="Eldara",
            pronouns="she/her",
            level=2,
            class_name="Wizard",
            race="half-elf",
            key_abilities=["arcane magic", "investigation", "history"],
            equipment=["staff", "spellbook", "component pouch"],
            description="A scholarly mage seeking ancient knowledge",
            traits=["analytical", "curious", "reserved"],
            ideals=["knowledge", "magical preservation"],
            bonds=["ancient magical texts", "wizard academy"],
            flaws=["overthinks simple problems", "dismissive of non-magical solutions"],
            quirks=["takes notes about everything", "speaks in unnecessarily complex terms"]
        )
    )

    player_characters = [brussae, shadowstep, eldara]

    game_master = GameMaster(
        dm_agent=dm_agent,
        player_characters=player_characters,
        chronicler_agent=chronicler_agent,
        enforcer_agent=enforcer_agent,
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
        """
    )



    for player in player_characters:
        await game_master.execute_player_turn(player)
    #    

# Run the main function (if using an async framework)
import asyncio
if __name__ == "__main__":
    asyncio.run(main())