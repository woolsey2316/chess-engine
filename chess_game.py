from enum import IntEnum, unique

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

# Squares indexed 0 to 63 (A1 = 0, H8 = 63)
# Little-Endian Rank-File Mapping
SQUARES = [f"{f}{r}" for r in range(1, 9) for f in "abcdefgh"]
Square = IntEnum('Square', {sq.upper(): i for i, sq in enumerate(SQUARES)})

class Move:
    """Encodes a move into a single object using bit manipulation or properties."""
    def __init__(self, from_sq: int, to_sq: int, flags: int = 0):
        self.from_sq = from_sq
        self.to_sq = to_sq
        self.flags = flags  # Can hold flags for promotion, en-passant, castling

    def __repr__(self):
        return f"Move({SQUARES[self.from_sq]} -> {SQUARES[self.to_sq]})"


class ChessGame:
    def __init__(self):
        # 12 Piece Bitboards: [Color][PieceType]
        self.pieces = [[0] * 6 for _ in range(2)]
        # 3 Occupancy Bitboards: [WHITE, BLACK, BOTH]
        self.occupancies = [0] * 3
        
        # Game State Variables
        self.side_to_move = Color.WHITE
        self.en_passant_sq = None
        self.castling_rights = 0xF  # Bitmask: 1=WK, 2=WQ, 4=BK, 8=BQ
        self.halfmove_clock = 0
        self.fullmove_number = 1
        
        self.reset_board()

    # --- Bit Manipulation Helpers ---
    @staticmethod
    def set_bit(bb: int, square: int) -> int:
        return bb | (1 << square)

    @staticmethod
    def clear_bit(bb: int, square: int) -> int:
        return bb & ~(1 << square)

    @staticmethod
    def get_bit(bb: int, square: int) -> bool:
        return bool(bb & (1 << square))

    def update_occupancies(self):
        """Recomputes global board occupancies using bitwise OR."""
        self.occupancies[Color.WHITE] = 0
        self.occupancies[Color.BLACK] = 0
        
        for p in PieceType:
            self.occupancies[Color.WHITE] |= self.pieces[Color.WHITE][p]
            self.occupancies[Color.BLACK] |= self.pieces[Color.BLACK][p]
            
        self.occupancies[Color.BOTH] = self.occupancies[Color.WHITE] | self.occupancies[Color.BLACK]

    def reset_board(self):
        """Initializes the engine bitboards to the standard starting layout."""
        # White Piece Placements
        self.pieces[Color.WHITE][PieceType.PAWN]   = 0x000000000000FF00
        self.pieces[Color.WHITE][PieceType.ROOK]   = 0x0000000000000081
        self.pieces[Color.WHITE][PieceType.KNIGHT] = 0x0000000000000042
        self.pieces[Color.WHITE][PieceType.BISHOP] = 0x0000000000000024
        self.pieces[Color.WHITE][PieceType.QUEEN]  = 0x0000000000000008
        self.pieces[Color.WHITE][PieceType.KING]   = 0x0000000000000010

        # Black Piece Placements
        self.pieces[Color.BLACK][PieceType.PAWN]   = 0x00FF000000000000
        self.pieces[Color.BLACK][PieceType.ROOK]   = 0x8100000000000000
        self.pieces[Color.BLACK][PieceType.KNIGHT] = 0x4200000000000000
        self.pieces[Color.BLACK][PieceType.BISHOP] = 0x2400000000000000
        self.pieces[Color.BLACK][PieceType.QUEEN]  = 0x0800000000000000
        self.pieces[Color.BLACK][PieceType.KING]   = 0x1000000000000000

        self.update_occupancies()
        self.side_to_move = Color.WHITE
        self.en_passant_sq = None
        self.castling_rights = 0xF
        self.halfmove_clock = 0
        self.fullmove_number = 1

    def make_move(self, move: Move) -> bool:
        """Executes a move using highly efficient bitwise changes."""
        us = self.side_to_move
        them = Color.BLACK if us == Color.WHITE else Color.WHITE
        
        moved_piece = None
        # Identify the piece type sitting on the 'from' square
        for p in PieceType:
            if self.get_bit(self.pieces[us][p], move.from_sq):
                moved_piece = p
                break
                
        if moved_piece is None:
            return False  # Illegal: No active piece on the source square

        # Handle Captures: Check if an enemy piece resides on the target square
        for p in PieceType:
            if self.get_bit(self.pieces[them][p], move.to_sq):
                self.pieces[them][p] = self.clear_bit(self.pieces[them][p], move.to_sq)
                break

        # Move the piece inside its relative bitboard
        self.pieces[us][moved_piece] = self.clear_bit(self.pieces[us][moved_piece], move.from_sq)
        self.pieces[us][moved_piece] = self.set_bit(self.pieces[us][moved_piece], move.to_sq)

        # Synchronize structural changes
        self.update_occupancies()
        
        # Turn cycling logic
        if self.side_to_move == Color.BLACK:
            self.fullmove_number += 1
        self.side_to_move = them
        
        return True

    def print_board(self):
        """Visualizes the internal bitboard layout directly inside the terminal."""
        piece_symbols = {
            (Color.WHITE, PieceType.PAWN):   "P", (Color.BLACK, PieceType.PAWN):   "p",
            (Color.WHITE, PieceType.KNIGHT): "N", (Color.BLACK, PieceType.KNIGHT): "n",
            (Color.WHITE, PieceType.BISHOP): "B", (Color.BLACK, PieceType.BISHOP): "b",
            (Color.WHITE, PieceType.ROOK):   "R", (Color.BLACK, PieceType.ROOK):   "r",
            (Color.WHITE, PieceType.QUEEN):  "Q", (Color.BLACK, PieceType.QUEEN):  "q",
            (Color.WHITE, PieceType.KING):   "K", (Color.BLACK, PieceType.KING):   "k"
        }
        
        print("\n  +-----------------+ ")
        for rank in range(7, -1, -1):
            row_str = f"{rank + 1} | "
            for file in range(8):
                square = rank * 8 + file
                char = "."
                for c in [Color.WHITE, Color.BLACK]:
                    for p in PieceType:
                        if self.get_bit(self.pieces[c][p], square):
                            char = piece_symbols[(c, p)]
                row_str += char + " "
            print(row_str + "|")
        print("  +-----------------+ ")
        print("    a b c d e f g h\n")
