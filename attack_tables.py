# from .sliding_attack import SLIDING_ATTACK
import json
import random
# sliding_attack_table = json.loads(SLIDING_ATTACK)
from magic_numbers import RMagic, BMagic
from utils import print_binary_chessboard
def random_uint64():
    # Natively generates a random number up to 64 bits wide
    return random.getrandbits(64)

def random_uint64_fewbits():
  return random_uint64() & random_uint64() & random_uint64();

def count_1s(b):
  r = 0
  while b:
    r += 1
    b &= b - 1
  return r

def pop_1st_bit(m: int) -> tuple[int, int]:
    """Finds the index of the lowest set bit and clears it from the mask."""
    lsb = m & -m          # Isolate the lowest set bit
    j = lsb.bit_length() - 1  # Get its 0-indexed position
    m &= m - 1            # Clear the lowest set bit
    return j, m

def index_to_uint64(index: int, bits: int, m: int) -> int:
    result = 0
    for i in range(0, bits):
        j, m = pop_1st_bit(m)  # Unpack index and updated mask
        if index & (1 << i):
            result |= (1 << j)
    return result

def rmask(sq: int):
  result = 0
  rk = int(sq/8)
  fl = sq%8 
  for r in range(rk+1, 7):
      result |= (1 << (fl + r*8));
  for r in range(rk-1, 0, -1):
      result |= (1 << (fl + r*8));
  for f in range(fl+1, 7):
      result |= (1 << (f + rk*8));
  for f in range(fl-1, 0, -1):
      result |= (1 << (f + rk*8));
  return result;

def bmask(sq: int) -> int:
  result = 0
  rk = int(sq/8)
  fl = sq%8
  r, f = rk+1, fl+1
  while r<=6 and f<=6:
      result |= (1 << (f + r*8));
      r+=1
      f+=1
  r, f = rk+1, fl-1
  while r<=6 and f>=1:
    result |= (1 << (f + r*8))
    r+=1
    f-=1
  r, f = rk-1, fl+1
  while r>=1 and f<=6:
    result |= (1 << (f + r*8))
    r-=1
    f+=1
  r, f = rk-1, fl-1
  while r>=1 and f>=1:
    result |= (1 << (f + r*8))
    r-=1
    f-=1
  return result;

def ratt(sq: int, block: int) -> int:
  result = 0
  rk, fl = int(sq/8), sq%8, 
  for r in range(rk+1, 8):
    result |= (1 << (fl + r*8))
    if(block & (1 << (fl + r*8))): break;
  for r in range(rk - 1, -1, -1):
    result |= (1 << (fl + r*8))
    if(block & (1 << (fl + r*8))): break;
  for f in range(fl+1, 8):
    result |= (1 << (f + rk*8))
    if(block & (1 << (f + rk*8))): break;
  for f in range(fl-1, -1, -1):
    result |= (1 << (f + rk*8))
    if(block & (1 << (f + rk*8))): break;
  return result

def batt(sq: int, block: int) -> int:
  result = 0
  rk, fl = int(sq/8), sq%8
  f = fl+1
  for r in range(rk+1, 8):
    result |= (1 << (f + r*8))
    if(block & (1 << (f + r * 8))): break
  f = fl-1
  for r in range(rk+1, 8):
    result |= (1 << (f + r*8))
    if(block & (1 << (f + r * 8))): break
  r, f = rk - 1, fl + 1
  while r >= 0 and f <= 7:
    result |= (1 << (f + r*8))
    if(block & (1 << (f + r * 8))): break
    r -= 1
    f += 1
  r, f = rk-1, fl-1
  while r >= 0 and f >= 0:
    result |= (1 << (f + r*8))
    if(block & (1 << (f + r * 8))): break
    r -= 1
    f -= 1
  return result


def transform(b: int, magic: int, bits: int) -> int:
    # 1. Force the multiplication to truncate at 64 bits (emulate unsigned __int64 overflow)
    masked_product = (b * magic) & 0xFFFFFFFFFFFFFFFF
    
    # 2. Shift right to get your index
    return masked_product >> (64 - bits)

def find_magic(sq: int, m: int, bishop: int):
  b, a, used = [0] * 4096, [0] * 4096, [0] * 4096
  magic = 0

  mask = bmask(sq) if bishop else rmask(sq)
  n = count_1s(mask)

  for i in range(0, 1 << n):
    b[i] = index_to_uint64(i, n, mask)
    a[i] = batt(sq, b[i]) if bishop else ratt(sq, b[i])
  
  for k in range(0, 100000000):
    magic = random_uint64_fewbits()
    if(count_1s((mask * magic) & 0xFF00000000000000) < 6): continue
    for i in range(0, 4096): used[i] = 0
    i, fail = 0, 0
    while not fail and i < (1 << n):
      j = transform(b[i], magic, m)
      if (used[j] == 0): used[j] = a[i]
      elif (used[j] != a[i]): fail = 1
      i += 1
    if(not fail): return magic
  print("***Failed***\n")
  return 0

RBits = [
  12, 11, 11, 11, 11, 11, 11, 12,
  11, 10, 10, 10, 10, 10, 10, 11,
  11, 10, 10, 10, 10, 10, 10, 11,
  11, 10, 10, 10, 10, 10, 10, 11,
  11, 10, 10, 10, 10, 10, 10, 11,
  11, 10, 10, 10, 10, 10, 10, 11,
  11, 10, 10, 10, 10, 10, 10, 11,
  12, 11, 11, 11, 11, 11, 11, 12
];

