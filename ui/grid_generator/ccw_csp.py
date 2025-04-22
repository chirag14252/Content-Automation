import json
import random
from logics.grid_generator.grid_gen_bitmaps import constant as const
from logics.grid_generator.grid_gen_bitmaps.crossowrd import *
import traceback,time
from copy import deepcopy,copy
import time
import csv
import re
import streamlit as st
import os
import zipfile
import io
import base64

from logics.grid_generator.grid_gen_bitmaps.bitmap_array import active_bits, and_bits, in_place_and, bit_count, zero, set_bit, unset_bit,count_set_bits

logics_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                          "logics", "grid_generator", "grid_gen_bitmaps")

class CrosswordCreator():
    
    
    def __init__(self, crossword,maps,use_quick_check=False):
        """
        Create new CSP crossword generate.
        """
        self.bitmap_map = deepcopy(maps)
        self.crossword = crossword
        self.other_counts=0
        self.max_other_counts=5
        self.num_variables=len(self.crossword.variables)
        self.max_time=time.time()+5 if use_quick_check else time.time()+1
        self.words_in_grid=set()
        self.groups_in_grid={}
        self.domains = {
            var: self.get_word_choices_bitmap(var,self.bitmap_map)
            for var in self.crossword.variables
        }
        sum_of_domains=0
        len_set=set()
        for var in self.domains:
            if var.length not in len_set:
                len_set.add(var.length)
                sum_of_domains+=bit_count(self.domains[var])
        print(sum_of_domains)
        print(len_set)
            
    def get_word_list_for_bitmaps(self,var):
        bitmap=self.domains[var] 
        matching_indexes = active_bits(bitmap)
        return [[self.bitmap_map["words"][str(var.length)][i],i] for i in matching_indexes]


    def get_word_choices_bitmap(self,var,maps):
        # Get bitmap key for words of this length
        length_bitmap_key = f"{var.length}__"
        # print(bit_count(maps['bitmaps'][length_bitmap_key]),len(maps['words'][str(var.length)]))
        # for i in maps['bitmaps'][length_bitmap_key]: 
            # print(length_bitmap_key,i,count_set_bits(i))
        # Get the bitmap for this length from maps
        return deepcopy(maps['bitmaps'][length_bitmap_key])

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        # letters = self.letter_grid(assignment)
        filled_grid=deepcopy(self.crossword.grid)

        for var in assignment:
            word = assignment[var][0]
            start_r,start_c,direction,length=var.i,var.j,var.direction,var.length
            inc=[0,1]
            if direction=="down":
                inc=[1,0]
            r,c=start_r,start_c
            len=0
            while len<length:
                filled_grid[r][c]=word[len]
                r,c=r+inc[0],c+inc[1]
                len+=1
        return filled_grid
    
    def solve_bitmap(self,use_quick_check=False, interleaving=True,):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        for var in self.domains:
            if len(self.domains[var])<=0:
                return False

        # self.enforce_node_consistency()
        if not interleaving:
            print('Solving Crossword with single arc consistency enforcement...')
            return self.backtrack(dict())
        else:
            print('Solving Crossword with interleaved backtracking and arc consistency enforcement... QUICK CHECK:',use_quick_check)
            return self.backtrack_ac3(dict(),use_quick_check)

    # def solve(self, interleaving=True):
    #     """
    #     Enforce node and arc consistency, and then solve the CSP.
    #     """
    #     for var in self.domains:
    #         if len(self.domains[var])<=0:
    #             return False

    #     # self.enforce_node_consistency()

    #     if not self.ac3():
    #         print_grid(self.crossword.grid)
    #         print("can't be filled")
    #         return False

    #     if not interleaving:
    #         print('Solving Crossword with single arc consistency enforcement...')
    #         return self.backtrack(dict())
    #     else:
    #         print('Solving Crossword with interleaved backtracking and arc consistency enforcement...')
    #         return self.backtrack_ac3(dict())
        
 

    def overlap_satisfied(self, x, y, val_x, val_y):
            """
            Helper function that returns true if val_x and val_y
            satisfy any overlap arc consistency requirement for
            variables x and y.

            Returns True if consistency is satisfied, False otherwise.
            """

            # If no overlap, no arc consistency to satisfy
            if not self.crossword.overlaps[x, y]:
                return True

            # Otherwise check that letters match at overlapping indices
            else:
                x_index, y_index = self.crossword.overlaps[x,y]
                if val_x[x_index] == val_y[y_index]:
                    return True
                else:
                    return False
                
    # def revise(self, x, y):
    #     """
    #     Make variable `x` arc consistent with variable `y`.
    #     To do so, remove values from `self.domains[x]` for which there is no
    #     possible corresponding value for `y` in `self.domains[y]`.

    #     Return True if a revision was made to the domain of `x`; return
    #     False if no revision was made.
    #     """

    #     revision = False
    #     to_remove = set()

    #     # Iterate over domain of x and y, track any inconsistent x:
    #     for val_x in self.domains[x]:
    #         consistent = False
    #         for val_y in self.domains[y]:
    #             if val_x != val_y and self.overlap_satisfied(x, y, val_x, val_y):
    #                 consistent = True
    #                 break

    #         if not consistent:
    #             to_remove.add(val_x)
    #             revision = True

    #     # Remove any domain variables that aren't arc consistent:
    #     self.domains[x] = self.domains[x] - to_remove
    #     return revision

    
    def ac3_bitmap(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent using bitmap operations.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # If no arcs, start with queue of all arcs:
        if not arcs:
            arcs = []
            for var_1 in self.domains:
                for var_2 in self.crossword.neighbors(var_1):
                    arcs.append((var_1, var_2))

        # Continue until no arcs left (arc consistency enforced):
        while arcs:
            var_x, var_y = arcs.pop()
            
            # Get intersection point
            i, j = self.crossword.overlaps[var_x, var_y]
            
            # Track if domain was revised
            old_count = bit_count(self.domains[var_x])
            
            # Get all words in x's domain
            x_domain_words = self.get_word_list_for_bitmaps(var_x)
            y_domain_words = self.get_word_list_for_bitmaps(var_y)
            
            # Track which words in x's domain have a matching word in y's domain
            valid_x_words = zero()
            for x_word,x_idx in x_domain_words:
                for y_word,y_idx in y_domain_words:
                    if x_word[i] == y_word[j]:
                        # Found a match, set bit for this x word
                        set_bit(valid_x_words, x_idx)
                        break
                        
            # Update x's domain to only include words that had matches
            in_place_and(self.domains[var_x], valid_x_words)
            
            # Check if domain was revised
            new_count = bit_count(self.domains[var_x])
            if new_count < old_count:
                if new_count == 0:
                    return False
                # Add neighbors back to queue
                for var_z in self.crossword.neighbors(var_x) - {var_y}:
                    arcs.append((var_z, var_x))
        return True
    
    def constraint_neighbor(self,var,assignment):
    # """
    # Remove the assigned word's bitmap from neighbors of same length
    # """
        var_word, var_idx = assignment[var]
        var_len = var.length
        
        # For each neighbor of var
        for neighbor in self.crossword.neighbors(var):
            # Only process neighbors of same length
            if neighbor.length == var_len:
                # Remove (unset) this word from neighbor's domain
                unset_bit(self.domains[neighbor], var_idx)
                
                # Check if neighbor's domain is now empty
                if bit_count(self.domains[neighbor]) == 0:
                    return False
                    
        return True
    
    def ac3_bitmap_quick(self, var, assignment):
        """
        For a given variable and assignment, return a dictionary mapping each neighbor
        to their updated domain after applying bitmap constraints from the intersection
        """
        
        # Get the word assigned to var
        var_word = assignment[var][0]
        
        # For each neighbor of var
        for neighbor in self.crossword.neighbors(var):
            # Get the intersection point between var and neighbor
            i, j = self.crossword.overlaps[var, neighbor]
            neighbor_len = neighbor.length
            # Get the letter at the intersection
            letter = var_word[i]
            
            # Form bitmap key like "5A2" for a 5-letter word with 'A' at position 2
            # neighbor_len = len(next(iter(self.domains[neighbor]))) # Length of neighbor words
            bitmap_key = f"{neighbor_len}{letter}{j}"
            
            # Get bitmap for this constraint and perform AND with neighbor's domain
            in_place_and(self.domains[neighbor],self.bitmap_map["bitmaps"][bitmap_key]) 
            if bit_count(self.domains[neighbor])==0:
                return False
        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        if len(assignment)==self.num_variables:
            return True
        return False


    

    # def order_domain_values(self, var):
    #     """
    #     Return a list of values in the domain of `var`, in order by
    #     the number of values they rule out for neighboring variables.
    #     The first value in the list, for example, should be the one
    #     that rules out the fewest values among the neighbors of `var`.
    #     """

    #     vals_ruleout = {val: 0 for val in self.domains[var]}

    #     # Iterate through all possible values of var:
    #     for val in self.domains[var]:

    #         # Iterate through neighboring variables and values:
    #         for other_var in self.crossword.neighbors(var):
    #             for other_val in self.domains[other_var]:

    #                 # If val rules out other val, add to ruled_out count
    #                 if not self.overlap_satisfied(var, other_var, val, other_val):
    #                     vals_ruleout[val] += 1
                        
    #     # values= [x for x in vals_ruleout]
    #     # random.shuffle(values)
    #     # return values
    #     # Return list of vals sorted from fewest to most other_vals ruled out:
    #     return sorted([x for x in vals_ruleout], key = lambda x: vals_ruleout[x])


        # SIMPLE, INEFFICIENT - RETURN IN ANY ORDER:
        #return [x for x in self.domains[var]]
    def order_domain_values_bitmap(self, var):
        """
        Orders possible word values for a crossword variable based on how much they constrain neighbor variables.
        
        This function uses bitmap operations to efficiently calculate the impact each word would have on the domains
        of neighboring variables. It works by:
        
        1. Creating a map for each character position in the word to track character impacts
        2. For each neighbor that intersects with this variable:
           - Finds which characters appear at the intersection point
           - Uses bitmap operations to calculate how many words would be eliminated from the neighbor's domain
             if each character was placed at the intersection
        3. Calculates a total "cost" for each word based on how many neighbor domain values it eliminates
        4. Returns the words sorted by ascending cost (least constraining values first)
        
        This helps implement the "least constraining value" heuristic for CSP solving, but uses efficient bitmap
        operations rather than checking individual word overlaps.
        
        Args:
            var: The crossword variable to get ordered domain values for
            
        Returns:
            List of words sorted from least constraining to most constraining
        """
        # Create array of maps to store chars and their impact at each position
        char_maps = [{} for _ in range(var.length)]
        
        # For each word in domain, add chars to corresponding position maps
        word_list = self.get_word_list_for_bitmaps(var) 
        for word,i in word_list:
            for j, char in enumerate(word):
                if char not in char_maps[j]:
                    char_maps[j][char] = 0
        
        # For each neighbor, get overlay position and check chars at intersection
        for neighbor in self.crossword.neighbors(var):
            # Get the intersection point between var and neighbor
            i, j = self.crossword.overlaps[var, neighbor]
            
            # Get chars at intersection point for var
            chars_at_i = char_maps[i].keys()
            
            # Create bitmap key for each possible char
            for char in chars_at_i:
                # Get bitmap key for words with this char at position i
                bitmap_key = f"{neighbor.length}{char}{j}"
                bitmap = self.bitmap_map["bitmaps"].get(bitmap_key, None)
                domainSize = bit_count(self.domains[neighbor])
                if bitmap:
                    # AND operation between neighbor's domain and this bitmap
                    domainSizeAfterIntersection=bit_count(and_bits(self.domains[neighbor], bitmap))
                    char_maps[i][char] += max(0,domainSize-domainSizeAfterIntersection)

        # Calculate total cost for each word based on character impacts
        word_costs = {}
        for word,i in word_list:
            cost = 0
            # Sum up impact costs for each character position
            for j, char in enumerate(word):
                cost += char_maps[j].get(char, 0)
            # Add small random factor (between -0.5 and 0.5) to break ties randomly
            # cost += random.random() - 0.5
            word_costs[word] = cost
            # print(word,cost)
        
        # Return words sorted by ascending cost
        return sorted(word_list, key=lambda x: word_costs[x[0]])

        

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        # Get set of unassigned variables
        unassigned = set(self.domains.keys()) - set(assignment.keys())

        # Create list of variables, sorted by MRV and highest degree
        result = [var for var in unassigned]
        result.sort(key = lambda x: (bit_count(self.domains[x]), -len(self.crossword.neighbors(x))))

        return result[0]


    def can_put(self,word):
        if word in self.words_in_grid:
            return False
        if word in const.WORD_GROUPS:
            group=const.WORD_GROUPS[word]
            if group in self.groups_in_grid and self.groups_in_grid[group]>0:
                return False
        return True
    def backtrack_ac3(self, assignment,use_quick_check=False, i=0):
        """
        Using Backtracking Search with AC-3 inference to solve crossword.
        Returns complete assignment if possible, None otherwise.
        """
        # print(i)
        # if self.other_counts > self.max_other_counts:
        #     return None

        if time.time()>self.max_time:
            return None
            
        if self.assignment_complete(assignment):
            return assignment

        var = self.select_unassigned_variable(assignment)

        # Store domains before assignment to restore if needed
        pre_assignment_domains = {k: v.copy() for k,v in self.domains.items()}
        
        # Build arcs for AC-3 once
        arcs = [(other_var, var) for other_var in self.crossword.neighbors(var) 
                if other_var not in assignment]

        # Get top 5 values to try
        values = self.order_domain_values_bitmap(var)
        
        for val,idx in values:
            if time.time()>self.max_time:
                return None
            # print(var,val)
            if not self.can_put(val):
                continue
                
            # Make assignment
            assignment[var] = [val,idx]
            self.words_in_grid.add(val)
            if val in const.WORD_GROUPS:
                group=const.WORD_GROUPS[val]
                self.groups_in_grid[group]=1            
            updated_domain=zero() 
            set_bit(updated_domain,idx)
            self.domains[var] = updated_domain
            # print(val," put", i, " depth")
            if not use_quick_check:
                filled_grid=self.print(assignment)
                print_grid(filled_grid) 
            # Run AC-3 inference
            if use_quick_check:
                if self.ac3_bitmap_quick(var,assignment) and self.constraint_neighbor(var,assignment):
                    result = self.backtrack_ac3(assignment,use_quick_check,i+1)
                    if result:
                        return result
            else:
                if self.ac3_bitmap(arcs) and self.constraint_neighbor(var,assignment):
                    result = self.backtrack_ac3(assignment,use_quick_check,i+1)
                    if result:
                        return result

            # Undo assignment and restore domains
            self.words_in_grid.remove(val)
            if val in const.WORD_GROUPS:
                group=const.WORD_GROUPS[val]
                self.groups_in_grid[group]=-1           
            del assignment[var]
            self.domains = {k: v.copy() for k,v in pre_assignment_domains.items()}

        return None


def createmaps(word_list):
    maps={}
    # TODO:: use clues here
    for word,clue in word_list.items():
        word_length = len(word)
        if word_length not in maps:
            maps[word_length] = []
        maps[word_length].append(word)
    
    # for word_length in maps: 
    #     random.shuffle(maps[word_length])  # Sort by score (highest first)
    
    # for word_length in maps:
    #     maps[word_length].sort(reverse=True, key=lambda x: x[0])  # Sort by score (highest first)
    #     # Extract only the words, keeping the sort order
    #     maps[word_length] = [word for _, word in maps[word_length]]
    return maps

def extract_words(grid):
    n=len(grid)
    m=max(len(line) for line in grid)
    words=[]
    for i in range(n):
        for j in range(m):
            if i==0 or grid[i-1][j]=='.':
                word=""
                k=i
                while k<n and grid[k][j]!='.':
                    word+=grid[k][j]
                    k+=1
                if len(word)>1 and "_" not in word:
                    words.append(word)
        
            if j==0 or grid[i][j-1]=='.':
                word=""
                k=j
                while k<m and grid[i][k]!='.':
                    word+=grid[i][k]
                    k+=1
                if len(word)>1 and "_" not in word:
                    words.append(word)
    return set(words)



def sanitize_string(str, replace="", regex=r"[^\w\s]"):
    string = re.sub(regex, replace, str).strip().upper()
    string = string.replace(" ", "")
    string = string.replace("\n", "")
    return string

# def read_word_list(file_path=const.WORD_LIST_PATH):
#     with open(file_path, "r") as f:
#         tsv_reader = csv.reader(f, delimiter='\t')
#         next(tsv_reader)  # Skip header row
#         for row in tsv_reader:
#             if not row or row[0].strip() == "":
#                 break
#             word = sanitize_string(row[0])
#             const.VALID_WORD_LIST.append(word)
#             const.WORD_LIST[word] = "10"  # Default score of 1 for all words
#     const.WORD_LIST_DATA = deepcopy(const.WORD_LIST)

def read_word_groups(file_path=const.GROUPED_WORD_PATH):
    file_path = os.path.join(logics_path, file_path)
    print("file_path",file_path)
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row_num, row in enumerate(reader, start=1):
            # Take only first 7 values from each row
            words = row[:7]
            for word in words:
                word = sanitize_string(word)
                if word:  # Skip empty strings
                    const.WORD_GROUPS[word] = row_num
                    if row_num not in const.WORD_BY_GROUPS:
                        const.WORD_BY_GROUPS[row_num] = []
                    const.WORD_BY_GROUPS[row_num].append(word)

TOTAL_PUZZLES_TO_GENERATE=50

def fill_grid_completely(start_puzzle_num=None,num_puzzles=5, use_quick_check=True, previous_content=None):
    num_of_formats = 6
    counter = 0
    reattempt = False
    generated_grids = []
    
    try:
        # read_word_list()
        read_word_groups()
        maps = load_word_index_maps()
        initial_puzzle_num = initialize_queues_from_tsv(maps, previous_content) 
        if start_puzzle_num is not None:
            initial_puzzle_num = start_puzzle_num
        current_puzzle_num = initial_puzzle_num
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        grid_display = st.empty()
        i=0
        while i<num_puzzles:
            status_text.text(f"Generating puzzle {i+1}/{num_puzzles}...")
            
            if not reattempt:
                use_quick_check = True
                
            # if ((counter % num_of_formats) + 1 == 6):
            #     counter += 1
            #     continue
            
            file_path = os.path.join(logics_path, const.LAYOUTS_PATH)
            crossword = Crossword(file_path + str((counter % num_of_formats) + 1) + '.txt')
            creator = CrosswordCreator(crossword, maps, use_quick_check)
            
            with st.spinner(f"Solving grid {i+1}..."):
                assignment = creator.solve_bitmap(use_quick_check)
            
            if not assignment:
                counter += 1
                status_text.text(f"Failed to generate puzzle {i+1}. Trying again...")
            else:
                filled_grid = creator.print(assignment)
                words_in_grid = extract_words(filled_grid)
                
                # Display the grid
                grid_text = "\n".join(["".join(row) for row in filled_grid])
                grid_display.text_area("Generated Grid:", grid_text, height=300)
                
                # Save filled grid to file
                format_num = (counter % num_of_formats) + 1
                filename = f"{current_puzzle_num:06d}.txt"
                os.makedirs('./logics/grid_generator/outputs', exist_ok=True)
                output_path = os.path.join('logics/grid_generator/outputs', filename)
                with open(output_path, "w") as f:
                    for row in filled_grid:
                        f.write("".join(row) + "\n")
                
                generated_grids.append((filename, filled_grid))
                remove_from_word_list(current_puzzle_num, assignment, maps)
                counter += 1
                current_puzzle_num += 1
                reattempt = False

                tsv_content = generate_grid_clues_tsv(generated_grids)
                # Dump the TSV content to a file
                os.makedirs('./logics/grid_generator/outputs', exist_ok=True)
                tsv_output_path = os.path.join('logics/grid_generator/outputs', 'grid_clues.tsv')
                with open(tsv_output_path, "w") as tsv_file:
                    tsv_file.write(tsv_content)
                i+=1
                
            progress_bar.progress((i) / num_puzzles)
            
        status_text.text(f"Generated {len(generated_grids)} puzzles successfully!")
        return generated_grids
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)
        return generated_grids


