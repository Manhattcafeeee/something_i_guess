#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║              D U N G E O N   O F   B A S E S                     ║
║   A text adventure that teaches computer-science number systems  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import random
import sys
from functools import partial

# ══════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════

MAX_FLOOR      = 40
BOSS_FLOORS    = (10, 20, 30, 40)
PLAYER_MAX_HP  = 40
DAMAGE_NORMAL  = 6
DAMAGE_BOSS    = 9
W              = 64

# ══════════════════════════════════════════════════════════════════
#  SMALL UTILITIES
# ══════════════════════════════════════════════════════════════════

def hr(ch="─"):
    print(ch * W)

def title(text):
    hr("═")
    print(text.center(W))
    hr("═")

def pause(msg="\n[Press Enter to continue]"):
    try:
        input(msg)
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)

def to_base(n, base):
    """Convert a non-negative int to a string in the given base."""
    if n == 0:
        return "0"
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out = ""
    while n > 0:
        out = digits[n % base] + out
        n //= base
    return out

def group_bits(b, size=4):
    pad = (-len(b)) % size
    b = "0" * pad + b
    return " ".join(b[i:i + size] for i in range(0, len(b), size))

def div_steps(n, base):
    x = n
    lines = []
    while x > 0:
        lines.append(f"{x} ÷ {base} = {x // base} r {x % base}")
        x //= base
    return "  →  ".join(lines)

def normalize(s):
    """Make an answer comparable: strip prefixes, spaces, leading zeros."""
    s = s.strip().lower().replace(" ", "").replace("_", "").replace(",", "")
    if not s:
        return ""
    for pre in ("0b", "0x", "0o"):
        if s.startswith(pre):
            s = s[len(pre):]
            break
    s = s.lstrip("0")
    return s if s else "0"


# ══════════════════════════════════════════════════════════════════
#  PLAYER
# ══════════════════════════════════════════════════════════════════

class Player:
    def __init__(self):
        self.max_hp   = PLAYER_MAX_HP
        self.hp       = PLAYER_MAX_HP
        self.coins    = 0
        self.inventory = {}
        self.shield   = False
        self.lucky    = False
        self.deaths   = 0
        self.correct  = 0
        self.wrong    = 0

    def add_item(self, name, n=1):
        self.inventory[name] = self.inventory.get(name, 0) + n

    def use_item(self, name):
        if self.inventory.get(name, 0) > 0:
            self.inventory[name] -= 1
            if self.inventory[name] == 0:
                del self.inventory[name]
            return True
        return False

    def heal(self, amount):
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before


# ══════════════════════════════════════════════════════════════════
#  QUESTION GENERATORS
#  Each returns: {"prompt", "answer", "hint", "explain"}
# ══════════════════════════════════════════════════════════════════

# ─────────────── TIER 1 : BINARY ───────────────

def q_place_value():
    p = random.randint(1, 8)
    val = 2 ** (p - 1)
    return {
        "prompt": (f"In an 8-bit binary number, what DECIMAL value does the bit in\n"
                   f"position {p} represent?  (Positions counted from the RIGHT, starting at 1.)"),
        "answer": str(val),
        "hint": ("The rightmost position is worth 1. Every step to the left DOUBLES the value:\n"
                 "  1, 2, 4, 8, 16, 32, 64, 128"),
        "explain": (f"Position {p} from the right is worth 2^{p-1} = {val}.\n"
                    f"Right-to-left place values: 1, 2, 4, 8, 16, 32, 64, 128.")
    }

def q_bin_to_dec(maxv=15):
    n = random.randint(1, maxv)
    b = bin(n)[2:]
    terms = [str(2 ** i) for i, c in enumerate(reversed(b)) if c == "1"]
    return {
        "prompt": f"Convert the BINARY number   {b}   to DECIMAL.",
        "answer": str(n),
        "hint": ("Add up the place values wherever a 1 appears.\n"
                 "From the right: 1, 2, 4, 8, 16, 32, 64, 128."),
        "explain": f"{b}  =  {' + '.join(reversed(terms))}  =  {n}"
    }

def q_dec_to_bin(maxv=15):
    n = random.randint(1, maxv)
    b = bin(n)[2:]
    rem, used = n, []
    for p in range(7, -1, -1):
        if 2 ** p <= rem:
            rem -= 2 ** p
            used.append(str(2 ** p))
    return {
        "prompt": f"Convert the DECIMAL number   {n}   to BINARY.",
        "answer": b,
        "hint": ("Take the biggest power of 2 that fits, subtract it, repeat.\n"
                 "Or divide by 2 repeatedly and read the remainders bottom-to-top."),
        "explain": (f"{n} = {' + '.join(used)}  →  {b}\n"
                    f"Written as a full 8-bit byte: {b.zfill(8)}")
    }

def q_bin_to_dec_small():  return q_bin_to_dec(15)
def q_bin_to_dec_mid():    return q_bin_to_dec(255)
def q_dec_to_bin_small():  return q_dec_to_bin(15)
def q_dec_to_bin_mid():    return q_dec_to_bin(255)

def q_next_binary():
    n = random.randint(1, 62)
    b = bin(n)[2:]
    return {
        "prompt": f"What BINARY number comes immediately AFTER   {b}   ?",
        "answer": bin(n + 1)[2:],
        "hint": ("Adding 1 in binary: flip every TRAILING 1 to 0, then flip the first 0 you meet to 1."),
        "explain": (f"{b} is {n} in decimal, so the next number is {n+1} = {bin(n+1)[2:]}.\n"
                    f"Notice how the trailing 1s became 0s and the first 0 became a 1.")
    }

def q_power_of_two():
    n = random.randint(2, 10)
    return {
        "prompt": f"What is  2^{n}  in DECIMAL?",
        "answer": str(2 ** n),
        "hint": "Start at 1 and double it n times.",
        "explain": (f"2^{n} = {2**n}.  The doubling sequence: "
                    + ", ".join(f"2^{i}={2**i}" for i in range(0, n + 1)))
    }

def q_count_values():
    n = random.choice([3, 4, 5, 8, 16])
    return {
        "prompt": f"How many DIFFERENT values can {n} bits represent?",
        "answer": str(2 ** n),
        "hint": "Each bit doubles the possibilities.  n bits  →  2^n combinations.",
        "explain": (f"{n} bits give 2^{n} = {2**n} combinations, "
                    f"numbered 0 through {2**n - 1}.")
    }

def q_bin_addition():
    a = random.randint(1, 60)
    b = random.randint(1, 60)
    return {
        "prompt": (f"Add these two BINARY numbers:\n\n"
                   f"      {bin(a)[2:]}\n"
                   f"   +  {bin(b)[2:]}\n\n"
                   f"Give the answer in BINARY."),
        "answer": bin(a + b)[2:],
        "hint": ("Binary addition rules:  0+0=0   0+1=1   1+0=1   1+1=10 (carry!)   1+1+1=11\n"
                 "Work right to left, just like decimal."),
        "explain": (f"{bin(a)[2:]} ({a})  +  {bin(b)[2:]} ({b})  =  {bin(a+b)[2:]} ({a+b})\n"
                    f"Decimal check: {a} + {b} = {a+b}.")
    }


# ─────────────── TIER 2 : OCTAL & HEX ───────────────

def q_dec_to_oct():
    n = random.randint(1, 255)
    return {
        "prompt": f"Convert the DECIMAL number   {n}   to OCTAL (base 8).",
        "answer": to_base(n, 8),
        "hint": ("Divide by 8 repeatedly and collect the remainders, then read them BOTTOM to TOP.\n"
                 "Octal digits only go 0–7."),
        "explain": (f"{n} in octal is {to_base(n,8)}.\n"
                    f"Steps: {div_steps(n, 8)}")
    }

