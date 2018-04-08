#!/usr/bin/env bash
unalias mv
unset -f mv
export OUT="/root/results"
mkdir -p $OUT
touch ${OUT}/percentiles.csv
for i in  *-152* ;
do tar -I pigz -xvf $i -C ${OUT} && \
head -n 1 "${OUT}/${i::-7}/simulation.log" > "${OUT}/${i::-7}/simulation-final.log" && \
tail -n +5760000 "${OUT}/${i::-7}/simulation.log" | head -n -2880000 >> "${OUT}/${i::-7}/simulation-final.log" && \
mv -f "${OUT}/${i::-7}/simulation-final.log" "${OUT}/${i::-7}/simulation.log" && \
java -jar /root/jvm_bench-assembly-0.1.jar "${OUT}/${i::-7}/simulation.log" "${OUT}/percentiles.csv" -Xmx2048m && \
rm -f "/root/results/${i::-7}/simulation.log";
done