def load_word_index_maps():
    file_path = os.path.join(logics_path, 'calc.json')
    with open(file_path, 'r') as f:
        return json.load(f)
    
def remove_from_word_list(puzzleNum,assignment,maps):
    for word,idx in assignment.values():
        const.USED_WORDS.append([word,idx])
        l=len(word) 
        if(l>2):
            track_used_word(word,puzzleNum,maps,word_idx=idx)






from collections import deque
import csv

# Dictionary to store word queues by length
word_queues = {length: deque() for length in range(2,11)}

# Dictionary to store repetition check limits by length  
rep_check_limits = { 
    2: 10,
    3: 40, 
    4: 40, 
    5: 50, 
    6: 50, 
    7: 70, 
    8: 70, 
    9: 70, 
    10: 5, 
}

def initialize_queues_from_tsv(maps, file_content=None):
    """Initialize queues from previous_content.tsv"""
    last_puzzle_id = 0
    
    if file_content:
        # Use the uploaded file content
        lines = file_content.decode('utf-8').splitlines()
        tsv_reader = csv.reader(lines, delimiter='\t')
        next(tsv_reader)  # Skip header
        
        for row in tsv_reader:
            # Convert string format puzzle_id (e.g. "000001") to integer (1)
            puzzle_id = int(row[0].lstrip('0') or '0')
            last_puzzle_id = max(last_puzzle_id, puzzle_id)
            word = row[1].strip().upper()
            length = len(word)
            
            if length in word_queues:
                try:
                    track_used_word(word, puzzle_id, maps)
                except ValueError:
                    # Word not found in maps, skip it
                    continue
    else:
        # Fall back to local file if no content provided
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'previous_content.tsv')
        if os.path.exists(file_path):
            with open(file_path, 'r') as tsv_file:
                tsv_reader = csv.reader(tsv_file, delimiter='\t')
                next(tsv_reader)  # Skip header
                
                for row in tsv_reader:
                    # Convert string format puzzle_id (e.g. "000001") to integer (1)
                    puzzle_id = int(row[0].lstrip('0') or '0')
                    last_puzzle_id = max(last_puzzle_id, puzzle_id)
                    word = row[1].strip().upper()
                    length = len(word)
                    
                    if length in word_queues:
                        try:
                            track_used_word(word, puzzle_id, maps)
                        except ValueError:
                            # Word not found in maps, skip it
                            continue
                    
    return last_puzzle_id + 1

