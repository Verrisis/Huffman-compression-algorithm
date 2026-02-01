# Configuration
BUFFER_SIZE = 5 * 1024 * 1024  # Read 5MB at a time (in case someone wants to compress 1TB file :))

def get_frequencies(filepath):
    """
    Reads the file piece by piece and counts how many times each byte appears.
    I use a list of 256 zeros instead of a dictionary because it's faster.
    """
    frequency = [0] * 256
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                for byte in chunk:
                    frequency[byte] += 1
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return None
        
    return frequency

class Node:
    """
    A single point in the Huffman tree.
    It holds the byte (if it's a leaf) and its frequency count.
    Also connects to left and right children.
    """
    def __init__(self, byte_value, frequency):
        self.byte_value = byte_value
        self.frequency = frequency
        self.left = None
        self.right = None

    # This allows me to compare two nodes using '<'
    def __lt__(self, other):
        # Compare by frequency first (smaller is better)
        if self.frequency != other.frequency:
            return self.frequency < other.frequency
        
        # If frequencies are equal, compare byte values to keep order stable
        # Treating 'None' (internal nodes) as 256 so they go to the end
        val_self = self.byte_value if self.byte_value is not None else 256
        val_other = other.byte_value if other.byte_value is not None else 256
        
        return val_self < val_other

def find_min_index(nodes):
    """
    Finds the position of the node with the smallest frequency.
    I wrote this manually to avoid using 'heapq' or other imports.
    """
    min_index = 0
    for i in range(1, len(nodes)):
        if nodes[i] < nodes[min_index]:  # Uses the __lt__ logic from Node class
            min_index = i
    return min_index

def build_tree(nodes):
    """
    Creates the Huffman tree.
    Logic: Take the two smallest nodes, combine them into a parent, 
    and put the parent back. Repeat until only one Root node remains.
    """
    while len(nodes) > 1:
        # 1. Find and remove the smallest node
        index_left = find_min_index(nodes)
        left_node = nodes.pop(index_left)
        
        # 2. Find and remove the second smallest node
        index_right = find_min_index(nodes)
        right_node = nodes.pop(index_right)
        
        # 3. Create a parent node that combines their frequencies
        parent = Node(None, left_node.frequency + right_node.frequency)
        parent.left = left_node
        parent.right = right_node
        
        # 4. Add the new parent back to the list
        nodes.append(parent)
    
    return nodes[0]  # The root of the tree

def generate_codes(node, current_path, codes):
    """
    Walks through the tree to create binary codes ('0' or '1').
    Left turn = '0', Right turn = '1'.
    When I reach a leaf (a byte), I save the code.
    """
    if node is None:
        return
    
    # Found a real byte! Save the path.
    if node.byte_value is not None:
        codes[node.byte_value] = current_path
        return
    
    # Keep going deeper
    generate_codes(node.left, current_path + "0", codes)
    generate_codes(node.right, current_path + "1", codes)

class BitWriter:
    """
    Helper class to write bits.
    Since computers write bytes (8 bits), I collect bits in a 'buffer'.
    When the buffer is full (8 bits), I write it to the file.
    """
    def __init__(self, filepath, header):
        self.file = open(filepath, "wb")
        
        # Write the dictionary first so we can decode later
        self.file.write(header)
        
        # Save this spot! We will come back here to write the padding size.
        self.padding_position = self.file.tell()
        self.file.write(bytes([0]))  # Placeholder
        
        self.buffer = 0
        self.bit_count = 0

    def write_bit(self, bit_val):
        bit = int(bit_val)
        
        # Shift bits to the left and add the new one
        self.buffer = (self.buffer << 1) | bit
        self.bit_count += 1
        
        # If I have a full byte, write it down and clear buffer
        if self.bit_count == 8:
            self.file.write(bytes([self.buffer]))
            self.buffer = 0
            self.bit_count = 0

    def flush(self):
        """
        Saves the last remaining bits and writes the padding info.
        """
        padding_size = 0
        if self.bit_count > 0:
            padding_size = 8 - self.bit_count
            # Move bits to the correct position (left alignment)
            self.buffer = (self.buffer << padding_size)
            self.file.write(bytes([self.buffer]))

        # Go back to the beginning placeholder and write the real padding size
        self.file.seek(self.padding_position)
        self.file.write(bytes([padding_size]))
        
        self.file.close()

def create_header(frequency_array):
    """
    Creates the file header.
    Format: [UniqueCount-1] + [Byte][Freq] + [Byte][Freq]...
    """
    data = bytearray()
    unique_count = 0

    for byte_value in range(256):
        count = frequency_array[byte_value]
        if count > 0:
            unique_count += 1
            data.append(byte_value)
            # Write frequency as 4 bytes (Big Endian)
            data.extend(count.to_bytes(4, byteorder='big'))

    # Fix for the "256 problem": 
    # A byte can only hold 0-255. If we have 256 unique symbols, it breaks.
    # So I subtract 1. The decoder must add 1 back.
    final_count_byte = (unique_count - 1) % 256
    
    return bytes([final_count_byte]) + data

def compress_file(input_file, output_file):
    print(f"=== Processing: {input_file} ===")
    
    # 1. First Pass: Count how often each byte appears
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

    # 2. Build the Tree and Codes
    print("Building Huffman tree...")
    root = build_tree(nodes)
    
    codes = [""] * 256
    generate_codes(root, "", codes)
    
    # 3. Prepare the Header (Dictionary)
    header_data = create_header(frequency_array)
    
    # 4. Second Pass: Read file again and write compressed bits
    print("Pass 2: Encoding and writing to file...")
    writer = BitWriter(output_file, header_data)
    
    try:
        with open(input_file, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                for byte_value in chunk:
                    code_string = codes[byte_value]
                    # Write the code bit by bit
                    for bit_char in code_string:
                        writer.write_bit(bit_char)
    except FileNotFoundError:
        print("Error: Input file lost during second pass.")
        return

    writer.flush()
    print(f"Success! Saved to: {output_file}")

# --- Main Execution ---
if __name__ == "__main__":
    # Change filenames here
    input_filename = "VID_20260113_204111.mp4"      
    output_filename = "compressed.bin" 
    
    compress_file(input_filename, output_filename)