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
        self.dem_attack_stage = 0


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
        if self.invert:
            return list(map(self.get_normalized_point, locations))
        else:
            return locations

    def strategy_v1(self, game_state):
        """
        Defense:
        """
        mp_available = game_state.get_resource(MP)
        enemy_mp = game_state.get_resource(MP, 1)
        self.get_normalized_point([3,4])  # wat is dis for

        right_side_walls = self.get_normalized_points([[14, 2], [15, 3], [16, 4], [17, 5], [18, 6], [19, 7], [20, 8], [21, 9],
                                                      [23, 11], [22, 12], [24, 12], [25, 12], [26, 12]])
        bottom_closure = right_side_walls + self.get_normalized_points([[13, 3], [12, 3], [11, 3], [10, 3]])
        left_side_walls = self.get_normalized_points([[9, 4], [8, 5], [7, 6], [6, 7], [5, 8], [4, 9], [3, 10], [2, 11]])
        full_v = bottom_closure + left_side_walls

        # check if they have a vulnerable line in the front
        enemy_front_vul_y = self.enemy_front_vulnerable(game_state)
        #gamelib.debug_write("Front enemy y loc attack: {}".format(enemy_front_vul_y))
        if enemy_front_vul_y != -1 and game_state.project_future_MP() >= 9 and self.total_structures(game_state) > 25:  # if they are
            # vulnerable, we have enough MP, and we have a decent amount of SP from refunds
            self.dem_attack_stage = 1

        #  this chunk of code tells the algo to deploy interceptors right after an attack if they have a lot of MP
        deploy_int = False
        if enemy_mp >= 9 and self.dem_attack_stage == 3:
            deploy_int = True
            self.dem_attack_stage = 0

        #  deals with control flow of a demolisher line attack
        if self.dem_attack_stage == 0:
            self.build_defenses_v1(game_state, deploy_int)
        elif self.dem_attack_stage == 1:
            self.build_defenses_v1(game_state, deploy_int)
            self.demolisher_stage1_v1(game_state)
        elif self.dem_attack_stage == 2:
            self.demolisher_stage2_v1(game_state, enemy_front_vul_y)

        if game_state.turn_number < 4:
            game_state.attempt_spawn(INTERCEPTOR, self.get_normalized_points([[6, 7], [20, 6]]), 2)  # interceptor stalling while base is built
        elif enemy_mp >= 9 and self.dem_attack_stage == 0:  # send interceptor for defense while rebuilding
            # send interceptors when enemy has at least 9 MP... can be optimized
            if not self.structures_intact_v1(game_state, full_v):
                if enemy_mp < 12:
                    game_state.attempt_spawn(INTERCEPTOR, [20, 6], 1)
                    game_state.attempt_spawn(INTERCEPTOR, [6, 7], 1)
                else:
                    game_state.attempt_spawn(INTERCEPTOR, [20, 6], 2)
                    game_state.attempt_spawn(INTERCEPTOR, [6, 7], 2)
            else:
                if enemy_mp < 12:
                    game_state.attempt_spawn(INTERCEPTOR, [21, 7], 2)
                    game_state.attempt_spawn(INTERCEPTOR, [15, 1], 1)
                else:
                    game_state.attempt_spawn(INTERCEPTOR, [20, 6], 2)
                    game_state.attempt_spawn(INTERCEPTOR, [6, 7], 2)
        elif enemy_mp >= 6 and self.dem_attack_stage < 2 and not game_state.contains_stationary_unit([6, 7]):  # send out interceptor if we have a hole in the V
            game_state.attempt_spawn(INTERCEPTOR, [6, 7], 1)

        if ((mp_available >= 12 and game_state.turn_number < 30) or (mp_available >= 22 and game_state.turn_number > 50)
            or (mp_available > 16 and 50 >= game_state.turn_number >= 30)) and self.dem_attack_stage == 0:  # scout attack (not during demolisher attack prep)
            if game_state.turn_number > 70 and random.randint(1, 4) == 3:
                game_state.attempt_spawn(DEMOLISHER, [13, 0], 100000)
            elif random.randint(1,4) == 4:
                game_state.attempt_spawn(SCOUT, [13, 0], math.floor(mp_available * 0.25))
                game_state.attempt_spawn(SCOUT, [11, 2], math.floor(mp_available * 0.75))

    def total_structures(self, game_state):  # returns total amount of structures we have (not the SP refund)
        total_num = 0
        for location in game_state.game_map:
            if location[1] <= 13:
                if game_state.contains_stationary_unit(location):
                    total_num += 1
        return total_num

    def structures_intact_v1(self, game_state, locations):  # checks if all locations are intact
        for location in locations:
            if not game_state.contains_stationary_unit(location):  # if the loc does not contain a building
                return False  # then we do not have our whole structure intact -> missing piece
        return True

    def demolisher_stage1_v1(self, game_state):  # removes all our defenses and spawns a few interceptors
        gamelib.debug_write("Demolisher stage 1.")
        for location in game_state.game_map:
            if location[1] <= 13:
                if game_state.contains_stationary_unit(location):
                    game_state.attempt_remove(location)

        self.dem_attack_stage += 1
        game_state.attempt_spawn(INTERCEPTOR, [14, 0], 1)
        game_state.attempt_spawn(INTERCEPTOR, [21, 7], 1)

    def demolisher_stage2_v1(self, game_state, enemy_y):  # builds the line of walls + supports and deploys demolishers
        gamelib.debug_write("Demolisher stage 2.")

        if game_state.get_resource(SP) > 20:  # we need enough SP to build a semi-respectable wall
            for x in range(27, 9, -1):  # spawn as many walls as we can (and remove)
                game_state.attempt_spawn(WALL, self.get_normalized_point([x, enemy_y - 2]))
                game_state.attempt_remove(self.get_normalized_point([x, enemy_y - 2]))
            for x in range(21, 5, -1):
                game_state.attempt_spawn(SUPPORT, self.get_normalized_point([x, enemy_y - 4]))
                game_state.attempt_remove(self.get_normalized_point([x, enemy_y - 4]))
            for x in range(21, 5, -1):
                game_state.attempt_upgrade(self.get_normalized_point([x, enemy_y - 4]))
            game_state.attempt_spawn(DEMOLISHER, self.get_normalized_point([24, 10]), 10000)
        else:
            gamelib.debug_write("Aborting demolisher stage 2: Insufficient SP")
        self.dem_attack_stage += 1

    def enemy_front_vulnerable(self, game_state):  # returns y position of their strongest horiz line of defenses
        # (only closest 3 y's considered)
        num_turrets = 0
        num_upgr_turr = 0
        num_struct = 0
        most_turrets_y = -1
        most_struct_y = -1
        for y in range(14, 16):
            for x in range(0, 27):
                unit = game_state.contains_stationary_unit(self.get_normalized_point([x, y]))
                if unit:
                    if unit.unit_type in [WALL, TURRET]:
                        if unit.unit_type == TURRET:
                            num_turrets += 1
                            if unit.upgraded:
                                num_upgr_turr += 1
                    num_struct += 1
            if num_turrets > 7:
                if num_upgr_turr <= 1:  # basically the upgraded turrets demolish the demolishers if they are stacked
                    most_turrets_y = y
            num_turrets = 0
            if num_struct > 22:
                most_struct_y = y
            num_struct = 0

        if most_turrets_y != -1:
            return most_turrets_y
        elif most_struct_y != -1:
            return most_struct_y
        else:
            return -1

    def build_defenses_v1(self, game_state, deploy_int):
        # TODO: replace turrets + walls every turn
        # TODO: upgrade or add second layer of support

        supp_pts = [[14, 3], [13, 2], [19, 8], [20, 9], [19, 9], [18, 7], [17, 6], [16, 5], [15, 4]]
        supp_stages = [0, 0, 2, len(supp_pts)]
        supp_upgr_stages = [2, 2, 2, len(supp_pts)]

        turret_pts = [[3, 13], [24, 13], [1, 12], [24, 12], [2, 12], [21, 10], [25, 13], [3, 12], [20, 11], [22, 13],
                      [4, 13], [3, 11], [23, 12], [23, 13], [19, 10], [19, 11], [20, 10], [4, 12]]
        turret_stages = [2, 4, 5, len(turret_pts)]
        turret_upgr_stages = turret_stages

        wall_pts = [[13, 3], [14, 2], [26, 12], [27, 13], [0, 13], [1, 13], [2, 13], [15, 3], [16, 4], [17, 5], [18, 6],
                       [12, 3], [11, 3], [10, 3], [9, 4], [8, 5], [7, 6], [5, 8], [4, 9], [3, 10], [2, 11],
                    [19, 7], [20, 8], [21, 9], [22, 12], [23, 11], [26, 13], [25, 12], [19, 12], [21, 13]]

        if not deploy_int:
            wall_pts.append([6, 7])

        wall_upgr_pts = [[0, 13], [1, 13], [2, 13], [27, 13], [26, 13], [26, 12], [1, 12], [25, 12], [21, 13], [22, 12],
                         [19, 12]]  # order for upgrading walls
        wall_stages = [2, 24, len(wall_pts), len(wall_pts)]
        wall_upgr_stages = [4, 4, 4, len(wall_upgr_pts)]

        # [TYPE, point[2], upgrade] - Default not upgraded
        build_order_V = [mkT(3,13, True), mkT(24, 13, True), mkT(1,12), mkT(21,10), # Main turrets
                        mkW(10,3), mkW(9,4), mkW(8,5), mkW(7,6), mkW(6,7), mkW(5,8), # Thin Wall (Most)
                        mkW(11,3), mkW(12,3), mkW(13,3), # Horizontal bottom
                        mkW(14, 2), mkW(15,3), mkW(16,4), mkW(17,5), mkW(18,6), mkW(19,7), mkW(20,8), mkW(21,9), #Thick Wall
                        mkT(23,12), mkT(25, 13), mkW(26, 12), mkW(27, 13), mkW(0, 13), mkW(4,9),
                        mkW(3,10), mkW(2,11), mkT(4,12), mkT(20,11), # Thick Corner Reinforcement
                        mkT(2,12), mkT(3, 11),  # Thin Corner completion
                        mkS(20,9, True), mkS(19,8, True),  # First Support
                        mkT(19,11), mkW(19,12), mkT(22,13), mkW(21,13), mkW(22,12), mkT(20,10), mkW(23,11), # Thick Corner Full Fortification 1
                        mkW(1,13), mkW(26,13), mkW(0,13, True), mkW(27,13, True), # Wall Upgrade 1
                        mkT(4,13), mkT(3,12), mkT(2,13), # Thin Corner Full Fortification
                        mkW(26,13, True), mkW(1,13, True), # Wall Upgrade 2
                        mkT(21,10), mkT(24,12), # Thick Corner Full Fortification 2
                        mkS(19,9), mkS(18,7), mkS(17,6), mkS(16,5), mkS(15,4), mkS(14,3), mkS(13,2)  # Rest Support
                        ]

        # Removed completely: Wall@[25,12],
        # Not upgraded: Wall@[[0,13], [1,13], [27,13], [26,13], [26,12], [1,12], [25,12], [21,13], [22,12], [19,12]]
        # Not upgraded: All turrets

        for struct in build_order_V:
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