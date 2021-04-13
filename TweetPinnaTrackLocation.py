#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TweetPinna - Twitter Status Archiver.

TweetPinna streams Twitter statuses into a
MongoDB database based on given search terms.
It is also capable of retrieving a user's timeline.

Author: Ingo Kleiber <ingo@kleiber.me> (2018)
License: MIT
Version: 1.1.1
Status: Protoype

Example8
    $ python TweetPinnaTrackLocation.py config.cfg
"""

from email.mime.text import MIMEText
from pymongo import errors
from pymongo import MongoClient
from time import sleep
from TweetPinna import Logger
from TweetPinna import check_config
import config
import datetime
import os
import signal
import smtplib
import subprocess
import sys
import _thread
import time
import tweepy


class TwitterStreamListener(tweepy.StreamListener):
    """The Tweepy StreamListener."""

    def __init__(self):
        """Docstring for Logger."""
        global end_script
        super(TwitterStreamListener, self).__init__()
        self.counter = 0
        self.status_buffer = []
        self.mongo_db_connected = False

        self.connect_mongodb()
        if not self.mongo_db_connected:
            print ("Cannot connect to MongoDB!")
            end_script(self)

    def connect_mongodb(self):
        """Connecting to MongoDB."""
        try:
            self.mongo_client = MongoClient(cfg['mongo_path'],
                                            connectTimeoutMS=500,
                                            serverSelectionTimeoutMS=500)

            # Check whether the connection is established or not
            self.mongo_client.server_info()

            self.mongo_db = self.mongo_client[cfg['mongo_db']]
            self.mongo_coll_tweets = self.mongo_db[cfg['mongo_coll']]

            self.mongo_db_connected = True
            log.log_add(2, 'Connection to MongoDB established')
        except:
            self.mongo_db_connected = False

    @staticmethod
    def media_download(insert_id):
        """Calling the media downloader."""
        if cfg['media_download_instantly'] == 1:
            try:
                fnull = open(os.devnull, 'w')
                subprocess.Popen(["python", "TweetPinnaImageDownloader.py",
                                  sys.argv[1], str(insert_id)],
                                 shell=False, stdout=fnull,
                                 stderr=subprocess.STDOUT)
            except Exception as e:
                log.log_add(4, 'Could not instantly download media files ({})'.
                            format(e))

    def add_to_mongodb(self, status):
        """Addint statuses to MongoDB."""
        try:
            insert = self.mongo_coll_tweets.insert_one(status._json)
            insert_it = insert.inserted_id
            self.media_download(insert_id)
            self.counter += 1
        except errors.ServerSelectionTimeoutError:
            log.log_add(cfg['log_email_threshold'],
                        'MongoDB ServerSelectionTimeoutError')
            self.connect_mongodb()
        except Exception as e:
            log.log_add(cfg['log_email_threshold'],
                        'Could not write to MongoDB ({})'.format(e))

    def clear_buffer(self):
        """Write the buffer to MongoDB."""
        if self.mongo_db_connected:
            while len(self.status_buffer) > 0:
                self.add_to_mongodb(self.status_buffer.pop())

        if len(self.status_buffer) == 0:
            log.log_add(3, 'Buffer has been cleared')

    def on_status(self, status):
        """Collecting statuses and handling them."""
        if self.mongo_db_connected:
            self.add_to_mongodb(status)

            if len(self.status_buffer) > 1:
                _thread.start_new(self.clear_buffer, ())
        else:
            if cfg['tweet_buffer'] == 1 and len(self.status_buffer) \
                < cfg['tweet_buffer_max']:
                self.status_buffer.append(status)
            _thread.start_new(self.connect_mongodb, ())

    def on_error(self, status_code):
        """Reacting to Twitter errors."""
        global end_script

        if status_code == 420:
            log.log_add(4, 'Twitter 420 Error')
            log.last_twitter_error_message = 420
            return False
        elif status_code == 429:
            log.log_add(4, 'Twitter 429 Error')
            log.last_twitter_error_message = 429
            return False
        elif status_code == 401:
            # Unauthorized
            log.log_add(4, 'Twitter 401 Error')
            log.last_twitter_error_message = 401
            print ('Twitter authentication error!')
            end_script(self)
            return False
        else:
            log.log_add(4, 'Twitter {}'.format(status_code))


def start_stream(stream):
    """Starting the Tweepy stream.

    :param stream object stream: the Tweepy stream object
    """
    log.log_add(1, 'Stream started by start_stream')

    bounding_boxes = [coordinate for box in cfg['twitter_tracking_locations'] for coordinate in box]
    print(bounding_boxes)

    try:
        twitter_stream.filter(locations=bounding_boxes, is_async=True)
    except Exception as e:
        log.log_add(cfg['log_email_threshold'],
                    'twitter_stream Exception ({})'.format(e.message))
        end_script(stream)


def stop_stream(stream):
    """Stopping the Tweepy stream.

    :param stream object stream: the Tweepy stream object
    """
    try:
        stream.disconnect()
        log.log_add(1, 'Stream disconnected by stop_stream')
    except:
        log.log_add(1, 'Stream could not be disconnected by stop_stream')


def signal_handler(signum, frame):
    """Handlig interrupt signals."""
    stop_stream(twitter_stream)
    log.log_add(1, 'Interrupted by signal {}'.format(signum))
    log.log_add(1, 'Ending TweetPinnaTrackLocation (Inst.: {})'.format(cfg['instance_name']))
    print ('[{}] Ending TweetPinnaTrackLocation (Inst.: {})'.
           format(time.strftime("%Y-%m-%d %H:%M:%S"), cfg['instance_name']))
    sys.exit(1)


def end_script(stream):
    """Gracefully ending the script.

    :param stream object stream: the Tweepy stream object
    """
    stop_stream(stream)
    log.log_add(1, 'Ending TweetPinnaTrackLocation (Inst.: {})'.format(cfg['instance_name']))
    print ('[{}] Ending TweetPinnaTrackLocation (Inst.: {})'.
           format(time.strftime("%Y-%m-%d %H:%M:%S"), cfg['instance_name']))

    os._exit(0)
    sys.exit(1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    # Config
    try:
        if os.path.isfile(sys.argv[1]):
            if check_config(sys.argv[1]):
                cfg = config.Config(open(sys.argv[1], 'r'))
                log = Logger(cfg)
            else:
                print ('Configuration appears to be faulty')
                sys.exit(1)
        else:
            print ('Configuration file {} could not be found'.
                   format(sys.argv[1]))
            sys.exit(1)
    except IndexError:
        print ('Using default configuration')
        cfg = config.Config(open('cfg/TweetPinnaDefault.cfg'), 'r')
        log = Logger(cfg)

    if len(cfg['twitter_tracking_locations']) == 0:
        log.add(1, 'No locations to track.')
        sys.exit()

    # TweetPinna
    print ('[{}] Starting TweetPinnaTrackLocation (Inst.: {})'.
           format(time.strftime("%Y-%m-%d %H:%M:%S"), cfg['instance_name']))
    log.log_add(1, 'Starting TweetPinnaTrackLocation (Inst.: {})'.format(cfg['instance_name']))

    # Initialize Tweepy
    twitter_listener = TwitterStreamListener()
    auth = tweepy.OAuthHandler(
        cfg['twitter_consumer_key'],
        cfg['twitter_consumer_secret'])
    auth.set_access_token(
        cfg['twitter_access_token'],
        cfg['twitter_access_token_secret'])
    api = tweepy.API(auth)
    twitter_stream = tweepy.Stream(auth=api.auth, listener=twitter_listener)
    start_stream(twitter_stream)

    twitter_420_429s = 0
    twitter_420_429_escalation = 0
    last_tweet_milestone = 0

    while True:
        # Handling 420 (Enhance Your Calm) and 429 (Too Many Requests) Errors
        if log.last_twitter_error_message in (420, 429):
            twitter_420_429s += 1
            if twitter_420_429s > 3 and twitter_420_429_escalation == 3:
                log.log_add(
                    cfg['log_email_threshold'],
                    'Too many 420/429s, Disengaging')
                end_script(twitter_stream)
            if twitter_420_429s == 3 and twitter_420_429_escalation == 2:
                twitter_420_429_escalation = 3
                log.log_add(1, 'Third 420/429, Sleeping for 5 Minutes')
                sleep(300)
            elif twitter_420_429s == 2 and twitter_420_429_escalation == 1:
                twitter_420_429_escalation = 2
                log.log_add(1, 'Second 420/429, Sleeping for 60 Seconds')
                sleep(60)
            elif twitter_420_429s == 1 and twitter_420_429_escalation == 0:
                twitter_420_429_escalation = 1
                log.log_add(1, 'First 420/429, Sleeping for 10 Seconds')
                sleep(10)

        # Handling 401 Error
        if log.last_twitter_error_message == 401:
            log.log_add(
                cfg['log_email_threshold'],
                'Twitter Authentication failed')
            stop_stream(twitter_stream)
            keep_running = False

        # Printing current streaming status
        current_count = twitter_listener.counter
        if (current_count % cfg['report_steps'] ==
                0 and current_count > last_tweet_milestone):
            last_tweet_milestone = current_count
            print ('[{}] {} Tweets (Location) have been saved'.
                   format(time.strftime("%Y-%m-%d %H:%M:%S"), current_count))
            log.log_add(1, '{} Tweets (Location) have been saved'.format(current_count))
