import pandas as pd
import openai
from dotenv import load_dotenv
import os

load_dotenv()

# Set up the API key and organization (if you're part of one)
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = "org-KHL9Qhf8DDW1g72cO8Kb56vR"  # You can comment this out if you're not part of an organization

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

SUPERPROMPT = """
There is a fantasy football draft taking place with 10 teams. Each team will have the following roster: 
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

Using aggregated data from ESPN, CBS, NFL, and Yahoo, which tallies the points each available player got last year according to the pool rules, and also considering general knowledge of the game of football, players and teams up to 2021, we need to make the best possible picks.
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
    
    # Get the top 25 from each dataset
    top_espn = espn_data[espn_data['Position'].isin(valid_positions) & ~espn_data['PLAYER'].str.lower().isin(players_taken_lower)].head(25)
    top_cbs = cbs_data[cbs_data['Position'].isin(valid_positions) & ~cbs_data['PLAYER'].str.lower().isin(players_taken_lower)].head(25)
    top_nfl = nfl_data[nfl_data['Position'].isin(valid_positions) & ~nfl_data['PLAYER'].str.lower().isin(players_taken_lower)].head(25)
    top_yahoo = yahoo_data[yahoo_data['Position'].isin(valid_positions) & ~yahoo_data['PLAYER'].str.lower().isin(players_taken_lower)].head(25)
    
    # Combine these lists
    combined_top_players = pd.concat([top_espn, top_cbs, top_nfl, top_yahoo]).drop_duplicates(subset=['PLAYER'])

    detailed_stats = combined_top_players.to_string(index=False)
    
    additional_context = ""
    if "Bench" in valid_positions:
        additional_context = "\nFor bench selections, consider the need for substitutions in positions like QB, WR, RB, and TE. A diversified bench is important to manage risks during the season."

    user_roster_str = "\n".join([f"{pos}: {', '.join(players) if players else 'None'}" for pos, players in user_roster.items()])

    context_message = SUPERPROMPT + additional_context + "\nThe following players have been taken by others: {}.\n\nYour current roster:\n{}\n\nTop available players based on multiple metrics:\n\n{}".format(
        ", ".join(players_taken),
        user_roster_str,
        detailed_stats
    )

    # Add print statements here to print out the context message:
    print("\n**************************************************************")
    print("Sending the following context to DraftGPT:")
    print(context_message)
    print("**************************************************************\n")

    messages = [
        {"role": "system", "content": "You are DraftGPT, a virtual assistant with expertise in the 2023 NFL Fantasy Draft. Your role is to provide insights and advice on player selections based on the current draft situation."},
        {"role": "user", "content": context_message},
        {"role": "user", "content": "Who should we pick next?"}
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
    all_data = all_data[all_data['PLAYER'] != actual_pick]
    return True

def main():
    print("Starting the NFL Fantasy Draft Helper!")
    
    first_pick = input("Do you have the first pick? (y/n): ").lower().strip()
    if first_pick == 'y':
        advice = get_advice([])  # No players taken yet
        print(f"\nModel's advice for the first pick: {advice}\n")
        actual_pick = input("Enter the name of the player you actually picked: ").strip()
        pick_player(actual_pick)

    while True:
        players_taken = input("Enter the names of players taken in the last round (comma-separated), or type 'exit' to quit: ").split(",")
        if "exit" in players_taken:
            print("\nExiting Draft Helper. Good luck with your draft!\n")
            break
        advice = get_advice(players_taken)
        print(f"\nModel's advice: {advice}\n")
        actual_pick = input("Enter the name of the player you actually picked: ").strip()
        pick_player(actual_pick)

if __name__ == "__main__":
    main()