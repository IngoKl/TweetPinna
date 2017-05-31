#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TweetPinna - Twitter Status Archiver.

TweetPinna streams Twitter statuses into a
MongoDB database based on given search terms.

Author: Ingo Kleiber <ingo@kleiber.me> (2017)
License: MIT
Version: 1.0.5
Status: Protoype

Example:
    $ python TweetPinna.py config.cfg
"""

from email.mime.text import MIMEText
from pymongo import errors
from pymongo import MongoClient
from time import sleep
import config
import datetime
import os
import signal
import smtplib
import subprocess
import sys
import thread
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
            print "Cannot connect to MongoDB!"
            end_script(self)

    def connect_mongodb(self):
        """Connecting to MongoDB."""
        try:
            self.mongo_client = MongoClient(cfg.mongo_path,
                                            connectTimeoutMS=500,
                                            serverSelectionTimeoutMS=500)

            # Check whether the connection is established or not
            self.mongo_client.server_info()

            self.mongo_db = self.mongo_client[cfg.mongo_db]
            self.mongo_coll_tweets = self.mongo_db[cfg.mongo_coll]

            self.mongo_db_connected = True
            log.log_add(2, 'Connection to MongoDB established')
        except:
            self.mongo_db_connected = False

    @staticmethod
    def media_download(insert_id):
        """Calling the media downloader."""
        if cfg.media_download_instantly == 1:
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
            insert_id = self.mongo_coll_tweets.insert(status._json)
            self.media_download(insert_id)
            self.counter += 1
        except errors.ServerSelectionTimeoutError:
            log.log_add(cfg.log_email_threshold,
                        'MongoDB ServerSelectionTimeoutError')
            self.connect_mongodb()
        except Exception as e:
            log.log_add(cfg.log_email_threshold,
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
                thread.start_new(self.clear_buffer, ())
        else:
            if cfg.tweet_buffer == 1:
                self.status_buffer.append(status)
            thread.start_new(self.connect_mongodb, ())

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


class Logger():
    """Handling all log events and keeping track of event logfiles."""

    def __init__(self, cfg):
        """Initialization."""
        self.cfg = cfg
        self.last_message = None
        self.last_twitter_error_message = None
        self.last_email_messages = {}
        if not os.path.isdir(self.cfg.log_dir):
            os.makedirs(self.cfg.log_dir)

    def log_add(self, level, message):
        """Adding an entry to the current logfile.

        :param int level: the log-level (usually 1-5) of the message
        """
        self.last_message = message
        log_date = time.strftime("%Y-%m-%d")
        log_time = time.strftime("%H:%M:%S")
        log_file = open('{}/{}-{}.log'.format(self.cfg.log_dir,
                                              self.cfg.instance_name,
                                              log_date), 'a')
        log_file.write('[{0} {1}][{2}] {3}\n'.
                       format(log_date, log_time, level, message))
        log_file.close()

        if (level >= self.cfg.log_email_threshold and
                self.cfg.log_email_enabled == 1):
            self.log_send_email(
                'Level {} Event in {}'.format(level, self.cfg.instance_name),
                message)

    def log_tail(self, n):
        """Returning the last n messages in the current logfile.

        :param int n: the number of messages to return; 0 returns all
        :return list: a list of entries
        """
        log_date = time.strftime("%Y-%m-%d")
        if os.path.isfile('{}/{}-{}.log'.format(self.cfg.log_dir,
                                                self.cfg.instance_name,
                                                log_date)):

            with open('{}/{}-{}.log'.format(self.cfg.log_dir,
                                            self.cfg.instance_name,
                                            log_date)) as log_file:
                lines = log_file.readlines()
                if n == 0:
                    return lines
                else:
                    return lines[-n:]
        else:
            return ['There is no logfile for {}'.format(log_date)]

    def log_send_email(self, subject, message):
        """Sending an email to the specified administrator.

        :param str subject: the subject of the email
        :param str message: the body of the message
        """
        try:
            time_div = datetime.datetime.now(
            ) - self.last_email_messages[message]
            time_div = divmod(time_div.days * 86400 + time_div.seconds, 60)
        except KeyError:
            time_div = (self.cfg.log_email_threshold + 1, 0)

        if (time_div[0] > self.cfg.email_spam_wait):
            try:
                self.last_email_messages[message] = datetime.datetime.now()

                msg = MIMEText(message)
                msg['Subject'] = subject
                msg['From'] = self.cfg.email_sender
                msg['To'] = self.cfg.email_receiver

                s = smtplib.SMTP(
                    self.cfg.email_server,
                    self.cfg.email_server_port)
                if self.cfg.email_starttls == 1:
                    s.starttls()
                s.login(self.cfg.email_user, self.cfg.email_password)
                s.sendmail(
                    self.cfg.email_sender, [
                        self.cfg.email_receiver], msg.as_string())
                s.quit()
                self.log_add(1, 'Email sent')
            except Exception:
                self.log_add(
                    self.cfg.log_email_threshold - 1,
                    'Could not send email')
        else:
            log.log_add(2, 'Email has not been sent to prevent spam')


def start_stream(stream):
    """Starting the Tweepy stream.

    :param stream object stream: the Tweepy stream object
    """
    log.log_add(1, 'Stream started by start_stream')

    try:
        twitter_stream.filter(track=cfg.twitter_tracking_terms, async=True)
    except Exception as e:
        log.log_add(cfg.log_email_threshold,
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
    log.log_add(1, 'Ending TweetPinna (Inst.: {})'.format(cfg.instance_name))
    print ('[{}] Ending TweetPinna (Inst.: {})'.
           format(time.strftime("%Y-%m-%d %H:%M:%S"), cfg.instance_name))
    sys.exit(1)


def end_script(stream):
    """Gracefully ending the script.

    :param stream object stream: the Tweepy stream object
    """
    stop_stream(stream)
    log.log_add(1, 'Ending TweetPinna (Inst.: {})'.format(cfg.instance_name))
    print ('[{}] Ending TweetPinna (Inst.: {})'.
           format(time.strftime("%Y-%m-%d %H:%M:%S"), cfg.instance_name))

    os._exit(0)
    sys.exit(1)


def check_config(config_file_path):
    """Checking a configuration file. Returns True if all entries are there.

    :param str config_file_path: path to the file that should be tested
    """
    reference_cfg = config.Config(file('cfg/TweetPinnaDefault.cfg'))
    test_cfg = config.Config(file(config_file_path))

    for cfg_entry in reference_cfg:
        if cfg_entry not in test_cfg:
            print ('Option {} is missing in the configuration'.
                   format(cfg_entry))
            return False
    return True


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    # Config
    try:
        if os.path.isfile(sys.argv[1]):
            if check_config(sys.argv[1]):
                cfg = config.Config(file(sys.argv[1]))
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
        cfg = config.Config(file('cfg/TweetPinnaDefault.cfg'))
        log = Logger(cfg)

    # TweetPinna
    print ('[{}] Starting TweetPinna (Inst.: {})'.
           format(time.strftime("%Y-%m-%d %H:%M:%S"), cfg.instance_name))
    log.log_add(1, 'Starting TweetPinna (Inst.: {})'.format(cfg.instance_name))

    # Initialize Tweepy
    twitter_listener = TwitterStreamListener()
    auth = tweepy.OAuthHandler(
        cfg.twitter_consumer_key,
        cfg.twitter_consumer_secret)
    auth.set_access_token(
        cfg.twitter_access_token,
        cfg.twitter_access_token_secret)
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
                    cfg.log_email_threshold,
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
                cfg.log_email_threshold,
                'Twitter Authentication failed')
            stop_stream(twitter_stream)
            keep_running = False

        # Printing current streaming status
        current_count = twitter_listener.counter
        if (current_count % cfg.report_steps ==
                0 and current_count > last_tweet_milestone):
            last_tweet_milestone = current_count
            print ('[{}] {} Tweets have been saved'.
                   format(time.strftime("%Y-%m-%d %H:%M:%S"), current_count))
            log.log_add(1, '{} Tweets have been saved'.format(current_count))
