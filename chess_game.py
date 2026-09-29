from enum import IntEnum
from move_validator import MoveValidator
from game_rules import Result, Color, PieceType

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
    
    def no_distance_moved(self) -> bool:
        return abs(self.from_sq - self.to_sq) == 0

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
        self.fifty_move_rule = 0
        self.move_validator = MoveValidator()
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
    
    def identify_piece(self, from_sq: int) -> PieceType:
        us = self.side_to_move
        # Identify the piece type sitting on the 'from' square
        for p in PieceType:
            if self.get_bit(self.pieces[us][p], from_sq):
                return p

    def any_legal_moves(self) -> bool:
        us = self.side_to_move
        them = Color.BLACK if us == Color.WHITE else Color.WHITE
        king_bb = self.pieces[us][PieceType.KING]
        possible_moves = []
        for sq in range(64):
            piece = self.identify_piece(sq)
            if piece is None:
                continue
            if piece == PieceType.PAWN:
                possible_moves.extend(self.move_validator.generate_legal_pawn_moves(sq, self.occupancies[us], self.occupancies[them], king_bb, us, self.pieces, self.en_passant_sq))
            elif piece == PieceType.BISHOP:
                possible_moves.extend(self.move_validator.generate_legal_bishop_moves(sq, self.occupancies[us], self.occupancies[them], king_bb, us, self.pieces))
            elif piece == PieceType.ROOK:
                possible_moves.extend(self.move_validator.generate_legal_rook_moves(sq, self.occupancies[us], self.occupancies[them], king_bb, us, self.pieces))
            elif piece == PieceType.KNIGHT:
                possible_moves.extend(self.move_validator.generate_legal_knight_moves(sq, self.occupancies[us], self.occupancies[them], king_bb, us, self.pieces))
            elif piece == PieceType.QUEEN:
                possible_moves.extend(self.move_validator.generate_legal_queen_moves(sq, self.occupancies[us], self.occupancies[them], king_bb, us, self.pieces))
            elif piece == PieceType.KING:
                possible_moves.extend(self.move_validator.generate_legal_king_moves(sq, self.occupancies[us], self.occupancies[them], us, self.pieces))
        return len(possible_moves) > 0
    
    def in_check(self) -> bool:
        us = self.side_to_move
        them = Color.BLACK if us == Color.WHITE else Color.WHITE
        king_bb = self.pieces[us][PieceType.KING]
        return self.move_validator.enemy_attacks_func(self.pieces, us, self.occupancies[them], self.occupancies[us]) & king_bb

    def get_result(self) -> bool:
        if self.is_fifty_move_rule_active():
            return Result.FIFTY_MOVE_RULE
        if not self.any_legal_moves():
            if self.in_check():
                return Result.CHECKMATE
            else:
                return Result.STALEMATE
        else:
            return Result.UNFINISHED

    def is_fifty_move_rule_active(self) -> bool:
        return self.fifty_move_rule >= 50
    
    def make_move(self, move: Move) -> bool:
        """Executes a move using highly efficient bitwise changes."""
        us = self.side_to_move
        them = Color.BLACK if us == Color.WHITE else Color.WHITE
        
        moved_piece = self.identify_piece(move.from_sq)        
                
        if moved_piece is None:
            return False  # Illegal: No active piece on the source square
        if move.from_sq == move.to_sq:
            return False

        ep_sq = self.en_passant_sq
        self.en_passant_sq = None

        if moved_piece == PieceType.PAWN:
            self.fifty_move_rule = 0
        else:
            self.fifty_move_rule += 1

        # En passant captures the pawn that just double-stepped, which is not on the landing square
        if moved_piece == PieceType.PAWN and ep_sq is not None and move.to_sq == ep_sq:
            captured_sq = move.to_sq - 8 if us == Color.WHITE else move.to_sq + 8
            self.pieces[them][PieceType.PAWN] = self.clear_bit(self.pieces[them][PieceType.PAWN], captured_sq)
        else:
            # Handle Captures: Check if an enemy piece resides on the target square
            for p in PieceType:
                if self.get_bit(self.pieces[them][p], move.to_sq):
                    self.pieces[them][p] = self.clear_bit(self.pieces[them][p], move.to_sq)
                    break

        # Move the piece inside its relative bitboard
        self.pieces[us][moved_piece] = self.clear_bit(self.pieces[us][moved_piece], move.from_sq)
        self.pieces[us][moved_piece] = self.set_bit(self.pieces[us][moved_piece], move.to_sq)

        if moved_piece == PieceType.PAWN and abs(move.to_sq - move.from_sq) == 16:
            self.en_passant_sq = (move.from_sq + move.to_sq) // 2

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
