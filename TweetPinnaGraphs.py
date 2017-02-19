#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TweetPinna - Twitter Status Archiver - Dashboard.

TweetPinna streams Twitter statuses into a
MongoDB database based on given search terms.

This script generates graphs for the dashboard.
It is supposed to run as a cronjob.

e.g.
*/10 * * * * bash -c "cd /root/TweetPinna &&
python TweetPinnaGraphs.py TweetPinnaDefault.cfg"

Author: Ingo Kleiber <ingo@kleiber.me> (2017)
License: MIT
Version: 1.0.1
Status: Protoype

Example:
    $ python TweetPinnaGraphs.py config.cfg
"""

import matplotlib
matplotlib.use('Agg')

from pymongo import MongoClient
from TweetPinna import check_config
from TweetPinna import Logger
import matplotlib
import config
import matplotlib.pyplot as plt
import os
import pandas as pd
import sys
import time

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

plt.style.use('ggplot')
log = Logger(cfg)

if not os.path.isdir('dashboard/static/img/results'):
    os.makedirs('dashboard/static/img/results')

# MongoDB
mongo_client = MongoClient(cfg.mongo_path)
mongo_db = mongo_client[cfg.mongo_db]
mongo_coll_tweets = mongo_db[cfg.mongo_coll]


def tweets_by_hour(n):
    """Generating a barchart showing the last n tweets by hour.

    :param int n: the number of tweets to consider
    """
    try:
        tweet_timestamps = list(mongo_coll_tweets.find(
            {}, {'timestamp_ms': 1, '_id': 0}).sort([['_id', -1]]).limit(n))
        tweet_datetimes = pd.to_datetime(
            map(int, [d['timestamp_ms'] for d in tweet_timestamps]), unit='ms')

        df = pd.DataFrame(tweet_datetimes, columns=['date'])
        df.set_index('date', drop=False, inplace=True)
        grouped_df = df.groupby(pd.TimeGrouper(freq='1h')).count()
        grouped_df_average = grouped_df["date"].sum() / len(grouped_df)
        tweets_by_hour = grouped_df.plot(
            kind='bar', legend=False, color='#262626', rot=75)
        tweets_by_hour.set_xlabel('Date', fontsize=12)
        tweets_by_hour.set_ylabel('Nr. of Tweets', fontsize=12)
        tweets_by_hour.set_title(
            'Tweets by Hour\n(%s Tweets, avg. %s Tweets/h)\n %s' % (
                n, grouped_df_average, time.strftime("%Y-%m-%d %H:%M:%S")),
            position=(0.5, 1.05))
        tweets_by_hour.get_figure().savefig(
            'dashboard/static/img/results/tweets-by-hour.png',
            bbox_inches='tight')

        log.log_add(1, 'Graph tweets-by-hour.png created')
    except Exception as e:
        log.log_add(3,
                    'Graph tweets-by-hour.png could not be created (%s)' % e)
        return False


def tweets_by_day(n):
    """Generating a barchart showing the last n tweets by day.

    :param int n: the number of tweets to consider
    """
    try:
        tweet_timestamps = list(mongo_coll_tweets.find(
            {}, {'timestamp_ms': 1, '_id': 0}).sort([['_id', -1]]).limit(n))
        tweet_datetimes = pd.to_datetime(
            map(int, [d['timestamp_ms'] for d in tweet_timestamps]), unit='ms')

        df = pd.DataFrame(tweet_datetimes, columns=['date'])
        df.set_index('date', drop=False, inplace=True)
        grouped_df = df.groupby(pd.TimeGrouper(freq='1d')).count()
        grouped_df_average = grouped_df["date"].sum() / len(grouped_df)
        grouped_df['day'] = grouped_df.date.keys().strftime('%Y-%m-%d')

        tweets_by_day = grouped_df.plot(
            kind='bar', x=grouped_df["day"], legend=False, color='#262626',
            rot=75)
        tweets_by_day.set_xlabel('Date', fontsize=12)
        tweets_by_day.set_ylabel('Nr. of Tweets', fontsize=12)
        tweets_by_day.set_title(
            'Tweets by Day\n(%s Tweets, avg. %s Tweets/day)\n %s' % (
                n, grouped_df_average, time.strftime("%Y-%m-%d %H:%M:%S")),
            position=(0.5, 1.05))

        tweets_by_day.get_figure().savefig(
            'dashboard/static/img/results/tweets-by-day.png',
            bbox_inches='tight')

        log.log_add(1, 'Graph tweets-by-day.png created')
    except Exception as e:
        log.log_add(3,
                    'Graph tweets-by-day.png could not be created (%s)' % e)
        return False


def tweets_over_time(n):
    """Generating a chart of the overall development of the collection.

    :param int n: the number of tweets to consider
    """
    try:
        tweet_timestamps = list(mongo_coll_tweets.find(
            {}, {'timestamp_ms': 1, '_id': 0}).sort([['_id', -1]]).limit(n))
        tweet_datetimes = pd.to_datetime(
            map(int, [d['timestamp_ms'] for d in tweet_timestamps]), unit='ms')

        df = pd.DataFrame(tweet_datetimes, columns=['date'])
        df.set_index('date', drop=False, inplace=True)
        grouped_df = df.groupby(pd.TimeGrouper(freq='1d')).count()
        grouped_df_average = grouped_df["date"].sum() / len(grouped_df)

        tweets_over_time = grouped_df.cumsum().plot(
            kind='area', legend=False, color='#262626',
            stacked='False', rot=75)
        tweets_over_time.set_xlabel('Date', fontsize=12)
        tweets_over_time.set_ylabel('Nr. of Tweets', fontsize=12)
        tweets_over_time.set_title('Tweets over Time\n(avg. %s Tweets/day)' %
                                   grouped_df_average, position=(0.5, 1.05))
        tweets_over_time.get_figure().savefig(
            'dashboard/static/img/results/tweets-over-time.png',
            bbox_inches='tight')

        log.log_add(1, 'Graph tweets-over-time.png created')
    except Exception as e:
        log.log_add(3,
                    'Graph tweets-over-time.png could not be created (%s)' % e)
        return False


if __name__ == '__main__':
    # Graphs
    # Tweets by Hour
    if (os.path.isfile('dashboard/static/img/results/tweets-by-hour.png')):
        if (os.path.getmtime
            ('dashboard/static/img/results/tweets-by-hour.png') <
                (time.time() - cfg.refresh_graphs * 60)):
            tweets_by_hour(cfg.tweets_by_hour_number)
    else:
        tweets_by_hour(cfg.tweets_by_hour_number)

    # Tweets by Day
    if (os.path.isfile('dashboard/static/img/results/tweets-by-day.png')):
        if (os.path.getmtime
            ('dashboard/static/img/results/tweets-by-day.png') <
                (time.time() - cfg.refresh_graphs * 60)):
            tweets_by_day(cfg.tweets_by_day_number)
    else:
        tweets_by_day(cfg.tweets_by_day_number)

    # Tweets over Time
    if (os.path.isfile('dashboard/static/img/results/tweets-over-time.png')):
        if (os.path.getmtime
            ('dashboard/static/img/results/tweets-over-time.png') <
                (time.time() - cfg.refresh_graphs * 60)):
            tweets_over_time(0)
    else:
        tweets_over_time(0)
