#!/usr/bin/env bash
sleep 120
unalias mv
unset -f mv
for i in  *20GB* ;
do tar -I pigz -xvf $i -C /root/results && \
head -n 1 "/root/results/${i::-7}/simulation.log" > "/root/results/${i::-7}/simulation-final.log" && \
tail -n +5760000 "/root/results/${i::-7}/simulation.log" | head -n -2880000 >> "/root/results/${i::-7}/simulation-final.log" && \
mv -f "/root/results/${i::-7}/simulation-final.log" "/root/results/${i::-7}/simulation.log" && \
/root/gatling-charts-highcharts-bundle-2.2.2/bin/gatling.sh -ro "/root/results/${i::-7}" && \
rm -f "/root/results/${i::-7}/simulation.log";
done
