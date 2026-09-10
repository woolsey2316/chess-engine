import tkinter as tk
import math
from PIL import Image, ImageTk
from chess_game import ChessGame, Move, Color, PieceType
from move_validator import MoveValidator
class ChessBoard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.game = ChessGame()
        self.move_validator = MoveValidator()
        self.title("Tkinter Chess Sprites")
        self.canvas_size = 512
        self.square_size = self.canvas_size / 8
        
        self.canvas = tk.Canvas(self, width=self.canvas_size, height=self.canvas_size)
        self.canvas.pack()
        
        self.pieces_images = {} 
        self.draw_board()
        self.load_sprites_and_pieces()
        
        # Original piece location 
        self.pickup_x = 0
        self.pickup_y = 0

        # Variables to track drag state
        self.dragged_item = None
        self.start_x = 0
        self.start_y = 0

        # Bind mouse events to the "piece" tag
        self.canvas.tag_bind("piece", "<Button-1>", self.on_start_drag)
        self.canvas.tag_bind("piece", "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind("piece", "<ButtonRelease-1>", self.on_drop)

    def draw_board(self):
        colors = ["#eeeed2", "#769656"] # Light and dark square hex colors
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def load_sprites_and_pieces(self):
        # Dictionary placeholder for loaded images (e.g., 'P' for white pawn)
        self.pieces_images['P'] = ImageTk.PhotoImage(Image.open("sprites/w_pawn.webp"))
        self.pieces_images['N'] = ImageTk.PhotoImage(Image.open("sprites/w_knight.webp"))
        self.pieces_images['B'] = ImageTk.PhotoImage(Image.open("sprites/w_bishop.webp"))
        self.pieces_images['Q'] = ImageTk.PhotoImage(Image.open("sprites/w_queen.webp"))
        self.pieces_images['K'] = ImageTk.PhotoImage(Image.open("sprites/w_king.webp"))
        self.pieces_images['R'] = ImageTk.PhotoImage(Image.open("sprites/w_rook.webp"))
        self.pieces_images['p'] = ImageTk.PhotoImage(Image.open("sprites/b_pawn.webp"))
        self.pieces_images['n'] = ImageTk.PhotoImage(Image.open("sprites/b_knight.webp"))
        self.pieces_images['b'] = ImageTk.PhotoImage(Image.open("sprites/b_bishop.webp"))
        self.pieces_images['q'] = ImageTk.PhotoImage(Image.open("sprites/b_queen.webp"))
        self.pieces_images['k'] = ImageTk.PhotoImage(Image.open("sprites/b_king.webp"))
        self.pieces_images['r'] = ImageTk.PhotoImage(Image.open("sprites/b_rook.webp"))
        
        # Example position mapping (W=White, B=Black, lowercase=black pieces)
        self.board_state = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]
        
        # Draw images based on board state
        for r in range(8):
            for c in range(8):
                piece = self.board_state[r][c]
                if piece:
                    x = (c + 0.5) * self.square_size
                    y = (r + 0.5) * self.square_size
                    self.canvas.create_image(x, y, image=self.pieces_images[piece], tags="piece")

    def on_start_drag(self, event):
        """Remembers the starting coordinates where the user clicked."""
        # Find closest item to the click
        self.dragged_item = self.canvas.find_closest(event.x, event.y)[0]
        self.start_x = event.x
        self.start_y = event.y
        self.pickup_x = event.x
        self.pickup_y = event.y
        
        sq = self.get_square_from_gui(self.pickup_x, self.pickup_y)
        piece = self.game.identify_piece(sq)
        pawn_idx = self.game.pieces[self.game.side_to_move][PieceType.PAWN]
        friendly_pieces = self.game.occupancies[self.game.side_to_move]
        enemy_pieces = self.game.occupancies[~self.game.side_to_move]
        king_idx = self.game.pieces[self.game.side_to_move][PieceType.KING]
        color = self.game.side_to_move
        print("piece: ", piece)
        print(type(self.move_validator))
        if piece == PieceType.PAWN:
            possible_moves = self.move_validator.generate_legal_pawn_moves(pawn_idx, friendly_pieces, enemy_pieces, king_idx, color, self.game.pieces)
        elif piece == PieceType.BISHOP:
            possible_moves = self.move_validator.generate_legal_bishop_moves(self.game.occupancies[Color.BOTH], sq, self.game.pieces)
        print("possible moves: ", possible_moves)

    def on_drag(self, event):
        """Calculates the movement delta and moves the piece in real time."""
        if self.dragged_item:
            # Calculate how far the mouse has moved
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            
            # Move the piece by that delta
            self.canvas.move(self.dragged_item, dx, dy)
            
            # Update the starting position for the next motion event
            self.start_x = event.x
            self.start_y = event.y

    def on_drop(self, event):
        """Clears the drag tracking when the mouse button is released."""
        # Remove captured piece if capture occurs
        move = Move(
                self.get_square_from_gui(self.pickup_x, self.pickup_y), 
                self.get_square_from_gui(event.x, event.y)
                )
        self.secondClosestPiece = ChessBoard.get_second_closest(self.canvas, event.x, event.y, self.dragged_item)

        secondClosestPieceCoords = self.canvas.coords(self.secondClosestPiece)
        is_captured = self.is_piece_captured(move.to_sq, secondClosestPieceCoords)
        if is_captured:
            self.canvas.moveto(self.secondClosestPiece, 1000, 100)
        # Grid-snapping logic here to snap to a chess board square
        end_col = math.floor(event.x / self.square_size)
        end_row = math.floor(event.y / self.square_size)
        end_x = end_col * self.square_size 
        end_y = end_row * self.square_size

        self.canvas.moveto(self.dragged_item, end_x, end_y)
        
        self.game.make_move(move)
        
        self.game.print_board()
        
        self.dragged_item = None

    def is_piece_captured(self, toSq, coords):
        col = int(coords[0] // self.square_size)
        row = int(7 - coords[1] // self.square_size)
        return row * 8 + col == toSq

    def get_square_from_gui(self, x, y):
        col = int(x // self.square_size)
        row = 7 - int(y // self.square_size)
        return row * 8 + col

    def get_second_closest(canvas, x, y, dragged_item):
        # Get all items on the canvas
        all_items = canvas.find_all()
        distances = []
        for item in all_items:
            item_type = canvas.type(item)
            if item == dragged_item:
                continue
            if item_type != "image":
                continue
            # Get coordinates [x1, y1, x2, y2] of the bounding box
            coords = canvas.bbox(item)
            if not coords:
                continue
            
            # Calculate the center point of the item
            cx = (coords[0] + coords[2]) / 2
            cx = coords[0] if len(coords) < 3 else (coords[0] + coords[2]) / 2
            cy = (coords[1] + coords[3]) / 2 if len(coords) >= 4 else coords[1]
            
            # Compute Euclidean distance squared (faster than Math.hypot/sqrt for sorting)
            dist_sq = (cx - x) ** 2 + (cy - y) ** 2
            distances.append((dist_sq, item))
        
        # Sort by distance
        distances.sort(key=lambda x: x[0])
        # Return the second closest item ID if it exists
        return distances[0][1] if len(distances) >= 1 else None
if __name__ == "__main__":
    app = ChessBoard()
    app.mainloop()
