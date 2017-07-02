#!/bin/bash
old=$(< lastcount.txt)
new_count=$(curl 127.0.0.1:8080/ajax/get/docs-in-collection 2>&1| awk '/[0-9]{7,10}/' | sed 's/ //g')
echo $new_count > lastcount.txt
echo "Old Count: $old"
echo "New Count: $new_count"

delta=$(expr $new_count - $old)

if ((delta < 100))
 then
  echo "There seem to be no new tweets..."
  . start.sh
fi
