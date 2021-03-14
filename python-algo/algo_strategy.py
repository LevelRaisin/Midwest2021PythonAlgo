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
        self.attack = False # whether we are attacking or not
        self.repl = [] # Which tiles got replaced

        self.rightT = [mkT(24,12), mkT(21, 10), mkT(20, 10)]
        self.rightTU = [mkT(s[1][0],s[1][1], True) for s in self.rightT]
        self.base_v = [mkW(0,13), mkW(1,13), mkT(2,12), mkW(2,11), mkW(3,10), mkW(4,9), mkW(5,8), mkW(6,7), mkW(7,6), mkW(8,5), mkW(9,4), mkW(10,3)] + (
                        self.rightT + [mkW(11,3), mkW(12,3), mkW(13,3),])

        self.diag = [[21,9], [20,8], [19,7], [18,6], [17,5], [16,4], [15,3], [14,2]]
        self.diagW = [mkW(p[0],p[1]) for p in self.diag] # list(map(lambda p : mkW(p[0], p[1]), self.diag))
        self.diagS = [mkS(p[0],p[1]) for p in self.diag] # list(map(lambda p : mkW(p[0], p[1]), self.diag))

        self.wall_v = [
                        [mkW(27,13), mkW(26,13), mkW(25,13), mkW(24,13), mkW(20,11)], # Thick
                        [mkW(2,13), mkW(3,13), mkW(4,13),] # Thin
                        ]
        self.wall_vU = [
                        [mkW(s[1][0],s[1][1], True) for s in self.wall_v[0]],
                        [mkW(s[1][0],s[1][1], True) for s in self.wall_v[1]]
                        ]

        self.reinf = [
                        [mkT(23,12), mkT(23,11), mkW(22,13)], # Thick
                        [mkT(3,12), mkT(3,11)] # Thin
                        ]
        self.reinfU = [
                        [mkT(s[1][0],s[1][1], True) for s in self.reinf[0]],
                        [mkT(s[1][0],s[1][1], True) for s in self.reinf[1]]
                        ]

        self.extra = [mkT(21,11, True), mkT(23,13, True), mkT(4,12, True), mkT(4,11, True),
                        mkT(24,11, True), mkT(19,11, True), mkT(1,12, True)]


    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        #gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.

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

    def sell_diag(self, game_state):
        if self.repl:
            game_state.attempt_remove(self.get_normalized_point(self.repl))

    def strategy_v1(self, game_state):
        # Defense
        self.build_defenses_v1(game_state)

        # Offense
        mp_available = game_state.get_resource(MP)
        if (game_state.turn_number < 4):
            game_state.attempt_spawn(INTERCEPTOR, self.get_normalized_point([2,11]), 1)
        if (game_state.turn_number <= 10):
            game_state.attempt_spawn(DEMOLISHER, self.get_normalized_point([20, 6]), 1)
        elif (self.attack):
            if random.getrandbits(1):
                game_state.attempt_spawn(SCOUT, self.get_normalized_point([13, 0]), math.floor(mp_available))
            else:
                game_state.attempt_spawn(DEMOLISHER, self.get_normalized_point([13, 0]), math.floor(mp_available))
            self.attack = False
            self.sell_diag(game_state)
        elif ((mp_available > 15 and game_state.turn_number < 30) or (mp_available > 21)):
            self.attack = True
            self.repl = []
            sp = game_state.get_resource(SP)
            for d in self.diag:
                if sp > 3:
                    self.repl.append(d)
                    sp = sp - 3
                else:
                    break
            if self.repl:
                self.sell_diag(game_state)



    def build_defenses_v1(self, game_state):
        # TODO: replace turrets + walls every turn
        # TODO: upgrade or add second layer of support

        build_order = self.base_v + (
                        self.wall_v[0] + self.wall_v[1] + self.reinf[0] + self.reinf[1] + (
                        self.rightTU + self.reinfU[0] + self.reinfU[1] + self.wall_vU[0] + self.wall_vU[1]
                        )) + self.extra

        if self.attack:
            build_order = self.diagS + build_order
        else:
            build_order = self.diagW + build_order

        # [TYPE, point[2], upgrade]
        for struct in build_order:
            loc = self.get_normalized_point(struct[1])
            game_state.attempt_spawn(struct[0], loc)
            if (struct[2]):
                game_state.attempt_upgrade(loc)

        if self.attack:
            shift = -1
            while True:
                shift = shift + 1
                succ = 0
                for p in self.diag:
                    loc = [p[0] - shift, p[1]]
                    if p[1] < 7:
                        loc[0] = loc[0] - 1

                    nloc = self.get_normalized_point(loc)
                    succ = game_state.attempt_spawn(SUPPORT, nloc)
                    if succ:
                        game_state.attempt_remove(nloc)
                    if p[1] >= 7:
                        succ = game_state.attempt_upgrade(nloc)
                    if not succ:
                        break
                if not succ:
                    break


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
