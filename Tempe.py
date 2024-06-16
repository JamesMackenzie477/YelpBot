import requests
import string
import random

# A wrapper for the tempemailaddress API.
class Tempe:

	# Creates a new temporary email.
	def __init__(self):
		# Creates a new random email address.
		self.email = self.__get_email()

	# Gets the inbox of the specified email address.
	def get_inbox(self):
		# Creates the request parameters.
		recv_params = {'action': 'receive', 'email': self.email}
		# Gets the email inbox from the API.
		return requests.get('http://tempemailaddress.com/jsapi.aspx', params=recv_params).json()

	# Returns a temporary email address.
	def __get_email(self):
		# Character list.
		char_list = string.digits + string.ascii_letters
		# Generates a random string.
		rnd_str = ''.join(char_list[random.randrange(0, len(char_list))] for x in range(0, random.randrange(10, 15)))
		# Constructs the email address.
		return '{}{}'.format(rnd_str, '@tempemailaddress.com')

	# The string method of the class.
	def __str__(self):
		# Returns the temporary email.
		return self.email

	# The represent method of the class.
	def __repr__(self):
		# Returns the temporary email.
		return self.email