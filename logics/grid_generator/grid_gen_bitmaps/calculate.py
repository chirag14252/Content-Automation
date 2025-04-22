import json
from collections import defaultdict

input_file = "list.tsv"
output_file = "calc.json"

def create_word_length_mapping():
    # Create a defaultdict to store words by their length
    word_length_map = defaultdict(list)
    
    # Read the input file and process each word
    with open(input_file, 'r') as f:
        # Skip the header line 'word'
        next(f)
        
        # Process each word
        seen_words = set()
        for line in f:
            word = line.strip()
            # Only add the word if we haven't seen it before
            if word not in seen_words:
                seen_words.add(word)
                # Add the word to its corresponding length list
                word_length_map[len(word)].append(word)
    
    # Convert defaultdict to regular dict and sort the words in each list
    result = {}
    for length in sorted(word_length_map.keys()):
        result[str(length)] = sorted(word_length_map[length])
    
    # Write the result to a JSON file
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print("Word length mapping has been created and saved to output file")
    
    # Print some statistics
    print("\nStatistics:")
    for length, words in result.items():
        print(f"Length {length}: {len(words)} words")

# File paths


# Create the mapping
create_word_length_mapping()