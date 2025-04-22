import json
import csv
from typing import Dict, List
from bitmap_array import BitArray, zero, set_bit, active_bits

def generate_bitmap_index() -> Dict:
    # Read words from TSV
    words_by_length: Dict[int, List[str]] = {}
    with open('list.tsv') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            word = row['words']
            length = len(word)
            if length not in words_by_length:
                words_by_length[length] = []
            words_by_length[length].append(word.upper())

    # Initialize result structure
    result = {
        'bitmaps': {},
        'words': words_by_length
    }

    # Generate bitmaps for each word length
    for length, words in words_by_length.items():
        # Create bitmap for all words of this length
        length_bitmap_key = f"{length}__"
        length_bitmap: BitArray = zero()
        for word_idx in range(len(words)):
            set_bit(length_bitmap, word_idx)
        result['bitmaps'][length_bitmap_key] = length_bitmap

        # For each position in words of this length
        for pos in range(length):
            # For each possible letter
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                # Create key like "3A0" for 3-letter words with A at pos 0
                bitmap_key = f"{length}{letter}{pos}"
                bitmap: BitArray = zero()

                # Set bits for matching words
                for word_idx, word in enumerate(words):
                    if pos < len(word) and word[pos] == letter:
                        set_bit(bitmap, word_idx)

                result['bitmaps'][bitmap_key] = bitmap
    

    return result

# Generate and save the index
index = generate_bitmap_index()

# Custom JSON encoder to handle BitArray (list[int])
class BitArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, list) and all(isinstance(x, int) for x in obj):
            return obj
        return json.JSONEncoder.default(self, obj)

# Save to JSON file
with open('calc.json', 'w') as f:
    json.dump(index, f, cls=BitArrayEncoder, indent=2)



# Testing for fetching the matching words
# def print_matching_words(bitmap_key: str, index: dict):
#     # Parse the bitmap key to get length and position
#     length = int(bitmap_key[0])
    
#     # Get the bitmap for this key
#     bitmap = index['bitmaps'].get(bitmap_key)
#     if not bitmap:
#         print(f"No bitmap found for key {bitmap_key}")
#         return
        
#     # Get word list for this length
#     words = index['words'].get(length, [])
#     if not words:
#         print(f"No words found of length {length}")
#         return
        
#     # Get matching word indexes
#     matching_indexes = active_bits(bitmap)
    
#     # Print all matching words
#     print(f"\nWords matching pattern {bitmap_key}:")
#     for idx in matching_indexes:
#         if idx < len(words):
#             print(words[idx])

# print_matching_words("5B3", index)