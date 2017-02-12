screen -S TweetPinna -X quit
screen -S TweetPinnaDB -X quit
screen -d -m -S TweetPinna bash -c 'python TweetPinna.py cfg/TweetPinnaDefault.cfg'
screen -d -m -S TweetPinnaDB bash -c 'python TweetPinnaDashboard.py cfg/TweetPinnaDefault.cfg'
