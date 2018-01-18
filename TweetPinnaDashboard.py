#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TweetPinna - Twitter Status Archiver - Dashboard.

TweetPinna streams Twitter statuses into a
MongoDB database based on given search terms.
It is also capable of retrieving a user's timeline.

This script provides a simple dashboard written in Flask.

Author: Ingo Kleiber <ingo@kleiber.me> (2017)
License: MIT
Version: 1.0.7
Status: Protoype

Example:
    $ python TweetPinnaDashboard.py config.cfg
"""

from bson.son import SON
from bson.json_util import dumps
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from pymongo import MongoClient
from TweetPinna import check_config
from TweetPinna import Logger
from TweetPinnaImageDownloader import download_media_file
from werkzeug.contrib.cache import SimpleCache
import config
import os
import sys
import re

try:
    if os.path.isfile(sys.argv[1]):
        if check_config(sys.argv[1]):
            cfg = config.Config(file(sys.argv[1]))
            log = Logger(cfg)
        else:
            print ('Configuration appears to be faulty')
            sys.exit(1)
    else:
        print ('Configuration file {} could not be found'.format(sys.argv[1]))
        sys.exit(1)
except IndexError:
    print ('Using default configuration')
    cfg = config.Config(file('cfg/TweetPinnaDefault.cfg'))
    log = Logger(cfg)

cache = SimpleCache()

# MongoDB
mongo_client = MongoClient(cfg.mongo_path, connectTimeoutMS=500,
                           serverSelectionTimeoutMS=500)
mongo_db = mongo_client[cfg.mongo_db]
mongo_coll_tweets = mongo_db[cfg.mongo_coll]


def html_ann_tweet(tweets):
    """Adding html to tweets in order to display them on the dashboard."""
    for tweet in tweets:
		
        if 'text' not in tweet.keys():
            tweet['text'] = tweet['full_text']
		
        # Hashtags
        tweet['text'] = re.sub(r'\B#\w\w+',
                               '<span class="hashtag">\g<0></span>',
                               tweet['text'])

        # Usernames
        tweet['text'] = re.sub(r'(?<=^|(?<=[^a-zA-Z0-9-_\.]))@'
                               r'([A-Za-z]+[A-Za-z0-9]+)',
                               '<span class="user">\g<0></span>',
                               tweet['text'])

        # Links
        tweet['text'] = re.sub(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|'
            r'(?:%[0-9a-fA-F][0-9a-fA-F]))+', '<a href="\g<0>">\g<0></a>',
            tweet['text'])

    return tweets


def get_hashtags():
    """Get a list of hashtags from highest to lowest frequency.

    :return list: all hashtags and their frequency
    """
    hashtags_list = cache.get('hashtags-list')
    if hashtags_list is None:
        pipeline = [
            {"$unwind": "$entities"},
            {"$unwind": "$entities.hashtags"},
            {"$unwind": "$entities.hashtags.text"},
            {"$group": {"_id": "$entities.hashtags.text", "count":
                        {"$sum": 1}}},
            {"$sort": SON([("count", -1), ("_id", -1)])}]

        hashtags = mongo_coll_tweets.aggregate(pipeline)
        hashtags_list = []
        for hashtag in hashtags:
            hashtags_list.append((hashtag.values()[1], hashtag.values()[0]))

        cache.set('hashtags-list', hashtags_list,
                  cfg.flask_cache_timeout * 60)

    return hashtags_list


def get_number_hashtags():
    """Getting the number of unique hashtags in the collection."""
    hashtags_number = cache.get('hashtags-number')
    if hashtags_number is None:
        hashtags_number = len(get_hashtags())
        cache.set('hashtags-number', hashtags_number,
                  cfg.flask_cache_timeout * 60)

    return hashtags_number


def get_folder_size(start_path):
    """Getting the size of a folder and all subfolders.

    :param str start_path: the folder path
    :return int: folder size in MB
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)

    return total_size / 1000000


def get_version():
    """Getting the TweetPinna version."""
    try:
        with open('version', 'r') as version_file:
            return str(version_file.readline())
    except:
        return False


def get_last_entry_time():
    """Getting the time of the last entry in the collection."""
    try:
        last_entry_time = list(mongo_coll_tweets.find().sort(
            [("_id", -1)]).limit(1))[0]["_id"].generation_time
    except:
        last_entry_time = 0

    return last_entry_time


def get_random_tweets(n):
    """Getting n random tweets from the collection."""
    sample = list(mongo_coll_tweets.aggregate([{'$sample': {'size': n}}]))
    return sample


def get_token_count():
    """Generate the token count based on all documents.

    A simple space tokenizer is utilized.
    The token count is cached for 60 minutes.
    """
    tokens = cache.get('tokens-number')

    if tokens is None:
        tokens = 0
        tweets = mongo_coll_tweets.find({}, {'text': 1})
        for tweet in tweets:
            if 'full_text' in tweet.keys():
                tokens += len(tweet['full_text'].split(' '))
            else:
                tokens += len(tweet['text'].split(' '))

    cache.set('tokens-number', tokens, 360)

    return tokens


