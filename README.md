# Custom Bit-Packing File Compressor

A low-level, memory-efficient file compression and decompression tool written in pure Python. Built from scratch without external libraries to demonstrate bitwise operations, manual memory buffering, and custom algorithmic logic.

## Key Features

*   **Low-Level Bitwise Manipulation:** Bypasses Python's standard byte-level operations. Implements custom bit-shifting, masking (`&`, `|`), and a bit-buffer state machine to pack fractional bytes (e.g., 5-bit or 3-bit characters) directly to disk.
*   **Memory-Efficient Chunking:** Capable of compressing massive files (GB/TB scale) on low-end machines. Both encoder and decoder read/write in strict 5MB/1MB chunks, ensuring RAM usage remains flat regardless of file size.
*   **Zero Dependencies:** Strictly uses standard libraries. Even sorting is handled via a custom algorithm implementation (`bubble_sort`) instead of relying on Python's built-in `sorted()`.
*   **Algorithmic File Seeking:** The decompressor calculates padding and stream positions using algebraic formulas and `f.seek()`, rather than looping through the file.

## Tech Stack
*   **Language:** Python 3
*   **Techniques:** Bitwise Operations, Stream Processing, Context Managers, Algorithmic Big-O optimization.

## How to use

**Compress a file:**
Configure `in_file` in the script and run:
```bash
python compress.py

```

*Outputs a compression report including dictionary size, bits per symbol (N), and processing time.*

**Decompress a file:**
Configure target files and run:

```bash
python decompress.py

```

## Technical Highlights

The algorithm calculates the strict minimum amount of bits needed for the unique characters in a file (Fixed-Length Encoding). For example, if a file only contains 4 unique ASCII characters, the engine will pack every character into exactly 2 bits, effectively reducing the file size by 75% without relying on variable-length prefix codes.
