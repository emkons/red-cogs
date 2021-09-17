import random
from enum import Enum

class Team(Enum):
    RED = 0
    BLUE = 1

class GameState(Enum):
    LOBBY = 0
    PLAYING = 1
    ENDED = 2

class CodenamesGame:

    def __init__(self) -> None:
        self.wordlist = None
        self.words = None

        self.team_word_count = None

        self.team_words = None
        self.black_word = None

        self.revealed_words = None

        self.teams = None
        self.spymasters = None

        self.current_team = None
        self.winner = None

        self.import_words()

        self.state = None

    def import_words(self):
        with open('./data/words.txt', 'r') as f:
            self.wordlist = f.readlines()
            print(self.wordlist)


    async def start_game(self):
        self.words = random.sample(self.wordlist, 25)
        red_words = random.sample(self.words, 8)
        blue_words = random.sample([word for word in self.words if word not in red_words], 9)
        self.black_word = random.choice([word for word in self.words if word not in red_words and word not in blue_words])

        self.team_word_count = {
            Team.BLUE: 8,
            Team.RED: 9
        }

        self.team_words = {
            Team.BLUE: blue_words,
            Team.RED: red_words
        }
        
        self.teams = {
            Team.BLUE: [],
            Team.RED: []
        }
        self.spymasters = {
            Team.BLUE: None,
            Team.RED: None
        }

        self.revealed_words = []
        
        self.winner = None
        self.current_team = Team.RED
        self.state = GameState.LOBBY
    
    async def begin_game(self):
        self.state = GameState.PLAYING

    async def join_team(self, player, team: Team) -> None:
        if not player in self.teams[team]:
            self.teams[team].append(player)

        if player in self.teams[(team + 1) % 2]:
            self.teams[(team + 1) % 2].remove(player)

        if player == self.spymasters[(team + 1) % 2]:
            self.spymasters[(team + 1) % 2] = None
    
    async def become_spymaster(self, player, team: Team) -> None:
        if not player in self.teams[team]:
            return
        self.spymasters[team] = player
    
    async def reveal(self, player, word) -> Team:
        if not player in self.teams[self.current_team]:
            return # Wrong team
        
        team = Team.RED if player in self.teams[Team.RED] else Team.BLUE
        
        if not word in self.words:
            return # Unknown word
        
        self.revealed_words.append(word)

        if word in self.team_words[team]:
            if self.check_guessed_all(team):
                return self.end_game(team)
            return # Correct guess
            
        if word in self.team_words[(team + 1) % 2]:
            if self.check_guessed_all((team + 1) % 2):
                return self.end_game((team + 1) % 2)
            return self.end_turn() # Incorrect guess, end turn
        
        if word == self.black_word:
            return self.end_game((team + 1) % 2) # End game with loss
    
    async def check_guessed_all(self, team: Team) -> bool:
        intersect = [x for x in self.revealed_words if x in self.team_words[team]]
        return len(intersect) == self.team_word_count[team]

    async def end_turn(self) -> Team:
        self.current_team = (self.current_team + 1) % 2
        return self.current_team
    
    async def end_game(self, winner_team: Team) -> Team:
        self.state = GameState.ENDED
        return winner_team