def add_word_to_queue(word, puzzle_num, word_idx):
    """Add a word, puzzle number and word index to the appropriate length queue"""
    length = len(word)
    if length in word_queues:
        word_queues[length].append((word, puzzle_num, word_idx))

def clean_old_words(current_puzzle_num, maps):
    """Remove words from queues that are beyond their repetition limit"""
    for length, queue in word_queues.items():
        while queue and (current_puzzle_num - queue[0][1]) > rep_check_limits[length]:
            word, _, word_idx = queue.popleft()
            # Re-enable this word in the bitmap
            bitmap_key = f"{length}__"
            set_bit(maps["bitmaps"][bitmap_key], word_idx)

def track_used_word(word, puzzle_num, maps, word_idx=None):
    """Track a used word and update bitmaps"""
    length = len(word)
    if length == 1:
        return
        
    # Get word index if not provided
    if word_idx is None:
        word_idx = maps["words"][str(length)].index(word)
    
    # Add to queue with index
    add_word_to_queue(word, puzzle_num, word_idx)
    
    # Disable in bitmap
    bitmap_key = f"{length}__"
    unset_bit(maps["bitmaps"][bitmap_key], word_idx)
    
    # Clean old words after adding new one
    clean_old_words(puzzle_num, maps)

def print_queue():
    """Print the current state of word queues showing length and words with puzzle numbers"""
    print("\nCurrent Word Queues:")
    print("-" * 50)
    for length in sorted(word_queues.keys()):
        print(f"\nLength {length} words:")
        if not word_queues[length]:
            print("  [Empty]")
        else:
            for word, puzzle_num, _ in word_queues[length]:
                print(f"  {word} (Puzzle #{puzzle_num})")
    print("-" * 50)

