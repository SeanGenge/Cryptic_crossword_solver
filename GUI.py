import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
from Menu import Menu


# Visual representation of the crossword
class GUI:
	class Id:
		square, subletter, letter = range(3)
	
	# root - The root window that will display the crossword
	# grid_size - The number of squares horizontally and vertically
	# disp_clue_size - The number of clues that should be displayed in the listbox
	def __init__(self, parent, app_size_x, app_size_y, grid_size, disp_clue_size):
		# The currently selected crossword square
		self.curr_sel = None
		
		# The number of squares in the grid
		self.grid_size = grid_size
		# the size of individual squares in the grid
		self.rect_size = 550 / 15  # grid_size
		
		# Fonts
		self.clue_label_font = Font(family="Arial", size=14)
		self.clue_font = Font(family="Arial", size=12)
		self.sub_font = Font(family="Arial", size=7)
		
		# Crossword grid
		self.crossword = [[[None, None, None] for x in range(self.grid_size)] for y in range(self.grid_size)]
		
		# Frames
		# Contains everything
		self.tk_main_frame = tk.Frame(parent, width=app_size_x, height=app_size_y)
		# Contains the two listboxes that will hold the across and down clues
		self.tk_clue_frame = tk.Frame(self.tk_main_frame)
		# contains the menu buttons
		self.tk_menu_frame = tk.Frame(self.tk_main_frame, width=500, height=app_size_y)
		
		# One frame for each listbox
		self.tk_across_frame = tk.Frame(self.tk_clue_frame)
		self.tk_down_frame = tk.Frame(self.tk_clue_frame)
		self.tk_info_frame = tk.Frame(self.tk_main_frame)
		
		# Canvas
		# Padding is used to the right and bottom side to display the grid completely. Some is cut off
		pad = 3
		self.tk_crossword_canvas = tk.Canvas(self.tk_main_frame, bd=0, width=self.rect_size * self.grid_size + pad, height=self.rect_size * self.grid_size + pad)
		# Listboxes
		lb_width = 70
		self.tk_across_listbox = tk.Listbox(self.tk_across_frame, width=lb_width, height=disp_clue_size, selectmode=tk.SINGLE)
		self.tk_down_listbox = tk.Listbox(self.tk_down_frame, width=lb_width, height=disp_clue_size, selectmode=tk.SINGLE)
		self.tk_info_listbox = tk.Listbox(self.tk_info_frame, width=lb_width, height=10, selectmode=tk.SINGLE)
		
		# Listbox scrollbars
		self.tk_across_vscrollbar = tk.Scrollbar(self.tk_across_frame)
		self.tk_across_hscrollbar = tk.Scrollbar(self.tk_across_frame, orient=tk.HORIZONTAL)
		
		self.tk_down_vscrollbar = tk.Scrollbar(self.tk_down_frame)
		self.tk_down_hscrollbar = tk.Scrollbar(self.tk_down_frame, orient=tk.HORIZONTAL)
		
		self.tk_info_vscrollbar = tk.Scrollbar(self.tk_info_frame)
		self.tk_info_hscrollbar = tk.Scrollbar(self.tk_info_frame, orient=tk.HORIZONTAL)
		
		self.tk_across_listbox.config(yscrollcommand=self.tk_across_vscrollbar.set)
		self.tk_across_vscrollbar.config(command=self.tk_across_listbox.yview)
		self.tk_across_listbox.config(xscrollcommand=self.tk_across_hscrollbar.set)
		self.tk_across_hscrollbar.config(command=self.tk_across_listbox.xview)
		
		self.tk_down_listbox.config(yscrollcommand=self.tk_down_vscrollbar.set)
		self.tk_down_vscrollbar.config(command=self.tk_down_listbox.yview)
		self.tk_down_listbox.config(xscrollcommand=self.tk_down_hscrollbar.set)
		self.tk_down_hscrollbar.config(command=self.tk_down_listbox.xview)
		
		self.tk_info_listbox.config(yscrollcommand=self.tk_info_vscrollbar.set)
		self.tk_info_vscrollbar.config(command=self.tk_info_listbox.yview)
		self.tk_info_listbox.config(xscrollcommand=self.tk_info_hscrollbar.set)
		self.tk_info_hscrollbar.config(command=self.tk_info_listbox.xview)
		
		# Labels
		self.tk_across_label = tk.Label(self.tk_clue_frame, font=self.clue_label_font, text="Across")
		self.tk_down_label = tk.Label(self.tk_clue_frame, font=self.clue_label_font, text="Down")
		self.tk_info_label = tk.Label(self.tk_info_frame, font=self.clue_label_font, text="Most probable letters:")
		self.tk_progress_label = tk.Label(parent, font=self.sub_font, text="")
		
		# Progress bar
		self.tk_progress = tk.ttk.Progressbar(parent, orient="horizontal", length=553, mode="determinate")
		
		# Create squares that will fill the crossword
		self.init_grid()
		
		# Create the menu (Buttons)
		self.menu = Menu(self.tk_menu_frame)
		
		# Packing and placing of the elements
		self.tk_main_frame.place(x=5, y=5)
		self.tk_clue_frame.place(x=560, y=0)
		self.tk_menu_frame.place(x=5, y=610)
		self.tk_crossword_canvas.place(x=0, y=50)
		
		self.tk_progress_label.place(x=6, y=10)
		self.tk_progress.place(x=6, y=30)
		
		self.tk_across_vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		self.tk_across_hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
		self.tk_down_vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		self.tk_down_hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
		
		self.tk_info_vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		self.tk_info_hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
		
		self.tk_across_label.pack(side=tk.TOP, pady=(10, 0))
		self.tk_across_frame.pack(side=tk.TOP)
		self.tk_across_listbox.pack(side=tk.LEFT, fill="y")
		self.tk_down_label.pack(side=tk.TOP, pady=(10, 0))
		self.tk_down_frame.pack(side=tk.BOTTOM)
		self.tk_down_listbox.pack(side=tk.LEFT, fill="y")
		
		self.tk_info_label.pack(side=tk.TOP)
		self.tk_info_frame.place(x=560, y=500)
		self.tk_info_listbox.pack(side=tk.TOP, fill="y")
	
	# Creates the crossword grid squares and aligns them
	def init_grid(self):
		start_x = 3
		start_y = 3
		
		for y in range(self.grid_size):
			for x in range(self.grid_size):
				top_x = start_x + (x * self.rect_size)
				top_y = start_y + (y * self.rect_size)
				bottom_x = start_x + (x * self.rect_size) + self.rect_size
				bottom_y = start_y + (y * self.rect_size) + self.rect_size
				
				self.crossword[y][x] = [self.tk_crossword_canvas.create_rectangle(top_x, top_y, bottom_x, bottom_y, fill='white', width=2),
				                        self.tk_crossword_canvas.create_text(top_x + 8, top_y + 8, font=self.sub_font, text=""),
				                        self.tk_crossword_canvas.create_text((top_x + bottom_x) / 2, (top_y + bottom_y) / 2, font=self.clue_font, text="")]
	
	# Clears the crossword of all text and sets all the squares to a specific colour
	# Also removes all the across and down clues
	def crossword_reset(self, colour):
		# Clears all listboxes
		self.tk_across_listbox.delete(0, tk.END)
		self.tk_down_listbox.delete(0, tk.END)
		self.tk_info_listbox.delete(0, tk.END)
		
		# Resets the crossword
		for y in range(self.grid_size):
			for x in range(self.grid_size):
				self.tk_crossword_canvas.itemconfig(self.crossword[y][x][self.Id.square], fill=colour)
				self.tk_crossword_canvas.itemconfig(self.crossword[y][x][self.Id.letter], text='')
				self.tk_crossword_canvas.itemconfig(self.crossword[y][x][self.Id.subletter], text='')
		
		# Clears the current selection
		self.curr_sel = None
	
	# Resizes the crossword grid
	def crossword_resize(self, grid_size):
		# Deletes all crossword related items
		for y in range(self.grid_size):
			for x in range(self.grid_size):
				for i in range(3):
					self.tk_crossword_canvas.delete(self.crossword[y][x][i])
		
		self.grid_size = grid_size
		
		# Recreate the crossword items
		self.init_grid()
	
	# Updates the crossword with the clues
	# additional_information: Can be used to gather additional information for each of the squares on the grid
	# additional_information must be a list within a list that contains a dictionary
	def update_crossword(self, clues, additional_information):
		self.crossword_reset("black")
		
		for clue, data in clues.items():
			# Add the clue to the listbox
			if data["direction"] == "across":
				self.tk_across_listbox.insert(tk.END, data["number"] + "    " + clue)
			elif data["direction"] == "down":
				self.tk_down_listbox.insert(tk.END, data["number"] + "    " + clue)
			
			# Add the clue to the crossword
			start = data["position"].split(",")
			start_x = int(start[0].split(":")[1])
			start_y = int(start[1].split(":")[1])
			
			self.tk_crossword_canvas.itemconfig(self.crossword[start_y][start_x][self.Id.subletter], text=data["number"])
			
			for i in range(int(data["length"])):
				across = start_x + (data["direction"] == "across") * i
				down = start_y + (data["direction"] == "down") * i
				
				self.tk_crossword_canvas.itemconfig(self.crossword[down][across][self.Id.square], fill="white")
				
				# Store additional information
				if data["direction"] == "across":
					additional_information[down][across]["across"] = {}
					additional_information[down][across]["across"]["pos"] = i
					additional_information[down][across]["across"]["len"] = int(data["length"])
				elif data["direction"] == "down":
					additional_information[down][across]["down"] = {}
					additional_information[down][across]["down"]["pos"] = i
					additional_information[down][across]["down"]["len"] = int(data["length"])