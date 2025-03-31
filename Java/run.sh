#!/bin/bash
cd `dirname $0`
PATH=$PATH:/usr/local/bin
# 休眠随机时间0-99s
#sleep $[$RANDOM%100]
java -jar mvn-artifact-wrapper-0.2.3.jar
echo "Java App run finished！"
