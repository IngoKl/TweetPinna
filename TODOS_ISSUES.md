# Todos and Issues

## New Features

- [ ] Video downloader
- [ ] add full support for 'extended_tweet' objects
- [ ] /tweet/id should be able to display the full tweet
- [ ] AWS S3 compatibility for images
- [ ] Fetching a list of friends/relationships and retrieve their tweets (with a given level of depth)
- [ ] Implement OSoMe's Botometer (see [botometer-python](https://github.com/IUNetSci/botometer-python))
- [ ] Implement basic testing
- [ ] Implement i18n
- [ ] Implement instant download functionality within the timeline module
- [ ] Provide better installation/running routines

## Refactoring

- [ ] Unify the individual modules and/or write a wrapper to access them all
- [ ] Switch over to f-Strings
- [ ] Separate config and tweepy initialization into a helper function for additional modularization
- [ ] Replace custom logger with Python's default logging
- [ ] Restructuring the project in a more (modern) Pythonic way

## Updates

- [ ] Update TweetPinna to new Tweepy API
- [ ] Update Sphinx Documentation

## Bugs and Issues

- [ ] get_hashtags() cosumes to much memory and cpu
- [ ] Too many hits on tweepy result in an `IncompleteRead exception`
- [ ] The "Tweets over Time" graph(s) doesn't show the actual number of tweets due to scaling effects
- [ ] Add calling module/file to the log
- [ ] Before adding a tweet to the DB we should check whether it already exists
- [ ] Dashboard should not start without MongoDB connection -> implement global db checks
- [ ] Fix xlabels in the dashboard
