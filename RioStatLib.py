'''
Intended to parse "decoded" files which would be present on a user's computer

How to use:
- import RioStatLib obviously
- open a Rio stat json file
- convert from json string to obj using json.loads(jsonStr)
- create StatObj with your stat json obj using the following:
	myStats = RioStatLib.StatObj(jsonObj)
- call any of the built-in methods to get some stats

- ex:
	import RioStatLib
	import json
	with open("path/to/RioStatFile.json", "r") as jsonStr:
		jsonObj = json.loads(jsonStr)
		myStats = RioStatLib.StatObj(jsonObj)
		homeTeamOPS = myStats.ops(0)
		awayTeamSLG = myStats.slg(1)
		booERA = myStats.era(0, 4) # Boo in this example is the 4th character on the home team

Team args:
- arg == 0 means team0 which is the away team (home team for Project Rio pre 1.9.2)
- arg == 1 means team1 which is the home team (away team for Project Rio 1.9.2 and later)
- arg == -1 or no arg provided means both teams (if function allows) (none currently accept this, but it might be added in the future)

Roster args:
- arg == 0 -> 8 for each of the 9 roster spots
- arg == -1 or no arg provided means all characters on that team (if function allows)

# For Project Rio versions pre 1.9.2
# teamNum: 0 == home team, 1 == away team
# For Project Rio versions 1.9.2 and later
# teamNum: 0 == home team, 1 == away team
# rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
'''


