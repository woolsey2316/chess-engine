def print_binary_chessboard(binary_input):
    # Convert integer to a 64-bit binary string, or clean up an existing binary string
    if isinstance(binary_input, int):
        binary_str = f"{binary_input:064b}"
    else:
        binary_str = str(binary_input).replace(" ", "").zfill(64)
        
    # Split the 64-character string into 8 rows of 8 bits
    for i in range(0, 64, 8):
        row = binary_str[i:i+8][::-1]
        # Print with spaces between bits for better visual readability
        print(" ".join(row))
