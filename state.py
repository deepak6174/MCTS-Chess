from copy import deepcopy
from mcts import mcts as MCTS
import chess


class State:
    def __init__(self, opponent=False):
        self.board = chess.Board()
        if opponent:
            self.board = deepcopy(opponent.board)

    def is_terminal(self):
        return self.board.is_game_over()
    
    def generate_states(self):
        states = []
        moves = self.board.legal_moves
        for move in moves:
            states.append(str(move))
        return states
    
    def take_action(self, move):
        new_state = State(self)
        new_state.board.push(chess.Move.from_uci(move))
        return new_state
    
    def game_loop(self):

        mcts = MCTS(timeLimit=1000)

        while True:
            best_move = mcts.search(self)
            self = self.takeAction(best_move)
            print(self)
            print("Best Move: ", best_move)
    def __str__(self):
        return self.board.unicode().replace('⭘', '.')
    





