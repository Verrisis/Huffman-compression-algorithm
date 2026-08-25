"""
Huffman Decompressor.
Algorithmic approach with Python best practices (Context Managers).
Complexity: O(N). Memory: Fixed Buffer.
"""

import time

# === Configuration ===
# Read 5MB at a time (Input Optimization)
INPUT_BUFFER_SIZE = 5 * 1024 * 1024  
# Write every 1MB (Output Optimization)
OUTPUT_BUFFER_LIMIT = 1 * 1024 * 1024 

def calc_bits(count):
    """
    Calculate bits needed for 'count' unique characters.
    """
    bits = 0
    capacity = 1
    while capacity < count:
        bits += 1
        capacity *= 2
    if bits == 0: 
        bits = 1
    return bits

def get_header(f):
    """
    Read the dictionary header.
    Format: [1 byte length] + [characters]
    """
    byte = f.read(1)
    if not byte: 
        return None

    length = ord(byte)
    data = f.read(length)
    
    # Return list of integer codes
    return list(data)

def decompress(input_path, output_path):
    print(f"-> Rozpoczynam dekompresje: {input_path}")
    start_time = time.time()

    # 1. Open Files safely using Context Manager
    try:
        with open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
            
            # 2. Parse Header
            header_dict = get_header(f_in)
            if not header_dict:
                print("Blad: Pusty lub uszkodzony plik.")
                return

            # Algorithm constants
            n_bits = calc_bits(len(header_dict))
            header_size = 1 + len(header_dict)

            # 3. Get Data Size (Algorithmic Seek)
            f_in.seek(0, 2)         # Go to end
            file_size = f_in.tell() # Get position
            data_size = file_size - header_size
            
            if data_size <= 0: 
                return

            # Go back to start of data
            f_in.seek(header_size)

            # 4. Read The First Byte (Padding Logic)
            first_byte = ord(f_in.read(1))
            
            padding = first_byte >> 5            # Trash bits
            data_bits = first_byte & 0b00011111  # Clean data
            
            # 5. Initialize State Machine
            bit_buffer = data_bits  # Bit container
            bit_count = 5           # Bits available
            
            # Output buffer (Mutable array for speed)
            output_buffer = bytearray()
            
            # Stop condition
            total_bits = (data_size * 8) - padding - 3
            processed_bits = 0

            # Pre-calculate mask
            mask = (1 << n_bits) - 1

            # === MAIN DECODING LOOP ===
            while True:
                
                # Part A: Process RAM buffer (Fast)
                while bit_count >= n_bits:
                    if processed_bits >= total_bits:
                        break
                    
                    # 1. Extract N bits
                    shift = bit_count - n_bits
                    index = (bit_buffer >> shift) & mask
                    
                    # 2. Add to output buffer
                    output_buffer.append(header_dict[index])
                    
                    # 3. Update counters
                    bit_count -= n_bits
                    processed_bits += n_bits

                    # 4. Flush to disk if full
                    if len(output_buffer) >= OUTPUT_BUFFER_LIMIT:
                        f_out.write(output_buffer)
                        output_buffer = bytearray() # Reset buffer

                # CRITICAL: Garbage collect used bits to prevent BigInt slowdown
                bit_buffer &= (1 << bit_count) - 1

                if processed_bits >= total_bits:
                    break

                # Part B: Read from disk
                chunk = f_in.read(INPUT_BUFFER_SIZE)
                if not chunk:
                    break
                
                # Part C: Feed the machine
                for byte in chunk:
                    # Shift left and add new byte
                    bit_buffer = (bit_buffer << 8) | byte
                    bit_count += 8
                    
                    # Process immediately
                    while bit_count >= n_bits:
                        if processed_bits >= total_bits:
                            break
                        
                        shift = bit_count - n_bits
                        index = (bit_buffer >> shift) & mask
                        
                        output_buffer.append(header_dict[index])
                        
                        if len(output_buffer) >= OUTPUT_BUFFER_LIMIT:
                            f_out.write(output_buffer)
                            output_buffer = bytearray()

                        bit_count -= n_bits
                        processed_bits += n_bits
                    
                    # Clean buffer inside the loop too
                    bit_buffer &= (1 << bit_count) - 1

            # Final flush of remaining data
            if len(output_buffer) > 0:
                f_out.write(output_buffer)

    except FileNotFoundError:
        print("Blad: Nie znaleziono pliku.")
        return

    duration = time.time() - start_time
    
    # === RAPORT ===
    print("=" * 40)
    print("DEKOMPRESJA ZAKONCZONA SUKCESEM")
    print("=" * 40)
    print(f" Rozmiar Slownika : {len(header_dict)} znakow")
    print(f" Szerokosc (N)    : {n_bits} bitow")
    print(f" Padding (R)      : {padding} bitow")
    print("-" * 40)
    print(f" Czas             : {duration:.4f} sek")
    print("=" * 40)

if __name__ == "__main__":
    decompress("skompresowany.txt", "zdekompresowany.txt")