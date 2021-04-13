#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TweetPinna - Twitter Status Archiver.

TweetPinna streams Twitter statuses into a
MongoDB database based on given search terms.
It is also capable of retrieving a user's timeline.

This script downloads image data found in tweets for further analysis.

Author: Ingo Kleiber <ingo@kleiber.me> (2017)
License: MIT
Version: 1.1.1
Status: Protoype

Example:
    $ python TweetPinnaImageDownloader.py config.cfg (objectId)
"""

from bson.objectid import ObjectId
from pymongo import MongoClient
from TweetPinna import check_config
from TweetPinna import Logger
import config
import datetime
import mimetypes
import os.path
import requests
import signal
import sys
from urllib.parse import urlparse
from urllib.parse import urlsplit
import shutil

try:
    if os.path.isfile(sys.argv[1]):
        if check_config(sys.argv[1]):
            cfg = config.Config(open(sys.argv[1], 'r'))
            log = Logger(cfg)
        else:
            print('Configuration appears to be faulty')
            sys.exit(1)
    else:
        print('Configuration file {} could not be found'.format(sys.argv[1]))
        sys.exit(1)
except IndexError:
    print('Using default configuration')
    cfg = config.Config(open('cfg/TweetPinnaDefault.cfg', 'r'))
    log = Logger(cfg)

# Create directories
if not os.path.exists(cfg['media_photo_storage']):
    os.makedirs(cfg['media_photo_storage'])
if not os.path.exists(cfg['media_user_storage']):
    os.makedirs(cfg['media_user_storage'])


def signal_handler(signum, frame):
    """Handlig interrupt signals."""
    sys.exit(1)


def get_file_extension(url):
    """Getting the extensions (filetype) of an url.

    :param str url: the url to the file
    """
    filetype = os.path.splitext(
        os.path.basename(
            urlsplit(url).path))[1]

    return filetype


def download_media_file(type, url, filename, filetype='', copy_to=''):
    """Downloading a media file.

    :param str type: the type of the file (photo, user-profile-img,
    user-banner-img, user-bg-img)
    :param str url: the url to download from
    :param str filename: the filename to save to
    :param str filetype: the filytype (optional)
    :param str copy_to: a folder to which a copy of the file is sent
    """
    if (len(url) > 0):
        try:
            if type == 'photo':
                path = cfg['media_photo_storage'] + filename
            elif type in (
                    'user-profile-img', 'user-banner-img', 'user-bg-img'):
                path = cfg['media_user_storage'] + filename
            else:
                return False

            if not os.path.exists(path):
                r = requests.get(url, stream=True)

                if not filetype:
                    try:
                        path = path + mimetypes.guess_extension(
                            r.headers['content-type'])
                    except:
                        path = path + '.unknown'

                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)

            if copy_to:
                shutil.copy2(path, copy_to)


        except Exception as e:
            log.log_add(3, 'Image download failed ({})'.format(e))


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    # MongoDB
    mongo_client = MongoClient(cfg['mongo_path'])
    mongo_db = mongo_client[cfg['mongo_db']]
    mongo_coll_tweets = mongo_db[cfg['mongo_coll']]

    # Whole collections vs. individual ObjectId
    try:
        search_object_id = sys.argv[2]
    except:
        search_object_id = False

    if search_object_id:
        try:
            tweets = mongo_coll_tweets.find({'_id': ObjectId(sys.argv[2])})
        except:
            print('ObjectId seems to be invalid')
            sys.exit(1)

        if tweets.count() < 1:
            print('ObjectId not found')
            sys.exit(1)
    else:
        tweets = mongo_coll_tweets.find()


    # Download
    number_tweets = tweets.count()
    current_count = 0
    for tweet in tweets:
        if current_count % 100 == 0:
            print ('{} of {} Tweets processed'.format(current_count,
                                                      number_tweets))

        object_id = tweet["_id"]
        tweet_timestamp_s = int(tweet["timestamp_ms"]) / 1000
        tweet_date = datetime.datetime.fromtimestamp(
            tweet_timestamp_s).strftime('%Y%m%d')

        tweet_id = int(tweet["id"])
        user_id = tweet["user"]["id"]

        print(tweet_id)

        if "profile_image_url" in tweet["user"]:
            user_profile_image_url = tweet["user"]["profile_image_url"]

            if cfg['media_profile_image_hd'] == 1:
                user_profile_image_url = user_profile_image_url.replace(
                    'normal', '400x400')

            filetype = get_file_extension(user_profile_image_url)
            download_media_file(
                'user-profile-img', user_profile_image_url, '{}-profile-{}{}'.
                format(user_id, tweet_date, filetype), filetype)

        if "profile_banner_url" in tweet["user"]:
            user_profile_banner_url = tweet["user"]["profile_banner_url"]
            filetype = get_file_extension(user_profile_banner_url)
            download_media_file(
                'user-banner-img', user_profile_banner_url, '{}-banner-{}{}'.
                format(user_id, tweet_date, filetype), filetype)

        if "profile_background_image_url" in tweet["user"]:
            user_profile_bg_url = tweet["user"]["profile_background_image_url"]
            filetype = get_file_extension(user_profile_bg_url)
            download_media_file(
                'user-bg-img', user_profile_bg_url, '{}-bg-{}{}'.
                format(user_id, tweet_date, filetype), filetype)

        if "media" in tweet["entities"]:
            for media in tweet["entities"]["media"]:
                media_id = media["id"]
                if media["type"] == "photo":
                    photo_url = media["media_url_https"]
                    filetype = get_file_extension(photo_url)
                    download_media_file(
                        'photo', photo_url, '{0}-{1}-{2}{3}'.format(object_id,
                                                                    tweet_id,
                                                                    media_id,
                                                                    filetype),
                        filetype)

        current_count += 1