BBits = [
  6, 5, 5, 5, 5, 5, 5, 6,
  5, 5, 5, 5, 5, 5, 5, 5,
  5, 5, 7, 7, 7, 7, 5, 5,
  5, 5, 7, 9, 9, 7, 5, 5,
  5, 5, 7, 9, 9, 7, 5, 5,
  5, 5, 7, 7, 7, 7, 5, 5,
  5, 5, 5, 5, 5, 5, 5, 5,
  6, 5, 5, 5, 5, 5, 5, 6
];

def generate_attacks_on_the_fly(sq: int, block: int, is_rook: bool) -> int:
    r, c = sq >> 3, sq & 7
    attacks = 0
    dirs = [(1,0), (-1,0), (0,1), (0,-1)] if is_rook else [(1,1), (1,-1), (-1,1), (-1,-1)]
    
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        # Real attacks can hit the true board edges
        while 0 <= nr < 8 and 0 <= nc < 8:
            attacks |= (1 << (nr * 8 + nc))
            if block & (1 << (nr * 8 + nc)):
                break  # Sliding ray is blocked by a piece
            nr += dr
            nc += dc
    return attacks

def generate_mask(sq: int, is_rook: bool) -> int:
    # Generates relevant occupancy mask (excluding board edges)
    r, c = sq >> 3, sq & 7
    mask = 0
    dirs = [(1,0), (-1,0), (0,1), (0,-1)] if is_rook else [(1,1), (1,-1), (-1,1), (-1,-1)]
    
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        while 0 < nr < 7 and 0 < nc < 7:
            mask |= (1 << (nr * 8 + nc))
            nr += dr
            nc += dc
    return mask

def get_occupancy(index: int, mask: int) -> int:
    occupancy = 0
    temp_mask = mask
    i = 0
    
    # Loop directly until temp_mask is completely emptied
    while temp_mask:
        square = (temp_mask & -temp_mask).bit_length() - 1
        temp_mask &= temp_mask - 1  # Clear LS1B
        
        if index & (1 << i):
            occupancy |= (1 << square)
        i += 1
        
    return occupancy
# Store structural configurations
B_MASKS = [0] * 64
R_MASKS = [0] * 64

# Calculate cumulative offsets for a single, flat fancy array
B_OFFSETS = [0] * 64
R_OFFSETS = [0] * 64

for i in range(1, 64):
    B_OFFSETS[i] = B_OFFSETS[i-1] + (1 << BBits[i-1])
    R_OFFSETS[i] = R_OFFSETS[i-1] + (1 << RBits[i-1])

# Flat attack tables
B_ATTACK_TABLE = [0] * (B_OFFSETS[-1] + (1 << BBits[-1]))
R_ATTACK_TABLE = [0] * (R_OFFSETS[-1] + (1 << RBits[-1]))

def init_attack_tables():
    for sq in range(64):
        B_MASKS[sq] = generate_mask(sq, is_rook=False)
        R_MASKS[sq] = generate_mask(sq, is_rook=True)
        # --- Populate Bishop Flat Table ---
        b_patterns = 1 << BBits[sq]
        for i in range(b_patterns):
            occ = get_occupancy(i, B_MASKS[sq])
            if sq == 58:
                print("i: ", i)
                print_binary_chessboard(i)
                print("occ")
                print_binary_chessboard(occ)
            # If using proper magic hashes: 
            # magic_index = (occ * BMagic[sq] & 0xFFFFFFFFFFFFFFFF) >> (64 - BBits[sq])
            # Since this is initialization, standard sequential indexing maps directly into the subset blocks
            B_ATTACK_TABLE[B_OFFSETS[sq] + i] = generate_attacks_on_the_fly(sq, occ, is_rook=False)
            if sq == 58:
                print("attack ray:")
                print_binary_chessboard(B_ATTACK_TABLE[B_OFFSETS[sq] + i])

            
        # --- Populate Rook Flat Table ---
        r_patterns = 1 << RBits[sq]
        for i in range(r_patterns):
            occ = get_occupancy(i, R_MASKS[sq])
            R_ATTACK_TABLE[R_OFFSETS[sq] + i] = generate_attacks_on_the_fly(sq, occ, is_rook=True)

def generate_between_masks() -> list[list[int]]:
  # Initialize a 64x64 matrix filled with 0s
  between_masks = [[0] * 64 for _ in range(64)]

  for sq1 in range(64):
    r1, f1 = divmod(sq1, 8)  # Rank and File of sq1

    for sq2 in range(64):
      if sq1 == sq2:
        continue

      r2, f2 = divmod(sq2, 8)  # Rank and File of sq2

      dr = r2 - r1  # Rank delta
      df = f2 - f1  # File delta

      # Determine if they share a straight line (Rook) or diagonal (Bishop)
      is_straight = dr == 0 or df == 0
      is_diagonal = abs(dr) == abs(df)

      if is_straight or is_diagonal:
        # Normalize the step direction to -1, 0, or 1
        step_r = (dr > 0) - (dr < 0)
        step_f = (df > 0) - (df < 0)
        step = step_r * 8 + step_f

        # Walk along the path from sq1 to sq2 (exclusive)
        mask = 0
        current_sq = sq1 + step
        while current_sq != sq2:
          mask |= 1 << current_sq
          current_sq += step

        between_masks[sq1][sq2] = mask

  return between_masks


# Precompute the array once at engine initialization
BETWEEN_MASKS = generate_between_masks()

def print_magic_numbers():
  print("RMagic = [")
  for square in range(0, 64):
      print(f"{find_magic(square, RBits[square], 0)},")
  print("];\n")
  print("BMagic = [\n")
  for square in range(0, 64):
    print(f"{find_magic(square, BBits[square], 1)},")
  print("];\n")
