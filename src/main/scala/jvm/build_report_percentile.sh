#!/usr/bin/env bash
unalias mv
unset -f mv
export OUT="/home/quentin/Downloads/jvm_result/result_ihop"
mkdir -p $OUT
touch ${OUT}/percentiles.csv
for i in  *-152*tar.gz ;
do tar -I pigz -xvf $i -C ${OUT} && \
head -n 1 "${OUT}/${i::-7}/simulation.log" > "${OUT}/${i::-7}/simulation-final.log" && \
tail -n +5760000 "${OUT}/${i::-7}/simulation.log" | head -n -2880000 >> "${OUT}/${i::-7}/simulation-final.log" && \
mv -f "${OUT}/${i::-7}/simulation-final.log" "${OUT}/${i::-7}/simulation.log" && \
java -jar /root/jvm_bench-assembly-0.1.jar "${OUT}/${i::-7}/simulation.log" "${OUT}/percentiles.csv" -Xmx2048m && \
rm -f "${OUT}/${i::-7}/simulation.log";
done

#/home/quentin/projects/jvm_bench/target/scala-2.12/jvm_bench-assembly-0.1.jar


unalias mv
unset -f mv
export OUT="/home/quentin/Downloads/jvm_result/ihop_0_6000qps"
mkdir -p $OUT
touch ${OUT}/percentiles.csv
for i in  *-152*tar.gz ;
do tar -I pigz -xvf $i -C ${OUT} && \
java -jar /home/quentin/projects/jvm_bench/target/scala-2.12/jvm_bench-assembly-0.1.jar "${OUT}/${i::-7}/simulation.log" "${OUT}/percentiles.csv" -Xmx2048m && \
rm -f "${OUT}/${i::-7}/simulation.log";
done


export START_PWD=$PWD
for i in `find -name  "tags"`; do
cd $i
java -cp /home/quentin/projects/HdrLogProcessing/target/HdrLogProcessing-1.0-SNAPSHOT-jar-with-dependencies.jar UnionHistogramLogs -if "(read|insert).*hgrm" -of "total.hgrm";
echo $i > histogram.csv;
java -cp /home/quentin/projects/HdrLogProcessing/target/HdrLogProcessing-1.0-SNAPSHOT-jar-with-dependencies.jar SummarizeHistogramLogs -ifp "total.hgrm" -st hgrm -e 1000 >> histogram.csv;
cat histogram.csv | sed 's/^[ \t]*//;s/[ \t]*$//' | sed '/^\s*$/d' | sed '/^#/d' | cut -d' ' -f1  > histogram_latency_only.csv
cd $START_PWD;
done
find -name histogram_latency_only.csv | xargs  paste > result.csv
cat result.csv

#for i in `ls test-tenu*152*.tar.gz`; do
#java -cp /home/quentin/projects/HdrLogProcessing/target/HdrLogProcessing-1.0-SNAPSHOT-jar-with-dependencies.jar UnionHistogramLogs -if "(read|insert).*hgrm" -of total.hgrm && java -cp /home/quentin/projects/HdrLogProcessing/target/HdrLogProcessing-1.0-SNAPSHOT-jar-with-dependencies.jar SummarizeHistogramLogs -ifp total.hgrm -st hgrm -e 120