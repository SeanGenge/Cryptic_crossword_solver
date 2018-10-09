import sys
import urllib.error
from urllib.request import urlopen
from bs4 import BeautifulSoup
from os import path

def get_crossword(type, num, num_crosswords):
	for i in range(int(num_crosswords)):
		curr_num = int(num) + i
		link = "https://www.theguardian.com/crosswords/" + type + "/" + str(curr_num)
		
		try:
			f = urlopen(link)
			html = f.read()
			
			print("read " + type + " No " + str(int(num) + i) + "/" + str(int(num_crosswords) - 1 + int(num)))
			
			raw = BeautifulSoup(html, 'html.parser')
			raw.prettify()
			
			# Finds the data that is needed
			data = raw.find('div', {'class': 'js-crossword'})
			
			data = str(data).split('\n')[0]
			data = data.replace('&quot;', '')
			data = data.replace('"', '')
			
			data = parse_data(data)
			save_data(path.relpath("Crosswords/" + type + "/" + type + " No " + str(curr_num) + ".txt"), data)
			
			f.close()
		except:
			print("https://www.theguardian.com/crosswords/" + type + "/" + str(curr_num) + " cannot be found/loaded")

def parse_data(data):
	d = "entries:\n"
	# The previously visited item
	prev_item = ""
	data = data.replace("\\", "\"")
	
	# Cleans up the data
	data = data.replace("{", "")
	data = data.replace("}", "")
	data = data.replace("[", "")
	data = data.replace("]", "")
	
	data = data[data.find("id", data.find("id") + 1):]
	data = data.split(",")
	
	for item in data:
		i = item.split(":")
		if len(i) != 2:
			if prev_item == "clue":
				d = d[:len(d) - 1] + "," + item + "\n"
			elif i[0] == "clue":
				d = d + item + "\n"
				prev_item = i[0]
			elif i[0] == "position":
				d = d + item + ","
			else:
				continue
		else:
			d = d + item + "\n"
			prev_item = i[0]
	
	return d

def save_data(file_name, data):
	file = open(file_name, 'w')
	
	data = [item for item in data.split("\n")]
	
	start = False
	file.write("size:15")
	
	for item in data:
		items = item.split(":", 1)
		
		if len(items) != 2:
			continue
		
		if items[0] == "entries":
			start = True
		
		if start == True:
			if items[0] == "id":
				# Start of a new clue
				file.write("\nnew clue\n")
			elif items[0] == "number" or items[0] == "clue" or items[0] == "direction" or items[0] == "position" or items[0] == "solution" or items[0] == "length":
				item = item.replace("[", "")
				item = item.replace("]", "")
				item = item.replace("{", "")
				item = item.replace("}", "")
				
				file.write(item + "\n")
				
if __name__ == "__main__":
	if len(sys.argv) != 4:
		print("Invalid number of arguments: type, num, num_crosswords")
	else:
		get_crossword(sys.argv[1], sys.argv[2], sys.argv[3])