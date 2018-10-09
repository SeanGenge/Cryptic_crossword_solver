from collections import defaultdict


# The model for the crossword
class Crossword:
	def __init__(self, grid_size):
		# The size of the grid
		self.grid_size = grid_size
		# Contains all the clues
		self.clues = {}
		# Contains all the squares that can be filled
		self.blank_squares = []
		# Contains the final frequencies for each square
		# Will be used after the burn in period in Gibbs sampling
		self.freq = [[defaultdict(int) for x in range(self.grid_size)] for y in range(self.grid_size)]
		# Contains information for each square on the crossword
		# Contains a dict of 'across' and 'down' with information for each
		self.crossword = [[{} for x in range(self.grid_size)] for y in range(self.grid_size)]
	
	# Used to reset the crossword
	def reset_crossword(self, grid_size, clues, blank_squares):
		self.grid_size = grid_size
		self.clues = clues
		self.blank_squares = blank_squares
		self.reset_letter_frequencies()
		self.crossword = [[{} for x in range(self.grid_size)] for y in range(self.grid_size)]
	
	# Updates the crossword
	def update_crossword(self, clues, blank_squares):
		self.clues = clues
		self.blank_squares = blank_squares
	
	# Updates the frequency table
	def update_letter_frequency(self, x, y, letter, freq_count):
		self.freq[y][x]["total"] += freq_count
		self.freq[y][x][letter] += freq_count
		
	# Clears the letter frequencies
	def clear_letter_frequency(self, x, y):
		self.freq[y][x].clear()
	
	# Sets the letter for a particular square
	def set_letter(self, x, y, letter):
		self.crossword[y][x]["letter"] = letter
	
	# Gets the letter of a particular sqyare
	def get_letter(self, x, y):
		if x >= 0 and x < self.grid_size and y >= 0 and y < self.grid_size:
			if "letter" in self.crossword[y][x]:
				return self.crossword[y][x]["letter"]
			
		return ""
	
	# Resets letter frequencies
	def reset_letter_frequencies(self):
		self.freq = [[defaultdict(int) for x in range(self.grid_size)] for y in range(self.grid_size)]