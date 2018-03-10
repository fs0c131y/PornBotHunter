#!/usr/bin/env python
# encoding: utf-8

"""
Twitter Porn bot hunter
"""

import datetime
import os
import pycurl
import re
import random
import requests
import time
import tweepy
import urllib
import urllib2
import json
import sys

from bs4 import BeautifulSoup
from googlesearch.googlesearch import GoogleSearch
from pastebin_python import PastebinPython
from pastebin_python.pastebin_exceptions import PastebinBadRequestException, PastebinFileException
from pastebin_python.pastebin_constants import PASTE_PUBLIC, EXPIRE_NEVER
from pastebin_python.pastebin_formats import FORMAT_NONE
from StringIO import StringIO

pseudos = []

def parse_google_web_search(search_result):
    """
    Parse a Google web search.

    Parameters
    ----------
    search_result : String[]
        Google web search result
    """
    for result_item in search_result.results:
        pseudo = result_item.url.split("/")[3]
        if pseudo not in pseudos:
            pseudos.insert(0, pseudo)
            print("pseudo: " + pseudo + ", length: " + str(len(pseudos)))


def publish_tweet(pseudo):
    """
    Publish a tweet.

    Parameters
    ----------
    pseudo : String
        pseudo of the bot

    Returns
    -------
    Boolean
        True if the tweet had been published, otherwise False
    """

    profile_url = get_profile_picture_url("https://twitter.com/" + pseudo)
    if profile_url and download_image(profile_url):
        user = api.get_user(name)
        message = "Pseudo: " + pseudo + "\nFollowers: " + str(user.followers_count) + "\nFollowing: " \
                  + str(user.friends_count) + "\nCreated at: " + str(user.created_at)
        description_link = get_link_description(user.description)
        if description_link:
            message = message + "\nBio link: " + description_link
        api.update_with_media(data["temp_file"], status=message)

        os.remove(data["temp_file"])

        return True
    else:
        message = "Pseudo: " + pseudo + "\nStatus: suspended"
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
        with open(data["temp_file"], 'wb') as image:
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
    String
        Profile picture URL
    """

    url_re = re.compile(r"https://pbs.twimg.com/profile_images/.*?jpg")

    page = urllib.urlopen(profile_url)
    if page:
        html = page.read()
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
    String
        HTTP link in the description
    """

    url_re = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
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

    returned_code = StringIO()
    full_url = search_url + image_url + '&q=site:twitter.com&intitle:"(@"'

    conn = pycurl.Curl()
    conn.setopt(conn.URL, str(full_url))
    conn.setopt(conn.FOLLOWLOCATION, 1)
    conn.setopt(conn.USERAGENT, 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11'
                                ' (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11')
    conn.setopt(conn.WRITEFUNCTION, returned_code.write)
    conn.perform()
    conn.close()

    soup = BeautifulSoup(returned_code.getvalue(), 'html.parser')
    for div in soup.findAll('div', attrs={'class': 'rc'}):
        sLink = div.find('a')
        if 'status' not in sLink:
            pseudo = sLink['href'].split("/")[3]
            if pseudo not in pseudos:
                pseudos.append(pseudo)
                print("pseudo: " + pseudo + ", length: " + str(len(pseudos)))


def publish_summary_tweet():
    """
    Publish the summary tweet
    """

    # Create the pastebin content
    paste_content = "Detected Twitter porn bots by @PornBotHunter:"
    for name in pseudos:
        paste_content = paste_content + "\n@" + name

    # Pastebin client
    pbin = PastebinPython(api_dev_key=data["pastebin_dev_key"])

    try:
        pbin.createAPIUserKey(data["pastebin_username"], data["pastebin_password"])
        now = datetime.datetime.now()
        url = pbin.createPaste(paste_content, 'Detected bots by @PornBotHunter ' + str(now.day) + "/" +
                               str(now.month) + "/" + str(now.year), FORMAT_NONE, PASTE_PUBLIC,
                               EXPIRE_NEVER)

        message = "Currently, @PornBotHunter detected " + str(len(pseudos)) + " #Twitter #porn #bots." \
                                                                              " Detailed list is available here: " + url
        api.update_status(message)
    except PastebinBadRequestException as e:
        print e
    except PastebinFileException as e:
        print e


if __name__ == '__main__':
    data = json.load(open('config.json'))
    auth = tweepy.OAuthHandler(data["consumer_key"], data["consumer_secret"])
    auth.set_access_token(data["access_token"], data["access_secret"])
    api = tweepy.API(auth)
    patterns = data["patterns"]
    while True:
        search_text = 'site:twitter.com "{}"'.format(random.choice(patterns))
        try:
            result = GoogleSearch().search(search_text, num_results=100)
        except urllib2.HTTPError as httperr:
            print("{}. Google has detected an automated search.".format(httperr))
            sys.exit()
        parse_google_web_search(result)

        publish_summary_tweet()
        time.sleep(data["delay_between_publication"])

        for name in pseudos:
            url = get_profile_picture_url("https://twitter.com/" + name)
            if url:
                google_image_search(url)

            publish_tweet(name)
            time.sleep(data["delay_between_publication"])
