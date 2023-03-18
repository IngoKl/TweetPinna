# TweetPinna

![Logo](https://cloud.githubusercontent.com/assets/16179317/22861826/93aa52be-f122-11e6-891d-5ce9b452ef01.png?raw=true)

Given recent changes at Twitter, the release of *Twitter API v2*, and the fact that *TweetPinna* hasn't been actively maintained for a while, I no longer recommend to use it.

TweetPinna is a tweet archiver that saves tweets and metadata to MongoDB. It is designed for long-running archival projects (e.g. for academic use) and is based on [Tweepy](http://www.tweepy.org/). As of now, TweetPinna is able to archive tweets based on search terms and/or hashtags as well as based on location. There is rudimentary support for archiving specific user's timelines.

> TweetPinna, as of 1.0.9, supports Python 3. However, the original TweetPinna, development started in early 2014, was in written in (legacy) Python (2.7x). I'm in the process of hopefully refactoring (and actually moving away from legacy Python) the whole codebase. The project, as it stands right now, works fine, but is fairly messy. There will be (very infrequent) marginal updates to this legacy version.

## Features

- Automatic image download (profile pictures, images in tweets)
- Flask-based web dashboard providing information and some basic statistics about the current archival project
- Email alerts in case of problems with the archiver
- Ability to manage multiple archival projects using configuration files
- Preview of random tweets
- Tracking user's timelines
- Tracking basd on locations / boundary boxes
- Archiving replies to tweets (limited)

## Installation and Usage

1. Install and configure MongoDB (currently TweetPinna does not support authentication)
2. Clone the repository into a dictionary
3. Either edit `cfg/TweetPinnaDefault.cfg` or create your own configuration file (see `docs/annotated-default-config.txt`). Remember to change the password for the dashboard!
4. Install all Python dependencies by running `pip install -r requirements.txt`
5. Install a cronjob that regularly runs `TweetPinnaGraphs.py`
6. If you want to regularly fetch timelines, install a cronjob that regularly runs `TweetPinnaTimeline.py`
7. Run both `TweetPinna.py` and `TweetPinnaDashboard.py` (either as a service or in a screen session). If you also want to track based on location, you have to run `TweetPinnaTrackLocation.py` in a similar fashion.

`install.sh` is an alternative to steps 4 and 5 and will use the default configuration. The installer will assume `python` and `pip` to be your preferred commands. The script will also create two new files `start_tp.sh` and `restart_tp.sh`. These are your files to modify so that you can easily upgrade using Git without loosing your changes. If you are working with a dedicated Python environment (strongly advised), you will have to change `start_tp.sh` and the cronjobs to use your environment.

For example:

`*/10 * * * * bash -c "cd /home/tweetpinna/TweetPinna && /home/tweetpinna/tp/bin/python TweetPinnaGraphs.py cfg/heiurban.cfg"`

`start.sh`will run both the archiver and the dashboard in a screen session.

All TweetPinna scripts require a valid configuration to run. The configuration is always passed as the first argument, e.g. `python TweetPinna.py cfg/TweetPinnaDefault.cfg`.

### Running TweetPinna in Production

If you plan to run TweetPinna in production, it is advisable to implement the following:

- Use virtualenv (see above)
- Use a dedicated webserver/WSGI
- If you plan on harvesting large amounts of data use `memcached` instead of `SimpleCache` and precache hashtags from time to time

### Media Download

Keep in mind that using the media/image downloader will generate a lot of traffic. Based on a sample of 600 tweets, an average tweet amounts to roughly 6 MB of image data.

If you decide to not download images immediately (`media_download_instantly : 0`) you can manually download all images by running `python TweetPinnaImageDownloader.py config.cfg`.

### Archiving Replies

Since Twitter (at least with free API access) does not allow you to track/search for replies directly, TweetPinna tries to archive these via the user's timelines. Tracking replies, due to these restrictions, is time-sensitive. Thus, you should set up a job running `TweetPinnaReplies.py config.cfg ` with a limit that resembles how many tweets have been tracked per job execution. Hence, if you are tracking approximately 500 tweets per hour, you should run this at least hourly with a limit of 500.

Also, keep in mind that this method is far from perfect and especially does not account for the fact that replies can be added later. Therefore, in the example above, you would only track replies which were made fairly immediately.

### restart.sh

If persistent logging/tracking is paramount, `restart.sh` can be called from time to time (cronjob) in order to restart both TweetPinna and the MongoDB service in case they are down for some reason. While this is certainly not the 'cleanest' solution, it works well in practice.

## Special Behaviour

If the database (MongoDB) becomes unavailable for any reason, TweetPinna continues to collect tweets. Once the connection is reestablished, the tweet-buffer is dumped into the database. While this behaviour can be memory heavy, it ensures that no (less) tweets are lost. If you want to disable this function set `tweet_buffer : 0`.

If there is no dashboard username set, the dashboard will be unprotected.

## Dashboard Screenshot

![Dashboard Screenshot, Version 1.0.5](https://user-images.githubusercontent.com/16179317/36260628-49f5e14e-1262-11e8-84ab-758fa8cd753e.PNG)