def q_oct_to_dec():
    n = random.randint(1, 255)
    o = to_base(n, 8)
    terms = []
    for i, c in enumerate(reversed(o)):
        v = int(c, 8)
        terms.append(f"{c}×8^{i}={v * 8 ** i}")
    return {
        "prompt": f"Convert the OCTAL number   {o}   to DECIMAL.",
        "answer": str(n),
        "hint": ("Each octal digit is multiplied by a power of 8.\n"
                 "From the right: 8^0=1, 8^1=8, 8^2=64, 8^3=512."),
        "explain": f"{o}  =  {' + '.join(reversed(terms))}  =  {n}"
    }

def q_dec_to_hex():
    n = random.randint(1, 255)
    h = to_base(n, 16)
    return {
        "prompt": f"Convert the DECIMAL number   {n}   to HEXADECIMAL (base 16).",
        "answer": h,
        "hint": ("Divide by 16 repeatedly. Remainders 10–15 become the letters A, B, C, D, E, F."),
        "explain": (f"{n} in hex is {h}.\n"
                    f"Steps: {div_steps(n, 16)}\n"
                    f"(Remember: remainder 10=A, 11=B, 12=C, 13=D, 14=E, 15=F)")
    }

def q_hex_to_dec():
    n = random.randint(1, 255)
    h = to_base(n, 16)
    terms = []
    for i, c in enumerate(reversed(h)):
        v = int(c, 16)
        terms.append(f"{c}({v})×16^{i}={v * 16 ** i}")
    return {
        "prompt": f"Convert the HEXADECIMAL number   {h}   to DECIMAL.",
        "answer": str(n),
        "hint": ("A=10, B=11, C=12, D=13, E=14, F=15.\n"
                 "Multiply each digit by 16^(its position from the right, starting at 0) and add."),
        "explain": f"{h}  =  {' + '.join(reversed(terms))}  =  {n}"
    }

def q_bin_to_hex():
    n = random.randint(16, 255)
    b = bin(n)[2:]
    h = to_base(n, 16)
    return {
        "prompt": (f"Convert the BINARY number   {b}   to HEXADECIMAL.\n"
                   f"(Tip: split into groups of 4 bits, starting from the RIGHT.)"),
        "answer": h,
        "hint": ("Each hex digit is EXACTLY 4 bits (a nibble).\n"
                 "  1010 = A,  1100 = C,  0110 = 6,  1111 = F"),
        "explain": (f"{b}  →  {group_bits(b, 4)}  →  {h}\n"
                    f"Group the bits in 4s from the right, then convert each group.")
    }

def q_hex_to_bin():
    n = random.randint(16, 255)
    h = to_base(n, 16)
    b = bin(n)[2:]
    groups = "  ".join(bin(int(c, 16))[2:].zfill(4) for c in h)
    return {
        "prompt": f"Convert the HEXADECIMAL number   {h}   to BINARY.",
        "answer": b,
        "hint": ("Each hex digit becomes exactly 4 bits:\n"
                 "  0→0000  1→0001 ... 9→1001  A→1010  B→1011 ... F→1111"),
        "explain": (f"{h}  →  {groups}  →  {b}\n"
                    f"Each hex digit expands to its own 4-bit group.")
    }

def q_bin_to_oct():
    n = random.randint(8, 255)
    b = bin(n)[2:]
    o = to_base(n, 8)
    return {
        "prompt": (f"Convert the BINARY number   {b}   to OCTAL.\n"
                   f"(Tip: split into groups of 3 bits, starting from the RIGHT.)"),
        "answer": o,
        "hint": ("Each octal digit is EXACTLY 3 bits.\n"
                 "  000=0  001=1  010=2  011=3  100=4  101=5  110=6  111=7"),
        "explain": (f"{b}  →  {group_bits(b, 3)}  →  {o}\n"
                    f"Group the bits in 3s from the right, then convert each group.")
    }

def q_oct_to_bin():
    n = random.randint(8, 255)
    o = to_base(n, 8)
    b = bin(n)[2:]
    groups = "  ".join(bin(int(c, 8))[2:].zfill(3) for c in o)
    return {
        "prompt": f"Convert the OCTAL number   {o}   to BINARY.",
        "answer": b,
        "hint": "Each octal digit becomes exactly 3 bits: 0→000, 5→101, 7→111.",
        "explain": f"{o}  →  {groups}  →  {b}"
    }


# ─────────────── TIER 3 : TWO'S COMPLEMENT & BITWISE ───────────────

def q_twos_comp_neg():
    n = random.randint(1, 120)
    val = (256 - n) % 256
    pos = bin(n)[2:].zfill(8)
    flipped = "".join("1" if c == "0" else "0" for c in pos)
    b = bin(val)[2:].zfill(8)
    return {
        "prompt": f"Write   -{n}   as an 8-BIT TWO'S COMPLEMENT binary number.",
        "answer": b,
        "hint": ("Three steps:\n"
                 "  1. Write the positive value in 8 bits.\n"
                 "  2. Flip every bit (0↔1).\n"
                 "  3. Add 1."),
        "explain": (f"  +{n}   = {pos}\n"
                    f"  flip  = {flipped}\n"
                    f"  +1    = {b}\n\n"
                    f"So -{n} = {b}.  Check: as unsigned, {b} = {val}, and {val} − 256 = -{n}. ✔")
    }

def q_twos_comp_read():
    val = random.randint(129, 255)
    b = bin(val)[2:].zfill(8)
    return {
        "prompt": f"The 8-bit TWO'S COMPLEMENT number   {b}   represents what DECIMAL value?",
        "answer": str(val - 256),
        "hint": ("If the LEFTMOST bit is 1, the number is negative.\n"
                 "Its value = (unsigned value) − 256."),
        "explain": (f"The leading bit is 1, so this is negative.\n"
                    f"Unsigned value of {b} is {val}.\n"
                    f"{val} − 2^8 = {val} − 256 = {val - 256}.")
    }

def q_signed_range():
    n = random.choice([4, 8])
    lo, hi = -(2 ** (n - 1)), 2 ** (n - 1) - 1
    return {
        "prompt": (f"In {n}-bit TWO'S COMPLEMENT, what is the LOWEST (most negative)\n"
                   f"value that can be represented?"),
        "answer": str(lo),
        "hint": "Two's complement splits unevenly:  −2^(n−1)  up to  +2^(n−1) − 1.",
        "explain": (f"{n}-bit two's complement ranges from −2^{n-1} = {lo} "
                    f"to 2^{n-1} − 1 = {hi}.\n"
                    f"There is one more negative value than positive, because 0 takes a slot.")
    }

def q_unsigned_max():
    n = random.choice([4, 8, 16])
    return {
        "prompt": f"What is the LARGEST value an UNSIGNED {n}-bit number can hold?",
        "answer": str(2 ** n - 1),
        "hint": "n bits give 2^n values, starting at 0. So the max is 2^n − 1.",
        "explain": f"{n} bits → 2^{n} = {2**n} values, numbered 0 through {2**n - 1}."
    }

