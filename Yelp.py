import requests
from bs4 import BeautifulSoup
# pip install lxml
import json
import time
from Tempe import Tempe
from twocaptcha import TwoCaptcha

# YelpProxy inherited class for using a proxy with the Yelp API.
# You're going to need private proxies, Yelp detected all the public ones I have tried.
# If not, then you'll have to use 2Captcha to deal with bot detection.

# Email verfication for accounts before they can post a review.
# Account HAS to be verified by an email.
# You could use gurilla-mail or a paid API for this.

# Buisness ID can be found of the page of the buisness to review.

# Generate YelpCaptchaException and return the sitekey as an attribute in order to not waste money.


# Used for Yelp API errors.
class YelpException(Exception):

	# Creates a new instance of the Yelp exception class.
	def __init__(self, message, err_code):
		# Call the base excepetion class.
		super(YelpException, self).__init__(message)
		# Sets the error code.
		self.err_code = err_code


# Raised when a captcha is found.
class YelpCaptchaException(YelpException):

	# Creates a new instance of the Yelp captcha exception class.
	def __init__(self, message, err_code, page_url, site_key):
		# Call the base excepetion class.
		super(YelpCaptchaException, self).__init__(message, err_code)
		# Sets the page url.
		self.page_url = page_url
		# Sets the site key.
		self.site_key = site_key


# Wrapper for a Yelp API response.
class YelpResponse:

	# Creates a new instance of the Yelp response class.
	def __init__(self, response):
		# Sets the response attribute.
		self.response = response
		# Adds the html content to beautiful soup.
		self.soup = BeautifulSoup(self.response.content, 'html.parser')

	# Extracts a form csrf token from the Yelp response.
	def get_form_csrf(self, form):
		# Finds the requested form.
		signup_form = self.soup.find('form', {'action': form})
		# Finds and returns the csrf token.
		return signup_form.find('input', {'name': 'csrftok'}).get('value')

	# Extracts a js csrf token from the Yelp response.
	def get_js_csrf(self, token):
		try:
			# Extracts the dictonary of tokens.
			csrf_tokens = json.loads(self.response.text.split('"csrfToks": ')[1].split(', "cashBack"')[0])
		except (json.decoder.JSONDecodeError, IndexError):
			# Raises a csrf token not found exception.
			raise YelpException('Csrf token not found.', None)
		# Returns the token.
		return csrf_tokens[token]

	# Gets the yelp config from the response.
	def get_yelp_config(self):
		try:
			# Extracts the Yelp config.
			yelp_config = json.loads('{' + self.response.text.split('yConfig = {')[1].split('};')[0] + '}')
		except (json.decoder.JSONDecodeError, IndexError):
			# Raises a csrf token not found exception.
			raise YelpException('Yelp config not found.', None)
		# Returns the Yelp config.
		return yelp_config

	# Extracts the google recpatcha public site key from the response.
	def get_site_key(self):
		# Gets the Yelp config.
		yelp_config = self.get_yelp_config()
		# Returns the site key.
		return yelp_config['recaptchaPublicKey']

	# Raises an exception if there is a problem with the API.
	def check_status(self):
		try:
			# Raises an exception if the status is an error.
			self.response.raise_for_status()
		except requests.exceptions.HTTPError:
			# Constructs the error message.
			err_msg = 'Bad status code: {}'.format(self.response.status_code)
			# Raises a bad status code exception.
			raise YelpException(err_msg, None)

	# Checks if the response is an error.
	def check_for_error(self):
		# If there is an error message in the response.
		if 'Error message' in self.response.text:
			# Finds the error container.
			err_container = self.soup.find('div', {'class': 'alert alert-error'})
			# Validates the container.
			if err_container:
				# Gets the error message
				err_msg = err_container.text.strip()
				# Checks if the error message involves a captcha.
				if err_msg == 'Are you a human? Please complete the bot challenge below.':
					# Raises a captcha exception instead.
					raise YelpCaptchaException(err_msg, None, self.response.url, self.get_site_key())
				else:
					# Raises a failed exception.
					raise YelpException(err_msg, None)

	# Returns the response success message.
	def get_success_message(self):
		# If there is an success message in the response.
		if 'Success message' in self.response.text:
			# Finds the success container.
			success_container = self.soup.find('div', {'class': 'alert alert-success'})
			# Validates the container
			if success_container:
				# Gets and returns the success message
				return success_container.text

	# Returns the response data in json format.
	def get_data(self, **kwargs):
		# Returns the response data in json format.
		return self.response.json(**kwargs)

	# Returns the status code of the response.
	def get_status(self):
		# Returns the status code.
		return self.response.status_code


