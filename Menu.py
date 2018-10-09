import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import codecs
import re


# Allows loading, saving and starting the algorithm to modify the crossword
class Menu:
	def __init__(self, parent):
		# Gibbs sampler stuff
		gibbs_frame_width = 230
		self.tk_gibbs_frame = tk.Frame(parent, width=gibbs_frame_width, height=200)
		self.tk_gibbs_label = tk.Label(self.tk_gibbs_frame, text="Gibbs Estimator")
		self.tk_load_button = tk.Button(self.tk_gibbs_frame, text="Load Crossword")
		self.tk_start_gibbs_button = tk.Button(self.tk_gibbs_frame, text="Start Gibbs Estimator")
		self.tk_burn_in_label = tk.Label(self.tk_gibbs_frame, text="Burn in")
		self.tk_num_iterations_label = tk.Label(self.tk_gibbs_frame, text="# of iterations")
		self.tk_burn_in_textbox = tk.Text(self.tk_gibbs_frame, width=10, height=1)
		self.tk_burn_in_textbox.insert(tk.END, '200')
		self.tk_num_iterations_textbox = tk.Text(self.tk_gibbs_frame, width=10, height=1)
		self.tk_num_iterations_textbox.insert(tk.END, '1000')
		self.random_start_var = tk.IntVar()
		self.random_start_var.set(1)
		self.tk_random_start_checkbox = tk.Checkbutton(self.tk_gibbs_frame, text="random start", variable=self.random_start_var)
		
		# Analysis stuff
		self.tk_analyse_button = tk.Button(self.tk_gibbs_frame, text="Analyse")
		self.tk_solve_button = tk.Button(self.tk_gibbs_frame, text="Solve")
		
		# Probability distribution stuff
		self.tk_prob_dist_frame = tk.Frame(parent, width=160, height=200)
		self.tk_prob_dist_label = tk.Label(self.tk_prob_dist_frame, text="Probability distribution")
		self.tk_filename_label = tk.Label(self.tk_prob_dist_frame, text="File name")
		# ADD NEW WORD FILES HERE
		self.filename_options = {"dictionary", "wordnet"}
		self.filename_var = tk.StringVar(self.tk_prob_dist_frame)
		self.filename_var.set("dictionary")
		self.tk_filename_dropdown = tk.OptionMenu(self.tk_prob_dist_frame, self.filename_var, *self.filename_options)
		self.tk_neighbours_label = tk.Label(self.tk_prob_dist_frame, text="# of neighbours")
		self.tk_neighbours_textbox = tk.Text(self.tk_prob_dist_frame, width=3, height=1)
		self.tk_neighbours_textbox.insert(tk.END, '1')
		self.pos_var = tk.IntVar()
		self.tk_pos_checkbox = tk.Checkbutton(self.tk_prob_dist_frame, text="Position of letters", variable=self.pos_var)
		self.length_var = tk.IntVar()
		self.tk_length_checkbox = tk.Checkbutton(self.tk_prob_dist_frame, text="Length of word", variable=self.length_var)
		
		# Gibbs sampler stuff
		self.tk_gibbs_frame.place(x=0, y=0)
		self.tk_gibbs_label.place(x=gibbs_frame_width // 2 - 50, y=0)
		self.tk_load_button.place(x=0, y=25)
		self.tk_start_gibbs_button.place(x=105, y=25)
		self.tk_burn_in_label.place(x=0, y=60)
		self.tk_num_iterations_label.place(x=0, y=80)
		self.tk_burn_in_textbox.place(x=80, y=60)
		self.tk_num_iterations_textbox.place(x=80, y=80)
		self.tk_random_start_checkbox.place(x=0, y=100)
		
		# Analysis stuff
		self.tk_analyse_button.place(x=0, y=125)
		self.tk_solve_button.place(x=60, y=125)
		
		# Probability distribution stuff
		pd_x = gibbs_frame_width + 50
		self.tk_prob_dist_frame.place(x=pd_x, y=0)
		self.tk_prob_dist_label.place(x=12, y=0)
		self.tk_filename_label.place(x=0, y=25)
		self.tk_filename_dropdown.place(x=60, y=20)
		self.tk_neighbours_label.place(x=0, y=60)
		self.tk_neighbours_textbox.place(x=95, y=60)
		self.tk_pos_checkbox.place(x=0, y=80)
		self.tk_length_checkbox.place(x=0, y=100)