def q_bitwise(op="AND"):
    a = random.randint(8, 200)
    b = random.randint(8, 200)
    ab, bb = bin(a)[2:].zfill(8), bin(b)[2:].zfill(8)
    sym = {"AND": "&", "OR": "|", "XOR": "^"}[op]
    if op == "AND":
        r = a & b
        rule = "AND gives 1 only when BOTH bits are 1."
    elif op == "OR":
        r = a | b
        rule = "OR gives 1 when AT LEAST ONE of the bits is 1."
    else:
        r = a ^ b
        rule = "XOR gives 1 when the two bits are DIFFERENT."
    rb = bin(r)[2:].zfill(8)
    return {
        "prompt": (f"Compute the bitwise {op}  (the  {sym}  operator):\n\n"
                   f"      {ab}    ({a})\n"
                   f"  {sym}   {bb}    ({b})\n"
                   f"      {'-' * 8}\n\n"
                   f"Give the answer in DECIMAL."),
        "answer": str(r),
        "hint": (f"{rule}\n"
                 f"Work column by column, then convert the 8-bit result back to decimal."),
        "explain": (f"      {ab}    ({a})\n"
                    f"  {sym}   {bb}    ({b})\n"
                    f"      {'-' * 8}\n"
                    f"      {rb}    ({r})\n\n"
                    f"{rule}")
    }

def q_shift(direction="left"):
    a = random.randint(5, 60)
    n = random.randint(1, 3)
    plural = "s" if n > 1 else ""
    if direction == "left":
        r = a << n
        return {
            "prompt": (f"What is   {a} << {n}   (i.e. {a} shifted LEFT by {n} bit{plural})?\n"
                       f"Give the answer in DECIMAL."),
            "answer": str(r),
            "hint": "Left shift by n = multiply by 2^n. Every bit moves n places to the left.",
            "explain": (f"{a} in binary is {bin(a)[2:]}.\n"
                        f"Shifting left {n} place{plural} gives {bin(r)[2:]} = {r}.\n"
                        f"Check: {a} × 2^{n} = {a} × {2**n} = {r}.")
        }
    else:
        r = a >> n
        return {
            "prompt": (f"What is   {a} >> {n}   (i.e. {a} shifted RIGHT by {n} bit{plural})?\n"
                       f"Give the answer in DECIMAL."),
            "answer": str(r),
            "hint": "Right shift by n = integer-divide by 2^n. Bits pushed off the right end vanish.",
            "explain": (f"{a} in binary is {bin(a)[2:]}.\n"
                        f"Shifting right {n} place{plural} gives {bin(r)[2:]} = {r}.\n"
                        f"Check: {a} ÷ 2^{n} = {a} ÷ {2**n} = {r} (remainder discarded).")
        }

def q_overflow():
    n = random.choice([4, 8])
    maxv = 2 ** n - 1
    return {
        "prompt": (f"Using {n}-bit UNSIGNED arithmetic, what is\n\n"
                   f"      {bin(maxv)[2:].zfill(n)}\n"
                   f"   +  {'0' * (n - 1)}1\n\n"
                   f"in binary?  (Think about what happens when you run out of bits.)"),
        "answer": "0",
        "hint": ("Adding 1 to a row of all-1s carries all the way out of the register.\n"
                 "The carry falls off the end and you are left with zero."),
        "explain": (f"All {n} bits are 1 (= {maxv}). Adding 1 carries through every column.\n"
                    f"The final carry has nowhere to go, so the result wraps to "
                    f"{'0' * n} = 0.\n"
                    f"This is called OVERFLOW — the result 'wraps around'.")
    }


# ─────────────── TIER 4 : NUMBER SYSTEMS IN THE WILD ───────────────

def q_char_to_bin():
    c = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    code = ord(c)
    return {
        "prompt": (f"In ASCII, the character '{c}' has decimal code {code}.\n"
                   f"What is that code in 8-bit BINARY?"),
        "answer": bin(code)[2:],
        "hint": "Convert the decimal number using place values 128, 64, 32, 16, 8, 4, 2, 1.",
        "explain": f"'{c}' → {code} decimal → {bin(code)[2:].zfill(8)} binary."
    }

def q_bin_to_char():
    c = random.choice("abcdefghijklmnopqrstuvwxyz")
    code = ord(c)
    b = bin(code)[2:].zfill(8)
    return {
        "prompt": (f"The 8-bit binary value   {b}   is an ASCII code.\n"
                   f"What DECIMAL value does it represent?\n"
                   f"(Answer with just the number.)"),
        "answer": str(code),
        "hint": ("Add the place values where the 1s appear.\n"
                 "ASCII reminder: 97='a', 98='b', 99='c' ..."),
        "explain": f"{b} = {code}, which is the ASCII character '{c}'."
    }

def q_hex_color():
    r, g, b = (random.randint(0, 255) for _ in range(3))
    hx = f"#{r:02X}{g:02X}{b:02X}"
    ch = random.choice("RGB")
    pair = {"R": hx[1:3], "G": hx[3:5], "B": hx[5:7]}[ch]
    val = {"R": r, "G": g, "B": b}[ch]
    name = {"R": "Red", "G": "Green", "B": "Blue"}[ch]
    return {
        "prompt": (f"A CSS color is written as  {hx}   (format #RRGGBB).\n\n"
                   f"What is the DECIMAL value of the {name} channel?\n"
                   f"(Its two hex digits are: {pair})"),
        "answer": str(val),
        "hint": ("Each channel is 2 hex digits = 1 byte.\n"
                 "Value = (first digit × 16) + second digit.  A=10 ... F=15."),
        "explain": (f"{hx} splits into  R={hx[1:3]}  G={hx[3:5]}  B={hx[5:7]}.\n"
                    f"{name} = {pair} hex = {int(pair[0],16)}×16 + {int(pair[1],16)} = {val}.\n"
                    f"(2 hex digits max out at FF = 255 — exactly one byte.)")
    }

def q_any_base():
    base = random.choice([3, 5, 6, 7, 9])
    n = random.randint(10, 200)
    return {
        "prompt": f"Convert the DECIMAL number   {n}   to BASE {base}.",
        "answer": to_base(n, base),
        "hint": (f"Divide by {base} repeatedly and read the remainders bottom-to-top.\n"
                 f"Valid digits are 0 through {base - 1}."),
        "explain": (f"{n} in base {base} is {to_base(n, base)}.\n"
                    f"Steps: {div_steps(n, base)}")
    }

def q_parity():
    bits = "".join(random.choice("01") for _ in range(7))
    ones = bits.count("1")
    par = "0" if ones % 2 == 0 else "1"
    return {
        "prompt": (f"For EVEN parity, what parity bit should be appended to\n\n"
                   f"      {bits}\n\n"
                   f"so that the total number of 1s is even?"),
        "answer": par,
        "hint": "Count the 1s. Already even → parity bit is 0. Odd → parity bit is 1.",
        "explain": (f"{bits} contains {ones} one{'s' if ones != 1 else ''} — "
                    f"{'even' if ones % 2 == 0 else 'odd'}.\n"
                    f"Parity bit = {par}.   Result: {bits}{par}  "
                    f"({ones + int(par)} ones total, which is even.)")
    }

def q_ip_binary():
    o = random.randint(1, 255)
    b = bin(o)[2:].zfill(8)
    rem, used = o, []
    for p in range(7, -1, -1):
        if 2 ** p <= rem:
            rem -= 2 ** p
            used.append(str(2 ** p))
    return {
        "prompt": (f"An IPv4 address has 4 octets — each one a byte.\n"
                   f"Convert the octet   {o}   to 8-bit BINARY."),
        "answer": b,
        "hint": "Use the place values 128, 64, 32, 16, 8, 4, 2, 1.",
        "explain": f"{o}  =  {' + '.join(used)}  =  {b}"
    }