# A wrapper for the Yelp API.
class Yelp:

	# Stores the wrapper's user agent
	USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0'
	# Stores the API host name.
	HOST_NAME = 'https://www.yelp.com/'
	# Stores the sign up directory.
	SIGN_UP = '/signup'
	# Stores the login directory.
	LOG_IN = '/login'
	# Stores the write review directory.
	WRITE_REVIEW = '/writeareview/biz'
	# Stores the post review directory.
	POST_REVIEW = '/writeareview/v2/review_post'

	# Creates a new instance of the Yelp API.
	def __init__(self):
		# Creates a new session for cookies.
		self.session = requests.session()
		# Adds the user agent to the session headers.
		self.session.headers.update({'User-Agent': Yelp.USER_AGENT})
		# Gets the main session cookies and checks if the website is running.
		YelpResponse(self.session.get('https://www.yelp.com/')).check_status()

	# Registers an account on Yelp.
	def register(self, first_name, last_name, email, password, zip_code, recaptcha_response=None):
		# Gets the page cookies.
		signup = YelpResponse(self.session.get('https://www.yelp.com/signup'))
		# Checks the status of the request.
		signup.check_status()
		# Gets the sing up csrf token.
		csrf_tok = signup.get_form_csrf('/signup')
		# Creates the register post data.
		reg_data = {'csrftok': csrf_tok, 'first_name': first_name, 'last_name': last_name, 'email': email, 'password': password, 'result_password_strength_meter': None, 'signup_source': 'default', 'city': None, 'zip': zip_code, 'other_country': 'US', 'birthdate_m': None, 'birthdate_d': None, 'birthdate_y': None, 'marketing_email_allowed': '0', 'g-recaptcha-response': recaptcha_response}
		# Posts the register data to Yelp.
		res = YelpResponse(self.session.post('https://www.yelp.com/signup', data=reg_data))
		# Checks the status of the request.
		res.check_status()
		# Validates the sign up.
		res.check_for_error()
		# Checks the success message
		# if res.get_success_message() != 'A confirmation email has been sent.':

	# Signs into the specified Yelp account.
	def login(self, email, password, recaptcha_response=None):
		# Gets the page cookies.
		signup = YelpResponse(self.session.get('https://www.yelp.com/login'))
		# Checks the status of the request.
		signup.check_status()
		# Gets the login up csrf token.
		csrf_tok = signup.get_form_csrf('/login')
		# Creates the login post data.
		login_data = {'csrftok': csrf_tok, 'email': email, 'password': password, 'g-recaptcha-response': recaptcha_response}
		# Posts the login data to Yelp.
		res = YelpResponse(self.session.post('https://www.yelp.com/login', data=login_data))
		# Checks the status of the request.
		res.check_status()
		# Validates the login.
		res.check_for_error()

	# Takes a email verification url and confirms the account email.
	def verify_email(self, url):
		# Validates the email.
		res = YelpResponse(self.session.get(url))
		# Validates the status
		res.check_status()
		# Validates the success message.
		# if res.get_success_message() != 'Congratulations, your email is now confirmed!':
		# Raises an error.
		# raise YelpException('Email address not confirmed.')

	# Returns the id of the specified buisness.
	def find_buisness(self):
		# You can make this function return the buisness id for the given buisness.
		pass

	# Posts a review with the current account.
	def post_review(self, business_id, post_to_fb, post_to_twitter, rating, text, tweet_text):
		# Gets the page cookies.
		review = YelpResponse(self.session.get('https://www.yelp.com/writeareview/biz/{}'.format(business_id)))
		# Checks the status of the request.
		review.check_status()
		# Gets the review post csrf token.
		csrf_tok = review.get_js_csrf('reviewPost')
		# Creates the review post data.
		rev_data = {'business_id': business_id, 'post_to_fb': post_to_fb, 'post_to_twitter': post_to_twitter, 'rating': rating, 'review_origin': 'writeareview', 'suggestion_uuid': None, 'text': text, 'tweet_text': tweet_text, 'csrftok': csrf_tok}
		# Creates some extra headers to prevent an error.
		headers = {'X-Requested-With': 'XMLHttpRequest'}
		# Posts the review data to Yelp.
		res = YelpResponse(self.session.post('https://www.yelp.com/writeareview/v2/review_post', headers=headers, data=rev_data))
		# Casts the response to json.
		res_data = res.get_data()
		# Validates the response.
		if not res_data['success']:
			# Gets the error message.
			err_msg = res_data['message']
			# Gets the error code.
			# err_code = res_data['code']
			# Raises an exception with the error.
			raise YelpException(err_msg, None)

	# Clears the session (logs out any logged in users).
	def clear_session(self):
		# Clears the session cookies.
		self.session.cookies.clear()


# Uses a proxy with the Yelp API.
class YelpProxy(Yelp):

	# Creates a new instance of the Yelp proxy class.
	def __init__(self, proxy):
		# Call the base Yelp class.
		# super(YelpProxy, self).__init__()
		# This part had to be reimplemented to avoid using our own IP to check if the site is running.
		# Creates a new session for cookies.
		self.session = requests.session()
		# Adds the user agent to the session headers.
		self.session.headers.update({'User-Agent': YelpProxy.USER_AGENT})
		# Sets the session proxy.
		self.session.proxies.update({'http': proxy, 'https': proxy})
		# Turns of SSL certificate verification.
		self.session.verify = False
		# Gets the main session cookies and checks if the website is running.
		YelpResponse(self.session.get('https://www.yelp.com/')).check_status()


