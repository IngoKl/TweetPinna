#!/bin/bash
read -p "Do you want to download all Python dependencies? [yes/no]: " yn
case $yn in
    [Yy]* ) 
		pip install -r requirements.txt
		pip install git+git://github.com/tweepy/tweepy/@master
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

read -p "Do you want to install a default cronjob for automated restart? [yes/no]: " yn
case $yn in
    [Yy]* ) 
		crontab -l > current_crons
		echo "*/30 * * * * bash -c \"cd $PWD && bash restart.sh\"" >> current_crons
		crontab current_crons
		rm current_crons
		;;
    [Nn]* ) ;;
    * ) echo "Please answer yes or no.";;
esac