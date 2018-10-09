import numpy


# The distribution that gets sampled
class Probability_distribution:
	def __init__(self):
		# Contains the conditional probability distribution
		self.dist = {}
		# Holds a cache of previously calculated probability distributions
		self.cache_dist = {}
	
	def set_distribution(self, new_dist):
		self.dist = new_dist
		self.cache_dist = {}
	
	# Returns a sample from the probability distribution
	# keys - The pattern within the crossword e.g. "_*A". [horizontal key, vertical key]
	def get_sample(self, keys):
		# Holds the new distribution
		dist = {}
		keys.sort()
		
		# Removes invalid keys
		keys = [key for key in keys if key != "_*_"]
		
		# the cache key needs the keys to be sorted
		cache_key = "".join(keys)
		
		if cache_key in self.cache_dist:
			# Saves multiple calculations every iteration by using the stored cache
			dist = self.cache_dist[cache_key]
		elif len(keys) == 1:
			# No overlapping words
			if keys[0] in self.dist:
				dist = self.dist[keys[0]]
			
			dist = self.norm_dist(dist)
			self.cache_dist[cache_key] = dist
		elif len(keys) == 2:
			# Two words overlap. Calculate the probabilities of the different combinations
			# The total probabilitity
			total = 0
			
			# Create the distribution for two overlapping keys by
			# finding any similar letters between the two and multiplying the probabilities together
			if keys[0] in self.dist:
				for key, data in self.dist[keys[0]].items():
					if key in self.dist[keys[1]]:
						# The two keys share the same letter
						value = data * self.dist[keys[1]][key]
						total += value
						
						dist[key] = value
			
			dist = self.norm_dist(dist)
			self.cache_dist[cache_key] = dist
		
		if dist:
			return numpy.random.choice(list(dist.keys()), p=list(dist.values()))
		
		# No elements have been found for that key implies no pattern has been found for that key
		return None
	
	# Normalizes a distribution
	def norm_dist(self, dist):
		total = 0
		
		if dist:
			# Calculate the total
			for key, value in dist.items():
				total += value
			
			# Normalize the distribution
			for key in dist.keys():
				dist[key] = dist[key] / total
		
		return dist