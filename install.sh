#!/bin/bash

cp start.sh start_tp.sh
cp restart.sh restart.tp.sh

read -p "Do you want to download all Python dependencies? [yes/no]: " yn
case $yn in
    [Yy]* ) 
		pip install -r requirements.txt

		# The Tweepy API changed after 3.10.0
		#pip install git+git://github.com/tweepy/tweepy/@master
		;;
    [Nn]* ) ;;
    * ) echo "Please answer yes or no.";;
esac

read -p "Do you want to install a default cronjob for the Dashboard? [yes/no]: " yn
case $yn in
    [Yy]* ) 
		crontab -l > current_crons
		echo "*/10 * * * * bash -c \"cd $PWD && python TweetPinnaGraphs.py cfg/TweetPinnaDefault.cfg\"" >> current_crons
		crontab current_crons
		rm current_crons
		;;
    [Nn]* ) ;;
    * ) echo "Please answer yes or no.";;
esac

read -p "Do you want to install a default cronjob for retrieving timelines? [yes/no]: " yn
case $yn in
    [Yy]* ) 
		crontab -l > current_crons
		echo "*/10 * * * * bash -c \"cd $PWD && python TweetPinnaTimeline.py cfg/TweetPinnaDefault.cfg\"" >> current_crons
		crontab current_crons
		rm current_crons
		;;
    [Nn]* ) ;;
    * ) echo "Please answer yes or no.";;
esac

read -p "Do you want to install a default cronjob for retrieving replies? [yes/no]: " yn
case $yn in
    [Yy]* ) 
		crontab -l > current_crons
		echo "*/30 * * * * bash -c \"cd $PWD && python TweetPinnaReplies.py cfg/TweetPinnaDefault.cfg 250\"" >> current_crons
		crontab current_crons
		rm current_crons
		;;
    [Nn]* ) ;;
    * ) echo "Please answer yes or no.";;
esac

read -p "Do you want to install a default cronjob for automated restart? [yes/no]: " yn
case $yn in
    [Yy]* ) 
		crontab -l > current_crons
		echo "*/30 * * * * bash -c \"cd $PWD && bash restart_tp.sh\"" >> current_crons
		crontab current_crons
		rm current_crons
		;;
    [Nn]* ) ;;
    * ) echo "Please answer yes or no.";;
esac