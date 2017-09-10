#!/bin/bash
old=$(< lastcount.txt)
new_count=$(curl 127.0.0.1:8080/ajax/get/docs-in-collection 2>&1| awk '/[0-9]{7,10}/' | sed 's/ //g')
echo $new_count > lastcount.txt
echo "Old Count: $old"
echo "New Count: $new_count"

delta=$(expr $new_count - $old)

if ((delta < 100))
 then
  echo "There seem to be no new tweets; restarting!"
  . start.sh
fi

# Restart MongoDB; Requires sudo rights: tweetpinna ALL=NOPASSWD:/usr/sbin/service mongodb *
service=mongodb
if (( $(ps -ef | grep -v grep | grep $service | wc -l) > 0 ))
 then
  echo "$service is running; no restart required!"
 else
  echo "$service has stopped; restarting!"
  sudo service mongodb start
fi
