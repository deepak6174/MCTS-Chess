from ctypes import *


nnue = cdll.LoadLibrary("./libnnueprobe.so")

# load NNUE weights file
nnue.nnue_init(b"nn-62ef826d1a6d.nnue")

print(nnue.nnue_evaluate_fen(bytes('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1', encoding='utf-8')))