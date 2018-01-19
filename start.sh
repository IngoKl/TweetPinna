screen -S TweetPinna -X quit
screen -S TweetPinnaTL -X quit
screen -S TweetPinnaDB -X quit
pkill -f '.*TweetPinna.*'
screen -d -m -S TweetPinna bash -c 'python TweetPinna.py cfg/TweetPinnaDefault.cfg'
screen -d -m -S TweetPinnaTL bash -c 'python TweetPinnaTrackLocation.py cfg/TweetPinnaDefault.cfg'
screen -d -m -S TweetPinnaDB bash -c 'python TweetPinnaDashboard.py cfg/TweetPinnaDefault.cfg'
