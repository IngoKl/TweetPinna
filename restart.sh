#!/bin/bash
old=$(< lastcount.txt)
new_count=$(curl 127.0.0.1:8080/ajax/get/docs-in-collection 2>&1| awk '/[0-9]{7,10}/' | sed 's/ //g')

if [ "$old" == "" ] && [ "$new_count" == "" ]
 then
  old=0
  new_count=0
fi

echo $new_count > lastcount.txt
echo "Old Count: $old"
echo "New Count: $new_count"

delta=$(expr $new_count - $old)

if ((delta < 100))
 then
  echo "There seem to be no new tweets..."
  . start.sh
fi

# Restart MongoDB; Requires sudo rights: tweetpinna ALL=NOPASSWD:/usr/sbin/service mongodb *
service=mongodb

if sudo service mongodb status | grep -q 'failed'
 then
  sudo service mongodb start
 else
  echo "$service is running (method primary)"
fi

# Alternative method based on ps
#if (( $(ps -ef | grep -v grep | grep $service | wc -l) > 0 ))
# then
#  echo "$service is running (method alt)"
# else
#  sudo service mongodb start
#fi
