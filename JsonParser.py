import json


class UniversalType:

	def __init__(self, data):

		self.data = data

	def find(self, value):

		return UniversalType.find_recurse(self.data, value)
	
	@staticmethod
	def find_recurse(data, value):

		if type(data) is list or type(data) is tuple or type(data) is set:

			values = data

		elif type(data) is dict:

			values = data.values()

		else:

			return None

		for item in values:

			if item == value:

				return UniversalType(data)

			else:

				result =  UniversalType.find_recurse(item, value)

				if result is not None:

					return result

	def __str__(self):

		return self.data.__str__()

	def __repr__(self):

		return self.data.__repr__()


# Opens the specified json file
def open_json(filename):
	# Opens the json file.
	with open(filename) as f:
		# Loads the json data into the parser and returns the object.
	    return json.load(f)


if __name__ == '__main__':
	# Opens the json file.
	data = UniversalType(open_json('data.json'))
	# Finds the Currency:MtxGiveaway dict.
	currency_dict = data.find('Currency:MtxGiveaway')
	# Prints the result
	print(currency_dict)
	# Waits for user.
	input()