def generate_grid_clues_tsv(generated_grids):
    """Generate a TSV file with clues for the generated grids"""
    tsv_content = "puzzleId\tword\trow\tcolumn\tdirection\tclueContent\n"
    
    for filename, grid in generated_grids:
        puzzle_id = filename.split('.')[0]  # Get puzzle ID from filename
        
        # Parse the grid to find words
        words = []
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        
        # Find across words
        for row in range(height):
            word = ""
            start_col = -1
            for col in range(width):
                if grid[row][col] != '.':
                    if start_col == -1:
                        start_col = col
                    word += grid[row][col]
                elif word:  # Word ended
                    if word != '_':  # Skip if word is just underscore
                        words.append({
                            'puzzleId': puzzle_id,
                            'word': word,
                            'row': row,
                            'column': start_col - 1,  # Clue position is one before word
                            'direction': 'across',
                            'clueContent': 'NA'
                        })
                    word = ""
                    start_col = -1
                else:
                    word = ""
                    start_col = -1
            # Check for word at end of row
            if word and word != '_':
                words.append({
                    'puzzleId': puzzle_id,
                    'word': word,
                    'row': row,
                    'column': start_col - 1,
                    'direction': 'across',
                    'clueContent': 'NA'
                })
        
        # Find down words
        for col in range(width):
            word = ""
            start_row = -1
            for row in range(height):
                if grid[row][col] != '.':
                    if start_row == -1:
                        start_row = row
                    word += grid[row][col]
                elif word:  # Word ended
                    if word != '_':  # Skip if word is just underscore
                        words.append({
                            'puzzleId': puzzle_id,
                            'word': word,
                            'row': start_row - 1,  # Clue position is one above word
                            'column': col,
                            'direction': 'down',
                            'clueContent': 'NA'
                        })
                    word = ""
                    start_row = -1
                else:
                    word = ""
                    start_row = -1
            # Check for word at end of column
            if word and word != '_':
                words.append({
                    'puzzleId': puzzle_id,
                    'word': word,
                    'row': start_row - 1,
                    'column': col,
                    'direction': 'down',
                    'clueContent': 'NA'
                })
        
        # Add words to TSV content
        for word_data in words:
            # Add +1 to row and column for 1-indexing in the final output
            tsv_content += f"{word_data['puzzleId']}\t{word_data['word']}\t{word_data['row']+1}\t{word_data['column']+1}\t{word_data['direction']}\t{word_data['clueContent']}\n"
    
    return tsv_content

