# from .sliding_attack import SLIDING_ATTACK
import json
import random
# sliding_attack_table = json.loads(SLIDING_ATTACK)

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

# The 64-element lookup table matching your exact hash function (fold * 0x783a9b23) >> 26
BitTable = [
    63,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1, 31, 
    32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 
    48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62,  2
]

def pop_1st_bit(bb: int) -> int:
    # Ensure the input fits inside a standard unsigned 64-bit integer
    bb &= 0xffffffffffffffff
    if bb == 0:
        return -1 # Handle empty bitboard edge case
        
    b = bb ^ (bb - 1)
    fold = ((b & 0xffffffff) ^ (b >> 32))
    
    # Python integers don't overflow automatically; we must manually mask 
    # to emulate 32-bit multiplication wrapping
    hash_value = ((fold * 0x783a9b23) & 0xffffffff) >> 26
    
    return BitTable[hash_value]

def index_to_uint64(index, bits, m):
  result = 0;
  for i in range(0, bits): 
    j = pop_1st_bit(m);
    if (index & (1 << i)):
        result |= (1 << j);
  return result;

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

def generate_mask(sq: int, is_rook: bool) -> int:
    # Generates relevant occupancy mask (excluding board edges)
    r, c = sq // 8, sq % 8
    mask = 0
    dirs = [(1,0), (-1,0), (0,1), (0,-1)] if is_rook else [(1,1), (1,-1), (-1,1), (-1,-1)]
    
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        while 0 < nr < 7 and 0 < nc < 7:
            mask |= (1 << (nr * 8 + nc))
            nr += dr
            nc += dc
    return mask

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

def print_magic_numbers():
  print("RMagic[64] = [")
  for square in range(0, 64):
      print(f"{find_magic(square, BBits[square], 1)},")
  print("];\n")
  print("BMagic[64] = [\n")
  for square in range(0, 64):
    print(f"{find_magic(square, BBits[square], 1)},")
  print("];\n")
