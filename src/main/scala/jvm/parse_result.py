#!/usr/bin/env python
import sys
import subprocess
import time
from cassandra.cluster import Cluster
from optparse import OptionParser
import csv
import json
import os
import re
import traceback
import math

#sudo apt-get install python-matplotlib
#https://github.com/juliojsb/sarviewer
#apt-get install sysstat gnuplot
#pip install cassandra-driver

#git reset --hard origin/master && git pull
#python3.4 ./test_jvm.py --gatlingFolder="/root/gatling-charts-highcharts-bundle-2.2.2" --dseFolder="/root/dse-5.1.7" --dseHost="37.187.28.208" --ssh="root@37.187.28.208" --testDurationSec="20" --writePerSecPerQuery="1000" --readPerSecPerQuery="1000"
#python3.4 ./test_jvm.py --gatlingFolder="/root/gatling-charts-highcharts-bundle-2.2.2" --dseFolder="/root/dse-5.1.7" --dseHost="37.187.28.208" --ssh="" --testDurationSec="20" --writePerSecPerQuery="1000" --readPerSecPerQuery="1000"
#git reset --hard origin/master && git pull && python3.4 ./test_jvm.py --gatlingFolder="/root/gatling-charts-highcharts-bundle-2.2.2" --dseFolder="/root/dse-5.1.7" --dseHost="10.10.10.3" --ssh="root@195.154.78.138" --testDurationSec="20" --writePerSecPerQuery="10000" --readPerSecPerQuery="10000" --sarViewFolder="/root/jvm_benchmark/src/main/scala/jvm/sarviewer-master"


parser = OptionParser()
parser.add_option("-f", "--folder", default="/home/quentin/Downloads/jvm_bench/results")
parser.add_option("-s", "--sarFolder", default="/home/quentin/Downloads/jvm_bench/sar")
parser.add_option("-o", "--output", default="/home/quentin/Downloads/jvm_bench/results/result.csv")

(options, args) = parser.parse_args()

# with open(options.output, 'wb') as csvfile:
#     result_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

def percentile(N, percent, key=lambda x:x):
    """
    Find the percentile of a list of values.

    @parameter N - is a list of values. Note N MUST BE already sorted.
    @parameter percent - a float value from 0.0 to 1.0.
    @parameter key - optional key function to compute value from each element of N.

    @return - the percentile of the values
    """
    if not N:
        return None
    k = (len(N)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0+d1

header =['allocationRate_MBs', 'heapSize_GB', 'maxPauseTarget', 'maxResponseTime', 'meanResponseTime_ms', 'standardDeviation_ms', '95pt', '98pt', '99pt', '99.9pt', '99.99pt',
       'gcTotalPause', 'gcMeanPause', 'gcMaxPause', 'gc50', 'gc90', 'gc95', 'gc99', 'gc99.9', 'gc99.99']
rows = [header]
onlyfiles = [f for f in os.listdir(options.folder) if not os.path.isfile(os.path.join(options.folder, f))]
for f in onlyfiles:
    #test-heap-size-24GB-400ms-1522505517170
    m = re.search("test-heap-size-(\d+)GB-(\d+)ms.*", f)
    heap = m.groups()[0]
    targetPause = m.groups()[1]
    #print(f)
    psum, pmean, pmax, p95, p98, p99, p999, p9999 = ('',) * 8

    ##########################
    #########GC STATS########
    pauses = []
    try:
        for line in [line.rstrip('\n') for line in open(os.path.join(options.sarFolder, "test-heap-size-" + heap +"GB-" + targetPause + "ms-sar", 'gc.log.0.current'))]:
            m = re.search(".*Total time for which application threads were stopped: (\d+),(\d+) seconds.*", line)
            if m:
                pause = float(m.groups()[0]+"."+m.groups()[1])
                pauses.append(pause)
        if len(pauses)>0:
            pauses.sort()
            # print ("PAUSE=")
            # print (pauses)
            psum = sum(pauses)
            pmean = psum / float(len(pauses))
            pmax = max(pauses)
            p50 = percentile(pauses, 0.5)
            p90 = percentile(pauses, 0.90)
            p95 = percentile(pauses, 0.95)
            p98 = percentile(pauses, 0.98)
            p99 = percentile(pauses, 0.99)
            p999 = percentile(pauses, 0.999)
            p9999 = percentile(pauses, 0.9999)
    except :
        traceback.print_exc()

    ##########################
    #######GATLING STATS######
    with open(os.path.join(options.folder, f, 'js', 'stats.json')) as json_data:
        d = json.load(json_data)
        stats = d['stats']
        row = ['1500', heap, targetPause, stats['maxResponseTime']['total'], stats['meanResponseTime']['total'], stats['standardDeviation']['total'], stats['percentiles1']['total'], stats['percentiles2']['total'],
               stats['percentiles3']['total'], stats['percentiles4']['total'], psum, pmean, pmax, p50, p90, p95, p99, p999, p9999]
        print (row)
        rows.append(row)
        #result_writer.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])

for row in rows:
    print (','.join([str(x) for x in row]))