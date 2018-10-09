import re
from nltk.corpus import wordnet as wn
from collections import defaultdict
import os


def is_word(string):
	string = string.lower()
	if re.match("^[a-z]*$", string):
		return True
	
	return False


# Calculates the frequencies from words in a file
# num_neighbours: The maximum number of neighbours that will be considered on each side
# pos: Whether the position of the letter should be taken into account
# length: Whether the length of the word should be taken into account
def calculate_frequencies(filename, num_neighbours, pos, length, progress_label, progress):
	freq = defaultdict(lambda: defaultdict(int))
	
	progress_label["text"] = "Calculating frequencies"
	progress['value'] = 0
	progress['maximum'] = 0
	p = 0
	
	filename = os.path.join('./words', filename)
	
	with open(filename, 'r') as f:
		for word in f:
			word = word.strip("\n")
			word = word.upper()
			
			if progress['maximum'] == 0:
				progress['maximum'] = word
				continue
			
			# Goes through each letters in the word
			for i in range(len(word)):
				# Use a set to prevent duplicate keys for one letter
				keys = set()
				
				# Goes through all the different combinations of neighbours on each side
				for l in range(1, num_neighbours + 1):
					for r in range(1, num_neighbours + 1):
						# key: P*N + pos in word (start from 0) + length of word
						left = word[max(i - l, 0):i]
						right = word[i + 1:i + r + 1]
						
						keys.add('_' * (num_neighbours - len(left)) + left + "*" + right + '_' * (num_neighbours - len(right)) + ('!P' + str(i)) * pos + ('!L' + str(len(word))) * length)
				
				for key in keys:
					freq[key]['total'] += 1
					freq[key][word[i].upper()] += 1
					
			if p % 1000 == 0:
				progress['value'] += 1000
				
			p += 1
	
	return freq
	
	
# Saves the frequencies
def save_frequencies(filename, freq, progress_label, progress):
	# Get the size of the frequency file
	freq_size = sum(len(v) for v in freq.values()) + len(freq)
	
	progress_label["text"] = "Saving frequencies"
	progress['value'] = 0
	progress['maximum'] = len(freq)
	p = 0
	
	filename = os.path.join("./frequencies", filename)
	
	with open(filename, 'w') as file:
		file.write(str(freq_size) + "\n")
		
		for key1, data1 in freq.items():
			file.write("new item:" + key1 + "\n")
			
			for key2, data2 in data1.items():
				if key2 == 'total':
					file.write(key2 + ":" + str(data2) + "\n")
				else:
					file.write(key2 + ":" + str(data2) + "\n")
					
			if p % 1000 == 0:
				progress['value'] += 1000
				
			p += 1