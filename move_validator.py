from chess_game import Color, PieceType
from attack_tables import B_ATTACK_TABLE, R_ATTACK_TABLE, R_MASKS, B_MASKS, BBits, RBits, B_OFFSETS, R_OFFSETS, BETWEEN_MASKS
from magic_numbers import RMagic, BMagic

# Representation of a 64-bit board using standard integer bitboards
# Bit 0 is a1, Bit 7 is h1, Bit 63 is h8

# Avoid wrapping around the edges of the board
FILE_A = 0x0101010101010101
FILE_B = 0x0202020202020202
FILE_G = 0x4040404040404040
FILE_H = 0x8080808080808080

RANK_2 = 0x000000000000FF00
RANK_7 = 0x00FF000000000000
class MoveValidator():
    def get_knight_attacks(self, knight_bitboard: int) -> int:
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

    def generate_legal_knight_moves(self, knight_idx: int, friendly_pieces: int, enemy_pieces: int, king_bb: int, color: Color, pieces: list[list[int]]) -> list:
        """Generates strictly legal moves for a single knight."""
        legal_moves = []
        knight_bb = 1 << knight_idx
        
        # 1. Get pseudo-legal targets (anywhere the piece can structurally jump)
        pseudo_attacks = self.get_knight_attacks(knight_bb)
        
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
            if not (self.enemy_attacks_func(pieces, color, next_enemy, next_friendly) & king_bb):
                legal_moves.append((knight_idx, target_idx))
                
            # Clear the bit to process the next move
            valid_targets &= valid_targets - 1
            
        return legal_moves

    def get_pawn_attacks(self, pawn_bitboard: int, color: Color) -> int:
        not_a = ~FILE_A & 0xFFFFFFFFFFFFFFFF
        not_h = ~FILE_H & 0xFFFFFFFFFFFFFFFF
        
        if color == Color.WHITE:    
            w_pawn_east_attacks = (pawn_bitboard << 9) & not_a
            w_pawn_west_attacks = (pawn_bitboard << 7) & not_h
            result = w_pawn_east_attacks | w_pawn_west_attacks
        else:
            b_pawn_east_attacks = (pawn_bitboard >> 7) & not_a
            b_pawn_west_attacks = (pawn_bitboard >> 9) & not_h
            result = b_pawn_east_attacks | b_pawn_west_attacks
            
        # Strictly truncate to a 64-bit unsigned int before returning
        return result & 0xFFFFFFFFFFFFFFFF

    def get_pawn_moves(self, pawn_bitboard: int, color: Color) -> int:
        if (color == Color.WHITE):
            one_step = pawn_bitboard << 8
            # two moves forward if on original square
            if pawn_bitboard & RANK_2:
                return one_step | pawn_bitboard << 16
            return one_step
        else:
            one_step = pawn_bitboard >> 8
            if pawn_bitboard & RANK_7:
                return one_step | pawn_bitboard >> 16
            return one_step

    def get_king_moves(self, king_bitboard: int, friendly: int) -> int:
        not_a = ~FILE_A & 0xFFFFFFFFFFFFFFFF
        not_h = ~FILE_H & 0xFFFFFFFFFFFFFFFF

        anti_diag_west_attacks = king_bitboard << 9 & not_a
        diag_east_attacks = king_bitboard << 7 & not_a
        diag_west_attacks = king_bitboard >> 7 & not_a
        anti_diag_east_attacks = king_bitboard >> 9 & not_h
        forwards = king_bitboard >> 8
        backwards = king_bitboard << 8
        west = king_bitboard >> 1 & not_h
        east = king_bitboard << 1 & not_a

        return (anti_diag_west_attacks | diag_east_attacks | diag_west_attacks | anti_diag_east_attacks | forwards | backwards | west | east) & ~friendly & 0xFFFFFFFFFFFFFFFF

    def get_king_attacks(self, occ: int, friendly: int):
        pseudo_moves = self.get_king_moves(occ, friendly)

        return pseudo_moves & 0xFFFFFFFFFFFFFFFF

    def generate_legal_bishop_moves(self, bishop_idx: int, friendly_pieces: int, enemy_pieces: int, king_bb: int, color: Color, pieces: list[list[int]]) -> list:
        """Generate strictly legal moves for a bishop"""
        legal_moves = []
        bishop_bb = 1 << bishop_idx

        pseudo_moves = self.get_bishop_moves(friendly_pieces | enemy_pieces, bishop_idx)
        valid_targets = pseudo_moves & ~friendly_pieces
        while valid_targets:
            # Isolate the lowest set bit 
            target_bb = valid_targets & -valid_targets
            target_idx = target_bb.bit_length() - 1

            # Simulate the board state change
            next_friendly = (friendly_pieces & ~bishop_bb) | target_bb
            next_enemy = enemy_pieces & ~target_bb # Handle potential capture

            # Check if enemy pieces can hit our king square after this move
            if not (self.enemy_attacks_func(pieces, color, next_enemy, next_friendly) & king_bb):
                legal_moves.append((bishop_idx, target_idx))
            else:
                print("piece attacks king")
                
            # Clear the bit to process the next move
            valid_targets &= valid_targets - 1
        return legal_moves

    def get_bishop_moves(self, occ: int, sq: int) -> int:
        occ   &= B_MASKS[sq]
        occ   *= BMagic[sq]
        occ   &= 0xFFFFFFFFFFFFFFFF
        occ  >>= 64 - BBits[sq]
        return B_ATTACK_TABLE[B_OFFSETS[sq] + occ]

    def get_bishop_attacks(self, occ: int, board: int, color: Color):
        b = occ
        pseudo_moves = 0
        valid_targets = 0
        bishop_idx = 0  # Start at square 0 (A1)

        while b > 0:
            # Check if there is a bishop on the current square
            if b & 1:
                # Create a bitboard isolated to just this single bishop
                bishop_bb = 1 << bishop_idx
                
                # Calculate moves from this specific square
                pseudo_moves = self.get_bishop_moves(board, bishop_idx)
                valid_targets |= pseudo_moves 
            b >>= 1         # Move to the next bit
            bishop_idx += 1 # Move to the next chessboard index       
        return valid_targets & 0xFFFFFFFFFFFFFFFF

    def get_rook_attacks(self, occ: int, board: int, color: Color):
        b = occ
        pseudo_moves = 0
        valid_targets = 0
        rook_idx = 0
        while b > 0:
            # Check if there is a bishop on the current square
            if b & 1:
                # Create a bitboard isolated to just this single bishop
                rook_bb = 1 << rook_idx
                
                # Calculate moves from this specific square
                pseudo_moves = self.get_rook_moves(board, rook_idx)
                valid_targets |= pseudo_moves
            b >>= 1       # Move to the next bit
            rook_idx += 1 # Move to the next chessboard index       
        return valid_targets & 0xFFFFFFFFFFFFFFFF
        
    def get_rook_moves(self, occ: int, sq: int) -> int:
        occ   &= R_MASKS[sq]
        occ   *= RMagic[sq]
        occ   &= 0xFFFFFFFFFFFFFFFF
        occ  >>= 64 - RBits[sq]
        return R_ATTACK_TABLE[R_OFFSETS[sq] + occ]

    def enemy_attacks_func(self, pieces: list[list[int]], color: Color, enemy: int, friendly: int) -> int:
        attacks = 0
        them = Color.WHITE if color == Color.BLACK else Color.BLACK
        for p in PieceType:
            p_bb = pieces[them][p]
            if not p_bb:
                continue
            if p == PieceType.PAWN:
                attacks |= self.get_pawn_attacks(p_bb, them)
            elif p == PieceType.BISHOP:
                attacks |= self.get_bishop_attacks(p_bb, friendly | enemy, color)
            elif p == PieceType.ROOK:
                attacks |= self.get_rook_attacks(p_bb, friendly | enemy, color)
            elif p == PieceType.QUEEN:
                attacks |= self.get_bishop_attacks(p_bb, friendly | enemy, color) | self.get_rook_attacks(p_bb, friendly | enemy, color)
            elif p == PieceType.KING:
                attacks |= self.get_king_attacks(p_bb, enemy)
            elif p == PieceType.KNIGHT:
                attacks |= self.get_knight_attacks(p_bb)
        return attacks

    def generate_legal_pawn_moves(self, pawn_idx: int, friendly_pieces: int, enemy_pieces: int, king_bb: int, color: Color, pieces: list[list[int]]) -> list:
        """Generate strictly legal moves for a pawn"""
        legal_moves = []
        
        pawn_bb = 1 << pawn_idx
        pseudo_attacks = self.get_pawn_attacks(pawn_bb, color) & enemy_pieces
        pseudo_moves = self.get_pawn_moves(pawn_bb, color)

        valid_targets = (pseudo_attacks | pseudo_moves) & ~friendly_pieces

        while valid_targets:
            # Isolate the lowest set bit 
            target_bb = valid_targets & -valid_targets
            target_idx = target_bb.bit_length() - 1

             # Simulate the board state change
            next_friendly = (friendly_pieces & ~pawn_bb) | target_bb
            next_enemy = enemy_pieces & ~target_bb # Handle potential capture

            # Check if enemy pieces can hit our king square after this move
            if not (self.enemy_attacks_func(pieces, color, next_enemy, next_friendly) & king_bb):
                legal_moves.append((pawn_idx, target_idx))
                
            # Clear the bit to process the next move
            valid_targets &= valid_targets - 1
        return legal_moves
    
    def generate_legal_rook_moves(self, rook_idx: int, friendly_pieces: int, enemy_pieces: int, king_bb: int, color: Color, pieces: list[list[int]]) -> list:
        """Generate strictly legal moves for a rook"""
        legal_moves = []
        rook_bb = 1 << rook_idx

        pseudo_moves = self.get_rook_moves(friendly_pieces | enemy_pieces, rook_idx)
        valid_targets = pseudo_moves & ~friendly_pieces
        while valid_targets:
            # Isolate the lowest set bit 
            target_bb = valid_targets & -valid_targets
            target_idx = target_bb.bit_length() - 1

            # Simulate the board state change
            next_friendly = (friendly_pieces & ~rook_bb) | target_bb
            next_enemy = enemy_pieces & ~target_bb # Handle potential capture

            # Check if enemy pieces can hit our king square after this move
            if not (self.enemy_attacks_func(pieces, color, next_enemy, next_friendly) & king_bb):
                legal_moves.append((rook_idx, target_idx))
            else:
                print("piece attacks king")

            # Clear the bit to process the next move
            valid_targets &= valid_targets - 1
        return legal_moves
    
    def generate_legal_queen_moves(self, queen_idx: int, friendly_pieces: int, enemy_pieces: int, king_bb: int, color: Color, pieces: list[list[int]]) -> list:
        """Generate strictly legal moves for a queen"""
        legal_moves = []
        queen_bb = 1 << queen_idx

        pseudo_moves = self.get_bishop_moves(friendly_pieces | enemy_pieces, queen_idx) | self.get_rook_moves(friendly_pieces | enemy_pieces, queen_idx)
        valid_targets = pseudo_moves & ~friendly_pieces
        while valid_targets:
            # Isolate the lowest set bit 
            target_bb = valid_targets & -valid_targets
            target_idx = target_bb.bit_length() - 1

            # Simulate the board state change
            next_friendly = (friendly_pieces & ~queen_bb) | target_bb
            next_enemy = enemy_pieces & ~target_bb # Handle potential capture

            # Check if enemy pieces can hit our king square after this move
            if not (self.enemy_attacks_func(pieces, color, next_enemy, next_friendly) & king_bb):
                legal_moves.append((queen_idx, target_idx))
                
            # Clear the bit to process the next move
            valid_targets &= valid_targets - 1
        return legal_moves

    def generate_legal_king_moves(self, king_idx: int, friendly_pieces: int, enemy_pieces: int, color: Color, pieces: list[list[int]]) -> list:
        """Generate strictly legal moves for a king"""
        legal_moves = []
        king_bb = 1 << king_idx

        pseudo_moves = self.get_king_moves(king_bb, friendly_pieces)
        valid_targets = pseudo_moves
        while valid_targets:
            # Isolate the lowest set bit 
            target_bb = valid_targets & -valid_targets
            target_idx = target_bb.bit_length() - 1

            # Simulate the board state change
            next_friendly = (friendly_pieces & ~king_bb) | target_bb
            next_enemy = enemy_pieces & ~target_bb # Handle potential capture
            
            # Check if enemy pieces can hit our king square after this move
            if not (self.enemy_attacks_func(pieces, color, next_enemy, next_friendly) & target_bb):
                legal_moves.append((king_idx, target_idx))
                
            # Clear the bit to process the next move
            valid_targets &= valid_targets - 1
        return legal_moves


