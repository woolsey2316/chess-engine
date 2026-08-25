class Piece():
    def __init__(self, color):
        self.color = color
    
    @abstractmethod
    def get_pseudo_legal_moves(self, pos, board):
        pass
class Knight():
    def get_pseudo_legal_moves(self, pos, board):
        r, c = pos
        moves = []
        offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]

        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr <= 8 and 0 <= nc <= 8
                target_piece = board.grid[nr][nc]
                if target_piece is None or target_piece.color != self.color
                    moves.append((nr,nc))

        return moves


