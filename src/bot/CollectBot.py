import networkx as nx
from src.bot.Bot import Bot
from src.symbols.ObjectSymbols import ObjectSymbols


class CollectBot(Bot):

    def __init__(self):
        super().__init__()
        self.pathfinder.create_graph = self.create_graph

    def get_name(self):
        return 'Python'

    def turn(self, game_state, character_state, other_bots):
        super().turn(game_state, character_state, other_bots)
        goal = (1, 1)

        direction = self.pathfinder.get_next_direction(self.character_state['location'], goal)
        if direction:
            return self.commands.move(direction)
        else:
            return self.commands.idle()

    def create_graph(self, game_map):
        graph = nx.Graph()
        size_x = len(game_map[0])
        size_y = len(game_map)

        for y in range(size_y):
            for x in range(size_x):
                graph.add_node((y, x))

        for y in range(size_y - 1):
            for x in range(size_x - 1):
                symbol = game_map[y][x]
                if symbol is ObjectSymbols.SPIKE and not self.pathfinder._is_start_or_goal((y, x)):
                    continue

                if symbol.can_pass_through() or self.pathfinder._is_start_or_goal((y, x)):
                    right_symbol = game_map[y][x + 1]
                    if right_symbol.can_pass_through() or self.pathfinder._is_start_or_goal((y, x+1)):
                        graph.add_edge((y, x), (y, x+1))

                    bottom_symbol = game_map[y + 1][x]
                    if bottom_symbol.can_pass_through() or self.pathfinder._is_start_or_goal((y+1, x)):
                        graph.add_edge((y, x), (y+1, x))

        return graph
