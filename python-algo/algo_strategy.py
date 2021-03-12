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
        self.dem_attack_stage = 0  # whether to prepare for a demolisher + wall attack (0 - don't prep, 1 - prep, 2 - attack)
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
        gamelib.debug_write("Front enemy y loc attack: {}".format(enemy_front_vul_y))
        if enemy_front_vul_y != -1 and mp_available >= 12 and self.total_structures(game_state) > 25:
            self.dem_attack_stage = 1

        deploy_int = False
        if enemy_mp >= 9 and self.dem_attack_stage == 3:
            deploy_int = True
            self.dem_attack_stage = 0

        if self.dem_attack_stage == 0:
            self.build_defenses_v1(game_state, deploy_int)
        elif self.dem_attack_stage == 1:
            self.build_defenses_v1(game_state, deploy_int)
            self.demolisher_stage1_v1(game_state)
        elif self.dem_attack_stage == 2:
            self.demolisher_stage2_v1(game_state, enemy_front_vul_y)

        if game_state.turn_number < 4:
            game_state.attempt_spawn(INTERCEPTOR, self.get_normalized_points([[6, 7], [20, 6]]), 2)  # interceptor stalling while base is built
        #elif self.enemy_front_vulnerable(game_state) and mp_available >= 12 and self.structures_intact_v1(game_state, weak_dem_walls_needed):
            #gamelib.debug_write("Weak demolisher attack.")
            #game_state.attempt_spawn(DEMOLISHER, self.get_normalized_point([15, 1]), 10000)
        elif enemy_mp >= 9 and self.dem_attack_stage < 2:  # send interceptor for defense while rebuilding
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
        elif enemy_mp >= 6 and self.dem_attack_stage < 2 and not game_state.contains_stationary_unit([6, 7]):
            game_state.attempt_spawn(INTERCEPTOR, [6, 7], 1)
        if ((mp_available >= 12 and game_state.turn_number < 30) or (mp_available >= 22 and game_state.turn_number > 50)
            or (mp_available > 16 and 50 >= game_state.turn_number >= 30)) and self.dem_attack_stage == 0:  # scout attack (not during demolisher attack prep)
            if game_state.turn_number > 70 and random.randint(1, 4) == 3:
                game_state.attempt_spawn(DEMOLISHER, [13, 0], 100000)
            elif random.randint(1,4) == 4:
                game_state.attempt_spawn(SCOUT, [13, 0], math.floor(mp_available * 0.25))
                game_state.attempt_spawn(SCOUT, [11, 2], math.floor(mp_available * 0.75))

    def total_structures(self, game_state):
        total_num = 0
        for location in game_state.game_map:
            if location[1] <= 13:
                if game_state.contains_stationary_unit(location):
                    total_num += 1
        return total_num

    def structures_intact_v1(self, game_state, locations):
        for location in locations:
            if not game_state.contains_stationary_unit(location):  # if the loc does not contain a building
                return False  # then we do not have our whole structure intact -> missing piece
        return True

    def demolisher_stage1_v1(self, game_state):
        gamelib.debug_write("Demolisher stage 1.")
        for location in game_state.game_map:
            if location[1] <= 13:
                if game_state.contains_stationary_unit(location):
                    game_state.attempt_remove(location)

        self.dem_attack_stage += 1
        game_state.attempt_spawn(INTERCEPTOR, [14, 0], 1)
        game_state.attempt_spawn(INTERCEPTOR, [21, 7], 1)

    def demolisher_stage2_v1(self, game_state, enemy_y):
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

    def enemy_front_vulnerable(self, game_state):
        """
        :return: True if the enemy is vulnerable to a demolisher + wall attack
        """
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
                if num_upgr_turr <= 2:  # basically the upgraded turrets demolish the demolishers if they are stacked
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

        if game_state.turn_number == 1:
            game_state.attempt_spawn(TURRET, turret_pts[:2])
            game_state.attempt_upgrade(turret_pts[:2])

        for i in range(4):  # go through building stages
            game_state.attempt_spawn(WALL, wall_pts[:wall_stages[i]])
            game_state.attempt_spawn(TURRET, turret_pts[:turret_stages[i]])

            game_state.attempt_upgrade(turret_pts[:turret_upgr_stages[i]])
            wall_pts_to_up = wall_upgr_pts[:wall_upgr_stages[i]]
            if len(wall_pts_to_up) > 0:
                game_state.attempt_upgrade(wall_pts_to_up)

            supp_pts_to_spawn = supp_pts[:supp_stages[i]]
            if len(supp_pts_to_spawn) > 0:
                game_state.attempt_spawn(SUPPORT, supp_pts[:supp_stages[i]])

            game_state.attempt_upgrade(supp_pts[:supp_upgr_stages[i]])

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        self.build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                self.demolisher_line_strategy(game_state)
            else:
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

                # Only spawn Scouts every other turn
                # Sending more at once is better since attacks can only hit a single scout at a time
                if game_state.turn_number % 2 == 1:
                    # To simplify we will just check sending them from back left and right
                    scout_spawn_location_options = [[13, 0], [14, 0]]
                    best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                    game_state.attempt_spawn(SCOUT, best_location, 1000)

                # Lastly, if we have spare SP, let's build some Factories to generate more resources
                support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                game_state.attempt_spawn(SUPPORT, support_locations)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        
        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[8, 12], [19, 12]]
        game_state.attempt_spawn(WALL, wall_locations)
        # upgrade walls so they soak more damage
        game_state.attempt_upgrade(wall_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + \
                         game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
