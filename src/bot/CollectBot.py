import networkx as nx
from networkx.algorithms.shortest_paths import astar_path

from src.bot.Bot import Bot
from src.symbols.ObjectSymbols import ObjectSymbols

MATERIAL_THRESHOLD = 100

class CollectBot(Bot):

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
        return 'Python'

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

        nearest_deposit = self.get_nearest_material_deposit(prefer_unvisited=True)
        if self.character_state['carrying'] > MATERIAL_THRESHOLD:
            goal = self.character_state['base']
        else:
            goal = nearest_deposit

        # [
        #     {
        #         'id': 0,
        #         'health': 100,
        #         'carrying': 0,
        #         'points': 0,
        #         'location': (7, 1),
        #         'base': (7, 1),
        #         'status': 'alive',
        #         'spawn': 0,
        #         'name': 'My bot'
        #     }
        # ]

        # self.commands.attack(direction)
        # self.commands.move(direction)
        # self.commands.collect()
        # self.commands.idle()
        # self.commands.rest()
        # self.commands.store()

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
            direction = self.pathfinder.convert_node_to_direction(path)
        except Exception:
            pass

        return direction

    @staticmethod
    def manhattan_distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])