def get_download_link(generated_grids):
    """Create a download link for the generated grids and clues TSV"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Add grid files
        for filename, grid in generated_grids:
            grid_text = "\n".join(["".join(row) for row in grid])
            zip_file.writestr(f"grids/{filename}", grid_text)
        
        # Generate and add the clues TSV file
        tsv_content = generate_grid_clues_tsv(generated_grids)
        zip_file.writestr("grid_clues.tsv", tsv_content)
    
    zip_buffer.seek(0)
    b64 = base64.b64encode(zip_buffer.read()).decode()
    
    return f'<a href="data:application/zip;base64,{b64}" download="crossword_grids.zip">Download Crossword Grids</a>'

# Add this function to display a grid in a more readable format
def display_grid(grid):
    """Display a crossword grid in a more readable format"""
    grid_html = "<div style='font-family: monospace; line-height: 1.0'>"
    for row in grid:
        for cell in row:
            if cell == '.':
                grid_html += "⬛"
            else:
                grid_html += f"{cell} "
        grid_html += "<br>"
    grid_html += "</div>"
    return grid_html

# Modify the main function to include file upload
def main():
    st.title("Crossword Grid Generator")
    
    st.write("""
    This app generates filled crossword grids using a constraint satisfaction algorithm.
    Please upload a previous content file to begin.
    """)
    
    # Add file uploader for previous_content.tsv
    st.subheader("Upload previous content")
    st.write("Please upload a previous_content.tsv file to continue.")
    uploaded_file = st.file_uploader("Upload previous_content.tsv", type=["tsv"])
    
    if uploaded_file is not None:
        previous_content = uploaded_file.read()
        st.success("File uploaded successfully!")
        start_puzzle_num = st.number_input("Start puzzle number", value=None, min_value=1, max_value=1000000, step=1)
        if start_puzzle_num:
            st.write(f"Starting from puzzle number: {start_puzzle_num}")
            st.write("""
            Select the number of puzzles to generate and click the button below.
            """)
            
            num_puzzles = st.slider("Number of puzzles to generate", 1, 200, 20)
            # use_quick = st.checkbox("Use quick check (faster but may fail more often)", value=True)
            use_quick = True
            if st.button("Generate Crossword Grids"):
                generated_grids = fill_grid_completely(start_puzzle_num,num_puzzles, use_quick, previous_content)
                
                if generated_grids:
                    st.success(f"Successfully generated {len(generated_grids)} crossword grids!")
                    
                    # Provide download link
                    st.markdown(get_download_link(generated_grids), unsafe_allow_html=True)

                    # Display a sample of the generated grids
                    st.subheader("Sample of Generated Grids")
                    for i, (filename, grid) in enumerate(generated_grids):
                        with st.expander(f"Grid {i+1} - {filename}"):
                            st.markdown(display_grid(grid), unsafe_allow_html=True)
                    
                    
                else:
                    st.warning("No grids were generated. Try again or adjust parameters.")
           
        else:
            st.warning("Please enter a starting puzzle number")
        
        
# Replace the direct call to fill_grid_completely with this
if __name__ == "__main__":
    main()
