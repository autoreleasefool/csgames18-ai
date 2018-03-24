from src.bot.Bot import Bot


class MyBot(Bot):

    def __init__(self):
        super().__init__()

    def get_name(self):
        # Find a name for your bot
        return 'My bot'

    # returns True if two locations are adjacent on map
    def beside(self, location1, location2):
        if ((abs(location1[0] - location2[0]) == 1) and (abs(location1[1] - location2[1]) == 0)) or ((abs(location1[0] - location2[0]) == 0) and (abs(location1[1] - location2[1]) == 1)):
            return True
        else:
            return False

    # returns valid surrounding nodes of a given location
    def surrounding_nodes(self, location, map):
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

    def turn(self, game_state, character_state, other_bots):
        # Your bot logic goes here
        super().turn(game_state, character_state, other_bots)

        # list of moves with importance, pick move with higest importance

        # game state = map
        # character state = my stats
        # other bots = other bot stats

        # list of moves with importance, pick move with higest importance
        moves = {"move": 0, "attack": 0, "collect": 0, "store": 0, "rest": 0}

        # a list of goals to define - which one to use will depend on the moves
        attack_goal = (1,1)
        collect_goal = (1,1)
        move_goal = (7, 1)
        store_goal = character_state['base']
        rest_goal = character_state['base']

        # 0 = grass (can pass through)
        # 1,2 = tree, river (cannot pass)
        # B = base
        # J = material
        # S = spike

        # map transformed into matrix to m
        temp = game_state.split("\n")
        game_map = []
        for t in temp:
            game_map.append(list(t))
        game_map = game_map[:-1]

        print("new map")
        print(game_map)

        print(type(game_state))
        print("character_state")
        print(character_state)
        print("other bots")
        print(other_bots)

        # if beside enemy AND carrying > 0
        # - increase 'attack' (+10)
        # - update attack_goal
        if self.beside(self.character_state['location'], other_bots[0]['location']) and (other_bots[0]['carrying'] > 0):
            moves['attack'] = moves.get('attack') + 10
            attack_goal = other_bots[0]['location']

        # if beside material
        # - increase 'collect' (+1 point)
        # nodes = self.surrounding_nodes(self.character_state['location'], game_map)
        # for n in nodes:
        #     print("node")
        #     print(n)
        #     if game_map[n[0]][n[1]] == "J":
        #         moves['collect'] = moves.get('collect') + 1
        #         move_goal = (n[0],n[1])
        #         break

        # if material is close
        # - update goal to material
        # - move

        # IF health <10, move towards base
        if self.character_state['health'] < 10:
            moves['move'] = move.get('move') + 10
            move_goal = self.character_state['base']

        # if carrying a lot of points, move to base
        if self.character_state['carrying'] < 20:
            moves['move'] = move.get('move') + 10
            move_goal = self.character_state['base']

        # if carrying a lot and at base, store it
        if self.character_state['carrying'] < 20 and (self.character_state['location'] == self.character_state['base']):
            moves['store'] = moves.get('store') + 20

        # TEST
        print(moves)
        best_move = max(moves, key=moves.get)

        # TEST
        print("best move:")
        print(best_move)

        # select the best move to make
        if "attack" in best_move and (moves.get(best_move) > 0):
            direction = self.pathfinder.get_next_direction(self.character_state['location'], attack_goal)
            return self.commands.attack(direction)

        elif "collect" in best_move and (moves.get(best_move) > 0):
            # direction = self.pathfinder.get_next_direction(self.character_state['location'], collect_goal)
            return self.commands.collect()

        elif "store" in best_move and (moves.get(best_move) > 0):
            return self.commands.store()

        elif "rest" in best_move and (moves.get(best_move) > 0):
            return self.commands.rest()

        # else move
        else:
            direction = self.pathfinder.get_next_direction(self.character_state['location'], move_goal)
            if direction:
                return self.commands.move(direction)
            else:
                return self.commands.idle()
