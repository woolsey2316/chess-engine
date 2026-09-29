from enum import IntEnum, unique

@unique
class Result(IntEnum):
    CHECKMATE = 0
    STALEMATE = 1
    FIFTY_MOVE_RULE = 2
    UNFINISHED = 3

@unique
class Color(IntEnum):
    WHITE = 0
    BLACK = 1
    BOTH = 2

@unique
class PieceType(IntEnum):
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5