def generate_statistics():
    """Generate basic statistics and return a dictionary."""
    statistics = cache.get('statistics')
    if statistics is None:
        statistics = {}
        statistics['nr_hashtags'] = ('Number of Hashtags',
                                     get_number_hashtags())
        statistics['nr_tokens'] = ('Number of Tokens', get_token_count())
        statistics['media_storage_size'] = ('Storage Folder Size (MB)',
                                            str(get_folder_size(
                                                cfg.media_storage)))

        cache.set('statistics', statistics,
                  cfg.flask_cache_timeout * 60)

    return statistics


def get_user(screen_name):
    """Get information about a tracked user."""
    # Get all tweets, sorted from newest to oldest
    user_tweets = list(mongo_coll_tweets.find({'user.screen_name':
                       screen_name[1:]}).sort([('id', -1)]))
    user = {}

    try:
        download_media_file('user-profile-img',
                            user_tweets[0]['user']['profile_image_url_https'],
                            'user-{}-current.jpg'.format(screen_name[1:]),
                            'jpg',
                            'dashboard/static/img/users')
        user["profile_picture"] = True
    except:
        # The user probably does not have any profile picture
        user["profile_picture"] = False

    user["screen_name"] = screen_name[1:]
    user["number_of_tweets"] = len(user_tweets)

    if user["number_of_tweets"] > 0:
        try:
            user["last_tweet"] = user_tweets[0]['text']
        except KeyError:
            user["last_tweet"] = user_tweets[0]['full_text']
        user["last_tweet_date"] = user_tweets[0]['created_at']
    else:
        user["last_tweet"] = 'N/A'
        user["last_tweet_date"] = 'N/A'

    return(user)


# Flask
app = Flask(
    __name__,
    template_folder='dashboard/templates',
    static_folder='dashboard/static')


@app.errorhandler(500)
def internal_error_handler(error):
    """Handling HTTP 500 errors."""
    return render_template('error.500.html')


@app.errorhandler(404)
def not_found_error_handler(error):
    """Handling HTTP 404 errors."""
    return render_template('error.404.html')


@app.route('/')
def index():
    """Flask Welcome Route."""
    return render_template('welcome.html', instance_name=cfg.instance_name,
                           instance_ver=get_version(),
                           docs_in_collection=mongo_coll_tweets.count(),
                           last_entry_time=get_last_entry_time(),
                           tracking_terms=cfg.twitter_tracking_terms,
                           random_tweets=html_ann_tweet(get_random_tweets(5)))


@app.route('/logfile')
def logfile():
    """Flask Logfile Route."""
    return render_template(
        'logfile.html', instance_name=cfg.instance_name,
        instance_ver=get_version(),
        logfile=log.log_tail(10))


@app.route('/hashtags')
def hashtags():
    """Flask Hashtag Route."""
    return render_template(
        'hashtags.html', instance_name=cfg.instance_name,
        instance_ver=get_version())


@app.route('/media')
def media():
    """Flask Media Route."""
    return render_template(
        'media.html', instance_name=cfg.instance_name,
        instance_ver=get_version())


@app.route('/statistics')
def statistics():
    """Flask Statistics Route."""
    return render_template(
        'statistics.html', instance_name=cfg.instance_name,
        instance_ver=get_version())


@app.route('/timelines')
def timelines():
    """Flask Timelines Route."""
    tracked_users = []
    for user in cfg.twitter_tracking_users:
        tracked_users.append(get_user(user))

    return render_template(
        'timelines.html', instance_name=cfg.instance_name,
        instance_ver=get_version(),
        no_tracked_users=len(cfg.twitter_tracking_users),
        users=tracked_users)


@app.route('/ajax/get/hashtags')
def ajax_get_hashtags():
    """Flask Ajax Get Hashtag Route."""
    f = request.args.get('f', 0, type=int)
    t = request.args.get('t', 0, type=int)

    hashtags_list = get_hashtags()

    try:
        if t == 0:
            return jsonify(dict(hashtags_list[f:]))
        elif t > len(hashtags_list):
            return jsonify(dict(hashtags_list[f:]))
        else:
            return jsonify(dict(hashtags_list[f:t]))
    except:
        return False


@app.route('/ajax/get/hashtags-number')
def ajax_get_number_hashtags():
    """Flask Ajax Get Hashtag Number Route."""
    return str(get_number_hashtags())


@app.route('/ajax/get/statistics')
def ajax_get_statistics():
    """Flask Ajax Get Statistics Route."""
    return jsonify(generate_statistics())


@app.route('/ajax/get/storage-size')
def ajax_get_storage_size():
    """Flask Ajax Get Storage Size Route."""
    return str(get_folder_size(cfg.media_storage))


@app.route('/ajax/get/docs-in-collection')
def ajax_get_docs_in_collection():
    """Flask Ajax Get Docs in Collection Route."""
    return jsonify(get_last_entry_time(), mongo_coll_tweets.count())


@app.route('/ajax/get/random_tweets/<n>')
def ajax_get_random_tweets(n):
    """Flask Ajax Get Random Tweets Route."""
    return dumps(get_random_tweets(int(n)))


if __name__ == "__main__":
    # In production, the dashboard should be used with an actual webserver
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.run(host=cfg.dashboard_host, port=cfg.dashboard_port, threaded=True)