def q_hex_address():
    val = random.randint(0x100, 0xFFFF)
    h = f"{val:04X}"
    terms = []
    for i, c in enumerate(reversed(h)):
        d = int(c, 16)
        if d:
            terms.append(f"{c}({d})×16^{i}={d * 16 ** i}")
    return {
        "prompt": (f"A memory address is shown in hex as   0x{h}   .\n"
                   f"What is this address in DECIMAL?"),
        "answer": str(val),
        "hint": "Multiply each hex digit by 16^(position from the right, starting at 0), then add.",
        "explain": f"0x{h}  =  {' + '.join(reversed(terms))}  =  {val}"
    }


# ══════════════════════════════════════════════════════════════════
#  LESSONS
# ══════════════════════════════════════════════════════════════════

LESSON_BINARY = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: THE LANGUAGE OF MACHINES                            ║
╚══════════════════════════════════════════════════════════════╝
A computer only knows two states: ON (1) and OFF (0).
A single 0 or 1 is called a BIT.

Every decimal number can be written with bits. Each bit position
has a PLACE VALUE that doubles as you move left:

   position:   8    7    6    5    4    3    2    1
   value:     128   64   32   16    8    4    2    1

To read a binary number, add the place values where a 1 appears.

     1 0 1 1
     8 4 2 1
     ↓   ↓ ↓
     8 + 2 + 1  =  11

Two useful words:
  NIBBLE = 4 bits        BYTE = 8 bits
"""

LESSON_DEC2BIN = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: DECIMAL → BINARY                                    ║
╚══════════════════════════════════════════════════════════════╝
METHOD 1 — Subtract the biggest power of two.
  Convert 13:
    13 - 8 = 5    → the 8-bit is ON      (so far: 1)
     5 - 4 = 1    → the 4-bit is ON      (so far: 11)
     1 - 2? no    → the 2-bit is OFF     (so far: 110)
     1 - 1 = 0    → the 1-bit is ON      (so far: 1101)
  13 = 1101

METHOD 2 — Divide by 2, keep the remainders.

    13 ÷ 2 = 6  r 1     ↑
     6 ÷ 2 = 3  r 0     ↑
     3 ÷ 2 = 1  r 1     ↑
     1 ÷ 2 = 0  r 1     ↑

  Read the remainders BOTTOM to TOP:  1 1 0 1

Both methods give the same answer. Use whichever feels natural.
"""

LESSON_BIN2DEC = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: BINARY → DECIMAL                                    ║
╚══════════════════════════════════════════════════════════════╝
Write the place values above each bit, then add the ones that
sit under a 1.

     1   0   1   1   0   1
    32  16   8   4   2   1
     ↓       ↓   ↓       ↓
    32   +   8 + 4   +   1   =  45

SHORTCUT — "double and add", left to right:

    1        → 1
    1×2+0    → 2
    2×2+1    → 5
    5×2+1    → 11
   11×2+0    → 22
   22×2+1    → 45   ✔

This shortcut works for any length of binary number.
"""

LESSON_BITS = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: BITS, BYTES & POWERS OF TWO                         ║
╚══════════════════════════════════════════════════════════════╝
   1 bit  →    2 values   (0, 1)
   2 bits →    4 values   (00, 01, 10, 11)
   3 bits →    8 values
   4 bits →   16 values   ← a NIBBLE
   8 bits →  256 values   ← a BYTE

   n bits → 2^n values, numbered 0 .. 2^n − 1

Powers of two worth memorising:

   2^0 = 1        2^4  = 16       2^8  = 256
   2^1 = 2        2^5  = 32       2^10 = 1024   ("1 Kilo")
   2^2 = 4        2^6  = 64       2^16 = 65536
   2^3 = 8        2^7  = 128

Notice how fast they grow — that's why 8 bits is such a natural
size for a computer to work with.
"""

LESSON_COUNTING = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: COUNTING IN BINARY                                  ║
╚══════════════════════════════════════════════════════════════╝
  0  1  10  11  100  101  110  111  1000  1001 ...

Adding 1 follows a simple rule:
   • Flip every TRAILING 1 to 0
   • Then flip the first 0 you reach to 1

  1011  +  1
   ↑↑↑
   the two trailing 1s become 0s, the 0 becomes 1
       ↓
  1100

This is exactly like decimal 1999 + 1 = 2000, where the trailing
9s all become 0 and the next digit goes up.
"""

LESSON_ADDITION = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: BINARY ADDITION                                     ║
╚══════════════════════════════════════════════════════════════╝
  0 + 0 = 0
  0 + 1 = 1
  1 + 0 = 1
  1 + 1 = 10         (write 0, carry 1)
  1 + 1 + 1 = 11     (write 1, carry 1)

Example:

      0 1 1 0      (6)
   +  0 0 1 1      (3)
   -----------
      1 0 0 1      (9)

Work right to left, column by column — exactly like decimal
addition. The only difference is that you run out of digits
after 1 instead of after 9.
"""

LESSON_OCTAL = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: OCTAL (BASE 8)                                      ║
╚══════════════════════════════════════════════════════════════╝
Octal uses only the digits 0–7. Each position is a power of 8.

   8^0 = 1
   8^1 = 8
   8^2 = 64
   8^3 = 512

   2 5 1 (octal)  =  2×64  +  5×8  +  1×1
                  =  128   +  40   +   1   =  169

WHY DOES OCTAL EXIST?
Because 8 = 2^3, ONE octal digit maps to EXACTLY THREE binary
bits. Before hex became standard, octal was the favourite
shorthand on 12-bit and 36-bit machines.

   binary:  011 101 010
   octal:     3   5   2
"""

LESSON_HEX = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: HEXADECIMAL (BASE 16)                               ║
╚══════════════════════════════════════════════════════════════╝
Hex needs 16 digits, so after 9 we borrow letters:

   0 1 2 3 4 5 6 7 8 9   A  B  C  D  E  F
                        10 11 12 13 14 15

Place values are powers of 16:  1, 16, 256, 4096 ...

   2 F (hex)  =  2×16  +  15×1  =  32 + 15  =  47

WHERE YOU'LL SEE IT:
   • Web colors      #FF8800
   • Memory addresses 0x7FFE
   • MAC addresses   00:1A:2B:3C:4D:5E
   • Cryptographic hashes

Two hex digits = one byte. That's the whole reason it's popular.
"""

LESSON_NIBBLE = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: BINARY ↔ HEX  (4 BITS PER DIGIT)                    ║
╚══════════════════════════════════════════════════════════════╝
Because 16 = 2^4, every hex digit is EXACTLY 4 bits (a nibble).

   0000 = 0    0100 = 4    1000 = 8    1100 = C
   0001 = 1    0101 = 5    1001 = 9    1101 = D
   0010 = 2    0110 = 6    1010 = A    1110 = E
   0011 = 3    0111 = 7    1011 = B    1111 = F

TO CONVERT: split the binary into groups of 4, STARTING FROM THE
RIGHT. (Pad the leftmost group with zeros if needed.)

   1101 0110   →   D 6   →   0xD6

Converting to hex is now just table lookup — no division needed!
"""

LESSON_TRIAD = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: BINARY ↔ OCTAL  (3 BITS PER DIGIT)                  ║
╚══════════════════════════════════════════════════════════════╝
Because 8 = 2^3, every octal digit is EXACTLY 3 bits.

   000 = 0     001 = 1     010 = 2     011 = 3
   100 = 4     101 = 5     110 = 6     111 = 7

TO CONVERT: split the binary into groups of 3, STARTING FROM THE
RIGHT. Pad the leftmost group with zeros if needed.

   1 011 110   →   1  3  6   →   136 octal
   ↑
   this lone "1" is padded to 001

  1 011 110  =  001 011 110  =  1 3 6  =  136₈
"""