# create stat obj
class StatObj:
    def __init__(this, statJson: dict):
        this.statJson = statJson

        # Loops through all envents
        # and finds events with specific plays 
        def eventsFilter():
            gameEvents = {
                'Bunt': set(),
                'SacFly': set(),
                'Strikeout': set(),
                'Ground Ball Double Play': set(),
                'Error - Chem': set(),
                'Error - Input': set(),
                'Walk HBP': set(),
                'Walk BB': set(),
                'Single': set(),
                'Double': set(),
                'Triple': set(),
                'HR': set(),
                'RBI': set(),
                'Steal': set(),
                'Star Hits': set(),
                'First Pitch of AB': set(),
                'Full Count Pitch': set(),
                'Star Pitch': set(),
                'Bobble': set(),
                'Five Star Dinger': set(),
                'Sliding Catch': set(),
                'Wall Jump': set(),
                'First Fielder Position': {
                    "P": set(),
                    "C": set(),
                    "1B": set(),
                    "2B": set(),
                    "3B": set(),
                    "SS": set(),
                    "LF": set(),
                    "CF": set(),
                    "RF": set(),
                },
                'Manual Character Selection': set(),
                'Inning': {},
                'Balls': {
                    0: set(),
                    1: set(),
                    2: set(),
                    3: set(),
                },
                'Strikes': {
                    0: set(),
                    1: set(),
                    2: set()
                },
                'Half Inning': {
                    0: set(),
                    1: set()
                },
                'Chem On Base':{
                    0: set(),
                    1: set(),
                    2: set(),
                    3: set()
                },
                'Runner On Base': {
                    0: set(),  # In this case 0 means no runners on base
                    1: set(),
                    2: set(),
                    3: set()
                },
                'Outs In Inning':{
                    0: set(),
                    1: set(),
                    2: set()
                }
            }

            characterEvents = {}
            for character in statJson["Character Game Stats"].keys():
                characterEvents[statJson["Character Game Stats"][character]['CharID']] = {'AtBat': set(),
                                                                                                  'Pitching': set(),
                                                                                                  'Fielding': set()}
            for i in range(1, this.statJson['Innings Played']+1):
                gameEvents['Inning'][i] = set()

            for event in this.statJson['Events']:
                eventNum = event["Event Num"]
                batting_team = event['Half Inning']
                fielding_team = abs(event['Half Inning']-1)

                batter = this.characterName(batting_team, event["Batter Roster Loc"])
                pitcher = this.characterName(fielding_team, event["Pitcher Roster Loc"])

                characterEvents[batter]['AtBat'].add(eventNum)
                characterEvents[pitcher]['Pitching'].add(eventNum)
                
                gameEvents['Outs In Inning'][event['Outs']].add(eventNum)
                gameEvents['Chem On Base'][event['Chemistry Links on Base']].add(eventNum)
                gameEvents['Strikes'][event['Strikes']].add(eventNum)
                gameEvents['Balls'][event['Balls']].add(eventNum)
                gameEvents['Inning'][event['Inning']].add(eventNum)

                gameEvents['Half Inning'][event['Half Inning']].add(eventNum)

                if event["Result of AB"] in gameEvents.keys():
                    gameEvents[event["Result of AB"]].add(eventNum)

                if event['RBI'] > 0:
                    gameEvents['RBI'].add(eventNum)

                runner_keys = {'Runner 1B': 1, 
                               'Runner 2B': 2, 
                               'Runner 3B': 3}
                
                no_runners = all(value not in event.keys() for value in runner_keys)
                if no_runners:
                    gameEvents['Runner On Base'][0].add(eventNum)
                else:
                    for key, storage_key in runner_keys.items(): 
                        if key not in event.keys():
                            continue
                        gameEvents['Runner On Base'][storage_key].add(eventNum)
                        if event[key]['Steal'] == 'None':
                            continue
                        gameEvents['Steal'].add(eventNum)

                if 'Pitch' not in event.keys():
                    continue

                if ((event["Result of AB"] in ['Single', 'Double', 'Triple', 'HR'])
                & ('Contact' in event['Pitch'].keys())
                & (event['Pitch']['Type of Swing'] == 'Star')):
                    gameEvents['Star Hits'].add(eventNum)

                if (event['Balls'] == 0) & (event['Strikes'] == 0):
                    gameEvents['First Pitch of AB'].add(eventNum)

                if (event['Balls'] == 3) & (event['Strikes'] == 2):
                    gameEvents['Full Count Pitch'].add(eventNum)

                if event['Pitch']['Star Pitch'] == 1:
                    gameEvents['Star Pitch'].add(eventNum)

                if 'Contact' not in event['Pitch'].keys():
                    continue

                if event['Pitch']['Contact']["Star Swing Five-Star"] == 1:
                    gameEvents['Five Star Dinger'].add(eventNum)

                if 'First Fielder' not in event['Pitch']['Contact'].keys():
                    continue

                fielding_data = event['Pitch']['Contact']['First Fielder']
                characterEvents[fielding_data["Fielder Character"]]['Fielding'].add(eventNum)

                if fielding_data['Fielder Bobble'] != 'None':
                    gameEvents['Bobble'].add(eventNum)

                if fielding_data['Fielder Action'] == 'Sliding':
                    gameEvents['Sliding Catch'].add(eventNum)

                if fielding_data['Fielder Action'] == 'Walljump':
                    gameEvents['Wall Jump'].add(eventNum)

                if fielding_data['Fielder Position'] in gameEvents['First Fielder Position'].keys():
                    gameEvents['First Fielder Position'][event['Pitch']['Contact']['First Fielder']['Fielder Position']].add(eventNum)

                if fielding_data['Fielder Manual Selected'] != 'No Selected Char':
                    gameEvents['Manual Character Selection'].add(eventNum)

            return gameEvents, characterEvents
        
        this.gameEventsDict, this.characterEventsDict = eventsFilter()

    def gameID(this):
        # returns it in int form
        return int(this.statJson["GameID"].replace(',', ''), 16)

    # should look to convert to unix or some other standard date fmt
    def startDate(this):
        return this.statJson["Date - Start"]
    
    def endDate(this):
        return this.statJson["Date - End"]

    def version(this):
        if "Version" in this.statJson.keys():
            return this.statJson["Version"]

        return "Pre 0.1.7"

    def isRanked(this):
        # tells if a game was a ranked game or not
        rankedStatus = this.statJson["Ranked"]
        return rankedStatus == 1
        

    def stadium(this):
        # returns the stadium that was played on
        return this.statJson["StadiumID"]

    def player(this, teamNum: int):
        # returns name of player
        # For Project Rio versions pre 1.9.2
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        VERSION_LIST_HOME_AWAY_FLIPPED = ["Pre 0.1.7", "0.1.7a", "0.1.8", "0.1.9", "1.9.1"]

        if this.version() in VERSION_LIST_HOME_AWAY_FLIPPED:
            if teamNum == 0:
                return this.statJson["Home Player"]
            elif teamNum == 1:
                return this.statJson["Away Player"]
            else:
                this.__errorCheck_teamNum(teamNum)

        if teamNum == 0:
            return this.statJson["Away Player"]
        elif teamNum == 1:
            return this.statJson["Home Player"]
        else:
            this.__errorCheck_teamNum(teamNum)


    def score(this, teamNum: int):
        # returns final score of said team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        if teamNum == 0:
            return this.statJson["Home Score"]
        elif teamNum == 1:
            return this.statJson["Away Score"]
        else:
            this.__errorCheck_teamNum(teamNum)

    def inningsTotal(this):
        # returns how many innings were selected for the game
        return this.statJson["Innings Selected"]

    def inningsPlayed(this):
        # returns how many innings were played in the game
        return this.statJson["Innings Played"]

    def isMercy(this):
        # returns if the game ended in a mercy or not
        if this.inningsTotal() - this.inningsPlayed() >= 1 and not this.wasQuit():
            return True
        else:
            return False

    def wasQuit(this):
        # returns if the same was quit out early
        if this.statJson["Quitter Team"] == "":
            return False
        else:
            return True

    def quitter(this):
        # returns the name of the quitter if the game was quit. empty string if no quitter
        return this.statJson["Quitter Team"]

    def ping(this):
        # returns average ping of the game
        return this.statJson["Average Ping"]

    def lagspikes(this):
        # returns number of lag spikes in a game
        return this.statJson["Lag Spikes"]

    def characterGameStats(this):
        # returns the full dict of character game stats as shown in the stat file
        return this.statJson["Character Game Stats"]

    def isSuperstarGame(this):
        # returns if the game has any superstar characters in it
        isStarred = False
        charStats = this.characterGameStats()
        for character in charStats:
            if charStats[character]["Superstar"] == 1:
                isStarred = True
        return isStarred

    # TODO: function that tells if no stars, stars, or mixed stars?

    # character stats
    # (this, teamNum: int, rosterNum: int):

    def getTeamString(this, teamNum: int, rosterNum: int):
        this.__errorCheck_teamNum(teamNum)
        this.__errorCheck_rosterNum(rosterNum)

        VERSION_LIST_OLD_TEAM_STRUCTURE = ["Pre 0.1.7", "0.1.7a", "0.1.8", "0.1.9", "1.9.1", "1.9.2", "1.9.3", "1.9.4"]
        if this.version() in VERSION_LIST_OLD_TEAM_STRUCTURE:
            return f"Team {teamNum} Roster {rosterNum}"

        #Newer Version Format
        teamStr = "Away" if teamNum == 0 else "Home"
        return f"{teamStr} Roster {rosterNum}"

    def characterName(this, teamNum: int, rosterNum: int = -1):
        # returns name of specified character
        # if no roster spot is provided, returns a list of characters on a given team
        # teamNum: 0 == home team, 1 == away team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        this.__errorCheck_teamNum(teamNum)
        this.__errorCheck_rosterNum(rosterNum)
        if rosterNum == -1:
            charList = []
            for x in range(0, 9):
                charList.append(this.statJson["Character Game Stats"][this.getTeamString(teamNum, x)]["CharID"])
            return charList
        else:
            return this.statJson["Character Game Stats"][this.getTeamString(teamNum, rosterNum)]["CharID"]

    def isStarred(this, teamNum: int, rosterNum: int = -1):
        # returns if a character is starred
        # if no arg, returns if any character on the team is starred
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        this.__errorCheck_teamNum(teamNum)
        this.__errorCheck_rosterNum(rosterNum)
        if rosterNum == -1:
            for x in range(0, 9):
                if this.statJson["Character Game Stats"][this.getTeamString(teamNum, x)]["Superstar"] == 1:
                    return True
        else:
            if this.statJson["Character Game Stats"][this.getTeamString(teamNum, rosterNum)]["Superstar"] == 1:
                return True
            else:
                return False

    def captain(this, teamNum: int):
        # returns name of character who is the captain
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        this.__errorCheck_teamNum(teamNum)
        captain = ""
        for character in this.characterGameStats():
            if character["Captain"] == 1 and int(character["Team"]) == teamNum:
                captain = character["CharID"]
        return captain

    def offensiveStats(this, teamNum: int, rosterNum: int = -1):
        # grabs offensive stats of a character as seen in the stat json
        # if no roster provided, returns a list of all character's offensive stats
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        this.__errorCheck_teamNum(teamNum)
        this.__errorCheck_rosterNum(rosterNum)
        if rosterNum == -1:
            oStatList = []
            for x in range(0, 9):
                oStatList.append(this.statJson["Character Game Stats"][this.getTeamString(teamNum, x)]["Offensive Stats"])
            return oStatList
        else:
            return this.statJson["Character Game Stats"][this.getTeamString(teamNum, rosterNum)]["Offensive Stats"]

    def defensiveStats(this, teamNum: int, rosterNum: int = -1):
        # grabs defensive stats of a character as seen in the stat json
        # if no roster provided, returns a list of all character's defensive stats
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        this.__errorCheck_teamNum(teamNum)
        this.__errorCheck_rosterNum(rosterNum)
        if rosterNum == -1:
            dStatList = []
            for x in range(0, 9):
                dStatList.append(this.statJson["Character Game Stats"][this.getTeamString(teamNum, x)]["Defensive Stats"])
            return dStatList
        else:
            return this.statJson["Character Game Stats"][this.getTeamString(teamNum, rosterNum)]["Defensive Stats"]

    def fieldingHand(this, teamNum: int, rosterNum: int):
        # returns fielding handedness of character
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: 0 -> 8 for each of the 9 roster spots
        this.__errorCheck_teamNum(teamNum)
        this.__errorCheck_rosterNum2(rosterNum)
        return this.statJson["Character Game Stats"][this.getTeamString(teamNum, rosterNum)]["Fielding Hand"]

    def battingHand(this, teamNum: int, rosterNum: int):
        # returns batting handedness of character
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: 0 -> 8 for each of the 9 roster spots
        this.__errorCheck_teamNum(teamNum)
        this.__errorCheck_rosterNum2(rosterNum)
        return this.statJson["Character Game Stats"][this.getTeamString(teamNum, rosterNum)]["Batting Hand"]

    # defensive stats
    def era(this, teamNum: int, rosterNum: int = -1):
        # tells the era of a character
        # if no character given, returns era of that team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        return 9 * float(this.runsAllowed(teamNum, rosterNum)) / this.inningsPitched(teamNum, rosterNum)

    def battersFaced(this, teamNum: int, rosterNum: int = -1):
        # tells how many batters were faced by character
        # if no character given, returns batters faced by that team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Batters Faced"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Batters Faced"]

    def runsAllowed(this, teamNum: int, rosterNum: int = -1):
        # tells how many runs a character allowed when pitching
        # if no character given, returns runs allowed by that team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Runs Allowed"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Runs Allowed"]

    def battersWalked(this, teamNum: int, rosterNum: int = -1):
        # tells how many walks a character allowed when pitching
        # if no character given, returns walks by that team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        return this.battersWalkedBallFour(teamNum, rosterNum) + this.battersHitByPitch(teamNum, rosterNum)

    def battersWalkedBallFour(this, teamNum: int, rosterNum: int = -1):
        # returns how many times a character has walked a batter via 4 balls
        # if no character given, returns how many times the team walked via 4 balls
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Batters Walked"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Batters Walked"]

    def battersHitByPitch(this, teamNum: int, rosterNum: int = -1):
        # returns how many times a character walked a batter by hitting them by a pitch
        # if no character given, returns walked via HBP for the team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Batters Hit"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Batters Hit"]

    def hitsAllowed(this, teamNum: int, rosterNum: int = -1):
        # returns how many hits a character allowed as pitcher
        # if no character given, returns how many hits a team allowed
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Hits Allowed"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Hits Allowed"]

    def homerunsAllowed(this, teamNum: int, rosterNum: int = -1):
        # returns how many homeruns a character allowed as pitcher
        # if no character given, returns how many homeruns a team allowed
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["HRs Allowed"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["HRs Allowed"]

    def pitchesThrown(this, teamNum: int, rosterNum: int = -1):
        # returns how many pitches a character threw
        # if no character given, returns how many pitches a team threw
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Pitches Thrown"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Pitches Thrown"]

    def stamina(this, teamNum: int, rosterNum: int = -1):
        # returns final pitching stamina of a pitcher
        # if no character given, returns total stamina of a team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Stamina"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Stamina"]
        
    def wasPitcher(this, teamNum: int, rosterNum: int):
        # returns if a character was a pitcher
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: 0 -> 8 for each of the 9 roster spots
        this.__errorCheck_rosterNum2(rosterNum)
        if this.defensiveStats(teamNum, rosterNum)["Was Pitcher"] == 1:
            return True
        else:
            return False

    def strikeoutsPitched(this, teamNum: int, rosterNum: int = -1):
        # returns how many strikeouts a character pitched
        # if no character given, returns how mnany strikeouts a team pitched
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Strikeouts"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Strikeouts"]

    def starPitchesThrown(this, teamNum: int, rosterNum: int = -1):
        # returns how many star pitches a character threw
        # if no character given, returns how many star pitches a team threw
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Star Pitches Thrown"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Star Pitches Thrown"]

    def bigPlays(this, teamNum: int, rosterNum: int = -1):
        # returns how many big plays a character had
        # if no character given, returns how many big plays a team had
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Big Plays"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Big Plays"]

    def outsPitched(this, teamNum: int, rosterNum: int = -1):
        # returns how many outs a character was pitching for
        # if no character given, returns how many outs a team pitched for
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.defensiveStats(teamNum, x)["Outs Pitched"]
            return total
        else:
            return this.defensiveStats(teamNum, rosterNum)["Outs Pitched"]

    def inningsPitched(this, teamNum: int, rosterNum: int = -1):
        # returns how many innings a character was pitching for
        # if no character given, returns how many innings a team pitched for
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        return float(this.outsPitched(teamNum, rosterNum)) / 3

    def pitchesPerPosition(this, teamNum: int, rosterNum: int):
        # returns a dict which tracks how many pitches a character was at a position for
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: 0 -> 8 for each of the 9 roster spots
        this.__errorCheck_rosterNum2(rosterNum)
        return this.defensiveStats(teamNum, rosterNum)["Pitches Per Position"][0]

    def outsPerPosition(this, teamNum: int, rosterNum: int):
        # returns a dict which tracks how many outs a character was at a position for
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: 0 -> 8 for each of the 9 roster spots
        this.__errorCheck_rosterNum2(rosterNum)
        return this.defensiveStats(teamNum, rosterNum)["Outs Per Position"][0]

    # offensive stats

    def atBats(this, teamNum: int, rosterNum: int = -1):
        # returns how many at bats a character had
        # if no character given, returns how many at bats a team had
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["At Bats"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["At Bats"]

    def hits(this, teamNum: int, rosterNum: int = -1):
        # returns how many hits a character had
        # if no character given, returns how many hits a team had
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Hits"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Hits"]

    def singles(this, teamNum: int, rosterNum: int = -1):
        # returns how many singles a character had
        # if no character given, returns how many singles a team had
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Singles"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Singles"]

    def doubles(this, teamNum: int, rosterNum: int = -1):
        # returns how many doubles a character had
        # if no character given, returns how many doubles a team had
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Doubles"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Doubles"]

    def triples(this, teamNum: int, rosterNum: int = -1):
        # returns how many triples a character had
        # if no character given, returns how many triples a teams had
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Triples"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Triples"]

    def homeruns(this, teamNum: int, rosterNum: int = -1):
        # returns how many homeruns a character had
        # if no character given, returns how many homeruns a team had
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Homeruns"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Homeruns"]

    def buntsLanded(this, teamNum: int, rosterNum: int = -1):
        # returns how many successful bunts a character had
        # if no character given, returns how many successful bunts a team had
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Successful Bunts"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Successful Bunts"]

    def sacFlys(this, teamNum: int, rosterNum: int = -1):
        # returns how many sac flys a character had
        # if no character given, returns how many sac flys a team had
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Sac Flys"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Sac Flys"]

    def strikeouts(this, teamNum: int, rosterNum: int = -1):
        # returns how many times a character struck out when batting
        # if no character given, returns how many times a team struck out when batting
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Strikeouts"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Strikeouts"]

    def walks(this, teamNum: int, rosterNum: int):
        # returns how many times a character was walked when batting
        # if no character given, returns how many times a team was walked when batting
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        return this.walksBallFour(teamNum, rosterNum) + this.walksHitByPitch(teamNum, rosterNum)

    def walksBallFour(this, teamNum: int, rosterNum: int = -1):
        # returns how many times a character was walked via 4 balls when batting
        # if no character given, returns how many times a team was walked via 4 balls when batting
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Walks (4 Balls)"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Walks (4 Balls)"]

    def walksHitByPitch(this, teamNum: int, rosterNum: int = -1):
        # returns how many times a character was walked via hit by pitch when batting
        # if no character given, returns how many times a team was walked via hit by pitch when batting
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Walks (Hit)"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Walks (Hit)"]

    def rbi(this, teamNum: int, rosterNum: int = -1):
        # returns how many RBI's a character had
        # if no character given, returns how many RBI's a team had
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["RBI"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["RBI"]

    def basesStolen(this, teamNum: int, rosterNum: int = -1):
        # returns how many times a character successfully stole a base
        # if no character given, returns how many times a team successfully stole a base
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Bases Stolen"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Bases Stolen"]

    def starHitsUsed(this, teamNum: int, rosterNum: int = -1):
        # returns how many star hits a character used
        # if no character given, returns how many star hits a team used
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        if rosterNum == -1:
            total = 0
            for x in range(0, 9):
                total += this.offensiveStats(teamNum, x)["Star Hits"]
            return total
        else:
            return this.offensiveStats(teamNum, rosterNum)["Star Hits"]

    # complicated stats

    def battingAvg(this, teamNum: int, rosterNum: int = -1):
        # returns the batting average of a character
        # if no character given, returns the batting average of a team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        nAtBats = this.atBats(teamNum, rosterNum)
        nHits = this.hits(teamNum, rosterNum)
        return float(nHits) / float(nAtBats)

    def obp(this, teamNum: int, rosterNum: int = -1):
        # returns the on base percentage of a character
        # if no character given, returns the on base percentage of a team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        nAtBats = this.atBats(teamNum, rosterNum)
        nHits = this.hits(teamNum, rosterNum)
        nWalks = this.walks(teamNum, rosterNum)
        return float(nHits + nWalks) / float(nAtBats)

    def slg(this, teamNum: int, rosterNum: int = -1):
        # returns the SLG of a character
        # if no character given, returns the SLG of a team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        nAtBats = this.atBats(teamNum, rosterNum)
        nSingles = this.singles(teamNum, rosterNum)
        nDoubles = this.doubles(teamNum, rosterNum)
        nTriples = this.triples(teamNum, rosterNum)
        nHomeruns = this.homeruns(teamNum, rosterNum)
        nWalks = this.walks(teamNum, rosterNum)
        return float(nSingles + nDoubles * 2 + nTriples * 3 + nHomeruns * 4) / float(nAtBats - nWalks)

    def ops(this, teamNum: int, rosterNum: int = -1):
        # returns the OPS of a character
        # if no character given, returns the OPS of a team
        # For Project Rio versions pre 1.9.2
        # teamNum: 0 == home team, 1 == away team
        # For Project Rio versions 1.9.2 and later
        # teamNum: 0 == away team, 1 == home team
        # rosterNum: optional (no arg == all characters on team), 0 -> 8 for each of the 9 roster spots
        return this.obp(teamNum, rosterNum) + this.slg(teamNum, rosterNum)

    # event stats
    # these all probably involve looping through all the events
    def events(this):
        # returns the list of events in a game
        return this.statJson['Events']

    def eventFinal(this):
        # returns the number of the last event
        eventList = this.events()
        return eventList[-1]["Event Num"]

    def eventByNum(this, eventNum: int):
        # returns a single event specified by its number
        # if event is less than 0 or greater than the highest event, returns the last event
        eventList = this.events()
        finalEvent = this.eventFinal()
        if eventNum < 0 or eventNum > finalEvent:
            return finalEvent
        for event in eventList:
            if event["Event Num"] == eventNum:
                return event
        return {}  # empty dict if no matching event found, which should be impossible anyway

    # TODO:aa
    # - add method for getting every stat from an event dict

    def successfulBuntEvents(this):
        #returns a set of events of successful bunts
        return this.gameEventsDict['Bunt']
    
    def sacFlyEvents(this):
        #returns a set of events of sac flys
        return this.gameEventsDict['SacFly']
    
    def strikeoutEvents(this):
        # returns a set of events where the result is a strikeout
        return this.gameEventsDict['Strikeout']
    
    def groundBallDoublePlayEvents(this):
        # returns a set of events where the result is a ground ball double play
        return this.gameEventsDict['Ground Ball Double Play']
    
    def chemErrorEvents(this):
        # returns a set of events where the result is a chem error
        return this.gameEventsDict['Error - Chem']
    
    def inputErrorEvents(this):
        # returns a set of events where the result is a input error
        return this.gameEventsDict['Error - Input']
    
    def walkEvents(this, include_hbp=True, include_bb=True):
        # returns a set of events where the batter recorded a type of hit
        # can be used to reutrn just walks or just hbp
        # defaults to returning both
        if include_hbp & include_bb:
            return this.gameEventsDict['Walk HBP'] | this.resultOfAtBatEvents['Walk BB']
        if include_hbp:
            return this.gameEventsDict['Walk HBP']
        if include_bb:
            return this.gameEventsDict['Walk BB']
        else:
            return set()

    def hitEvents(this, numberOfBases=0):
        # returns a set of events where the batter recorded a type of hit
        # can return singles, doubles, triples, HRs or all hits
        # returns all hits if numberOfBases is not 1-4
        if numberOfBases == 1:
            return this.gameEventsDict['Single']
        elif numberOfBases == 2:
            return this.gameEventsDict['Double']
        elif numberOfBases == 3:
            return this.gameEventsDict['Triple']
        elif numberOfBases == 4:
            return this.gameEventsDict['HR']
        else:
            return this.gameEventsDict['Single'] | this.gameEventsDict['Double'] | this.gameEventsDict['Triple'] | this.gameEventsDict['HR']
    
    def rbiEvents(this):
        # returns a set of events where an RBI happened
        return this.gameEventsDict['RBI']
    
    def stealEvents(this):
        # returns a set of events where an steal happened
        # types of steals: None, Ready, Normal, Perfect
        return this.gameEventsDict['Steal']
    
    def starHitEvents(this):
        # returns a set of events where a star hit lands for a hit
        return this.gameEventsDict['Star Hit']
    
    def startOfAtBatEvents(this):
        # returns a set of events for the first pitch of an AB
        return this.gameEventsDict['First Pitch of AB']
    
    def fullCountPitchEvents(this):
        # returns a set of events for the first pitch of an AB
        return this.gameEventsDict['Full Count Pitch']
    
    def starPitchEvents(this):
        # returns a set of events where a star pitch is used
        return this.gameEventsDict['Star Pitch']
    
    def bobbleEvents(this):
        # returns a set of events where any kind of bobble occurs
        # Bobble types: "None" "Slide/stun lock" "Fumble", "Bobble", 
        # "Fireball", "Garlic knockout" "None"
        return this.gameEventsDict['Bobble']
    
    def fiveStarDingerEvents(this):
        # returns a set of events where a five star dinger occurs
        return this.gameEventsDict['Five Star Dinger']
    
    def slidingCatchEvents(this):
        # returns a set of events where the fielder made a sliding catch
        # not to be confused with the character ability sliding catch
        return this.gameEventsDict['Sliding Catch']
    
    def wallJumpEvents(this):
        # returns a set of events where the fielder made a wall jump
        return this.gameEventsDict['Wall Jump']
    
    def firstFielderPositionEvents(this, location_abbreviation):
        # returns a set of events where the first fielder on the ball
        # is the one provided in the function argument
        if location_abbreviation not in this.gameEventsDict['First Fielder Position'].keys():
            raise Exception(f'Invalid roster arg {location_abbreviation}. Function only location abbreviations {this.gameEventsDict["First Fielder Position"].keys()}')
        return this.gameEventsDict['First Fielder Position'][location_abbreviation]
    
    def manualCharacterSelectionEvents(this):
        # returns a set of events where a fielder was manually selected
        return this.gameEventsDict['Manual Character Selection']
    
    def runnerOnBaseEvents(this, baseNums: list):
        # returns a set of events where runners were on the specified bases
        # the input baseNums is a list of three numbers -3 to 3
        # the numbers indicate what base the runner is to appear on
        # if the base number is positive, then the returned events will all have a runner
        # on that base.
        # if the base number is negative, then the returned events will not care whether a runner
        # appears on that base or not
        # if the base number is not provided, then the returned events will not have a runner 
        # on that base.

        for num in baseNums:
            this.__errorCheck_baseNum(num)
        
        if len(baseNums) > 3:
            raise Exception('Too many baseNums provided. runnerOnBaseEvents accepts at most 3 bases')

        if baseNums == [0]:
            return this.gameEventsDict['Runner On Base']['None']

        runner_on_base = this.gameEventsDict['Runner On Base']

        exclude_bases = [1,2,3]
        required_bases = []
        optional_bases = []
        for i in baseNums:
            if abs(i) in exclude_bases:
                exclude_bases.remove(abs(i))
            if i > 0:
                required_bases.append(i)
            else:
                optional_bases.append(abs(i))

        if required_bases and (0 in optional_bases):
            raise Exception(f'The argument 0 may only be provided alongside optional arguments or itself')

        if required_bases:
            print('required_bases')
            result = set(range(this.eventFinal()+1))
            for base in required_bases:
                result.intersection_update(runner_on_base[base])
        else:
            result = set()

        if not result:
            for base in optional_bases:
                result = result.union(runner_on_base[base])

        if exclude_bases:
            for base in exclude_bases:
                result.difference_update(runner_on_base[base])

        return result
        

    def inningEvents(this, inningNum: int):
        inningNum = int(inningNum)
        # returns a set of events that occurered in the inning input
        if inningNum not in this.gameEventsDict['Inning'].keys():
            return set()
        return this.gameEventsDict['Inning'][inningNum]

    def halfInningEvents(this, halfInningNum: int):
          this.__errorCheck_halfInningNum(halfInningNum)
          return this.gameEventsDict['Half Inning'][halfInningNum]
        
    def characterAtBatEvents(this, char_id):
        # returns a set of events where the input character was at bat
        # returns an empty set if the character was not in the game
        # rather than raising an error
        if char_id not in this.characterEventsDict.keys():
            return set()
        return this.characterEventsDict[char_id]['AtBat']
    
    def characterPitchingEvents(this, char_id):
        # returns a set of events where the input character was pitching
        # returns an empty set if the character was not in the game
        # rather than raising an error
        if char_id not in this.characterEventsDict.keys():
            return set()
        return this.characterEventsDict[char_id]['Pitching']
    
    def characterFieldingEvents(this, char_id):
        # returns a set of events where the input character is the first fielder
        # returns an empty set if the character was not in the game
        # rather than raising an error
        if char_id not in this.characterEventsDict.keys():
            return set()
        return this.characterEventsDict[char_id]['Fielding']
    
    def positionFieldingEvents(this, fielderPos):
        # returns a set of events where the input fielding pos is the first fielder
        # raises an error when the imput fielding pos is not valid
        this.__errorCheck_fielder_pos(fielderPos)
        return this.gameEventsDict['First Fielder Position'][fielderPos.upper()]
    
    def inningOfEvent(this, eventNum):
        # returns the ininng from a specified event
        this.__errorCheck_eventNum(eventNum)
        eventList = this.events()
        return eventList[eventNum]["Inning"]
    
    def halfInningOfEvent(this, eventNum):
        # returns the half ininng from a specified event
        this.__errorCheck_eventNum(eventNum)
        eventList = this.events()
        return eventList[eventNum]["Half Inning"]
    
    def strikesOfEvent(this, eventNum):
        # returns the strikes from a specified event
        this.__errorCheck_eventNum(eventNum)
        eventList = this.events()
        return eventList[eventNum]["Strikes"]
    
    def ballsOfEvent(this, eventNum):
        # returns the ininng from a specified event
        this.__errorCheck_eventNum(eventNum)
        eventList = this.events()
        return eventList[eventNum]["Balls"]
    
    def outsOfEvent(this, eventNum):
        # returns the ininng from a specified event
        this.__errorCheck_eventNum(eventNum)
        eventList = this.events()
        return eventList[eventNum]["Outs"]
    
    def runnersOfEvent(this, eventNum):
         # returns the ininng from a specified event
        this.__errorCheck_eventNum(eventNum)
        eventList = this.events()
        return set(eventList[eventNum].keys()).intersection(['Runner 1B', 'Runner 2B', 'Runner 3B'])
    
    # manual exception handling stuff
    def __errorCheck_teamNum(this, teamNum: int):
        # tells if the teamNum is invalid
        if teamNum != 0 and teamNum != 1:
            raise Exception(
                f'Invalid team arg {teamNum}. Function only accepts team args of 0 (home team) or 1 (away team).')

    def __errorCheck_rosterNum(this, rosterNum: int):
        # tells if rosterNum is invalid. allows -1 arg
        if rosterNum < -1 or rosterNum > 8:
            raise Exception(f'Invalid roster arg {rosterNum}. Function only accepts roster args of 0 to 8.')

    def __errorCheck_rosterNum2(this, rosterNum: int):
        # tells if rosterNum is invalid. does not allow -1 arg
        if rosterNum < 0 or rosterNum > 8:
            raise Exception(f'Invalid roster arg {rosterNum}. Function only accepts roster args of 0 to 8.')

    def __errorCheck_eventNum(this, eventNum: int):
        # tells if eventNum is outside of events in the game
        if eventNum < 0 or eventNum > this.eventFinal():
            raise Exception(f'Invalid event num {eventNum}. Event num is outside of events in this game')

    def __errorCheck_fielder_pos(this, fielderPos):
        # tells if fielderPos is valid
         if fielderPos.upper() not in ['P','C','1B','2B','3B','SS','LF','CF','RF']:
            raise Exception(f"Invalid fielder position {fielderPos}. Function accepts {['p','c','1b','2b','3b','ss','lf','cf','rf']}")

    def __errorCheck_baseNum(this, baseNum: int):
         # tells if baseNum is valid representing 1st, 2nd and 3rd base
        if abs(baseNum) not in [0,1,2,3]:
            raise Exception(f'Invalid base num {baseNum}. Function only accepts base numbers of -3 to 3.')

    def __errorCheck_halfInningNum(this, halfInningNum: int):
        if halfInningNum not in [0,1]:
            raise Exception(f'Invalid Half Inning num {halfInningNum}. Function only accepts base numbers of 0 or 1.')

    '''
    "Event Num": 50,
      "Inning": 3,
      "Half Inning": 1,
      "Away Score": 0,
      "Home Score": 1,
      "Balls": 0,
      "Strikes": 1,
      "Outs": 1,
      "Star Chance": 0,
      "Away Stars": 0,
      "Home Stars": 0,
      "Pitcher Stamina": 9,
      "Chemistry Links on Base": 0,
      "Pitcher Roster Loc": 8,
      "Batter Roster Loc": 2,
      "Catcher Roster Loc": 4,
      "RBI": 0,
      "Num Outs During Play": 0,
      "Result of AB": "None",
      "Runner Batter": {
        "Runner Roster Loc": 2,
        "Runner Char Id": "Waluigi",
        "Runner Initial Base": 0,
        "Out Type": "None",
        "Out Location": 0,
        "Steal": "None",
        "Runner Result Base": 0
      },
      "Runner 1B": {
        "Runner Roster Loc": 1,
        "Runner Char Id": "Luigi",
        "Runner Initial Base": 1,
        "Out Type": "None",
        "Out Location": 0,
        "Steal": "None",
        "Runner Result Base": 1
      },
      "Runner 2B": {
        "Runner Roster Loc": 0,
        "Runner Char Id": "Baby Mario",
        "Runner Initial Base": 2,
        "Out Type": "None",
        "Out Location": 0,
        "Steal": "None",
        "Runner Result Base": 2
      },
      "Pitch": {
        "Pitcher Team Id": 0,
        "Pitcher Char Id": "Dixie",
        "Pitch Type": "Charge",
        "Charge Type": "Slider",
        "Star Pitch": 0,
        "Pitch Speed": 162,
        "Ball Position - Strikezone": -0.260153,
        "In Strikezone": 1,
        "Bat Contact Pos - X": -0.134028,
        "Bat Contact Pos - Z": 1.5,
        "DB": 0,
        "Type of Swing": "Slap",
        "Contact": {
          "Type of Contact":"Nice - Right",
          "Charge Power Up": 0,
          "Charge Power Down": 0,
          "Star Swing Five-Star": 0,
          "Input Direction - Push/Pull": "Towards Batter",
          "Input Direction - Stick": "Right",
          "Frame of Swing Upon Contact": "2",
          "Ball Power": "139",
          "Vert Angle": "158",
          "Horiz Angle": "1,722",
          "Contact Absolute": 109.703,
          "Contact Quality": 0.988479,
          "RNG1": "4,552",
          "RNG2": "5,350",
          "RNG3": "183",
          "Ball Velocity - X": -0.592068,
          "Ball Velocity - Y": 0.166802,
          "Ball Velocity - Z": 0.323508,
          "Ball Contact Pos - X": -0.216502,
          "Ball Contact Pos - Z": 1.5,
          "Ball Landing Position - X": -45.4675,
          "Ball Landing Position - Y": 0.176705,
          "Ball Landing Position - Z": 17.4371,
          "Ball Max Height": 4.23982,
          "Ball Hang Time": "89",
          "Contact Result - Primary": "Foul",
          "Contact Result - Secondary": "Foul"
        }
      }
    },
    '''
