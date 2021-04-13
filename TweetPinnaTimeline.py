#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TweetPinna - Twitter Status Archiver - Dashboard.

TweetPinna streams Twitter statuses into a
MongoDB database based on given search terms.
It is also capable of retrieving a user's timeline.

This script retrieves retrieves timelines.
It is supposed to run as a cronjob.

e.g.
*/10 * * * * bash -c "cd /root/TweetPinna &&
python TweetPinnaTimeline.py TweetPinnaDefault.cfg"

Author: Ingo Kleiber <ingo@kleiber.me> (2017)
License: MIT
Version: 1.1.1
Status: Protoype

Example:
    $ python TweetPinnaTimeline.py config.cfg
"""

from pymongo import MongoClient
from TweetPinna import check_config
from TweetPinna import Logger
import tweepy
import config
import os
import sys
import time


def get_tweets(screen_name, throttle=5):
    """Grabbing all tweets of a given screen_name."""
    tweets = []
    new_tweets = api.user_timeline(screen_name=screen_name, count=200, tweet_mode='extended')
    tweets.extend(new_tweets)
    oldest = tweets[-1].id - 1

    while len(new_tweets) > 0:
        # Throttle the connection
        time.sleep(throttle)
        new_tweets = api.user_timeline(screen_name=screen_name, count=200,
                                       max_id=oldest, tweet_mode='extended')
        tweets.extend(new_tweets)
        oldest = tweets[-1].id - 1

    return tweets


if __name__ == '__main__':
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
        cfg = config.Config(open('cfg/TweetPinnaDefault.cfg', 'r'))
        log = Logger(cfg)

    # TweetPinna
    log.log_add(1, 'Tracking Timelines {}'.format(cfg['instance_name']))

    # Initialize Tweepy
    try:
        auth = tweepy.OAuthHandler(
            cfg['twitter_consumer_key'],
            cfg['twitter_consumer_secret'])
        auth.set_access_token(
            cfg['twitter_access_token'],
            cfg['twitter_access_token_secret'])
        api = tweepy.API(auth)
        test = api.home_timeline()

    except:
        log.log_add(3, 'Timeline: Cannot connect to Twitter API {}'.
                    format(cfg['instance_name']))
        sys.exit(1)

    # mongoDB
    try:
        mongo_client = MongoClient(cfg['mongo_path'], connectTimeoutMS=500,
                                   serverSelectionTimeoutMS=500)
        mongo_db = mongo_client[cfg['mongo_db']]
        mongo_coll_tweets = mongo_db[cfg['mongo_coll']]
    except:
        log.log_add(3, 'Timeline: Cannot connect to MongoDB! {}'.
                    format(cfg['instance_name']))
        sys.exit(1)

    for screen_name in cfg['twitter_tracking_users']:
        try:
            tweets = get_tweets(screen_name)
            for tweet in tweets:
                if mongo_coll_tweets.find({'id': tweet._json["id"]}).count() == 0:
                    insert = mongo_coll_tweets.insert_one(tweet._json)
                    insert_id = insert.inserted_id
        except Exception as e:
                log.log_add(2, 'Timeline: {} {}'.format(e, cfg['instance_name']))
