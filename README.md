# TweetPinna
![Logo](https://cloud.githubusercontent.com/assets/16179317/22861826/93aa52be-f122-11e6-891d-5ce9b452ef01.png?raw=true)

TweetPinna is a tweet archiver written in Python (2.7x) that saves tweets and metadata to MongoDB. It is designed for long-running archival projects (e.g. for academic use) and is based on [Tweepy](http://www.tweepy.org/). As of now, TweetPinna is able to archive tweets based on search terms and/or hashtags.

## Features
* Automatic image download (profile pictures, images in tweets)
* Flask-based web dashboard providing information and some basic statistics about the current archival project
* Email alerts in case of problems with the archiver
* Ability to manage multiple archival projects using configuration files

## Installation and Usage
1. Install and configure MongoDB (currently TweetPinna does not support authentication)
2. Clone the repository into a dictionary
3. Either edit `cfg/TweetPinnaDefault.cfg` or create your own configuration file (see `docs/annotated-default-config.txt`).
4. Install all Python dependencies by running `pip install -r requirements.txt`
5. Install a cronjob that regularly runs `TweetPinnaGraphs.py`
6. Run both `TweetPinna.py` and `TweetPinnaDashboard.py` (either as a service or in a screen session)

`install.sh` is an alternative to steps 4 and 5 and will use the default configuration. 
`start.sh`will run both the archiver and the dashboard in a screen session.

All TweetPinna scripts require a valid configuration to run. The configuration is always passed as the first argument, e.g. `python TweetPinna.py cfg/TweetPinnaDefault.cfg`.

### Running TweetPinna in Production
If you plan to run TweetPinna in production, it is advisable to implement the following:

- Use virtualenv
- Use a dedicated webserver/WSGI
- If you plan on harvesting large amounts of data use `memcached` instead of `SimpleCache` and precache hashtags from time to time

### Media Download
Keep in mind that using the media/image downloader will generate a lot of traffic. Based on a sample of 600 tweets, an average tweet amounts to roughly 6 MB of image data.

If you decide to not download images immediately (`media_download_instantly : 0`) you can manually download all images by running `python TweetPinnaImageDownloader.py config.cfg`.

## Todo
[![quantifiedcode Code Issues](https://www.quantifiedcode.com/api/v1/project/403e7e6703344916a14ea9d7f64cc020/badge.svg)](https://www.quantifiedcode.com/app/project/403e7e6703344916a14ea9d7f64cc020)

- [ ] Video downloader
- [ ] MongoDB auth compatibility
- [ ] AWS S3 compatibility for images
- [ ] Fix xlabels in the dashboard
- [ ] Provide better installation/running routines
- [ ] Restructuring the project / "make it more pythonic"
- [ ] Too many hits on tweepy result in an `IncompleteRead exception`
- [ ] Replace print/own logger with logging
- [ ] Add calling module/file to the log
- [ ] Testing
- [ ] get_hashtags() cosumes to much memory and cpu
- [X] Optimize caching / move caching away from views
- [X] Basic statistics (e.g. Token count; Nr. of tweets)

## Special Behaviour
If the database (MongoDB) becomes unavailable for any reason, TweetPinna continues to collect tweets. Once the connection is reestablished, the tweet-buffer is dumped into the database. While this behaviour can be memory heavy, it ensures that no (less) tweets are lost. If you want to disable this function set `tweet_buffer : 0`.

## Dashboard Screenshot
![Screenshot](https://cloud.githubusercontent.com/assets/16179317/22861790/cbc597f4-f121-11e6-880f-177f50dc6ba2.png?raw=true)
