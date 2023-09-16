from __future__ import division
from __future__ import print_function
from trie import TrieNode
from ctypes import *
import time
import math
import random
import chess
import pickle

# load NNUE shared library
nnue = cdll.LoadLibrary("./libnnueprobe.so")

# load NNUE weights file
nnue.nnue_init(b"nn-62ef826d1a6d.nnue")

opening_root = pickle.load(open('./opening.pkl', 'rb'))

def randomPolicy(state):
    while not state.is_terminal():
        try:
            action = random.choice(state.generate_states())
        except IndexError:
            raise Exception("Non-terminal state has no possible actions: " + str(state))
        state = state.take_action(action)
    return state.getReward()

# NNUE evalauation
def nnue_policy(state):    
    # case black is checkmated
    if state.board.is_checkmate(): return -10000
    
    # case stale mate
    elif state.board.is_stalemate(): return 0
    
    # case draw
    elif state.board.can_claim_draw(): return 0
        
    # case in insufficient material
    elif state.board.is_insufficient_material(): return 0
    
    # get NNUE evaluation score
    score = nnue.nnue_evaluate_fen(bytes(state.board.fen(), encoding='utf-8'))
    
    # on material inbalance
    if get_material_score(state):
        # get quiescence score
        quiescence_score = quiescence(state, -10000, 10000)
        
        # use either direct static evaluation score or quiescence score
        # depending on which on is greater
        return max(score, quiescence_score)
    
    # on material balance
    else:
        # use static evaluation score
        return score
    


class treeNode():
    def __init__(self, state, parent):
        self.state = state
        self.isTerminal = state.is_terminal()
        self.isFullyExpanded = self.isTerminal
        self.parent = parent
        self.numVisits = 0
        self.totalReward = 0
        self.children = {}

def get_material_score(state):
    # material score
    score = 0

    # relative piece values
    material = {
        'P': 100,
        'N': 300,
        'B': 350,
        'R': 500,
        'Q': 900,
        'K': 1000,
        'p': -100,
        'n': -300,
        'b': -350,
        'r': -500,
        'q': -900,
        'k': -1000,
    }
    
    # loop over board squares
    for square in range(64):
        # init piece
        piece = state.board.piece_at(square)
        
        # if not empty square
        if piece is not None:
            # calculate material score
            score += material[str(piece)]
    
    # return material score
    return score

# quiescence search
def quiescence(state, alpha, beta):
    # static evaluation score
    stand_pat = nnue.nnue_evaluate_fen(bytes(state.board.fen(), encoding='utf-8'))
    
    if stand_pat >= beta:
        return beta
    
    if alpha < stand_pat:
        alpha = stand_pat

    # loop over legal moves
    for move in state.board.legal_moves:
        # pick up only captures
        if state.board.is_capture(move):
            # make move on board
            state.board.push(chess.Move.from_uci(str(move)))
            
            # recursive quiescence call
            score = -quiescence(state, -beta, -alpha)
            
            # take move back (restore board position)
            state.board.pop()

            if score >= beta:
                return beta

            if score > alpha:
               alpha = score
    
    return alpha

class mcts():
    def __init__(self, timeLimit=None, iterationLimit=None, explorationConstant=1/2,
                 rolloutPolicy=nnue_policy, moves=[]):
        if timeLimit != None:
            if iterationLimit != None:
                raise ValueError("Cannot have both a time limit and an iteration limit")
            # time taken for each MCTS search in milliseconds
            self.timeLimit = timeLimit
            self.limitType = 'time'
            self.flag = 0
            self.opening = self.searchOpening(moves)
        else:
            if iterationLimit == None:
                raise ValueError("Must have either a time limit or an iteration limit")
            # number of iterations of the search
            if iterationLimit < 1:
                raise ValueError("Iteration limit must be greater than one")
            self.searchLimit = iterationLimit
            self.limitType = 'iterations'
        self.explorationConstant = explorationConstant
        self.rollout = rolloutPolicy

    

    def search(self, initialState, moves=[]):        
        self.root = treeNode(initialState, None)

        if self.limitType == 'time':
            timeLimit = time.time() + self.timeLimit / 1000
            while time.time() < timeLimit:
                self.executeRound()
        else:
            for i in range(self.searchLimit):
                self.executeRound()

        bestChild = self.getBestChild(self.root, 0)
        return self.getAction(self.root, bestChild), -nnue_policy(bestChild.state)
    
    def searchOpening(self, moves):
        board = chess.Board()
        san_list = []
        # print(moves)
        for x in moves:
            move = chess.Move.from_uci(x)
            san_list.append(board.san(move))
            board.push(move)
        
        root = opening_root
        
        for y in san_list:
            try:
                if root.children[y]:
                    root = root.children[y]
            except:
                self.flag=1
                return None
            
        return root


    def executeRound(self):
        node = self.selectNode(self.root)
        reward = self.rollout(node.state)
        self.backpropogate(node, reward)

    def selectNode(self, node):
        r=None
        if self.flag == 0:
            r = self.opening
        while not node.isTerminal:
            if node.isFullyExpanded:
                k = self.getBestChild(node, self.explorationConstant, r)
                if self.flag==0:
                    try:
                        r = r.children[str(node.state.board.san(k.state.board.peek()))]
                    except:
                        self.flag=1
                node = k
            else:
                return self.expand(node)
        return node

    def expand(self, node):
        actions = node.state.generate_states()
        for action in actions:
            if action not in node.children:
                newNode = treeNode(node.state.take_action(action), node)
                node.children[action] = newNode
                if len(actions) == len(node.children):
                    node.isFullyExpanded = True
                return newNode

        raise Exception("Should never reach here")

    def backpropogate(self, node, reward):
        turn = -1
        while node is not None:
            node.numVisits += 1
            node.totalReward += reward * turn
            node = node.parent
            turn *= -1

    def getBestChild(self, node, explorationValue, root=None):
        bestValue = float("-inf")
        bestNodes = []
        for child in node.children.values():
            k = 1
            if self.flag==0:
                try:
                    board = node.state.board
                    move = chess.Move.from_uci(str(child.state.board.peek()))

                    if board.san(move) in root.children:
                        k = root.children[board.san(move)].OpeningDepth
                except:
                    pass
            nodeValue = child.totalReward /(1 + child.numVisits) +  explorationValue * k * math.sqrt((1 + node.numVisits) / (1 + child.numVisits))
            if explorationValue==0:
                nodeValue = child.numVisits
            
            if nodeValue > bestValue:
                bestValue = nodeValue
                bestNodes = [child]
            elif nodeValue == bestValue:
                bestNodes.append(child)
        return random.choice(bestNodes)

    def getAction(self, root, bestChild):
        for action, node in root.children.items():
            if node is bestChild:
                return action

