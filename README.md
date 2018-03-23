# AI Competition

## Context

Your spaceship has crashed into an unknown planet. To escape, you need to collect materials from the nearby debris. However, you were not the only ones to crash here. You must quickly create a bot that will be able to collect as many materials as possible, before there are is nothing left and you are stuck on this planet forever.

### Goal

Your goal is to collect more materials than the other players. The player with the most points after a 1000 turns wins the game. To gain points, you need to collect materials on the map in the material deposits and store them in your base. Points are only given when the materials are stored.

If a bot dies, it loses all the materials it was carrying and respawns after 10 turns.
If a bot kills another bot, it steals all of the other bot's materials.

## Gameplay

Each turn, your bot will receive the following information:
1. The map
2. Information about all the bots, including your own bot.

Using this information, you need to generate commands to control your bot.

### Map

The map you receive will look like this:

1111111111122211111111111</br>
1000000000022200000000C01</br>
1000000000002000000000001</br>
1000200011000001100002001</br>
100020J01100J00110J002001</br>
1000200011000001100002001</br>
1C00S00000002000000000001</br>
1000S00000022200000000001</br>
1111111111122211111111111</br>

0 - Ground</br>
1 - Tree</br>
2 - Water</br>
J - Material deposit</br>
S - Dangerous zone. Your bot will take between 5 and 15 damage if it crosses one.</br>

The bots cannot traverse the following elements:</br>
1 - Tree</br>
2 - Water</br>
The other bots</br>
An enemy base</br>

### Bot information

In addition to the map, you will receive the following information on each bot.

base: The base location of that bot (line, column)</br>
carrying: How many materials the bot is carrying</br>
health: Health left</br>
id: Unique id</br>
location: The bot location (line, column)</br>
points: Number of points</br>
spawn: How many turns before the bot respawns (0 = alive, 1-10 = turns left)</br>
status: Current bot status ('alive', 'dead', 'disconnected')</br>

### Material deposits

Each time a player attempts to collect materials, the amount a player gets depends on the Gaussian distribution of the deposit. Each deposit has a distribution with a mean ranging from 5 to 20 and a standard deviation ranging from 1 to 10.

### Base

The base of a player is a secure zone for their bot. A bot can heal inside the base and it cannot be attacked by the other bots.

### Additional information

Only one player at a time can collect materials from a deposit.</br>
There is no limit to the amount of materials a bot can carry.</br>
To accelerate the development, a pathfinder is provided. However, this pathfinder will not avoid dangerous zones.

### Command list

1. Attack: Attack in a specific direction ('N', 'S', 'E' 'W'). If a bot is hit, it takes 10 damage. If it dies, the attacker gets everything the bot was carrying.</br>
2. Collect: Can only be used on a material deposit. Collect materials.</br>
3. Idle: Do nothing</br>
4. Move: Move in a specific direciton ('N', 'S', 'E', 'W').</br>
5. Rest: Can only be used inside the base. Heals 10 health.</br>
6. Store: Can only be used in the base. Converts the materials carried into points.

## Setup

```bash
# Create a virtual environment
python3 -m venv env
source env/bin/activate

# Install the dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Launch the game

Use the following command:

```bash
python3 main.py -m map1 -p BOT1 BOT2
```

Arguments:</br>
-p : Python bots list. The bots need to be in the `src.bot module`.</br>
-j : Use bots in Java (view Section Java).</br>
-m : Map name. The map needs to be in the folder `maps`.

## Java

Add [py4j](https://www.py4j.org/install.html#install-instructions) to your project dependencies.

In the `java` folder,

1. Add your bot in the `JavaBotEntryPoint` file.
2. Run `JavaBotEntryPoint`
3. Run the python main with `-j`.

## Other rules

You cannot install dependencies. You can only use the ones given in the repository.

## Submission

Submit a single zip file containing your bot and any other necessary file at </br>
mathieu.carpentier.3@ulaval.ca

Make sure to submit before Sat. 11h30 AM.</br>
Make sure to include your team name in the email.
