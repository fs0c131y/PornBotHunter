#!/usr/bin/env python3

"""
Twitter Porn bot hunter
"""

import datetime
import os
import pycurl
import random
import re
import time
from io import BytesIO
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import requests
import tweepy
from bs4 import BeautifulSoup
from googlesearch.googlesearch import GoogleSearch

from secrets import *

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)

pseudos = []
patterns = [
	'site:twitter.com "Twerk dancer/Fitness lover"',
	'site:twitter.com "Cosplay master \\ Travel lover"',
	'site:twitter.com "Cosplay master/Travel lover"',
	'site:twitter.com "Cosplay master \\\\ Travel lover"',
	'site:twitter.com "Cosplay master // MARVEL fan"',
	'site:twitter.com "Cosplay fan // MARVEL fan"',
	'site:twitter.com "Sweet lady. Dancing \\\\ DC fan"',
	'site:twitter.com "Sweet lady. Twerk dancer. Cats lover"',
	'site:twitter.com "Pretty girl. Dancing. Fitness"',
	'site:twitter.com "Actress \\\\ Travel"',
	'site:twitter.com "Costume designer // Dogs lover"',
	'site:twitter.com "Gamer / Dogs lover"',
	'site:twitter.com "Cute girl. Cosplay fan/MARVEL fan"',
	'site:twitter.com "Humble girl. Cosplayer/DC fan"',
	'site:twitter.com "Simple girl. Gamer \ Traveler"',
	'site:twitter.com "Voice actress. Dogs lover'
]

TEMP_FILE = 'temp.jpg'
DELAY_BETWEEN_PUBLICATION = 3600


def paste(content, title, key):
	"""
	Create a paste on https://pastebin.com

	Parameters
	----------
	content: String
		Body of the paste

	title: String
		Title of the paste

	key: String
		The API dev key from https://pastebin.com

	Returns
	-------
	Optional[String]
		The URL of the paste if successful, None otherwise
	"""

	options = {
		'api_dev_key': key,
		'api_option': 'paste',
		'api_paste_name': title,
		'api_paste_code': content,
		'api_paste_private': 0
	}

	try:
		response = urlopen('http://pastebin.com/api/api_post.php', urlencode(options).encode('utf-8'))

		return response.read()
	except (URLError, Exception):
		return None


def parse_google_web_search(search_result):
	"""
	Parse a Google web search.

	Parameters
	----------
	search_result : String[]
		Google web search result
	"""

	for result_item in search_result.results:
		handle = result_item.url.split("/")[3]

		if handle not in pseudos:
			pseudos.insert(0, handle)
			print("pseudo: {}, length: {}".format(handle, len(pseudos)))


def publish_tweet(handle):
	"""
	Publish a tweet.

	Parameters
	----------
	handle : String
		pseudo of the bot

	Returns
	-------
	Boolean
		True if the tweet had been published, otherwise False
	"""

	profile_url = get_profile_picture_url("https://twitter.com/{}".format(
		handle))

	if profile_url and download_image(profile_url):
		user = api.get_user(handle)
		message = ("Pseudo: {}"
		           "\nFollowers: {}"
		           "\nFollowing: {}"
		           "\nCreated at: {}").format(handle, user.followers_count,
		                                      user.friends_count,
		                                      user.created_at)
		description_link = get_link_description(user.description)

		if description_link:
			message = message + "\nBio link: " + description_link
		api.update_with_media(TEMP_FILE, status=message)

		os.remove(TEMP_FILE)

		return True
	else:
		message = "Pseudo: " + handle + "\nStatus: suspended"
		api.update_status(message)


def download_image(profile_picture_url):
	"""
	Download image.

	Parameters
	----------
	profile_picture_url : String
		URL of the Twitter profile picture

	Returns
	-------
	Boolean
		True if the image had been downloaded, otherwise False
	"""

	request = requests.get(profile_picture_url, stream=True)

	if request.status_code == 200:
		with open(TEMP_FILE, 'wb') as image:
			for chunk in request:
				image.write(chunk)
			return True
	else:
		print("Unable to download image")
		return False


def get_profile_picture_url(profile_url):
	"""
	Get the profile picture URL.

	Parameters
	----------
	profile_url : String
		URL of the Twitter profile

	Returns
	-------
	Optional[String]
		Profile picture URL otherwise None
	"""

	url_re = re.compile(r"https://pbs.twimg.com/profile_images/.*?jpg")

	page = urlopen(profile_url)

	if page:
		html = page.read().decode('utf-8')

		if html:
			profile_picture_url = url_re.findall(html)

			if profile_picture_url:
				return profile_picture_url[0]


def get_link_description(description):
	"""
	Get the link in the description.

	Parameters
	----------
	description : String
		Twitter description of the bot

	Returns
	-------
	Optional[String]
		HTTP link in the description otherwise None
	"""

	url_re = re.compile("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
	link_description = url_re.findall(description)

	if link_description:
		return link_description[0]


def google_image_search(image_url):
	"""
	Get the link in the description.

	Parameters
	----------
	image_url : String
		Url of the profile picture of the Twitter bot
	"""

	search_url = 'https://www.google.com/searchbyimage?&image_url='

	buffer = BytesIO()
	full_url = search_url + image_url + '&q=site:twitter.com&intitle:"(@"'

	conn = pycurl.Curl()
	conn.setopt(conn.URL, str(full_url))
	conn.setopt(conn.FOLLOWLOCATION, 1)
	conn.setopt(conn.USERAGENT,
	            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11'
	            ' (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11')
	conn.setopt(conn.WRITEFUNCTION, buffer.write)
	conn.perform()
	conn.close()

	soup = BeautifulSoup(buffer.getvalue().decode('utf-8'), 'html.parser')

	for div in soup.findAll('div', attrs={'class': 'rc'}):
		s_link = div.find('a')

		if 'status' not in s_link:
			handle = s_link['href'].split("/")[3]

			if handle not in pseudos:
				pseudos.append(handle)
				print("pseudo: {}, length: {}".format(handle, len(pseudos)))


def publish_summary_tweet():
	"""
	Publish the summary tweet
	"""

	# Create the pastebin content
	paste_content = "Detected Twitter porn bots by @PornBotHunter:"

	for name in pseudos:
		paste_content += "\n@{}".format(name)

	now = datetime.datetime.now()
	title = "Detected bots by @PornBotHunter {}".format(
		now.strftime("%d/%m/%Y"))

	pbin_url = paste(paste_content, title, pastebin_dev_key)

	if pbin_url:
		message = ("Currently, @PornBotHunter detected {} #Twitter #porn #bots."
		           "Detailed list is available here: {}").format(len(pseudos),
		                                                         pbin_url)
		api.update_status(message)


if __name__ == '__main__':
	while True:
		result = GoogleSearch().search(random.choice(patterns), num_results=100)
		parse_google_web_search(result)

		publish_summary_tweet()
		time.sleep(DELAY_BETWEEN_PUBLICATION)

		for pseudo in pseudos:
			url = get_profile_picture_url("https://twitter.com/{}".format(
				pseudo))

			if url:
				google_image_search(url)

			publish_tweet(pseudo)
			time.sleep(DELAY_BETWEEN_PUBLICATION)
