#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TweetPinna - Twitter Status Archiver - Dashboard.

TweetPinna streams Twitter statuses into a
MongoDB database based on given search terms.

This script provides a simple dashboard written in Flask.

Author: Ingo Kleiber <ingo@kleiber.me> (2017)
License: MIT
Version: 1.0.1
Status: Protoype

Example:
    $ python TweetPinnaDashboard.py config.cfg
"""

from bson.son import SON
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from pymongo import MongoClient
from TweetPinna import check_config
from TweetPinna import Logger
from werkzeug.contrib.cache import SimpleCache
import config
import os
import sys

try:
    if os.path.isfile(sys.argv[1]):
        if check_config(sys.argv[1]):
            cfg = config.Config(file(sys.argv[1]))
            log = Logger(cfg)
        else:
            print ('Configuration appears to be faulty')
            sys.exit(1)
    else:
        print ('Configuration file %s could not be found' % sys.argv[1])
        sys.exit(1)
except IndexError:
    print ('Using default configuration')
    cfg = config.Config(file('cfg/TweetPinnaDefault.cfg'))
    log = Logger(cfg)

cache = SimpleCache()

# MongoDB
mongo_client = MongoClient(cfg.mongo_path)
mongo_db = mongo_client[cfg.mongo_db]
mongo_coll_tweets = mongo_db[cfg.mongo_coll]


def get_hashtags():
    """Get a list of hashtags from highest to lowest frequency.

    :return list: all hashtags and their frequency
    """
    pipeline = [
        {"$unwind": "$entities"},
        {"$unwind": "$entities.hashtags"},
        {"$unwind": "$entities.hashtags.text"},
        {"$group": {"_id": "$entities.hashtags.text", "count":
                    {"$sum": 1}}},
        {"$sort": SON([("count", -1), ("_id", -1)])}]

    hashtags = list(mongo_coll_tweets.aggregate(pipeline))
    hashtags_list = []
    for hashtag in hashtags:
        hashtags_list.append((hashtag.values()[1], hashtag.values()[0]))

    return hashtags_list


def get_number_hashtags():
    """Getting the number of unique hashtags in the collection."""
    return len(get_hashtags())


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


# Flask
app = Flask(
    __name__,
    template_folder='dashboard/templates',
    static_folder='dashboard/static')


@app.route('/')
def index():
    """Flask Welcome Route."""
    return render_template('welcome.html', instance_name=cfg.instance_name,
                           instance_ver=get_version(),
                           docs_in_collection=mongo_coll_tweets.count(),
                           last_entry_time=get_last_entry_time(),
                           tracking_terms=cfg.twitter_tracking_terms)


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


@app.route('/ajax/get/hashtags')
def ajax_get_hashtags():
    """Flask Ajax Get Hashtag Route."""
    f = request.args.get('f', 0, type=int)
    t = request.args.get('t', 0, type=int)

    hashtags_list = cache.get('hashtags-list')
    if hashtags_list is None:
        hashtags_list = get_hashtags()
        cache.set('hashtags-list', hashtags_list,
                  cfg.flask_cache_timeout * 60)

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
    hashtags_number = cache.get('hashtags-number')
    if hashtags_number is None:
        hashtags_number = get_number_hashtags()
        cache.set('hashtags-number', hashtags_number,
                  cfg.flask_cache_timeout * 60)

    return str(hashtags_number)


@app.route('/ajax/get/storage-size')
def ajax_get_storage_size():
    """Flask Ajax Get Storage Size Route."""
    return str(get_folder_size(cfg.media_storage))


@app.route('/ajax/get/docs-in-collection')
def ajax_get_docs_in_collection():
    """Flask Ajax Get Docs in Collection Route."""
    return jsonify(get_last_entry_time(), mongo_coll_tweets.count())


if __name__ == "__main__":
    # In production, the dashboard should be used with an actual webserver
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.run(host=cfg.dashboard_host, port=cfg.dashboard_port, threaded=True)
