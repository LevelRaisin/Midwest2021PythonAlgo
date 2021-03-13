import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

def mkT(x, y, upg = False):
    return [TURRET, [x, y], upg]

def mkW(x, y, upg = False):
    return [WALL, [x, y], upg]

def mkS(x, y, upg = False):
    return [SUPPORT, [x, y], upg]

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.invert = False # whether we are inverted or not
        self.scored_on_locations = []


    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        #self.starter_strategy(game_state)
        self.strategy_v1(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def get_normalized_point(self, point):
        """
        Returns point if not self.invert and inverted point if self.invert
        """
        if self.invert:
            return [27 - point[0], point[1]]
        else:
            return point

    def get_normalized_points(self, locations):
        """
        Takes in list of points
        Returns list of normalized points
        """
        temp = locations
        if self.invert:
            for i in range(len(locations)):
                temp[i] = self.get_normalized_point(locations[i])
            return temp
        else:
            return locations

    def strategy_v1(self, game_state):
        # Defense
        self.build_defenses_v1(game_state)

        # Offense
        mp_available = game_state.get_resource(MP)
        #game_state.attempt_spawn(INTERCEPTOR, [[23, 9], [16, 2]], 1)
        if (game_state.turn_number < 5 and mp_available > 12 and game_state.turn_number < 30) or (mp_available > 16):
            game_state.attempt_spawn(SCOUT, self.get_normalized_point([13, 0]), math.floor(mp_available * 0.25))
            game_state.attempt_spawn(SCOUT, self.get_normalized_point([11, 2]), math.floor(mp_available * 0.75))
        else :
            game_state.attempt_spawn(INTERCEPTOR, self.get_normalized_points([[2, 11], [20, 6]]), 1)



    def build_defenses_v1(self, game_state):
        # TODO: replace turrets + walls every turn
        # TODO: upgrade or add second layer of support

        # [TYPE, point[2], upgrade] - Default not upgraded
        build_order = [mkT(3,13, True), mkT(24, 13, True), mkT(3,11), mkT(21,10), # Main turrets
                        mkW(10,3), mkW(9,4), mkW(8,5), mkW(7,6), mkW(6,7), mkW(5,8), # Thin Wall (Most)
                        mkW(11,3), mkW(12,3), mkW(13,3), # Horizontal bottom
                        mkW(14, 2), mkW(15,3), mkW(16,4), mkW(17,5), mkW(18,6), mkW(19,7), mkW(20,8), mkW(21,9), #Thick Wall
                        mkT(23,12), mkT(20,11), # Thick Corner Reinforcement
                        mkW(4,9), mkW(3,10), mkW(2,11), # Thin Wall (Rest)
                        mkT(2,12), mkT(4,12), # Thin Corner Turret Reinforcement
                        mkS(20,9, True), mkS(19,8, True), # First Support
                        mkW(0,13), mkT(1,12), # Thin Corner completion
                        mkT(25,13), mkW(26,12), mkW(27,13), # Thick Corner completion
                        mkT(19,11), mkW(19,12), mkT(22,13), mkW(21,13), mkW(22,12), mkT(20,10), mkW(23,11), # Thick Corner Full Fortification 1
                        mkW(1,13), mkW(26,13), mkW(0,13, True), mkW(27,13, True), # Wall Upgrade 1
                        mkT(4,13), mkT(3,12), mkT(2,13), # Thin Corner Full Fortification
                        mkW(26,13, True), mkW(1,13, True), # Wall Upgrade 2
                        mkT(21,10), mkT(24,12), # Thick Corner Full Fortification 2
                        mkS(19,9), mkS(18,7), mkS(17,6), mkS(16,5), mkS(15,4), mkS(14,3), mkS(13,2), # Rest Support
                        ] 
        # Removed completely: Wall@[25,12],
        # Not upgraded: Wall@[[0,13], [1,13], [27,13], [26,13], [26,12], [1,12], [25,12], [21,13], [22,12], [19,12]]
        # Not upgraded: All turrets

        for struct in build_order:
            loc = self.get_normalized_point(struct[1])
            game_state.attempt_spawn(struct[0], loc)
            if (struct[2]):
                game_state.attempt_upgrade(loc)

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        #state = json.loads(turn_string)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
