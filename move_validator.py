from chess_game import Color
from attack_tables import B_ATTACK_TABLE, R_ATTACK_TABLE, RMASKS, BMASKS
from magic_numbers import RMagic, BMagic
class MoveValidator():
    # Representation of a 64-bit board using standard integer bitboards
    # Bit 0 is a1, Bit 7 is h1, Bit 63 is h8

    # Avoid wrapping around the edges of the board
    FILE_A = 0x0101010101010101
    FILE_B = 0x0202020202020202
    FILE_G = 0x4040404040404040
    FILE_H = 0x8080808080808080

def get_knight_attacks(knight_bitboard: int) -> int:
    """Generates all pseudo-legal knight targets from a bitboard of knights."""
    attacks = 0
    # Clear columns to prevent wrapping around the board edges
    not_a = ~FILE_A & 0xFFFFFFFFFFFFFFFF
    not_ab = ~(FILE_A | FILE_B) & 0xFFFFFFFFFFFFFFFF
    not_h = ~FILE_H & 0xFFFFFFFFFFFFFFFF
    not_gh = ~(FILE_G | FILE_H) & 0xFFFFFFFFFFFFFFFF

    # 8 possible directional jumps for a knight
    attacks |= (knight_bitboard << 17) & not_a
    attacks |= (knight_bitboard << 10) & not_ab
    attacks |= (knight_bitboard >>  6) & not_ab
    attacks |= (knight_bitboard >> 15) & not_a
    attacks |= (knight_bitboard << 15) & not_h
    attacks |= (knight_bitboard <<  6) & not_gh
    attacks |= (knight_bitboard >> 10) & not_gh
    attacks |= (knight_bitboard >> 17) & not_h

    return attacks & 0xFFFFFFFFFFFFFFFF

def generate_legal_knight_moves(knight_idx: int, friendly_pieces: int, enemy_pieces: int, king_idx: int, enemy_attacks_func) -> list:
    """Generates strictly legal moves for a single knight."""
    legal_moves = []
    knight_bb = 1 << knight_idx
    
    # 1. Get pseudo-legal targets (anywhere the piece can structurally jump)
    pseudo_attacks = get_knight_attacks(knight_bb)
    
    # 2. Remove targets occupied by friendly pieces
    valid_targets = pseudo_attacks & ~friendly_pieces
    
    # 3. Filter for King Safety (Strict Legality)
    while valid_targets:
        # Isolate the lowest set bit (target square)
        target_bb = valid_targets & -valid_targets
        target_idx = target_bb.bit_length() - 1
        
        # Simulate the board state change
        next_friendly = (friendly_pieces & ~knight_bb) | target_bb
        next_enemy = enemy_pieces & ~target_bb # Handle potential capture
        
        # Check if enemy pieces can hit our king square after this move
        if not (enemy_attacks_func(next_enemy, next_friendly) & (1 << king_idx)):
            legal_moves.append((knight_idx, target_idx))
            
        # Clear the bit to process the next move
        valid_targets &= valid_targets - 1
        
    return legal_moves

def get_pawn_attacks(pawn_bitboard: int, color: Color) -> int:
    not_a = ~FILE_A & 0xFFFFFFFFFFFFFFFF
    not_h = ~FILE_H & 0xFFFFFFFFFFFFFFFF
    if (color == Color.WHITE):    
        wPawnEastAttacks = pawn_bitboard << 9 | not_a
        wPawnWestAttacks = pawn_bitboard << 7 | not_h
        return wPawnEastAttacks | wPawnWestAttacks
    else:
        bPawnEastAttacks = pawn_bitboard >> 7 | not_h
        bPawnWestAttacks = pawn_bitboard >> 9 | not_a
        return bPawnEastAttacks | bPawnWestAttacks

def get_pawn_moves(pawn_bitboard: int, color: Color) -> int:
    if (color == Color.WHITE)
        return pawn_bitboard << 8
    else:
        return pawn_bitboard >> 8

def generate_legal_pawn_moves(pawn_idx: int, friendly_pieces: int, enemy_pieces: int, king_idx: int,enemy_attacks_func, color: Color) -> list:
    """Generate strictly legal moves for a pawn"""
    legal_moves = []
    
    pseudo_attacks = get_pawn_attacks(pawn_idx, color) 
    pseudo_moves = get_pawn_moves(pawn_idx, color)

    valid_targets = (pseudo_attacks | pseudoMoves) & ~friendly_pieces

    while valid_targets:
        # Isolate the lowest set bit 
        target_bb = valid_targets & -valid_targets
        target_idx = target_bb.bit_length() - 1

         # Simulate the board state change
        next_friendly = (friendly_pieces & ~knight_bb) | target_bb
        next_enemy = enemy_pieces & ~target_bb # Handle potential capture

        # Check if enemy pieces can hit our king square after this move
        if not (enemy_attacks_func(next_enemy, next_friendly) & (1 << king_idx)):
            legal_moves.append((pawn_idx, target_idx))
            
        # Clear the bit to process the next move
        valid_targets &= valid_targets - 1
    return legal_moves

def get_bishop_moves(occ: int, sq: int) -> int:
    occ   &= B_MASKS[sq]
    occ   *= BMagic[sq]
    occ  >>= 64 - B_BITS[sq]
    return B_ATTACK_TABLE[B_OFFSETS[sq] + occ]

def get_rook_moves(occ: int, sq: int) -> int:
    occ   &= R_MASKS[sq]
    occ   *= RMagic[sq]
    occ  >>= 64 - R_BITS[sq]
    return R_ATTACK_TABLE[R_OFFSETS[sq] + occ]