# Inherits from tempe in order to provide the ability to find a Yelp verification email.
class YelpEmail(Tempe):

	# Gets the Yelp email verify link from a tempe object.
	def get_email_verify_link(self):
		# Gets the current inbox.
		inbox = self.get_inbox()
		# Iterates through the emails.
		for email in inbox:
			# Checks the sender and subject.
			if email['From'] == 'no-reply@yelp.com' and email['Subject'] == 'Please confirm your email':
				# Gets the email body.
				soup = BeautifulSoup(email['Body'], 'html.parser')
				# Finds the link tags.
				link = soup.find('a', {'style': 'border-radius: 3px; font-size: 16px; color: white; padding: 12px 28px; background: #d91213; white-space: nowrap; font-family: Helvetica Neue, Arial, sans-serif;; border: 1px solid #a50508; text-align: center; background-image: linear-gradient(#d90007, #d32323); -webkit-border-radius: 3px; text-decoration: none; width: initial; font-weight: bold; display: inline-block;'})
				# Returns the link.
				return link.get('href')


if __name__ == '__main__':

	# You can either create a non proxied class or a proxied class. Both can be seen below.
	# I suggest using proxies or else you will have to deal with captchas.

	# Initializes a non-proxied Yelp API wrapper.
	yelp = Yelp()

	# Initializes the Yelp API wrapper with a proxy.
	# Make sure to only use working proxies with this, else things will go bad.
	# This constructor will raise a YelpException of "Bad status code" if the proxy is blocked by Yelp.
	# I suggest you catch this exception and then try a different proxy.
	# yelp = YelpProxy('127.0.0.1:8080')

	# Creates a new temporay email.
	# This class will be used later to request the Yelp email varification url.
	temp_email = YelpEmail()

	# Creates the 2Captcha instance in order to solve any captchas given by Yelp.
	# The only argument for this is the users 2Captcha API key.
	solver = TwoCaptcha('8e7855b990d576dfe5949d4442c393cd')

	# Notifies the user.
	# print('Creating account:', temp_email)

	# Registers an account on Yelp.
	# A YelpException is raised if anything goes wrong with the registration process.
	# A YelpCaptchaException is raised if a captcha is found.
	# YelpCaptchaException iherits from YelpException, so both can be caught with a YelpException catch.
	# The code below will loop and attempt to solve a present captcha.

	# Captcha token is null for now, just in case the site doesn't require a captcha for now.
	token = None
	# Loops while there is a captcha.
	while True:
		# Handles a captcha.
		try:
			# Attempts to register with Yelp.
			yelp.register('Test', 'Account', temp_email, 'RandomPassword123', 'LO1', token)
			# Register successful.
			break
		# If a captcha is found.
		except YelpCaptchaException as captcha:
			# Solves the captcha and tries again.
			token = solver.solve_captcha(captcha.site_key, captcha.page_url)

	# Before the next function is called you MUST verify the email address associated with the account.
	# The code below will verifiy the email associated with the Yelp account.

	# Loops while attempting to get the link.
	while True:
		# Gets the email verify link
		ver_link = temp_email.get_email_verify_link()
		# Validates the link
		if ver_link:
			# Takes a verfication link for the logged in account and verifies the email.
			yelp.verify_email(ver_link)
			# Time for verfication to take affect.
			time.sleep(5)
			# Breaks from the loop.
			break

	# I also suggest you implement a function that will use the Yelp search function to find an id for a buisness.
	# This is crucial since the id is used in the next function.
	# However, the id can manually be given by the user.

	# Below we attempt to login via the account we just created.
	# Since by default Yelp logs us in after registration we have to clear the current session.
	# Clears the Yelp session in order for a clean login.
	yelp.clear_session()

	# Captcha token is null for now, just in case the site doesn't require a captcha for now.
	token = None
	# Loops while there is a captcha.
	while True:
		# Handles a captcha.
		try:
			# Attempts to login with Yelp.
			yelp.login(temp_email, 'RandomPassword123', token)
			# Login successful.
			break
		# If a captcha is found.
		except YelpCaptchaException as captcha:
			# Solves the captcha and tries again.
			token = solver.solve_captcha(captcha.site_key, captcha.page_url)

	# Now that we are logged into the Yelp account we can post a review.

	# Posts a review with the account.
	# A YelpException is raised if anything goes wrong with the review process.
	yelp.post_review('hsQNfOJFFn6Bqf22YL1pKA', False, False, 5, 'Thanks for all the fish! I have given them a small house in my bath tub so I\'ll never be lonely in the bath.', 'Fish are NOT potatoes!... #Twitter #CoolGuy #PotatoFish')