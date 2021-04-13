#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TweetPinna - Twitter Status Archiver - Replies.

TweetPinna streams Twitter statuses into a
MongoDB database based on given search terms.
It is also capable of retrieving a user's timeline.

This script tries to retrieve replies to tweets.

Author: Ingo Kleiber <ingo@kleiber.me> (2019)
License: MIT
Version: 1.1.1
Status: Protoype

Example:
    $ python TweetPinnaReplies.py config.cfg <limit_tweets>
"""

from pymongo import MongoClient
from TweetPinna import check_config
from TweetPinna import Logger
import tweepy
import config
import os
import sys
import time


def get_replies(user_name, tweet_id):
    replies = []

    """Get the replies for a tweet via the user timeline/time method. We are retrieving, as far as possible, 
    all tweets 'to' that user and pick the ones which are replies."""
    for status in tweepy.Cursor(api.search, q=f'to:{user_name}', since_id=tweet_id, tweet_mode='extended').items():
        if not hasattr(status, 'in_reply_to_status_id_str'):
            continue
        if status.in_reply_to_status_id == tweet_id:
            replies.append(status)

    return replies


def store_tweets(status_objects):
    insert_ids = []

    for tweet in status_objects:
        try:
            if mongo_coll_tweets.find({'id': tweet._json["id"]}).count() == 0:
                insert = mongo_coll_tweets.insert_one(tweet._json)
                insert_ids.append(insert.inserted_id)
        except Exception as e:
            log.log_add(3, f'Could not store tweet {e}')

    return insert_ids


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
    log.log_add(1, 'Replies {}'.format(cfg['instance_name']))

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
        log.log_add(3, 'Replies: Cannot connect to Twitter API {}'.
                    format(cfg['instance_name']))
        sys.exit(1)

    # mongoDB
    try:
        mongo_client = MongoClient(cfg['mongo_path'], connectTimeoutMS=500,
                                   serverSelectionTimeoutMS=500)
        mongo_db = mongo_client[cfg['mongo_db']]
        mongo_coll_tweets = mongo_db[cfg['mongo_coll']]
    except:
        log.log_add(3, 'Replies: Cannot connect to MongoDB! {}'.
                    format(cfg['instance_name']))
        sys.exit(1)

    # Looping over collected tweets
    if sys.argv[1]:
        lim = int(sys.argv[2])
    else:
        lim = 100

    tweets = mongo_coll_tweets.find().sort([('_id', -1)]).limit(lim)
    for tweet in tweets:
        try:
            # Throttle 10
            time.sleep(10)

            replies = get_replies(tweet['user']['screen_name'], tweet['id'])
            if len(replies) > 0:
                stored = store_tweets(replies)
                log.log_add(1, f'Archieved {len(stored)} replies to {tweet["id"]}')
        except Exception as e:
            log.log_add(3, f'Could not retrieve replies for {tweet["id"]} because {e}')
