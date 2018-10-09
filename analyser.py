import re
import itertools
import os
import operator

# Returns a set of english words
def load_english_words():
	english_words = None
	
	with open(os.path.join('./words', "dictionary.txt")) as word_file:
		english_words = set(word.strip().upper() for word in word_file)
		
	return english_words

# Returns True whether a word is in english
def is_word_english(english_words, word):
	return word.upper() in english_words

# Gets anagram materal for a set of clues
# clues: A dictionary where the key is the clue plus the length in brackets
def get_anagram_material(clues):
	for clue, data in clues.items():
		clue_and_len = clue.replace(')', '').replace('.', '').replace('\'', '').split('(')
		
		clues[clue]['anagram material'] = get_clue_list(clue_and_len[0], int(clue_and_len[1]))

# Gets combinations of words that are the same size as the answer_len
def get_clue_list(clue, answer_len):
	clue_lists = []
	curr_word_index = 0
	
	for word in clue.split(" "):
		word_c = [word]
		
		for word2 in clue.split(" ")[curr_word_index + 1:]:
			if len(''.join(word_c)) == answer_len:
				clue_lists.append(' '.join(word_c).upper())
				break
			elif len(''.join(word_c)) > answer_len:
				break
			else:
				word_c.append(word2)
		
		curr_word_index += 1
	
	return clue_lists

# analyses clues to determine possible anagram solutions
def anagram_analyser(clues, probable_letters, min_prob, english_words):
	# Create anagram material for each clue
	get_anagram_material(clues)
	
	for clue, data in clues.items():
		if "anagram material" not in data:
			continue
		
		pos = re.split(",|:", clues[clue]["position"])
		pos.remove("x")
		pos.remove("y")
		pos = [int(p) for p in pos]
		dir = ["across" in clues[clue]["direction"], "down" in clues[clue]["direction"]]
		# Possible solutions
		solution = []
		
		for material in clues[clue]["anagram material"]:
			material = material.replace(" ", "")
			anagrams = ["".join(perm) for perm in set(itertools.permutations(material))]
			
			# Remove the word that was anagrammed
			anagrams.remove(material)
			
			# Remove non english anagram words
			for anagram in anagrams.copy():
				if not is_word_english(english_words, anagram):
					anagrams.remove(anagram)
			
			for anagram in anagrams:
				prob = 1.0
				
				for l in range(len(anagram)):
					letter = anagram[l]
					
					# Calculate the probability of this word being valid
					prob *= probable_letters[pos[1] + l * dir[1]][pos[0] + l * dir[0]][letter] / max(1.0, probable_letters[pos[1]][pos[0]]["total"])
				
				if prob >= min_prob:
					solution.append((anagram, prob))
		
		solution = sorted(solution, key=operator.itemgetter(1), reverse=True)
		# Store the possible solutions to the clues
		clues[clue]["possible solutions"] = solution
		
# Returns the clue and a possible solution with the highest probability
# clues: A dictionary of clues
def get_most_probable_solutions(clues):
	best_solutions = []
	
	for clue, data in clues.items():
		sol = []
		
		for item in data["possible solutions"]:
			item = [clue] + list(item)
			sol.append(item)
		
		best_solutions += sol
		
	best_solutions = sorted(best_solutions, key=operator.itemgetter(2), reverse=True)
	
	return best_solutions