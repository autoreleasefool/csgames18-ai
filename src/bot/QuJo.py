import networkx as nx
from networkx.algorithms.shortest_paths import astar_path

from src.bot.Bot import Bot
from src.symbols.ObjectSymbols import ObjectSymbols

MATERIAL_THRESHOLD = 100

class QuJo(Bot):

    def __init__(self):
        super().__init__()
        self.game_initialized = False
        self.materials = {}
        self.other_bot_locs = set()

        # Custom pathfinder
        self.pathfinder.create_graph = self.create_graph
        self.pathfinder.get_next_direction = self.get_next_direction

    def game_init(self):
        self.game_initialized = True
        game_map = self.game_state.strip().split('\n')
        size_x = len(game_map[0])
        size_y = len(game_map)

        for y in range(size_y):
            for x in range(size_x):
                if game_map[y][x] == 'J':
                    self.materials[(y, x)] = { 'visited': False }

    def get_name(self):
        return 'QuJo'

    def turn(self, game_state, character_state, other_bots):
        super().turn(game_state, character_state, other_bots)

        # Initialize bot on first turn
        if not self.game_initialized:
            self.game_init()

        # Update visited positions
        if self.character_state['location'] in self.materials:
            self.materials[self.character_state['location']]['visited'] = True

        # Create set of other bot positions
        self.other_bot_locs.clear()
        for bot in self.other_bots:
            self.other_bot_locs.add(bot['location'])

        # list of moves with importance, pick move with higest importance
        moves = {"move": 0, "attack": 0, "collect": 0, "store": 0, "rest": 0}

        attack_goal = (1,1)
        move_goal = (7, 1)
        store_goal = character_state['base']
        rest_goal = character_state['base']
        collect_goal = self.get_nearest_material_deposit(prefer_unvisited=True)

        # if health is low and currently on base, rest
        if self.character_state['health'] < 20:
            moves['rest'] = moves.get('rest') + 20

        # if beside enemy attack enemy
        # attack bot with lowest health that is carrying > 0
        # bot_to_attack = None
        # for bots in other_bots:
        #     if self.beside(self.character_state['location'], bot['location']):
        #         if (bot_to_attack is None) or (bot['health'] < bot_to_attack['health'] and bot['carrying'] != 0):
        #             bot_to_attack = bot
        # if (bot_to_attack is not None):
        #     print("bot to attack")
        #     print(bot_to_attack)
        #     moves['attack'] = moves.get('attack') + bot_to_attack['carrying']
        #     attack_goal = bot_to_attack['location']

        # attacking first bot that is beside me
        if self.beside(self.character_state['location'], other_bots[0]['location']):
            moves['attack'] = moves.get('attack') + other_bots[0]['carrying']
            attack_goal = other_bots[0]['location']

        # if health <20, heal
        if self.character_state['health'] < 20:
            moves['rest'] = moves.get('rest') + 100
            # move_goal = self.character_state['base']

        # if carrying a lot and at base, store it
        if self.character_state['carrying'] > 20 and (self.character_state['location'] == self.character_state['base']):
            moves['store'] = moves.get('store') + 20

        # follow other bot to attack
        # if its carrying a lot AND more than me AND distance is closer than the closest material
        if other_bots[0]['carrying'] > 50 and other_bots[0]['carrying'] > self.character_state['carrying'] and self.get_distance(self.character_state['location'], other_bots[0]['location']) > self.get_distance(self.character_state['location'], self.get_nearest_material_deposit(prefer_unvisited=True)):
            moves['move'] = moves.get('move') + other_bots[0]['carrying']
            move_goal = other_bots[0]['location']

        best_move = max(moves, key=moves.get)

        # select the best move to make
        if "attack" in best_move and (moves.get(best_move) > 0):
            direction = self.pathfinder.get_next_direction(self.character_state['location'], attack_goal)
            command = self.commands.attack(direction)

        elif "collect" in best_move and (moves.get(best_move) > 0):
            # direction = self.pathfinder.get_next_direction(self.character_state['location'], collect_goal)
            command = self.commands.collect()

        elif "store" in best_move and (moves.get(best_move) > 0):
            command = self.commands.store()

        elif "rest" in best_move and (moves.get(best_move) > 0):
            command = self.commands.rest()

        elif "move" in best_move and (moves.get(best_move) > 0):
            direction = self.pathfinder.get_next_direction(self.character_state['location'], move_goal)
            if direction:
                command = self.commands.move(direction)
            else:
                command = self.commands.idle()

        # else move to get nearest materials deposit
        else:
            nearest_deposit = self.get_nearest_material_deposit(prefer_unvisited=True)
            if self.character_state['carrying'] > MATERIAL_THRESHOLD:
                goal = self.character_state['base']
            else:
                goal = nearest_deposit

            direction = self.pathfinder.get_next_direction(self.character_state['location'], goal)
            command = self.commands.idle()
            if self.character_state['location'] in self.materials and self.character_state['carrying'] < MATERIAL_THRESHOLD:
                command = self.commands.collect()
            elif direction:
                command = self.commands.move(direction)
            elif self.character_state['base'] == self.character_state['location'] and self.character_state['carrying'] > 0:
                command = self.commands.store()
            else:
                command = self.commands.collect()
            return command


            # move_goal = collect_goal
            # direction = self.pathfinder.get_next_direction(self.character_state['location'], move_goal)
            # if direction:
            #     command = self.commands.move(direction)
            # else:
            #     command = self.commands.idle()

        return command

    def get_nearest_material_deposit(self, prefer_unvisited=False):
        possible_goals = []
        for material in self.materials:
            if not self.materials[material]['visited'] or not prefer_unvisited:
                possible_goals.append(material)

        if not possible_goals and prefer_unvisited:
            return self.get_nearest_material_deposit()

        nearest = None
        for possible in possible_goals:
            start = self.pathfinder.start = self.character_state['location']
            goal = self.pathfinder.goal = possible
            game_map = self.pathfinder.parse_game_state(self.game_state)
            graph = self.pathfinder.create_graph(game_map)
            path = astar_path(graph, start, goal, self.manhattan_distance)

            if nearest is None or len(path) < nearest[0]:
                nearest = (len(path), possible)

        return nearest[1]

    # Overwrite Pathfinder
    def create_graph(self, game_map):
        graph = nx.Graph()
        size_x = len(game_map[0])
        size_y = len(game_map)

        def can_pass_through(pos, symbol):
            if  self.pathfinder._is_start_or_goal(pos):
                return True
            elif pos in self.other_bot_locs:
                return False
            elif symbol is ObjectSymbols.SPIKE:
                return False
            elif symbol.can_pass_through():
                return True

            return False

        for y in range(size_y):
            for x in range(size_x):
                graph.add_node((y, x))

        for y in range(size_y - 1):
            for x in range(size_x - 1):
                pos = (y, x)
                symbol = game_map[y][x]

                if can_pass_through(pos, symbol):
                    right_pos = (y, x + 1)
                    right_symbol = game_map[y][x + 1]
                    if can_pass_through(right_pos, right_symbol):
                        graph.add_edge((y, x), (y, x+1))

                    bottom_pos = (y + 1, x)
                    bottom_symbol = game_map[y + 1][x]
                    if can_pass_through(bottom_pos, bottom_symbol):
                        graph.add_edge((y, x), (y+1, x))

        return graph

    # Overwrite Pathfinder
    def get_next_direction(self, start, goal):
        self.pathfinder.start = start
        self.pathfinder.goal = goal
        graph = self.pathfinder.create_graph(self.pathfinder.game_map)
        direction = None
        try:
            path = astar_path(graph, start, goal)
            print('hello')
            direction = self.pathfinder.convert_node_to_direction(path)
        except Exception:
            pass

        return direction

    @staticmethod
    def manhattan_distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    # returns True if two locations are adjacent on map
    @staticmethod
    def beside(location1, location2):
        return ((abs(location1[0] - location2[0]) == 1) and (abs(location1[1] - location2[1]) == 0)) or ((abs(location1[0] - location2[0]) == 0) and (abs(location1[1] - location2[1]) == 1))

    @staticmethod
    def get_distance(location1, location2):
        x_diff = abs(location1[0] - location2[0])
        y_diff = abs(location1[1] - location2[1])
        return x_diff + y_diff

    # returns valid surrounding nodes of a given location
    @staticmethod
    def surrounding_nodes(location, map):
        nodes = []
        if (location[0] + 1 < len(map[0])):
            nodes.append([location[0] + 1, location[1]])
        if (location[1] + 1 < len(map)):
            nodes.append([location[0], location[1] + 1])
        if (location[0] - 1 >= 0 ):
            nodes.append([location[0] - 1, location[1]])
        if (location[1] - 1 >= 0):
            nodes.append([location[0] - 1, location[1]])
        return nodes
