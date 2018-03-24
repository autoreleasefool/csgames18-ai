import networkx as nx
from networkx.algorithms.shortest_paths import astar_path

from src.bot.Bot import Bot
from src.symbols.ObjectSymbols import ObjectSymbols

HEALTH_THRESHOLD = 25
DEFAULT_MOVE = 1
NEVER = -1
DEFINITELY = 100000
PREFERABLE = 50
MAX_TURNS = 1000

class QuJo(Bot):

    def __init__(self):
        super().__init__()
        self.last_character_state = None
        self.game_initialized = False
        self.materials = {}
        self.other_bot_locs = {}
        self.current_turn = 0
        self.game_map = None
        self.graph_attr = None
        self.graph_attr_turn = -1
        self.healed_spike = False


        # Custom pathfinder
        self.pathfinder.create_graph = self.create_graph
        self.pathfinder.get_next_direction = self.get_next_direction

        # keep track of whether we were attacked
        self.being_attacked = False

    def game_init(self):
        self.game_initialized = True
        game_map = self.game_state.strip().split('\n')
        self.game_map = game_map
        size_x = len(game_map[0])
        size_y = len(game_map)
        being_attacked = False

        for y in range(size_y):
            for x in range(size_x):
                if game_map[y][x] == 'J':
                    self.materials[(y, x)] = {
                        'visited': False,
                        'history': [],
                        'dist_to_base': len(self.path_between(self.character_state['base'], (y, x)))
                    }

    def get_name(self):
        return 'QuJo'

    def turn(self, game_state, character_state, other_bots):
        self.last_character_state = self.character_state
        self.current_turn += 1
        super().turn(game_state, character_state, other_bots)

        # Initialize bot on first turn
        if not self.game_initialized:
            self.game_init()

        # Update visited positions
        if self.character_state['location'] in self.materials:
            self.materials[self.character_state['location']]['visited'] = True

        # Update average value of material deposit
        if self.last_character_state:
            collected = self.character_state['carrying'] - self.last_character_state['carrying']
            if collected > 0:
                self.materials[self.get_nearest_material_deposit()]['history'].append(collected)

        # Create set of other bot positions
        self.other_bot_locs.clear()
        for bot in self.other_bots:
            self.other_bot_locs[bot['location']] = bot
        nearest_enemy = self.get_nearest_enemy()

        # check if being attacked
        # add "and beside an enemy?"
        if self.last_character_state is not None and self.last_character_state['health'] - self.character_state['health'] > 0:
            self.being_attacked = True

        elif self.last_character_state is not None and self.last_character_state['health'] - self.character_state['health'] == 0:
            self.being_attacked = False

        if self.game_is_critical():
            return self.critical_action()

        # Heal after crossing spikes
        bot_x, bot_y = self.character_state['location']
        if self.game_map[bot_x][bot_y] == 'S' and not self.healed_spike:
            self.healed_spike = True
            return self.commands.rest()
        self.healed_spike = False

        if self.being_attacked:

            # define clear traits
            # TODO: run away
            # TODO: defend
            # TODO: attack back

            # list of moves with importance, pick move with higest importance
            moves = {"move": DEFAULT_MOVE, "attack": 0, "collect": 0, "store": 0, "rest": 0}

            store_goal = character_state['base']
            rest_goal = character_state['base']
            attack_goal = nearest_enemy['location']
            collect_goal = self.get_best_material_deposit()
            move_goal = collect_goal

            if self.character_state['location'] in self.materials:
                moves['collect'] += PREFERABLE * 2

            # if beside enemy AND carrying > 0
            # - increase 'attack' (+10)
            # - update attack_goal
            if self.beside(self.character_state['location'], nearest_enemy['location']) and nearest_enemy['carrying'] > 0:
                moves['attack'] += PREFERABLE

            # IF health < threshold, move towards base
            if self.character_state['health'] < HEALTH_THRESHOLD:
                if self.feels_safe(nearest_enemy=nearest_enemy):
                    moves['rest'] += DEFINITELY
                else:
                    moves['move'] += DEFINITELY
                    move_goal = self.character_state['base']

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

            # if carrying a lot and at base, store it
            if self.character_state['carrying'] > 0 and self.in_base():
                moves['store'] = DEFINITELY

            # Make this last - we crash if we try to collect a non-material
            if self.character_state['location'] not in self.materials:
                moves['collect'] = NEVER

            # follow other bot to attack
            # if its carrying a lot AND more than me AND distance is closer than the closest material
            if other_bots[0]['carrying'] > 50 and other_bots[0]['carrying'] > self.character_state['carrying'] and self.get_distance(self.character_state['location'], other_bots[0]['location']) > self.get_distance(self.character_state['location'], self.get_nearest_material_deposit()):
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

        else:
            # keep picking up materials
            best_deposit = self.get_best_material_deposit()
            goal = best_deposit

            direction = self.pathfinder.get_next_direction(self.character_state['location'], goal)
            command = self.commands.idle()
            if self.character_state['location'] in self.materials:
                command = self.commands.collect()
            elif direction:
                command = self.commands.move(direction)
            elif self.character_state['base'] == self.character_state['location'] and self.character_state['carrying'] > 0:
                command = self.commands.store()
            else:
                command = self.commands.collect()
            return command

        return command

    # Get the best material deposit - distance vs value
    def get_best_material_deposit(self):
        if not self.last_character_state:
            return self.get_nearest_material_deposit(prefer_unvisited=True)
        else:
            best_value = None
            for pos in self.materials:
                location = self.materials[pos]
                mean = sum(location['history']) / len(location['history']) if len(location['history']) > 0 else 15
                dist = location['dist_to_base']
                point_per_turn = mean / (dist * 2)
                if not best_value or point_per_turn > best_value[0]:
                    best_value = (point_per_turn, pos)

            return best_value[1]


    # Get the closest material location
    def get_nearest_material_deposit(self, prefer_unvisited=False):
        possible_goals = []
        for material in self.materials:
            if not self.materials[material]['visited'] or not prefer_unvisited:
                possible_goals.append(material)

        if not possible_goals and prefer_unvisited:
            return self.get_nearest_material_deposit()

        return self.get_nearest(possible_goals)

    # Get the closest enemy
    def get_nearest_enemy(self):
        nearest = self.get_nearest(list(self.other_bot_locs.keys()), avoid_bots=False)
        return self.other_bot_locs[nearest]

    # Get the closest point from a list of points
    def get_nearest(self, locations, avoid_bots=True):
        nearest = None
        for location in locations:
            path = self.path_between(self.character_state['location'], location, avoid_bots=avoid_bots)
            if nearest is None or len(path) < nearest[0]:
                nearest = (len(path), location)
        return nearest[1]

    def feels_safe(self, nearest_enemy=None):
        if not nearest_enemy:
            nearest_enemy = self.get_nearest_enemy()
        return len(self.path_between(self.character_state['location'], nearest_enemy['location'])) > 2

    def game_is_critical(self):
        return len(self.path_between(self.character_state['location'], self.character_state['base'])) == MAX_TURNS - 1 - self.current_turn

    def critical_action(self):
        if self.in_base():
            return self.commands.store()
        else:
            direction = self.pathfinder.get_next_direction(self.character_state['location'], self.character_state['base'])
            return self.commands.move(direction)

    # Overwrite Pathfinder
    def create_graph(self, game_map, avoid_bots=True):
        graph = nx.Graph()
        size_x = len(game_map[0])
        size_y = len(game_map)

        def can_pass_through(pos, symbol):
            if  self.pathfinder._is_start_or_goal(pos):
                return True
            elif avoid_bots and pos in self.other_bot_locs.keys():
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

        # {e: e[1][0]*2 for e in G.edges()}
        if self.graph_attr_turn != self.current_turn:
            self.graph_attr = {}
            self.graph_attr_turn = self.current_turn
            for edge in graph.edges():
                v1, v2 = edge
                if self.game_map[v1[0]][v1[1]] == 'S' or self.game_map[v2[0]][v2[1]] == 'S':
                    self.graph_attr[edge] = 1.5 if self.character_state['health'] > HEALTH_THRESHOLD else 100
                else:
                    self.graph_attr[edge] = 1

        nx.set_edge_attributes(graph, self.graph_attr, 'cost')

        return graph

    # Overwrite Pathfinder
    def get_next_direction(self, start, goal):
        self.pathfinder.start = start
        self.pathfinder.goal = goal
        graph = self.pathfinder.create_graph(self.pathfinder.game_map)
        direction = None
        try:
            path = astar_path(graph, start, goal, weight='cost')
            direction = self.pathfinder.convert_node_to_direction(path)
        except Exception:
            pass

        return direction

    def in_base(self):
        return self.character_state['location'] == self.character_state['base']

    def path_between(self, pointA, pointB, avoid_bots=True):
        start = self.pathfinder.start = pointA
        goal = self.pathfinder.goal = pointB
        game_map = self.pathfinder.parse_game_state(self.game_state)
        graph = self.pathfinder.create_graph(game_map, avoid_bots=avoid_bots)
        path = astar_path(graph, start, goal, self.manhattan_distance)

        return path

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
