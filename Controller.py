import tkinter as tk
import tkinter.filedialog
import codecs
from Crossword import Crossword
from create_distribution import calculate_frequencies, save_frequencies, is_word
from Probability_distribution import Probability_distribution
from GUI import GUI
from collections import defaultdict
import random
import threading
import time
import os
import analyser
import copy
import re


class Controller:
	def __init__(self):
		self.app = tk.Tk()
		app_size_x = 1025
		app_size_y = 770
		app_left_x = self.app.winfo_screenwidth() // 2 - (app_size_x // 2)
		app_lext_y = self.app.winfo_screenheight() // 2 - (app_size_y // 2) - 30
		self.app.geometry(str(app_size_x) + 'x' + str(app_size_y) + '+' + str(app_left_x) + '+' + str(app_lext_y))
		self.app.wm_title("Gibbs Estimator")
		
		self.current_filename = ""
		
		# Starting value is the max grid size
		self.grid_size = 15
		self.clue_size = 10
		
		# English words
		self.english_words = analyser.load_english_words()
		
		# The Gibbs sampler thread
		self.gibbs_thread = None
		# The solve thread
		self.solve_thread = None
		# The total number of backtracks made
		self.num_backtracks = 0
		
		# True if the solver found a solution
		self.solve = True
		# The number of clues that needs to be solved
		self.num_solvable_clues = 0
		
		# The probability distribution
		self.prob_num_neighbours = 0
		self.prob_pos = 0
		self.prob_length = 0
		
		self.dist = Probability_distribution()
		self.no_dist = Probability_distribution()
		self.crossword = Crossword(self.grid_size)
		self.GUI = GUI(self.app, app_size_x, app_size_y, self.grid_size, self.clue_size)
		
		# Bind the menu buttons to methods
		self.GUI.menu.tk_load_button.bind("<Button>", self.load_crossword)
		self.GUI.menu.tk_start_gibbs_button.bind("<Button>", self.gibbs)
		self.GUI.menu.tk_analyse_button.bind("<Button>", self.analyse_clues)
		self.GUI.menu.tk_solve_button.bind("<Button>", self.solve_anagram_crossword_button)
		
		# Allows the canvas to get focus
		self.GUI.tk_crossword_canvas.bind("<Button-1>", lambda event: self.GUI.tk_crossword_canvas.focus_set())
		self.GUI.tk_crossword_canvas.bind('<Key>', self.key_press)
		self.GUI.tk_across_listbox.bind('<<ListboxSelect>>', self.clue_select)
		self.GUI.tk_down_listbox.bind('<<ListboxSelect>>', self.clue_select)
		
		# Used to resize the crossword grid within the crossword representation and the GUI
		self.crossword_resize(15)
		
	# Resizes the crossword grid
	def crossword_resize(self, grid_size):
		# Removes any current binds
		for y in range(self.grid_size):
			for x in range(self.grid_size):
				for i in range(3):
					self.GUI.tk_crossword_canvas.tag_unbind(self.GUI.crossword[y][x][i], '<ButtonPress-1>')
		
		# Resizes the grid
		self.grid_size = grid_size
		# Resize the GUI and the Crossword
		self.GUI.crossword_resize(grid_size)
		self.crossword.reset_crossword(grid_size, self.crossword.clues, self.crossword.blank_squares)
		
		# Add a click event to each of the elements in the canvas
		for y in range(self.grid_size):
			for x in range(self.grid_size):
				for i in range(3):
					self.GUI.tk_crossword_canvas.tag_bind(self.GUI.crossword[y][x][i], '<ButtonPress-1>', self.on_click)
	
	# Runs the application
	def run(self):
		self.app.mainloop()
	
	# callback: Called when a clue from the across or down listbox is selected
	def clue_select(self, event):
		w = event.widget
		
		try:
			# Get the clue that will be analysed
			if w == self.GUI.tk_across_listbox or w == self.GUI.tk_down_listbox:
				index = int(w.curselection()[0])
				clue = w.get(index).split("    ")[1]
				
				self.update_analysis_clue(clue)
		except IndexError:
			pass
	
	# Callback: Called when a key is pressed on the keyboard
	def key_press(self, event):
		if self.GUI.curr_sel is not None:
			ignored_words = ["Space", "Enter", "Left", "Up", "Right", "Down"]
			
			# A key was pressed
			if event.keysym == "BackSpace":
				# Erase the current letter in the square
				self.update_square(self.GUI.curr_sel[0], self.GUI.curr_sel[1], char='', tag="*clear")
				self.crossword.set_letter(self.GUI.curr_sel[0], self.GUI.curr_sel[1], '')
			elif is_word(event.keysym) and event.keysym not in ignored_words:
				# Enter the current letter in the square
				fill = '#%02x%02x%02x' % (150, 0, 150)
				letter = str(event.char).upper()
				
				self.update_square(self.GUI.curr_sel[0], self.GUI.curr_sel[1], char=letter, text_fill=fill, tag="typed")
				self.crossword.set_letter(self.GUI.curr_sel[0], self.GUI.curr_sel[1], letter)
			
			# Check for arrow key presses
			dir = [(-(event.keysym == "Left" * 1)) + (event.keysym == "Right" * 1), (-(event.keysym == "Up" * 1)) + (event.keysym == "Down" * 1)]
			new_loc = [self.GUI.curr_sel[0] + dir[0], self.GUI.curr_sel[1] + dir[1]]
			
			if (dir[0] == -1 or dir[0] == 1) and new_loc[0] >= 0 and new_loc[0] <= self.grid_size - 1 or (
							(dir[1] == -1 or dir[1] == 1) and new_loc[1] >= 0 and new_loc[1] <= self.grid_size - 1):
				if self.GUI.tk_crossword_canvas.itemcget(self.GUI.crossword[new_loc[1]][new_loc[0]][self.GUI.Id.square], "fill") != "black":
					self.update_square(self.GUI.curr_sel[0], self.GUI.curr_sel[1], square_fill="white")
					self.GUI.curr_sel = new_loc
					fill = '#%02x%02x%02x' % (173, 216, 230)
					self.update_square(self.GUI.curr_sel[0], self.GUI.curr_sel[1], square_fill=fill)
					self.update_list_probable_letters(self.GUI.curr_sel[0], self.GUI.curr_sel[1])
	
	# Callback: Called when a crossword square is clicked
	def on_click(self, event):
		# Deselect the previously selected square
		if self.GUI.curr_sel is not None:
			self.update_square(self.GUI.curr_sel[0], self.GUI.curr_sel[1], square_fill="white")
		
		# Find the currently selected square
		for y in range(self.grid_size):
			for x in range(self.grid_size):
				for i in range(3):
					if self.GUI.crossword[y][x][i] == event.widget.find_withtag("current")[0]:
						if self.GUI.tk_crossword_canvas.itemcget(self.GUI.crossword[y][x][self.GUI.Id.square], "fill") != "black":
							self.GUI.curr_sel = [x, y]
		
		# Highlight the selected square
		if self.GUI.curr_sel is not None:
			fill = '#%02x%02x%02x' % (173, 216, 230)
			self.update_square(self.GUI.curr_sel[0], self.GUI.curr_sel[1], square_fill=fill)
			
			self.update_list_probable_letters(self.GUI.curr_sel[0], self.GUI.curr_sel[1])
	
	# Loads the crossword into the model and GUI
	def load_crossword(self, event):
		try:
			# Retrieve the clue data for the crossword
			clues, grid_size = self.read_crossword_file()
			
			# Holds all the blank squares in the crossword GUI
			blank_squares = []
			
			# Resize the crossword grid
			self.crossword_resize(grid_size)
			
			# Update the GUI with the clues
			self.GUI.update_crossword(clues, self.crossword.crossword)
			
			# Get all the blank squares from the gui
			for y in range(self.grid_size):
				for x in range(self.grid_size):
					if self.GUI.tk_crossword_canvas.itemcget(self.GUI.crossword[y][x][self.GUI.Id.square], "fill") != "black":
						blank_squares.append((x, y))
			
			# Update the crossword information
			self.crossword.update_crossword(clues, blank_squares)
		except TypeError:
			# the user closes the dialog
			pass
	
	# Reads the crossword file
	def read_crossword_file(self):
		try:
			clues = {}
			size = 0
			
			filename = tk.filedialog.askopenfilename()
			file = codecs.open(filename, 'r', 'utf-8')
			
			# the key is the clue and the data is everything else
			key = ""
			data = {}
			
			# Read the selected file
			for line in file.readlines():
				# Remove the new line at the end
				line = line.replace("\n", "")
				line = line.replace("\r", "")
				info = line.split(":", 1)
				
				if info[0] == "size":
					size = int(info[1])
				if info[0] == "new clue":
					if key != "":
						clues[key] = data
					
					key = ""
					data = {}
				elif line != "":
					if info[0] == "clue":
						key = info[1]
					else:
						data[info[0]] = info[1]
			
			# The last clue needs to be added
			clues[key] = data
			
			return clues, size
		except FileNotFoundError:
			pass
	
	# Returns the distribution from a frequency file
	def read_freq_file(self, filename):
		self.GUI.tk_progress_label["text"] = "Reading Frequency file"
		self.GUI.tk_progress['value'] = 0
		self.GUI.tk_progress['maximum'] = 0
		p = 0
		
		filename = os.path.join("./frequencies", filename)
		
		dist = defaultdict(lambda: defaultdict(int))
		curr = ""
		curr_total = 0
		total = 0
		
		with open(filename, 'r') as file:
			for line in file:
				if p == 0:
					self.GUI.tk_progress['maximum'] = int(line.replace("\n", ""))
					p += 1
					continue
				
				line = line.replace("\n", "")
				line = line.split(":")
				
				if line[0] == "new item":
					curr = line[1]
					curr_total = 0
				elif line[0] == "total":
					total = int(line[1])
				else:
					curr_total += int(line[1]) / total
					dist[curr][line[0]] = int(line[1]) / total
				
				if p % 1000 == 0:
					self.GUI.tk_progress['value'] += 1000
				
				p += 1
		
		return dist
	
	# Returns two keys given a specific square
	# square: [x, y] coordinate
	# num_neighbours: If not the same as self.prob_num_neighbours then ignores the other letters at the edges
	def get_keys(self, square, num_neighbours):
		hor_key = "_*_"
		vert_key = "_*_"
		
		x, y = square[0], square[1]
		
		if "across" in self.crossword.crossword[square[1]][square[0]]:
			pos = self.crossword.crossword[square[1]][square[0]]["across"]["pos"]
			length = self.crossword.crossword[square[1]][square[0]]["across"]["len"]
			
			# Get the horizontal word
			word = ''.join([a["letter"] for a in self.crossword.crossword[y][x - pos:x - pos + length]])
			
			left = word[max(0, pos - num_neighbours):pos]
			right = word[pos + 1:pos + num_neighbours + 1]
			hor_key = (self.prob_num_neighbours - len(left)) * '_' + left + '*' + right + (self.prob_num_neighbours - len(right)) * '_'
		
		# Generate the vertical key
		if "down" in self.crossword.crossword[square[1]][square[0]]:
			pos = self.crossword.crossword[square[1]][square[0]]["down"]["pos"]
			length = self.crossword.crossword[square[1]][square[0]]["down"]["len"]
			
			# Get the vertical word
			word = ''.join([a["letter"] for a in [b[x] for b in self.crossword.crossword[y - pos:y - pos + length]]])
			
			left = word[max(0, pos - num_neighbours):pos]
			right = word[pos + 1:pos + num_neighbours + 1]
			vert_key = (self.prob_num_neighbours - len(left)) * '_' + left + '*' + right + (self.prob_num_neighbours - len(right)) * '_'
		
		# append the additional information to the key
		info = self.crossword.crossword[square[1]][square[0]]
		
		if "across" in info:
			hor_key += ("!P" + str(info["across"]["pos"])) * self.prob_pos + ("!L" + str(info["across"]["len"])) * self.prob_length
		
		if "down" in info:
			vert_key += ("!P" + str(info["down"]["pos"])) * self.prob_pos + ("!L" + str(info["down"]["len"])) * self.prob_length
		
		return [hor_key, vert_key]
	
	def gibbs(self, event):
		# Create the file name based on the menu items
		filename_save = self.GUI.menu.filename_var.get() + "_freq_N" + self.GUI.menu.tk_neighbours_textbox.get("1.0", tk.END).strip("\n") + "P" + str(
			self.GUI.menu.pos_var.get()) + "L" + str(self.GUI.menu.length_var.get()) + ".txt"
		filename_load = self.GUI.menu.filename_var.get() + ".txt"
		
		# Start the Gibbs estimator on a different thread
		self.gibbs_thread = threading.Thread(target=self.gibbs_estimator, args=(filename_load, filename_save,))
		self.gibbs_thread.start()
	
	# Callback: Creates a thread that will run the Gibbs sampler on the grid
	def gibbs_estimator(self, filename_load, filename_save):
		start = time.time()
		
		# Load the file if not already loaded
		if filename_save != self.current_filename:
			# Get important information
			self.prob_num_neighbours = int(self.GUI.menu.tk_neighbours_textbox.get("1.0", tk.END).strip("\n"))
			self.prob_pos = int(self.GUI.menu.pos_var.get())
			self.prob_length = int(self.GUI.menu.length_var.get())
			
			# Free up any memory before loading or calculating a new distribution
			self.dist.set_distribution({})
			
			try:
				self.dist.set_distribution(self.read_freq_file(filename_save))
			except FileNotFoundError:
				# The file does not exist, create it
				freq = calculate_frequencies(filename_load, self.prob_num_neighbours, self.prob_pos, self.prob_length, self.GUI.tk_progress_label,
				                             self.GUI.tk_progress)
				save_frequencies(filename_save, freq, self.GUI.tk_progress_label, self.GUI.tk_progress)
				del freq
				self.dist.set_distribution(self.read_freq_file(filename_save))
			
			self.current_filename = filename_save
		
		# Burn in period
		burn_in = int(self.GUI.menu.tk_burn_in_textbox.get("1.0", tk.END))
		# The number of iterations after the burn in period
		num_iterations = int(self.GUI.menu.tk_num_iterations_textbox.get("1.0", tk.END))
		# The starting state of the crossword. Pick any letter with equal probability
		letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
		
		# Reset the letter frequencies
		self.crossword.reset_letter_frequencies()
		
		# Progress bar stuff
		self.GUI.tk_progress_label["text"] = "Running the Gibbs Estimator"
		self.GUI.tk_progress['value'] = 0
		self.GUI.tk_progress['maximum'] = burn_in + num_iterations + 1
		progress_iter = max(1, (burn_in + num_iterations) // 25)
		
		for num_iter in range(burn_in + num_iterations + 1):
			if num_iter % progress_iter == 0:
				self.GUI.tk_progress['value'] += progress_iter
			
			for square in self.crossword.blank_squares:
				# The letter that will be updated for that particular square. Also called the sample
				letter = None
				max_letter = None
				# The colour of the square
				fill = "black"
				
				if num_iter == 0:
					if self.GUI.menu.random_start_var.get():
						# random initialisation of the grid
						letter = random.choice(letters)
				else:
					i = 0
					
					# Get a random sample that is valid
					while letter is None:
						if i == 0:
							keys = self.get_keys(square, self.prob_num_neighbours)
							# The sample from the probability distribution
							letter = self.dist.get_sample(keys)
						elif i == 1:
							keys = self.get_keys(square, 1)
							# The sample from the probability distribution
							letter = self.dist.get_sample(keys)
						else:
							# Pick a random letter as the sample
							letter = random.choice(letters)
						
						i += 1
					
					if num_iter >= burn_in + 1:
						if self.is_letter_typed(square[0], square[1]):
							letter = self.crossword.get_letter(square[0], square[1])
						
						# Update the frequencies
						self.crossword.update_letter_frequency(square[0], square[1], letter, 1)
						
						# Get the most frequently used letter for that square
						max_letter = max([k for k, v in self.crossword.freq[square[1]][square[0]].items() if k != 'total'], key=self.crossword.freq[square[1]][square[0]].get)
						prob = max(0, min(255, int(255 * (1 - (self.crossword.freq[square[1]][square[0]][max_letter] / self.crossword.freq[square[1]][square[0]]['total'])))))
						fill = '#%02x%02x%02x' % (prob, prob, prob)
				
				if letter is not None:
					# Update the letter in the crossword (Not GUI update)
					if not self.is_letter_typed(square[0], square[1]):
						self.crossword.set_letter(square[0], square[1], letter)
					
				if max_letter is not None:
					letter = max_letter
				
				# Only update the gui every x iterations
				if (num_iter % (burn_in // 10) == 0 and num_iter <= burn_in + 2) or num_iter == burn_in + num_iterations:
					if not self.is_letter_typed(square[0], square[1]):
						self.update_square(square[0], square[1], char=letter, text_fill=fill)
		
		self.GUI.tk_progress_label["text"] = "Finished running the Gibbs Estimator. Time taken: " + "{0:.2f}".format(time.time() - start) + " seconds"
	
	# Updates a crossword square
	def update_square(self, x, y, char=None, text_fill='', square_fill='', tag=''):
		# Make sure only one letter is in a square
		assert len(str(char)) <= 1 or char == None, "A crossword square can only contain one letter: (" + str(x) + ", " + str(y) + ") -> " + str(char)
		
		if char != None:
			self.GUI.tk_crossword_canvas.itemconfig(self.GUI.crossword[y][x][self.GUI.Id.letter], text=char)
		
		if text_fill != '':
			self.GUI.tk_crossword_canvas.itemconfig(self.GUI.crossword[y][x][self.GUI.Id.letter], fill=text_fill)
		
		if square_fill != '':
			self.GUI.tk_crossword_canvas.itemconfig(self.GUI.crossword[y][x][self.GUI.Id.square], fill=square_fill)
		
		if tag == '*clear':
			self.GUI.tk_crossword_canvas.itemconfig(self.GUI.crossword[y][x][self.GUI.Id.letter], tag='')
		elif tag != '':
			self.GUI.tk_crossword_canvas.itemconfig(self.GUI.crossword[y][x][self.GUI.Id.letter], tag=tag)
	
	# Returns True if the letter at the particular coordinate has been typed
	def is_letter_typed(self, x, y):
		return "typed" in self.GUI.tk_crossword_canvas.itemcget(self.GUI.crossword[y][x][self.GUI.Id.letter], "tag").split(" ")
	
	# Updates the listbox that holds the most probable letters
	def update_list_probable_letters(self, x, y):
		# Display the coordinates in the label
		self.GUI.tk_info_label['text'] = "Most probable letters: (" + str(x) + ", " + str(y) + ")"
		
		# Clear the listbox
		self.GUI.tk_info_listbox.delete(0, tk.END)
		
		# Adds the most probable letters in descending order
		if self.crossword.freq[y][x]:
			for key, data in sorted(self.crossword.freq[y][x].items(), key=lambda x: x[1], reverse=True):
				if key != 'total' and key != None:
					prob = data / max(1.0, self.crossword.freq[y][x]['total'])
					
					if prob != 0:
						self.GUI.tk_info_listbox.insert(tk.END, key + ": " + str(data) + "    - " + '{0:.6f}'.format(prob))
	
	# Analyses the clues
	def analyse_clues(self, event, clues=None, min_prob=10e-15):
		if clues is None:
			clues = self.crossword.clues
		
		analyser.anagram_analyser(clues, self.crossword.freq, min_prob, self.english_words)
	
	# Attempts to solve an anagram only crossword by using greedy backtracking
	def solve_anagram_crossword_button(self, event):
		clues = copy.deepcopy(self.crossword.clues)
		self.solve = False
		
		# Go through the whole crossword grid to find if any clue already has a solution
		for clue, data in self.crossword.clues.items():
			length = int(data["length"])
			dir = ["across" in data["direction"], "down" in data["direction"]]
			pos = re.split(",|:", data["position"])
			pos.remove("x")
			pos.remove("y")
			pos = [int(p) for p in pos]
			
			# All the possible squares that are not typed
			squares = []
			
			for l in range(length):
				if not self.is_letter_typed(pos[0] + dir[0] * l, pos[1] + dir[1] * l):
					squares.append([pos[0] + dir[0] * l, pos[1] + dir[1] * l])
			
			if len(squares) == 0:
				# The clue is solved, remove it from clues
				clues.pop(clue)
			
			self.num_solvable_clues = len(clues)
		
		# Test
		t = threading.Thread(target=self.run_program, args=(event, clues))
		t.start()
		
				
		'''self.num_backtracks = 0
		
		self.solve_thread = threading.Thread(target=self.solve_anagram_crossword, args=(event, clues))
		self.solve_thread.start()'''
	
	# Attempts to solve an anagram only crossword by using greedy backtracking
	def solve_anagram_crossword(self, event, clues=None, solution=None, state=None, prev_states=None):
		if clues is None:
			clues = copy.deepcopy(self.crossword.clues)
		if solution is None:
			solution = {}
		if state is None:
			state = {}
		if prev_states is None:
			prev_states = []
		
		if len(solution) == self.num_solvable_clues:
			print(solution)
			self.solve = True
			self.analyse_clues(event)
			
			return solution
		else:
			# Run the Gibbs estimator
			self.gibbs(event)
			
			# Wait until the gibbs estimator is finished
			while (self.gibbs_thread.is_alive()):
				# Wait a little while. Prevents the thread using all the resources (Freezes if you use pass)
				time.sleep(0.01)
			
			if len(solution) == 0:
				# Run the clue analyser for all the clues
				self.analyse_clues(event, clues, 0)
			else:
				self.analyse_clues(event, clues)
			
			# Get the best possible solution in the grid (Greedy)
			possible_solutions = analyser.get_most_probable_solutions(clues)
			
			for sol in possible_solutions:
				if self.can_word_fit(sol[0], sol[1]):
					# Store the previous states to prevent trying the same combinations
					state[sol[0]] = sol[1]
					
					# The state has already been visited
					if state in prev_states:
						state.pop(sol[0])
						
						continue
					
					# Add possible solution to the final solution
					solution[sol[0]] = sol[1:]
					
					fill = '#%02x%02x%02x' % (150, 0, 150)
					length = int(clues[sol[0]]["length"])
					dir = ["across" in clues[sol[0]]["direction"], "down" in clues[sol[0]]["direction"]]
					pos = re.split(",|:", clues[sol[0]]["position"])
					pos.remove("x")
					pos.remove("y")
					pos = [int(p) for p in pos]
					squares = []
					
					# Fill the possible solution within the grid
					for l in range(length):
						x = pos[0] + dir[0] * l
						y = pos[1] + dir[1] * l
						
						letter = sol[1][l]
						
						if not self.is_letter_typed(x, y):
							self.update_square(x, y, char=letter, text_fill=fill, tag="typed")
							self.crossword.set_letter(x, y, letter)
							squares.append([x, y])
					
					# All the squares that were modified for this clue
					clues[sol[0]]["squares"] = squares
					
					clues_copy = copy.deepcopy(clues)
					clues_copy.pop(sol[0])
					
					self.solve_anagram_crossword(event, clues_copy, solution, state, prev_states)
					
					# Check whether the solver is solved. If yes then don't search for other solutions or backtrack
					if self.solve:
						return solution
					
					# Backtracking: Remove the word from the grid
					if "squares" in clues[sol[0]]:
						for square in clues[sol[0]]["squares"]:
							self.update_square(square[0], square[1], text_fill="black", tag="*clear")
							
						self.num_backtracks += 1
						
						if state not in prev_states:
							prev_states.append(copy.deepcopy(state))
						
						state.pop(sol[0])
						
						# Remove the clue from the solution
						solution.pop(sol[0])
					
						self.GUI.menu.tk_gibbs_label["text"] = "# backtracking: " + str(self.num_backtracks)
						
	# Displays the analysis for the particular clue
	def update_analysis_clue(self, clue):
		self.GUI.tk_info_label["text"] = clue
		
		# Clear the listbox
		self.GUI.tk_info_listbox.delete(0, tk.END)
		
		# Populate the listbox with analysis
		if "possible solutions" in self.crossword.clues[clue]:
			self.GUI.tk_info_listbox.insert(tk.END, "Possible solutions - Probability")
			
			for solution in self.crossword.clues[clue]["possible solutions"]:
				self.GUI.tk_info_listbox.insert(tk.END, solution[0] + " - " + str(solution[1]))
	
	# Returns True whether a given word can fit within a space on the grid
	# Takes into account typed letters and whether the word can fit
	def can_word_fit(self, clue, word):
		length = int(self.crossword.clues[clue]["length"])
		dir = ["across" in self.crossword.clues[clue]["direction"], "down" in self.crossword.clues[clue]["direction"]]
		pos = re.split(",|:", self.crossword.clues[clue]["position"])
		pos.remove("x")
		pos.remove("y")
		pos = [int(p) for p in pos]
		
		if len(word) != length:
			return False
		
		for l in range(length):
			x = pos[0] + dir[0] * l
			y = pos[1] + dir[1] * l
			
			if self.is_letter_typed(x, y) and self.crossword.get_letter(x, y) != word[l]:
				return False
		
		return True
	
	# Fills in a word for a clue
	def fill_word(self, clue, word):
		clues = self.crossword.clues
		word = word.upper()
		
		fill = '#%02x%02x%02x' % (150, 0, 150)
		length = int(clues[clue]["length"])
		dir = ["across" in clues[clue]["direction"], "down" in clues[clue]["direction"]]
		pos = re.split(",|:", clues[clue]["position"])
		pos.remove("x")
		pos.remove("y")
		pos = [int(p) for p in pos]
		squares = []
		
		# Fill the possible solution within the grid
		for l in range(length):
			x = pos[0] + dir[0] * l
			y = pos[1] + dir[1] * l
			
			letter = word[l]
			
			if not self.is_letter_typed(x, y):
				self.update_square(x, y, char=letter, text_fill=fill, tag="typed")
				self.crossword.set_letter(x, y, letter)
				squares.append([x, y])
				
		return squares
	
	def run_program(self, event, clues):
		# Tries to solve the puzzle using brute force

		file = open(str(self.GUI.menu.tk_neighbours_textbox.get("1.0",'end-1c')) + " neighbours.txt", 'w')
		
		clues = copy.deepcopy(self.crossword.clues)
		self.solve = False
		
		# Go through the whole crossword grid to find if any clue already has a solution
		for clue, data in self.crossword.clues.items():
			length = int(data["length"])
			dir = ["across" in data["direction"], "down" in data["direction"]]
			pos = re.split(",|:", data["position"])
			pos.remove("x")
			pos.remove("y")
			pos = [int(p) for p in pos]
			
			# All the possible squares that are not typed
			squares = []
			
			for l in range(length):
				if not self.is_letter_typed(pos[0] + dir[0] * l, pos[1] + dir[1] * l):
					squares.append([pos[0] + dir[0] * l, pos[1] + dir[1] * l])
			
			if len(squares) == 0:
				# The clue is solved, remove it from clues
				clues.pop(clue)
			
			self.num_solvable_clues = len(clues)
		
		self.num_backtracks = 0
		
		self.solve_thread = threading.Thread(target=self.solve_anagram_crossword, args=(event, clues))
		self.solve_thread.start()
		
		while (self.solve_thread.is_alive()):
			# Wait a little while. Prevents the thread using all the resources (Freezes if you use pass)
			time.sleep(0.01)
		
		file.write(str(self.solve) + " " + str(self.GUI.menu.tk_burn_in_textbox.get("1.0",'end-1c')) + " " + str(self.GUI.menu.tk_num_iterations_textbox.get("1.0",'end-1c')) + " " + str(
			self.num_backtracks) + "\n")
		print(str(self.GUI.menu.tk_num_iterations_textbox.get("1.0",'end-1c')) + " " + str(self.solve) + " " + str(self.GUI.menu.tk_burn_in_textbox.get("1.0",'end-1c')) + " " + str(self.GUI.menu.tk_num_iterations_textbox.get("1.0",'end-1c')) + " " + str(
			self.num_backtracks))
		
		file.close()

	def run_program_auto(self, event, clues):
		# Automatic run for different burn in and stats
		burn_in_v = [500, 1000]
		stats_v = [1000, 2000]
		
		for n in [3, 4]:
			file = open(str(n) + " neighbours.txt", 'w')
			
			self.GUI.menu.tk_neighbours_textbox.delete("1.0", tk.END)
			
			self.GUI.menu.tk_neighbours_textbox.insert(tk.END, str(n))
			
			for burn_in in burn_in_v:
				for stats in stats_v:
					for avg in range(2):
						self.load_crossword(event)
						clues = copy.deepcopy(self.crossword.clues)
						self.solve = False
						
						# Go through the whole crossword grid to find if any clue already has a solution
						for clue, data in self.crossword.clues.items():
							length = int(data["length"])
							dir = ["across" in data["direction"], "down" in data["direction"]]
							pos = re.split(",|:", data["position"])
							pos.remove("x")
							pos.remove("y")
							pos = [int(p) for p in pos]
							
							
							# All the possible squares that are not typed
							squares = []
							
							for l in range(length):
								if not self.is_letter_typed(pos[0] + dir[0] * l, pos[1] + dir[1] * l):
									squares.append([pos[0] + dir[0] * l, pos[1] + dir[1] * l])
							
							if len(squares) == 0:
								# The clue is solved, remove it from clues
								clues.pop(clue)
							
							self.num_solvable_clues = len(clues)
						
						self.GUI.menu.tk_burn_in_textbox.delete("1.0", tk.END)
						self.GUI.menu.tk_num_iterations_textbox.delete("1.0", tk.END)
						
						self.GUI.menu.tk_burn_in_textbox.insert(tk.END, str(burn_in))
						self.GUI.menu.tk_num_iterations_textbox.insert(tk.END, str(stats))
						
						self.num_backtracks = 0
						
						self.solve_thread = threading.Thread(target=self.solve_anagram_crossword, args=(event, clues))
						self.solve_thread.start()
						
						while (self.solve_thread.is_alive()):
							# Wait a little while. Prevents the thread using all the resources (Freezes if you use pass)
							time.sleep(0.01)
							
						file.write(str(self.solve) + " " + str(burn_in) + " " + str(stats) + " " + str(self.num_backtracks) + "\n")
						print(str(n) + " " + str(self.solve) + " " + str(burn_in) + " " + str(stats) + " " + str(self.num_backtracks))
						
			file.close()