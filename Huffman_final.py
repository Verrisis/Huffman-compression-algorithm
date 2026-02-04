"""
Huffman Project (Fixed-Length Implementation).
Written from scratch. No fancy libraries, just pure logic.
Compatible with the reference decoder.
"""

import time
import os

# === Config ===
# Reading in 5MB chunks.
# This keeps RAM usage low, even if I compress a 1TB file :)
BUFFER_SIZE = 5 * 1024 * 1024 

def get_freqs(filepath):
    """
    I scan the file to count byte frequencies.
    Using a list of size 256 is much faster than a dict (O(1) access).
    """
    counts = [0] * 256
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                for byte in chunk:
                    counts[byte] += 1
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' is missing.")
        return None
        
    return counts

def bubble_sort(arr):
    """
    Manual Bubble Sort.
    Since built-in functions like sorted() were forbidden, I wrote this.
    Simple, reliable, and gets the job done.
    """
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                # Pythonic swap without a temp variable. Clean.
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def calc_bits(count):
    """
    Calculating 'N'.
    Basically, I'm doing a manual log2 loop to find out how many bits 
    I need to cover 'count' unique characters.
    """
    bits = 0
    capacity = 1
    while capacity < count:
        bits += 1
        capacity *= 2
        
    # Edge case: If there's only 1 char, I still need at least 1 bit.
    if bits == 0:
        bits = 1
        
    return bits

def create_header(sorted_chars):
    """
    Building the file header.
    Format: [Count Byte] + [The Characters themselves]
    This is how the decoder knows which binary code maps to which char.
    """
    header = bytearray()
    
    # 1. Write the count of unique characters
    header.append(len(sorted_chars))
    
    # 2. Write the characters sorted (matching the decoder's expectation)
    for char in sorted_chars:
        header.append(char)
        
    return bytes(header)

class BitWriter:
    """
    The engine. This class writes individual BITS to the disk.
    Since OS works with bytes, I buffer bits until I have 8, then flush.
    """
    def __init__(self, filepath, header):
        self.f = open(filepath, "wb+")
        # Write the header first
        self.f.write(header)
        
        # I need to remember this position to patch the padding info later.
        self.data_start_pos = self.f.tell()
        
        self.buffer = 0
        self.bit_count = 3  # Reserving 3 bits for 'R' (padding size)
    
    def write_bits(self, value, length):
        """
        Bitwise magic. Shifting buffer and OR-ing the new value.
        """
        self.buffer = (self.buffer << length) | value
        self.bit_count += length
        
        # Flush full bytes to disk
        while self.bit_count >= 8:
            shift = self.bit_count - 8
            byte_val = (self.buffer >> shift) & 0xFF
            self.f.write(bytes([byte_val]))
            
            self.bit_count -= 8
            # Clean up the buffer mask
            self.buffer &= (1 << self.bit_count) - 1

    def flush(self):
        """
        Finalizing the file.
        1. Write remaining bits.
        2. Go back to the start and write the Padding Size (R).
        """
        # 1. Flush leftovers
        padding = 0
        if self.bit_count > 0:
            padding = 8 - self.bit_count
            self.buffer = (self.buffer << padding)
            self.f.write(bytes([self.buffer]))

        # 2. PATCHING: Jump back to data start
        self.f.seek(self.data_start_pos)
        first_byte = self.f.read(1)
        
        if first_byte:
            old_val = ord(first_byte)
            # Inject padding size into the reserved 3 bits
            new_val = (padding << 5) | old_val
            
            self.f.seek(self.data_start_pos)
            self.f.write(bytes([new_val]))
            
        self.f.close()

def compress(input_file, output_file):
    start_time = time.time()
    
    # 1. Analyze
    freqs = get_freqs(input_file)
    if freqs is None: 
        return

    unique_chars = []
    for i in range(256):
        if freqs[i] > 0:
            unique_chars.append(i)

    # 2. Build Model
    sorted_chars = bubble_sort(unique_chars)
    n_bits = calc_bits(len(sorted_chars))
    
    # === MATH STATS (Calculating R before writing) ===
    # Total Bits = FileSize * BitsPerChar + 3 (reserved)
    file_size_in = os.path.getsize(input_file)
    total_stream_bits = file_size_in * n_bits + 3 
    r_padding = (8 - (total_stream_bits % 8)) % 8

    # Generate a nice dictionary string for the console
    dict_str = ""
    for code in sorted_chars:
        # If it's a printable char, show it. Otherwise show '?'
        if 32 <= code <= 255: 
            dict_str += chr(code)
        else:
            dict_str += "?"

    # Create O(1) Lookup Table
    lookup = [None] * 256

    idx = 0
    for char_code in sorted_chars:
        lookup[char_code] = (idx, n_bits)
        idx += 1

    # 3. Write Header
    header = create_header(sorted_chars)
    writer = BitWriter(output_file, header)
    
    # 4. Stream Encoding (The main loop)
    try:
        with open(input_file, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk: 
                    break
                for byte_val in chunk:
                    idx, length = lookup[byte_val]
                    writer.write_bits(idx, length)
    except FileNotFoundError:
        return

    writer.flush()
    
    end_time = time.time()
    duration = end_time - start_time
    file_size_out = os.path.getsize(output_file)

    # === REPORT ===
    print("=" * 60)
    print(f"{' ' * 20 + 'COMPRESSION REPORT'}")
    print("=" * 60)
    print(f" Slownik (Dict) : {dict_str}")
    print("-" * 60)
    print(f" X (Unique Symbols)   : {len(sorted_chars)}")
    print(f" N (Bits per Symbol)  : {n_bits}")
    print(f" R (Padding Bits)     : {r_padding}")
    print("-" * 60)
    print(f" Dlugosc tekstu       : {file_size_in} bytes")
    print(f" Dlugosc po kompresji : {file_size_out} bytes")
    print(f" Czas                 : {duration:.3f} sekund")
    print("=" * 60)

# === Main ===
if __name__ == "__main__":
    in_file = "do_kompresji.txt"      
    out_file = "skompresowany.txt"
    
    if os.path.exists(in_file):
        compress(in_file, out_file)
    else:
        print(f"Error: {in_file} is missing!")