LESSON_RANGE = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: HOW MANY VALUES FIT?                                ║
╚══════════════════════════════════════════════════════════════╝
UNSIGNED (only zero and positive values):
      n bits  →  values  0  ..  2^n − 1
      8 bits  →  0 .. 255

SIGNED — two's complement:
      n bits  →  values  −2^(n−1)  ..  2^(n−1) − 1
      8 bits  →  −128 .. 127

THE KEY INSIGHT:
The SAME 8 bits can mean different things depending on how you
interpret them.

   1100 1000

   unsigned:            200
   signed (two's comp): −56

The bit pattern never changes — only the meaning does. This is
why type systems in programming languages matter so much.
"""

LESSON_TWOS = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: TWO'S COMPLEMENT                                    ║
╚══════════════════════════════════════════════════════════════╝
How do you store a NEGATIVE number with only 0s and 1s?

Two's complement, in three steps:
   1. Write the positive value in binary.
   2. Flip every bit  (0→1, 1→0).   ← "one's complement"
   3. Add 1.

EXAMPLE:  −5 in 8 bits

     +5   =  0000 0101
    flip  =  1111 1010
     +1   =  1111 1011      ← this is −5

THE MAGIC PROPERTY:
Add a number to its two's complement and you get ZERO (the final
carry falls off the end). That means the CPU can SUBTRACT using
only an adder circuit. That's why every modern computer uses it.

TO READ ONE: if the leftmost bit is 1, it's negative. Take the
unsigned value and subtract 2^n.

   1111 1011  →  251 unsigned  →  251 − 256  =  −5   ✔
"""

LESSON_LOGIC = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: BITWISE OPERATORS                                   ║
╚══════════════════════════════════════════════════════════════╝
These operators work column by column, one bit at a time.

   AND (&)  →  1 only if BOTH bits are 1
   OR  (|)  →  1 if AT LEAST ONE bit is 1
   XOR (^)  →  1 if the two bits are DIFFERENT
   NOT (~)  →  flips every bit

EXAMPLE:

      1010
   &  1100
   --------
      1000

REAL USES:
   • AND → masking off bits you don't want
   • OR  → setting specific flags
   • XOR → toggling bits on and off
   • XOR → also the basis of simple encryption and checksums
"""

LESSON_SHIFT = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: BIT SHIFTS                                          ║
╚══════════════════════════════════════════════════════════════╝
   x << n   (LEFT shift)
     Moves every bit n places left, padding with 0s.
     Same as multiplying by 2^n.

       0011  (3)  << 2  →  1100  (12)        3 × 4 = 12

   x >> n   (RIGHT shift)
     Moves every bit n places right. Bits that fall off are lost.
     Same as integer-dividing by 2^n.

       1100  (12) >> 2  →  0011  (3)        12 ÷ 4 = 3

WHY IT MATTERS:
Old CPUs had no multiply instruction — they just shifted.
Even today, compilers turn "x * 8" into "x << 3" because it's
faster.
"""

LESSON_OVERFLOW = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: OVERFLOW                                            ║
╚══════════════════════════════════════════════════════════════╝
A fixed-width register cannot hold arbitrarily large numbers.

   4-bit unsigned max = 1111 = 15

   1111 + 0001 = 1 0000

   ...but only 4 bits fit! The leading 1 falls off the end,
   leaving 0000 = 0.

This is OVERFLOW — the result "wraps around."

   • In unsigned arithmetic:  max + 1  →  0
   • In 8-bit signed:         127 + 1  →  −128

Sometimes it's a bug (spacecraft, banking software).
Sometimes it's intentional (hash functions, counters, crypto).

Knowing it exists is half the battle.
"""

LESSON_ASCII = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: ASCII — NUMBERS AS LETTERS                          ║
╚══════════════════════════════════════════════════════════════╝
Computers store numbers, not letters. ASCII assigns a number to
each character:

   '0' .. '9'  →  48 .. 57
   'A' .. 'Z'  →  65 .. 90
   'a' .. 'z'  →  97 .. 122
   ' '         →  32

So 'A' is really the byte 65, or 0100 0001 in binary.

A NICE TRICK:
   'a' − 'A' = 32

32 is 2^5 — a single bit! The 6th bit from the right is the
"lowercase flag." Flip it and you change the case of a letter.
That's how case-conversion worked in early software.
"""

LESSON_HEXCOLOR = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: HEX IN THE WILD — COLORS                            ║
╚══════════════════════════════════════════════════════════════╝
A CSS color like  #3F8AC2  is really three bytes:

     #  3F  8A  C2
        ↑   ↑   ↑
        R   G   B       (Red, Green, Blue — one byte each)

Each pair is 2 hex digits = 8 bits = a value from 0 to 255.

   #FF0000  =  pure red
   #00FF00  =  pure green
   #0000FF  =  pure blue
   #FFFFFF  =  white      (255, 255, 255)
   #000000  =  black      (0, 0, 0)

2 hex digits max out at FF = 255 — exactly one byte, exactly
one color channel. It's not a coincidence; it's a design.
"""

LESSON_ANYBASE = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: ANY BASE AT ALL                                     ║
╚══════════════════════════════════════════════════════════════╝
Everything you've learned generalises to any base.

   Base B uses digits 0 .. B−1
   Each position is a power of B

DECIMAL → BASE B:
   Divide by B repeatedly; read the remainders bottom-to-top.

   45 in base 6:
       45 ÷ 6 = 7  r 3     ↑
        7 ÷ 6 = 1  r 1     ↑
        1 ÷ 6 = 0  r 1     ↑
       →  113₆

BASE B → DECIMAL:
   Multiply each digit by its power of B and add.

   113₆  =  1×36  +  1×6  +  3×1  =  36 + 6 + 3  =  45  ✔

The only thing that changes between bases is B.
"""

LESSON_PARITY = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: PARITY BITS                                         ║
╚══════════════════════════════════════════════════════════════╝
A parity bit is the simplest form of error detection.

EVEN parity: choose the parity bit so the total number of 1s is
             EVEN.
ODD parity:  ...so the total is ODD.

EXAMPLE — the 7 bits  1011010  contain four 1s (even):

   even parity bit = 0   →   10110100   (still four 1s)
   odd  parity bit = 1   →   10110101   (five 1s)

If a single bit flips during transmission, the parity check
fails and the receiver knows something went wrong.

LIMITATION: it catches 1 flipped bit, but not 2.
For that you need a checksum or a hash.
"""

LESSON_ADDRESS = """
╔══════════════════════════════════════════════════════════════╗
║  LESSON: HEX IN THE WILD — ADDRESSES & NETWORKS              ║
╚══════════════════════════════════════════════════════════════╝
MEMORY ADDRESSES are almost always shown in hex, because hex is
a compact way to write binary.

   0x1F4  =  0001 1111 0100  =  500 decimal

IPv4 ADDRESSES are four octets (four bytes):

   192 . 168 . 1 . 10

   each octet is 0..255 — exactly one byte

   192 = 11000000
   168 = 10101000
     1 = 00000001
    10 = 00001010

Network engineers read these binary forms all day. Subnet masks,
routing tables, and firewall rules are all just bit patterns.
"""


# ══════════════════════════════════════════════════════════════════
#  SHOP
# ══════════════════════════════════════════════════════════════════

SHOP_ITEMS = [
    ("Healing Potion",  20, "Restore 15 HP"),
    ("Greater Potion",  45, "Restore FULL HP"),
    ("Shield Charm",    25, "Block damage from your next wrong answer"),
    ("Skip Rune",       30, "Skip a question (counts as a hit, no coins)"),
    ("Scholar's Tome",  35, "Reveal the answer + full explanation"),
    ("Lucky Coin",      15, "Double the coins from your next correct answer"),
]

def shop(player):
    print()
    title("⚒   THE WANDERING MERCHANT")
    while True:
        print(f"  Your coins: {player.coins}      HP: {player.hp}/{player.max_hp}")
        hr()
        for i, (name, cost, desc) in enumerate(SHOP_ITEMS, 1):
            print(f"  {i}. {name:<16} {cost:>3} coins   {desc}")
        print("  0. Leave")
        hr()
        choice = input("Buy which? ").strip().lower()
        if choice in ("0", "leave", "exit", "q", ""):
            print("\n  The merchant nods. 'Come back with more coins!'")
            break
        if not choice.isdigit() or not (1 <= int(choice) <= len(SHOP_ITEMS)):
            print("  'Pick a number from the list, friend.'")
            continue
        name, cost, _ = SHOP_ITEMS[int(choice) - 1]
        if player.coins < cost:
            print("  'Not enough coins for that one.'")
            continue
        player.coins -= cost
        if name == "Lucky Coin":
            player.lucky = True
            print("  🍀 You flip the Lucky Coin. Your next correct answer pays DOUBLE!")
        else:
            player.add_item(name)
            print(f"  ✔ Purchased {name}.  (Coins left: {player.coins})")

def shop_prompt(player):
    print()
    hr("═")
    ans = input("🏪  A merchant's lantern flickers nearby.  Visit the shop? (y/n) ").strip().lower()
    if ans.startswith("y"):
        shop(player)


# ══════════════════════════════════════════════════════════════════
#  CURRICULUM
# ══════════════════════════════════════════════════════════════════

CURRICULUM = {
    # ── TIER 1 : BINARY ──────────────────────────────────────────
    1:  ("The Iron Gate",          LESSON_BINARY,   [q_place_value, q_power_of_two, q_bin_to_dec_small]),
    2:  ("Hall of Halving",        LESSON_DEC2BIN,  [q_dec_to_bin_small, q_dec_to_bin_small, q_place_value]),
    3:  ("The Reading Room",       LESSON_BIN2DEC,  [q_bin_to_dec_small, q_bin_to_dec_small, q_power_of_two]),
    4:  ("Corridor of Conversion", None,            [q_dec_to_bin_small, q_bin_to_dec_small, q_dec_to_bin_small]),
    5:  ("Vault of Bits",          LESSON_BITS,     [q_count_values, q_power_of_two, q_place_value]),
    6:  ("The Counting Stair",     LESSON_COUNTING, [q_next_binary, q_next_binary, q_bin_to_dec_small]),
    7:  ("Deep Binary Halls",      None,            [q_dec_to_bin_mid, q_bin_to_dec_mid, q_dec_to_bin_mid]),
    8:  ("The Adder's Forge",      LESSON_ADDITION, [q_bin_addition, q_bin_addition, q_next_binary]),
    9:  ("Antechamber of Bits",    None,            [q_bin_addition, q_dec_to_bin_mid, q_bin_to_dec_mid]),
    10: ("BOSS: The Binary Behemoth", None,         None),

    # ── TIER 2 : OCTAL & HEX ─────────────────────────────────────
    11: ("The Octagon Gate",       LESSON_OCTAL,    [q_dec_to_oct, q_oct_to_dec]),
    12: ("Hall of Eights",         None,            [q_dec_to_oct, q_oct_to_dec, q_bin_to_oct]),
    13: ("The Octal Library",      None,            [q_oct_to_dec, q_bin_to_oct, q_oct_to_bin]),
    14: ("The Hex Vault",          LESSON_HEX,      [q_dec_to_hex, q_hex_to_dec]),
    15: ("Chamber of Sixteens",    None,            [q_dec_to_hex, q_hex_to_dec, q_dec_to_hex]),
    16: ("The Hex Library",        None,            [q_hex_to_dec, q_dec_to_hex, q_hex_to_bin]),
    17: ("The Nibble Bridge",      LESSON_NIBBLE,   [q_bin_to_hex, q_hex_to_bin]),
    18: ("The Triad Bridge",       LESSON_TRIAD,    [q_bin_to_oct, q_oct_to_bin]),
    19: ("Antechamber of Bases",   None,            [q_bin_to_hex, q_hex_to_dec, q_dec_to_oct]),
    20: ("BOSS: The Hexadecimal Hydra", None,       None),

    # ── TIER 3 : TWO'S COMPLEMENT & BITWISE ──────────────────────
    21: ("Hall of Ranges",         LESSON_RANGE,    [q_unsigned_max, q_count_values, q_unsigned_max]),
    22: ("The Mirror Room",        LESSON_TWOS,     [q_twos_comp_neg, q_twos_comp_read]),
    23: ("Chamber of Inversion",   None,            [q_twos_comp_neg, q_twos_comp_neg, q_twos_comp_read]),
    24: ("The Negative Depths",    None,            [q_twos_comp_read, q_twos_comp_neg, q_signed_range]),
    25: ("The AND / OR Altar",     LESSON_LOGIC,    [partial(q_bitwise, "AND"), partial(q_bitwise, "OR")]),
    26: ("The XOR Crypt",          None,            [partial(q_bitwise, "XOR"), partial(q_bitwise, "AND"),
                                                     partial(q_bitwise, "OR")]),
    27: ("The Shifting Sands",     LESSON_SHIFT,    [partial(q_shift, "left"), partial(q_shift, "right")]),
    28: ("The Overflow Pit",       LESSON_OVERFLOW, [q_overflow, q_unsigned_max]),
    29: ("Antechamber of Bits II", None,            [q_twos_comp_neg, partial(q_bitwise, "XOR"),
                                                     partial(q_shift, "left")]),
    30: ("BOSS: The Complement Colossus", None,     None),

    # ── TIER 4 : NUMBER SYSTEMS IN THE WILD ──────────────────────
    31: ("The Scribe's Hall",      LESSON_ASCII,    [q_char_to_bin, q_bin_to_char]),
    32: ("The Painter's Vault",    LESSON_HEXCOLOR, [q_hex_color, q_hex_color]),
    33: ("The Base Bazaar",        LESSON_ANYBASE,  [q_any_base, q_any_base]),
    34: ("The Parity Well",        LESSON_PARITY,   [q_parity, q_parity]),
    35: ("The Address Tunnels",    LESSON_ADDRESS,  [q_hex_address, q_ip_binary]),
    36: ("Chamber of Checksums",   None,            [q_parity, q_hex_address, q_any_base]),
    37: ("The Network Nexus",      None,            [q_ip_binary, q_bin_to_hex, q_hex_to_dec]),
    38: ("The Kernel's Antechamber", None,          [q_any_base, q_hex_color, q_twos_comp_neg]),
    39: ("The Final Gate",         None,            [q_bin_to_hex, q_any_base, q_parity]),
    40: ("FINAL BOSS: The Kernel of Chaos", None,   None),
}

MONSTERS = [
    "Bit Slime", "Nibble Rat", "Byte Bat", "Carry Gremlin",
    "Logic Wraith", "Hex Hound", "Overflow Ooze", "Parity Phantom",
    "Shift Shade", "Mantissa Mite", "Register Rustler", "Cache Creeper",
    "Nibble Knight", "Boolean Banshee", "Bitmask Basilisk",
]


# ══════════════════════════════════════════════════════════════════
#  BOSSES
# ══════════════════════════════════════════════════════════════════
def get_tier_pool(start_floor, end_floor, dedupe=False):
    """Collect question generators from floors in [start, end].

    If dedupe=True, each generator appears only once (uniform probability).
    If dedupe=False, duplicates are preserved (weighted toward core skills).
    """
    pool = []
    seen = set()
    for f in range(start_floor, end_floor + 1):
        if f not in CURRICULUM:
            continue
        _, _, gens = CURRICULUM[f]
        if not gens:
            continue
        for g in gens:
            if dedupe:
                if g not in seen:
                    seen.add(g)
                    pool.append(g)
            else:
                pool.append(g)
    return pool


def build_boss_pool(signature, tier, cross=None):
    """Combine sub-pools into a weighted list.

    signature: list of generators given heavy weight (designer's choice)
    tier:      list of generators given normal weight
    cross:     optional list of generators given lighter weight

    Returns a flat list where signature generators appear more often.
    """
    pool = []
    pool.extend(signature * 4)   # 4 copies → heavy weight
    pool.extend(tier * 2)        # 2 copies → normal weight
    if cross:
        pool.extend(cross * 1)   # 1 copy  → light weight
    return pool
BOSSES = {
    10: {
        "name": "THE BINARY BEHEMOTH",
        "max_hp": 5,
        "gens": build_boss_pool(
            signature=[q_bin_addition, q_dec_to_bin_mid],
            tier=get_tier_pool(1, 9, dedupe=True),
        ),
        "intro": (...),
        "outro": (...),
    },
    20: {
        "name": "THE HEXADECIMAL HYDRA",
        "max_hp": 5,
        "gens": build_boss_pool(
            signature=[q_bin_to_hex, q_hex_to_bin],
            tier=get_tier_pool(11, 19, dedupe=True),
            cross=[q_bin_addition, q_dec_to_bin_mid],
        ),
        "intro": (...),
        "outro": (...),
    },
    30: {
        "name": "THE COMPLEMENT COLOSSUS",
        "max_hp": 5,
        "gens": build_boss_pool(
            signature=[q_twos_comp_neg, partial(q_bitwise, "XOR"), partial(q_shift, "left")],
            tier=get_tier_pool(21, 29, dedupe=True),
            cross=[q_dec_to_bin_mid, q_bin_to_hex],
        ),
        "intro": (...),
        "outro": (...),
    },
    40: {
        "name": "THE KERNEL OF CHAOS",
        "max_hp": 6,
        "gens": build_boss_pool(
            signature=[q_hex_color, q_parity, q_ip_binary],
            tier=get_tier_pool(1, 39, dedupe=True),
        ),
        "intro": (...),
        "outro": (...),
    },
}
# ══════════════════════════════════════════════════════════════════
#  GAMEPLAY
# ══════════════════════════════════════════════════════════════════

def print_commands():
    print("""
  ┌─ COMMANDS ────────────────────────────────────────────────────┐
  │  hint / h        show a hint                (always free)      │
  │  potion / p      drink a healing potion                        │
  │  shield / c      use a Shield Charm                            │
  │  skip / s        use a Skip Rune                               │
  │  tome / t        use a Scholar's Tome                          │
  │  inventory / i   show your bag                                 │
  │                                                                │
  │  quit / exit     leave the dungeon                             │
  │  Ctrl + C        force-quit at any time                        │
  │                                                                │
  │  (or just type your answer)                                    │
  └────────────────────────────────────────────────────────────────┘""")

def show_inventory(player):
    print(f"\n  HP: {player.hp}/{player.max_hp}      Coins: {player.coins}")
    if not player.inventory:
        print("  Inventory: (empty)")
    else:
        print("  Inventory:")
        for item, count in player.inventory.items():
            print(f"    • {item} ×{count}")

def reveal(q):
    print()
    hr("·")
    print("📘  EXPLANATION")
    print()
    print(q["explain"])
    hr("·")


def ask(q, player, is_boss=False):
    """Prompt until the player gives an answer or uses an item.
       Returns: 'correct' | 'wrong' | 'skip' | 'tome'"""
    print()
    hr("─")
    print(q["prompt"])
    hr("─")
    print("  (type 'hint' for a free hint, 'help' for all commands)")

    while True:
        try:
            raw = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nThe dungeon fades away...")
            sys.exit(0)

        low = raw.lower()

        if not low:
            continue

        # ── free hint ─────────────────────────────────────────
        if low in ("hint", "h", "?"):
            print("\n💡  HINT")
            print(q["hint"])
            continue

        # ── help ──────────────────────────────────────────────
        if low == "help":
            print_commands()
            continue

        # ── inventory ─────────────────────────────────────────
        if low in ("inventory", "i", "bag", "inv"):
            show_inventory(player)
            continue

        # ── potions ───────────────────────────────────────────
        if low in ("potion", "p", "drink"):
            if player.hp >= player.max_hp:
                print("\n  You're already at full health.")
                continue
            if player.use_item("Healing Potion"):
                h = player.heal(15)
                print(f"\n  🧪 You drink a Healing Potion and recover {h} HP."
                      f"  (HP: {player.hp}/{player.max_hp})")
            elif player.use_item("Greater Potion"):
                h = player.heal(player.max_hp)
                print(f"\n  🧪 You drink a Greater Potion and recover {h} HP."
                      f"  (HP: {player.hp}/{player.max_hp})")
            else:
                print("\n  You have no potions.")
            continue

        # ── shield charm ──────────────────────────────────────
        if low in ("shield", "c"):
            if player.shield:
                print("\n  Your shield is already raised.")
            elif player.use_item("Shield Charm"):
                player.shield = True
                print("\n  🛡  You raise the Shield Charm. The next wrong answer won't hurt you.")
            else:
                print("\n  You have no Shield Charms.")
            continue

        # ── skip rune ─────────────────────────────────────────
        if low in ("skip", "s"):
            if player.use_item("Skip Rune"):
                print("\n  🌀 You crush the Skip Rune. A shimmering path opens —")
                print("     you bypass the puzzle entirely.")
                reveal(q)
                return "skip"
            else:
                print("\n  You have no Skip Runes.")
            continue

        # ── scholar's tome ────────────────────────────────────
        if low in ("tome", "t"):
            if player.use_item("Scholar's Tome"):
                print("\n  📖 You open the Scholar's Tome. The answer reveals itself...")
                print(f"\n  ➜  ANSWER: {q['answer']}")
                reveal(q)
                return "tome"
            else:
                print("\n  You have no Scholar's Tomes.")
            continue

        # ── evaluate the answer ───────────────────────────────
        if normalize(raw) == normalize(q["answer"]):
            return "correct"
        return "wrong"


def check_death(player):
    """Revive the player if they've fallen. Returns True if revived."""
    if player.hp <= 0:
        player.deaths += 1
        lost = player.coins // 2
        player.coins -= lost
        player.hp = player.max_hp
        print()
        hr("═")
        print("💀  You collapse...")
        print("    But the dungeon's magic refuses to let you go.")
        print(f"    You lose {lost} coins, but wake at full health.")
        print("    (The dungeon wants you to LEARN, not to die.)")
        hr("═")
        pause()
        return True
    return False


def run_normal_floor(floor, player):
    name, lesson, gens = CURRICULUM[floor]
    title(f"FLOOR {floor}  —  {name}")

    if lesson:
        print(lesson)
        pause()

    enemy = random.choice(MONSTERS)
    enemy_hp = random.choices([1, 2, 3], weights=[1, 4, 1])[0]
    print(f"\n⚔  A {enemy} blocks your path!   (Enemy HP: {enemy_hp})")

    while enemy_hp > 0:
        q = random.choice(gens)()
        result = ask(q, player, is_boss=False)
        print()

        if result in ("correct", "skip", "tome"):
            enemy_hp -= 1
            if result == "correct":
                reward = 10 + floor
                if player.lucky:
                    reward *= 2
                    player.lucky = False
                    print("🍀  Your Lucky Coin glows — DOUBLE coins!")
                player.coins += reward
                player.correct += 1
                print(f"✔  Correct! Your strike lands.")
                print(f"   {enemy} HP: {max(enemy_hp, 0)}      +{reward} coins   (total: {player.coins})")
            else:
                print(f"✔  You slip past the puzzle.")
                print(f"   {enemy} HP: {max(enemy_hp, 0)}")
            reveal(q)
        else:
            player.wrong += 1
            if player.shield:
                player.shield = False
                print("🛡  The Shield Charm absorbs the blow! No damage taken.")
            else:
                player.hp -= DAMAGE_NORMAL
                print(f"✘  Wrong! The {enemy} strikes you for {DAMAGE_NORMAL} damage.")
                print(f"   Your HP: {max(player.hp, 0)}/{player.max_hp}")
            reveal(q)
            if check_death(player):
                print(f"\nThe {enemy} reforms, but you feel steadier now.")
        print()

    print(f"🎉  The {enemy} dissolves into pixels. Floor {floor} cleared!")
    if floor % 5 == 0 or floor in (9, 19, 29, 39):
        player.heal(5)
        print("   The dungeon's calm air restores 5 HP.")


def run_boss(floor, player):
    boss = BOSSES[floor]
    title(f"FLOOR {floor}  —  {boss['name']}")
    print()
    print(boss["intro"])
    pause("\n[Press Enter to face it]")

    max_hp = boss["max_hp"]
    boss_hp = max_hp

    while boss_hp > 0:
        print()
        hr("═")
        print(f"🐲  {boss['name']}   HP: {boss_hp}/{max_hp}")
        hr("═")

        q = random.choice(boss["gens"])()
        result = ask(q, player, is_boss=True)
        print()

        if result in ("correct", "skip", "tome"):
            boss_hp -= 1
            if result == "correct":
                reward = 30 + floor * 2
                if player.lucky:
                    reward *= 2
                    player.lucky = False
                    print("🍀  Lucky Coin! Double coins!")
                player.coins += reward
                player.correct += 1
                print(f"⚔  Your answer strikes true!")
                print(f"   Boss HP: {max(boss_hp, 0)}/{max_hp}      +{reward} coins   (total: {player.coins})")
            else:
                print(f"⚔  You evade the puzzle.   Boss HP: {max(boss_hp, 0)}/{max_hp}")
            reveal(q)
        else:
            player.wrong += 1
            if player.shield:
                player.shield = False
                print("🛡  The Shield Charm absorbs the blast!")
            else:
                player.hp -= DAMAGE_BOSS
                print(f"✘  Wrong! {boss['name']} blasts you for {DAMAGE_BOSS} damage!")
                print(f"   Your HP: {max(player.hp, 0)}/{player.max_hp}")
            reveal(q)
            if check_death(player):
                boss_hp = max_hp
                print(f"\n{boss['name']} laughs and reforms — but you remember what you learned.")
                print("   The fight begins anew.")

    print()
    hr("═")
    print(boss["outro"])
    hr("═")
    print(f"\n🏆  {boss['name']} IS DEFEATED!")
    player.heal(player.max_hp)
    print("   A wave of energy restores you to full health.")


# ══════════════════════════════════════════════════════════════════
#  INTRO / OUTRO
# ══════════════════════════════════════════════════════════════════

def intro():
    print(r"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║           D U N G E O N   O F   B A S E S                 ║
    ║                                                           ║
    ║        A text adventure that teaches number systems       ║
    ║                 from computer science                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    print("  The dungeon has 40 floors. Every 10th floor holds a BOSS.")
    print()
    print("  You will learn: binary, octal, hexadecimal, two's complement,")
    print("  bitwise logic, and how all of it shows up in real computing.")
    print()
    hr("═")
    print("  HOW IT WORKS")
    hr("─")
    print("  • Each floor TEACHES a concept, then asks you to apply it.")
    print("  • Answer correctly to damage the enemy.")
    print("  • Wrong answers hurt YOU — but you'll always see the full")
    print("    explanation, so you never lose without learning something.")
    print("  • Stuck? Type  hint  at any time. Hints are always FREE.")
    print("    This is a teaching dungeon: understanding beats guessing.")
    print("  • Earn coins, buy supplies, and prepare before bosses.")
    print("  • If you fall, the dungeon revives you. You only lose coins.")
    hr("═")
    print()
    print("  COMMANDS DURING A QUESTION")
    print("    hint / h       show a hint (free, always available)")
    print("    potion / p     drink a healing potion")
    print("    shield / c     raise a Shield Charm")
    print("    skip / s       use a Skip Rune")
    print("    tome / t       use a Scholar's Tome")
    print("    inventory / i  show your bag")
    print("    quit / exit    leave the dungeon")
    print("    Ctrl + C       force-quit at any time")
    print()
    pause("  Press Enter to enter the dungeon...")
    print()


def ending(player):
    print()
    title("☀   YOU HAVE CLEARED THE DUNGEON OF BASES   ☀")
    print()
    print("  Forty floors. Four bosses. One idea.")
    print()
    print("  Every number system you met is the same machine:")
    print("  a set of symbols, and a place value for each position.")
    print("  Change the symbols and the base — the logic never changes.")
    print()
    hr("─")
    print("  YOUR RECORD")
    hr("─")
    total = player.correct + player.wrong
    acc = (player.correct / total * 100) if total else 0
    print(f"    Correct answers .......... {player.correct}")
    print(f"    Wrong answers ............ {player.wrong}")
    print(f"    Accuracy ................. {acc:.1f}%")
    print(f"    Times revived ............ {player.deaths}")
    print(f"    Coins remaining .......... {player.coins}")
    print()
    if acc >= 90:
        print("  The dungeon whispers: \"You didn't just memorise. You understood.\"")
    elif acc >= 70:
        print("  The dungeon whispers: \"Solid. Revisit what tripped you up.\"")
    else:
        print("  The dungeon whispers: \"You stumbled — but you kept going.\"")
        print("  That's the whole skill. Come back and try again.")
    print()
    print("  ═══════════════════════════════════════════════════════")
    print("   Next steps to explore on your own:")
    print("     • Binary fractions (0.101₂ = 0.625₁₀)")
    print("     • IEEE 754 floating point")
    print("     • Base64 encoding")
    print("     • Gray codes and error-correcting codes")
    print("  ═══════════════════════════════════════════════════════")
    print()
    pause("  Press Enter to leave the dungeon.")


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    intro()
    player = Player()

    for floor in range(1, MAX_FLOOR + 1):
        print()
        if floor in BOSS_FLOORS:
            run_boss(floor, player)
        else:
            run_normal_floor(floor, player)

        if floor < MAX_FLOOR:
            shop_prompt(player)

    ending(player)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nThe dungeon fades away. Until next time.\n")
        sys.exit(0)