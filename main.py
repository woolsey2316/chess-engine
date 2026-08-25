# main.py
import tkinter as tk
# Import your custom class from the other file
from chess_view import ChessBoard 

# 3. Import and inject your external GUI layout
imported_gui = ChessBoard()

# 4. Start the app
imported_gui.mainloop()
