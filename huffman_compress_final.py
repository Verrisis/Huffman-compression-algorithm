# Configuration
BUFFER_SIZE = 5 * 1024 * 1024  # Read 5MB chunks. In case someone wants to compress a 1TB file :)

def get_frequencies(filepath):
    """
    Reads the file piece by piece and counts frequencies.
    I use a list of 256 zeros instead of a dict because it's O(1) access.
    """
    frequency = [0] * 256
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                for byte in chunk:
                    # Using byte value as index (Counting Sort style)
                    frequency[byte] += 1
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return None
        
    return frequency

class Node:
    """
    Represents a point in the Huffman tree.
    """
    def __init__(self, byte_value, frequency):
        self.byte_value = byte_value
        self.frequency = frequency
        self.left = None
        self.right = None

    # Overriding '<' for comparison
    def __lt__(self, other):
        # Priority 1: Frequency
        if self.frequency != other.frequency:
            return self.frequency < other.frequency
        
        # Priority 2: Byte value (stability fix).
        # None (internal nodes) treated as 256 to go to the end.
        val_self = self.byte_value if self.byte_value is not None else 256
        val_other = other.byte_value if other.byte_value is not None else 256
        
        return val_self < val_other

def find_min_index(nodes):
    """
    Finds the index of the node with the smallest frequency.
    Written manually to avoid 'heapq' imports - keeping it algorithmic.
    """
    min_index = 0
    for i in range(1, len(nodes)):
        if nodes[i] < nodes[min_index]:
            min_index = i
    return min_index

def build_tree(nodes):
    """
    Merges nodes until one Root remains.
    """
    while len(nodes) > 1:
        # 1. Grab the two smallest nodes
        index_left = find_min_index(nodes)
        left_node = nodes.pop(index_left)
        
        index_right = find_min_index(nodes)
        right_node = nodes.pop(index_right)
        
        # 2. Create a parent 'container' node
        parent = Node(None, left_node.frequency + right_node.frequency)
        parent.left = left_node
        parent.right = right_node
        
        # 3. Throw the parent back into the pile
        nodes.append(parent)
    
    return nodes[0]

def generate_codes(node, current_path, codes):
    """
    Recursive traversal to build '0' and '1' strings.
    """
    if node is None:
        return
    
    if node.byte_value is not None:
        codes[node.byte_value] = current_path
        return
    
    generate_codes(node.left, current_path + "0", codes)
    generate_codes(node.right, current_path + "1", codes)

def create_lookup_table(codes):
    """
    Converts string codes (e.g. "101") into integers using manual bitwise loop.
    This creates a lookup table for O(1) encoding speed.
    """
    lookup = [(0, 0)] * 256
    for i in range(256):
        code_str = codes[i]
        if code_str:
            # Manual binary to int conversion (Horner's method)
            # instead of using int(x, 2) shortcut.
            val = 0
            for char in code_str:
                val = val << 1       # Shift left (multiply by 2)
                if char == '1':
                    val = val | 1    # Set the last bit to 1
            
            length = len(code_str)
            lookup[i] = (val, length)

    return lookup

class BitWriter:
    """
    Writes bits to file using a buffer.
    Optimized to write chunks of bits instead of loop-per-bit.
    """
    def __init__(self, filepath, header):
        self.file = open(filepath, "wb")
        self.file.write(header)
        
        # Placeholder for padding size
        self.padding_position = self.file.tell()
        self.file.write(bytes([0]))
        
        self.buffer = 0
        self.bit_count = 0

    def write_int(self, value, length):
        """
        Writes 'length' bits from 'value' into the buffer.
        """
        # Shift buffer to make room for new bits
        self.buffer = (self.buffer << length) | value
        self.bit_count += length
        
        # Flush full bytes to disk
        while self.bit_count >= 8:
            shift_amount = self.bit_count - 8
            # Extract top 8 bits
            byte_to_write = (self.buffer >> shift_amount) & 0xFF
            self.file.write(bytes([byte_to_write]))
            
            self.bit_count -= 8
            # Clean the buffer mask (keep only remaining bits)
            self.buffer &= (1 << self.bit_count) - 1

    def flush(self):
        """
        Saves remaining bits and writes padding info.
        """
        padding_size = 0
        if self.bit_count > 0:
            padding_size = 8 - self.bit_count
            self.buffer = (self.buffer << padding_size)
            self.file.write(bytes([self.buffer]))

        # Write real padding size at the beginning
        self.file.seek(self.padding_position)
        self.file.write(bytes([padding_size]))
        
        self.file.close()

def create_header(frequency_array):
    """
    Creates metadata: [UniqueCount] + [Byte][Freq]...
    """
    data = bytearray()
    unique_count = 0

    for byte_value in range(256):
        count = frequency_array[byte_value]
        if count > 0:
            unique_count += 1
            data.append(byte_value)
            # Big Endian (Standard for file formats)
            data.extend(count.to_bytes(4, byteorder='big'))

    # Store (Count - 1) to fit 256 into a single byte (0-255)
    final_count_byte = (unique_count - 1) % 256
    
    return bytes([final_count_byte]) + data

def compress_file(input_file, output_file):
    print(f"=== Processing: {input_file} ===")
    
    # 1. Analysis Pass
    print("Pass 1: Analyzing frequencies...")
    frequency_array = get_frequencies(input_file)
    if frequency_array is None:
        return

    nodes = []
    for i in range(256):
        if frequency_array[i] > 0:
            nodes.append(Node(i, frequency_array[i]))
            
    if not nodes:
        print("Error: File is empty.")
        return

    # 2. Build Model
    print("Building Huffman tree...")
    root = build_tree(nodes)
    
    codes = [""] * 256
    generate_codes(root, "", codes)
    
    # Optimization: Create Lookup Table
    print("Creating lookup table (manual bitwise calculation)...")
    lookup_table = create_lookup_table(codes)
    
    # 3. Create Header
    header_data = create_header(frequency_array)
    
    # 4. Encoding Pass
    print("Pass 2: Fast encoding...")
    writer = BitWriter(output_file, header_data)
    
    try:
        with open(input_file, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                for byte_value in chunk:
                    # O(1) Access - fast!
                    val, length = lookup_table[byte_value]
                    writer.write_int(val, length)
                    
    except FileNotFoundError:
        print("Error: Input file lost.")
        return

    writer.flush()
    print(f"Success! Saved to: {output_file}")

# --- Main Execution ---
if __name__ == "__main__":
    input_filename = "test.txt"      
    output_filename = "compressed.bin" 
    
    compress_file(input_filename, output_filename)