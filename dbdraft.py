import pandas as pd
import openai
from dotenv import load_dotenv
import os

load_dotenv()

# Set up the API key and organization (if you're part of one)
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORG")  # You can comment this out if you're not part of an organization

# Load the datasets
espn_data = pd.read_csv('ESPN.csv')
cbs_data = pd.read_csv('CBS.csv')
nfl_data = pd.read_csv('NFL.csv')
yahoo_data = pd.read_csv('Yahoo.csv')

# Combine datasets and calculate mean stats
all_data = pd.concat([espn_data, cbs_data, nfl_data, yahoo_data])

# Roster setup
ROSTER = {
    "QB": 1,
    "WR": 3,
    "RB": 2,
    "TE": 1,
    "Kicker": 1,
    "Defense": 1,
    "Bench": 7
}

# Initialized user roster
user_roster = {
    "QB": [],
    "WR": [],
    "RB": [],
    "TE": [],
    "Kicker": [],
    "Defense": [],
    "Bench": []
}

# Initialized drafted players list
drafted_players = []

SUPERPROMPT = """
There is a fantasy football draft taking place with *10 teams*. Each team will have the following roster: 
- 1 QB
- 3 WRs
- 2 RBs
- 1 TE
- 1 Kicker
- 1 Defense
- 7 Bench Spots

SCORING SYSTEM:
The league operates on a Point Per Reception (PPR) format. Here's a detailed breakdown of the scoring:
- **Passing Yards**: Players earn 1 point for every 25 passing yards.
- **Passing Touchdown**: A passing touchdown earns the player 6 points.
- **Interception**: Players lose 1 point for every interception thrown.
- **Rushing Yards**: Players earn 1 point for every 10 rushing yards.
- **Receiving Yards**: Players earn 1 point for every 10 receiving yards.
- **Reception**: Every reception made by a player earns them 1 point (highlighting the PPR format).
- **Fumble**: Players lose 2 points for every fumble.

You will be provided aggregated data from ESPN, CBS, NFL, and Yahoo, which tallies the stats each available player is forecasted by those sources to get this year this year according to the pool rules. You must also consider general knowledge of the game of football, players and teams up to 2021, different fantasy football leagues and strategies to make the best possible picks. It is critical that we consider other pool participants picks, as well as the caliber of players left for each position, the number of positions left for our user to fill and all overall fantasy football strategy.
"""

def available_positions():
    positions_needed = []
    for position, players in user_roster.items():
        if len(players) < ROSTER[position]:
            positions_needed.append(position)
    return positions_needed

def get_advice(players_taken):
    global all_data
    players_taken_lower = [player.strip().lower() for player in players_taken]
    all_data = all_data[~all_data['PLAYER'].str.lower().isin(players_taken_lower)]
    valid_positions = available_positions()
    
    # Get the top 75 from the dataset
    top_players = all_data[all_data['Position'].isin(valid_positions) & ~all_data['PLAYER'].str.lower().isin(players_taken_lower)].head(75)  # Increased limit to cover possible needs

    detailed_stats = top_players.to_string(index=False)
    
    additional_context = ""
    if "Bench" in valid_positions:
        additional_context = "\nFor bench selections, consider the need for substitutions in positions like QB, WR, RB, and TE. A diversified bench is important to manage risks during the season."

    user_roster_str = "\n".join([f"{pos}: {', '.join(players) if players else 'None'}" for pos, players in user_roster.items()])

    context_message = SUPERPROMPT + additional_context + "\nThe following players have been taken by others: {}.\n\nYour current roster:\n{}\n\nTop available players based on aggregated data in .csv format:\n\n{}".format(
        ", ".join(players_taken),
        user_roster_str,
        detailed_stats
    )

    # Add print statements here to print out the context message:
    # print("\n**************************************************************")
    # print("Sending the following context to DraftGPT:")
    # print(context_message)
    # print("**************************************************************\n")

    print("\n\n\n**************************************************************")
    print("Data sent to DraftGPT, awaiting response.       *You are an A*")
    print("**************************************************************\n\n\n")

    messages = [
        {"role": "system", "content": "You are DraftGPT, a virtual assistant with expertise in the 2023 NFL Fantasy Draft. Your role is to provide insights and advice on player selections based on the current draft situation."},
        {"role": "user", "content": context_message},
        {"role": "user", "content": "Who should we pick next? It is critical to ensure we employ the best strategy possible considering the fantasy football league type, structure, roster and scoring system. We must assess which players from the top players remaining are likely to both make the best contribution, but also have the best value considering the current round, roster positions and the depth of each type of point getting position in the overall NFL league. This means picking the right positions at the right time considering the depth of available talent, and it is a critical consideration. Please provide advice on the top three picks we could make, along with logic why each would be a good pick, followed by your overall recommendation for the best pick from available players."}
    ]

    response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    return response.choices[0].message.content.strip()

def pick_player(actual_pick):
    """Handle picking a player and updating rosters and available data."""
    global all_data
    # Convert the provided name to lowercase
    actual_pick_lower = actual_pick.lower()
    # Check if the player is in the available data using lowercase
    if actual_pick_lower not in all_data['PLAYER'].str.lower().values:
        print("The player name isn't recognized or has already been taken. Please try again.")
        return False

    player_position = all_data[all_data['PLAYER'].str.lower() == actual_pick_lower]['Position'].values[0]

    if player_position in ROSTER:
        # Check if there's still space in the main roster for the position
        if len(user_roster[player_position]) < ROSTER[player_position]:
            user_roster[player_position].append(actual_pick)
        else:
            # If main roster is full, add to bench
            user_roster["Bench"].append(actual_pick)
    else:
        user_roster["Bench"].append(actual_pick)
    all_data = all_data[all_data['PLAYER'].str.lower() != actual_pick_lower]
    return True

def main():
    print("Starting the NFL Fantasy Draft Helper!")
    
    first_pick = input("Do you have the first pick? (y/n): ").lower().strip()
    if first_pick == 'y':
        advice = get_advice(drafted_players)  # Initially no players taken yet
        print(f"\nModel's advice for the first pick: {advice}\n")
        actual_pick = input("Enter the name of the player you actually picked: ").strip()
        pick_player(actual_pick)
        drafted_players.append(actual_pick)

    while True:
        players_taken = input("Enter the names of players taken in the last round (comma-separated), or type 'exit' to quit: ").split(",")
        if "exit" in players_taken:
            print("\nExiting Draft Helper. Good luck with your draft, A Train!\n")
            break
        drafted_players.extend([player.strip() for player in players_taken])
        advice = get_advice(drafted_players)
        print(f"\nModel's advice: {advice}\n")
        actual_pick = input("Enter the name of the player you actually picked: ").strip()
        pick_player(actual_pick)
        drafted_players.append(actual_pick)


if __name__ == "__main__":
    main()