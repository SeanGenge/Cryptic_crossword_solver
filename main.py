from Controller import Controller
import random


def test(pos, n):
	a = "panda"
	left = a[max(0, pos - n):pos]
	right = a[pos + 1:pos + n + 1]
	pattern = (n - len(left)) * '_' + left + '*' + right + (n - len(right)) * '_'
	return pattern


if __name__ == "__main__":
	controller = Controller()
	controller.run()
	
	'''for p in range(4):
		print(test(p, 3))'''