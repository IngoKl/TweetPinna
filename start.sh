screen -S TweetPinna -X quit
screen -S TweetPinnaDB -X quit
pkill -f '.*TweetPinna.*'
screen -d -m -S TweetPinna bash -c 'python TweetPinna.py cfg/BrooklynTest.cfg'
screen -d -m -S TweetPinnaDB bash -c 'python TweetPinnaDashboard.py cfg/BrooklynTest.cfg'
