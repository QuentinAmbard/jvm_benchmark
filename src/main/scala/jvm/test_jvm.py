#!/usr/bin/env python
import sys
import subprocess
import time
from cassandra.cluster import Cluster
from optparse import OptionParser
import os

#sudo apt-get install python-matplotlib
#https://github.com/juliojsb/sarviewer
#apt-get install sysstat gnuplot
#pip install cassandra-driver

#git reset --hard origin/master && git pull
#python3.4 ./test_jvm.py --gatlingFolder="/root/gatling-charts-highcharts-bundle-2.2.2" --dseFolder="/root/dse-5.1.7" --dseHost="37.187.28.208" --ssh="root@37.187.28.208" --testDurationSec="20" --writePerSecPerQuery="1000" --readPerSecPerQuery="1000"
#python3.4 ./test_jvm.py --gatlingFolder="/root/gatling-charts-highcharts-bundle-2.2.2" --dseFolder="/root/dse-5.1.7" --dseHost="37.187.28.208" --ssh="" --testDurationSec="20" --writePerSecPerQuery="1000" --readPerSecPerQuery="1000"
#git reset --hard origin/master && git pull && python3.4 ./test_jvm.py --gatlingFolder="/root/gatling-charts-highcharts-bundle-2.2.2" --dseFolder="/root/dse-5.1.7" --dseHost="10.10.10.3" --ssh="root@195.154.78.138" --testDurationSec="20" --writePerSecPerQuery="10000" --readPerSecPerQuery="10000" --sarViewFolder="/root/jvm_benchmark/src/main/scala/jvm/sarviewer-master"


parser = OptionParser()
parser.add_option("-g", "--gatlingFolder", default="/home/quentin/tools/gatling-charts-highcharts-bundle-2.2.2")
parser.add_option("-f", "--dseFolder", default="/home/quentin/dse/dse-5.1.4")
parser.add_option("-s", "--dseHost", default="127.0.0.1")
parser.add_option("-z", "--ssh", default="")
parser.add_option("-d", "--testDurationSec", default="20")
parser.add_option("-w", "--writePerSecPerQuery", default="1000")
parser.add_option("-r", "--readPerSecPerQuery", default="1000")
parser.add_option("-j", "--oracleJdkPath", default="/opt/jdk1.8.0_161/bin/java")
parser.add_option("-a", "--zingJdkPath", default="/opt/zing/zing-jdk1.8.0-18.02.0.0-4-x86_64/bin/java")
parser.add_option("-t", "--sarViewFolder", default="/root/jvm_benchmark/src/main/scala/jvm/sarviewer-master")




(options, args) = parser.parse_args()
testDurationSec = int(options.testDurationSec)
writePerSecPerQuery = int(options.writePerSecPerQuery)
readPerSecPerQuery = int(options.readPerSecPerQuery)

#gatlingFolder = "/home/quentin/tools/gatling-charts-highcharts-bundle-2.2.2"
outputFolder = options.gatlingFolder+"/results/"+time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
print("Gatling ouptput folder:"+outputFolder)

class Test:
    def __init__(self, name, xmx, xms, G1MaxGCPauseMilli = 300, xss=256):
        self.name = name
        self.params = {}
        self.useG1()
        self.params["xmx"] = "-Xmx"+xmx
        self.params["xms"] = "-Xms"+xms
        self.setG1MaxGCPauseMilli(G1MaxGCPauseMilli)
        self.setG1UpdatingPausePersent(5)
        self.enableTlab()
        self.enableNuma()
        self.enableHsperfdata()
        self.setXss(xss)
        self.java = "alternatives --set java "+options.oracleJdkPath
        self.clean_memory_command = "sync && echo 3 > /proc/sys/vm/drop_caches && "

    def useZing(self):
        #self.java = "alternatives --set java "+options.zingJdkPath
        self.java = "alternatives --set java /opt/zing/zing-jdk1.8.0-18.03.0.0-6-x86_64/bin/java"

    def setHeapWastePercent(self, percent):
        self.params["g1HeapWastePercent"] = str(percent)

    def setNewSizePercent(self, percent):
        self.params["g1NewSizePercent"] = str(percent)

    def setRegionSize(self, regionSize):
        self.params["g1RegionSize"] = "-XX:G1HeapRegionSize="+regionSize

    def setXmn(self, xmn):
        self.params["xmn"] = "-Xmn"+xmn

    def enableTlab(self):
        self.params["tlab"] = "-XX:+UseTLAB"
        self.params["tlab_size_auto"] = "-XX:+ResizeTLAB"

    def setXss(self, size):
        self.params["xss"] = "-Xss"+str(size)+"k"

    def enableNuma(self):
        self.params["numa"] = "-XX:+UseNUMA"

    def enableHsperfdata(self):
        self.params["hsperfdata"] = "-XX:+PerfDisableSharedMem"

    def useG1(self):
        self.params["useg1"] = "-XX:+UseG1GC"

    def setG1UpdatingPausePersent(self, percent):
        self.params["g1UpdatingPausePercent"] = "-XX:G1RSetUpdatingPauseTimePercent="+str(percent)

    def setG1MaxGCPauseMilli(self, milli):
        self.params["g1MaxGCPauseMillis"] = "-XX:MaxGCPauseMillis="+str(milli)

    def setInitiatingHeapOccupancyPercent(self, percent):
        self.params["g1InitiatingHeapOccupancyPercent"] = "-XX:InitiatingHeapOccupancyPercent="+str(percent)

    def setParallelGCThreads(self, threads):
        self.params["g1ParallelGCThreads"] = "-XX:ParallelGCThreads="+str(threads)

    def setConcGCThreads(self, threads):
        self.params["g1ConcGCThreads"] = "-XX:ConcGCThreads="+str(threads)

    def setObjectAlignment(self, value):
        self.params["ObjectAlignmentInBytes"] = "-XX:ObjectAlignmentInBytes="+str(value)

    def useCompressedOops(self):
        self.params["UseCompressedOops"] = "-XX:-UseCompressedOops"

    def setMaxTenuring(self, threshold):
        self.params["maxTenuringThreshold"] = "-XX:MaxTenuringThreshold="+str(threshold)

    def setParallelRefProcEnabled(self):
        self.params["ParallelRefProcEnabled"] = "-XX:+ParallelRefProcEnabled"

    def setNewSize(self, size):
        self.params["NewSize"] = "-XX:NewSize="+size

    def setMixedGCLiveThresholdPercent(self, value):
        self.params["G1MixedGCLiveThresholdPercent"] = "-XX:G1MixedGCLiveThresholdPercent="+str(value)
        self.params["UnlockExperimentalVMOptions"] = "-XX:+UnlockExperimentalVMOptions"

    def enableStringDedup(self):
        self.params["UseStringDeduplication"] = "-XX:+UseStringDeduplication"

    def useLargPage(self):
        self.params["LargePageSizeInBytes"] = "-XX:LargePageSizeInBytes=2m"
        self.params["UseLargePages"] = "-XX:+UseLargePages"

    def loadConfigurationFile(self):
        with open('./jvm.options.template') as infile, open('./jvm.options', 'w') as outfile:
            for line in infile:
                for key, value in self.params.items():
                    line = line.replace("#${"+key+"}", value)
                outfile.write(line)

        if options.ssh == "":
            command = "cp jvm.options "+options.dseFolder+"/resources/cassandra/conf/jvm.options"
        else:
            command = "scp jvm.options "+options.ssh+":"+options.dseFolder+"/resources/cassandra/conf/jvm.options"
        subprocess.call(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def archiveResults(self):
        print("archive results")

    def sshCommand(self, command):
        if options.ssh == "":
            return command
        return "ssh "+options.ssh+" '"+command+"'"

    def restartDSE(self):
        command = self.sshCommand("/root/killdse.sh")
        print("killing DSE:"+command)
        subprocess.call(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        time.sleep(1)
        command = self.sshCommand(self.clean_memory_command+self.java+" && "+options.dseFolder+"/bin/dse cassandra -R")
        print("Restarting DSE"+command)
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #subprocess.call(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("Sleeping 30sec")
        time.sleep(30)

    def resetDSE(self, count = 0):
        try:
            cluster = Cluster([options.dseHost])
            session = cluster.connect()
            session.execute("create keyspace if not exists jvm with replication = {'class': 'SimpleStrategy', 'replication_factor': 1} AND durable_writes = false ")
            session.execute("create table if not exists jvm.person (id int, firstname text, lastname text, age int, city text, address text, zipcode text, description text, primary key (id)) WITH compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy', 'max_threshold': '2048', 'min_threshold': '1024'}")# WITH compaction= { 'class': 'MemoryOnlyStrategy' } AND caching = {'keys':'NONE', 'rows_per_partition':'NONE'}")
            session.execute("create table if not exists jvm.message (person_id int, id int, header text, content blob, content2 blob, score float, primary key ((person_id), id)) WITH compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy', 'max_threshold': '2048', 'min_threshold': '1024'}")#WITH compaction= { 'class': 'MemoryOnlyStrategy' } AND caching = {'keys':'NONE', 'rows_per_partition':'NONE'}")
            session.execute("create table if not exists jvm.comment (id int, time timestamp, content text, like int, categories map<text, text>, primary key ((id), time)) WITH compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy', 'max_threshold': '2048', 'min_threshold': '1024'}")#WITH compaction= { 'class': 'MemoryOnlyStrategy' } AND caching = {'keys':'NONE', 'rows_per_partition':'NONE'}")
            session.execute("truncate table jvm.person")
            session.execute("truncate table jvm.comment")
            session.execute("truncate table jvm.message")
            print("Tables truncated, disabling compaction...")
            command = self.sshCommand("nodetool disableautocompaction")
            print (command)
            disable_compaction_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            disable_compaction_command.wait()
            print("compaction disabled, DSE is ready")
        except:
            time.sleep(1)
            print("trying to connect to"+options.dseHost)
            if count > 120:
                print("ERROR, DSE hasn't restarted, something is wrong...")
            else:
                self.resetDSE(count+1)


    def startGatlingTest(self):
        # print("Warming up jvm, (60 sec gatling stress)")
        # #from time to time Zing won't start if it can't allocate the required heap memory (even if it's only used by buffers). drop all cache before starting gatling.
        # process = subprocess.Popen(self.clean_memory_command + """alternatives --set java """+options.oracleJdkPath+""" && export JAVA_OPTS="-DcontactPoint="""+options.dseHost+""" -DtestDurationSec=60 -DwritePerSecPerQuery=5000 -DreadPerSecPerQuery=5000" && """+options.gatlingFolder+"""/bin/gatling.sh -m -nr > """+self.name+"""-warmup.log.txt 2>&1 """, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # process.wait()
        # time.sleep(20)
        print("Running "+self.name)
        # #from time to time Zing won't start if it can't allocate the required heap memory (even if it's only used by buffers). drop all cache before starting gatling.
        #command = self.clean_memory_command + """alternatives --set java """+options.zingJdkPath+""" && export JAVA_OPTS="-DcontactPoint=%s -DtestDurationSec=%d -DwritePerSecPerQuery=%d -DreadPerSecPerQuery=%d" && %s/bin/gatling.sh -m -nr -rf %s -on %s > %s 2>&1 """ % (options.dseHost, testDurationSec, writePerSecPerQuery, readPerSecPerQuery, options.gatlingFolder, outputFolder, self.name, self.name+".log.txt")
        command = self.clean_memory_command + "alternatives --set java "+options.zingJdkPath+" && cd /root/dse-benchmarks && mvn clean scala:testCompile gatling:execute -Dgatling.disableCompiler -Dgatling.simulationClass=jvm.TestJVM -DcontactPoint=%s -DtestDurationSec=%d -DwritePerSecPerQuery=%d -DreadPerSecPerQuery=%d -Dgatling.core.directory.results=/root/results/%s > %s 2>&1 " % (options.dseHost, testDurationSec, writePerSecPerQuery, readPerSecPerQuery, self.name, self.name+".log.txt")
        #java -cp /home/quentin/projects/HdrLogProcessing/target/HdrLogProcessing-1.0-SNAPSHOT-jar-with-dependencies.jar SummarizeHistogramLogs -ifp total.hgrm -st hgrm
        print(command)
        process_injector = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        command_sar = self.sshCommand(options.sarViewFolder+"/data_collector.sh -n %d -i 1 && /root/dump_jvm.sh " % (testDurationSec + 80))
        print(command_sar)
        process_sar = subprocess.Popen(command_sar, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process_injector.wait()
        process_sar.wait()
        command_copy_sar = "mkdir -p "+outputFolder+"/"+self.name+"-sar "
        if options.ssh == "":
            command_copy_sar += "&& cp -r "+options.sarViewFolder+"/graphs/* "+outputFolder+"/"+self.name+"-sar/ "
            command_copy_sar += "&& cp -r /var/log/cassandra/gc.log* "+outputFolder+"/"+self.name+"-sar/ "
        else:
            command_copy_sar += "&& scp -r "+options.ssh+":"+options.sarViewFolder+"/graphs/* "+outputFolder+"/"+self.name+"-sar "
            command_copy_sar += "&& scp -r "+options.ssh+":/var/log/cassandra/gc.log* "+outputFolder+"/"+self.name+"-sar/ "
            command_copy_sar += "&& cd "+outputFolder+" "
            command_copy_sar += "&& for i in "+self.name+"* ; do tar -I pigz -cvf $i.tar.gz $i  --remove-files; done"

        print(command_copy_sar)
        process_copy_sar = subprocess.Popen(command_copy_sar, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process_copy_sar.wait()
        print("test done")

    def test(self):
        print("Starting test "+self.name)
        self.loadConfigurationFile()
        self.restartDSE()
        self.resetDSE()
        self.startGatlingTest()



# 8k/sec * 6 = 2880000/min, 5760000/2min
# remove the 2 first minutes && remove the last minute.

# sleep 120
# unalias mv
# unset -f mv
# for i in  *20GB* ;
# do tar -I pigz -xvf $i -C /root/results && \
# head -n 1 "/root/results/${i::-7}/simulation.log" > "/root/results/${i::-7}/simulation-final.log" && \
# tail -n +5760000 "/root/results/${i::-7}/simulation.log" | head -n -2880000 >> "/root/results/${i::-7}/simulation-final.log" && \
# mv -f "/root/results/${i::-7}/simulation-final.log" "/root/results/${i::-7}/simulation.log" && \
# /root/gatling-charts-highcharts-bundle-2.2.2/bin/gatling.sh -ro "/root/results/${i::-7}" && \
# rm -rf "/root/results/${i::-7}/simulation.log";
# done
#
#sleep 30; for i in  *48GB* ; do tar -I pigz -xvf $i -C /root/results && head -n 1 "/root/results/${i::-7}/simulation.log" > "/root/results/${i::-7}/simulation-final.log" && tail -n +5760000 "/root/results/${i::-7}/simulation.log" | head -n -2880000 >> "/root/results/${i::-7}/simulation-final.log" && mv -f "/root/results/${i::-7}/simulation-final.log" "/root/results/${i::-7}/simulation.log" && /root/gatling-charts-highcharts-bundle-2.2.2/bin/gatling.sh -ro "/root/results/${i::-7}" && rm -rf "/root/results/${i::-7}/simulation.log"; done
# plt.plot([1,2,3,4])
# plt.ylabel('some numbers')
# plt.savefig('foo.png', dpi=200)


def test_pause_time_32():
    #Heap size & pause time
    for maxPause in [50, 100, 200, 300, 400, 500, 600]:
        test1 = Test("test-pause-time-32GB-"+str(maxPause)+"ms", "32G", "32G", G1MaxGCPauseMilli=maxPause)
        test1.test()
        time.sleep(2)

def test_heap_pause_200():
    maxPause = 200
    #Heap size & pause time
    for i in range(8, 62, 4):
        test1 = Test("test-heap-size-"+str(maxPause)+"ms-"+str(i)+"GB", str(i)+"G", str(i)+"G", G1MaxGCPauseMilli=maxPause)
        test1.test()
        time.sleep(2)

def test_32_31_simple():
    maxPause = 300
    test1 = Test("test-32-31GB-small-"+str(maxPause)+"ms-rs-16", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setRegionSize("16m")
    test1.useCompressedOops()
    test1.test()
    test1 = Test("test-32-32GB-small"+str(maxPause)+"ms-rs-16", "32G", "32G", G1MaxGCPauseMilli=maxPause)
    test1.setRegionSize("16m")
    test1.test()

#32GB vs 31GB
def test_32_31():
    maxPause = 300
    test1 = Test("test-32-32GB-"+str(maxPause)+"ms-rs-8", "32G", "32G", G1MaxGCPauseMilli=maxPause)
    test1.setRegionSize("8m")
    test1.test()
    time.sleep(2)
    test1 = Test("test-32-31GB-"+str(maxPause)+"ms-rs-16", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setRegionSize("16m")
    test1.useCompressedOops()
    test1.test()
    time.sleep(2)
    for i in range(31, 33):
        test1 = Test("test-32-"+str(i)+"GB-"+str(maxPause)+"ms-rs-default", str(i)+"G", str(i)+"G", G1MaxGCPauseMilli=maxPause)
        test1.test()
        time.sleep(2)
    test1 = Test("test-32-32GB-"+str(maxPause)+"ms-byte-alignment-16-rs-default", "32G", "32G", G1MaxGCPauseMilli=maxPause)
    test1.setObjectAlignment(16)
    test1.useCompressedOops()
    test1.test()
    time.sleep(2)
    test1 = Test("test-32-32GB-"+str(maxPause)+"ms-byte-alignment-16-rs-8", "32G", "32G", G1MaxGCPauseMilli=maxPause)
    test1.setObjectAlignment(16)
    test1.setRegionSize("8m")
    test1.useCompressedOops()
    test1.test()
    time.sleep(2)

def test_new_size():
    maxPause = 300
    test1 = Test("test-new-size-4GB-31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setNewSize("4G")
    test1.test()
    time.sleep(2)

def test_heap_pause_time():
    #Heap size & pause time
    for maxPause in [50, 100, 200, 300, 400, 500, 600]:
        for i in range(8, 62, 4):
            test1 = Test("test-heap-size-"+str(i)+"GB-"+str(maxPause)+"ms", str(i)+"G", str(i)+"G", G1MaxGCPauseMilli=maxPause)
            test1.test()
            time.sleep(2)

def test_parallel_gc_thread():
    maxPause = 300
    for thread in [8, 16, 32, 40]:
        test1 = Test("test-par-thread-"+str(thread)+"31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
        test1.setParallelGCThreads(thread)
        test1.test()
        time.sleep(2)

def test_ihop(maxTenuring):
    maxPause = 300
    for ihop in [60,70,80,45]:
        test1 = Test("test-ihop-"+str(ihop)+"31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
        test1.setInitiatingHeapOccupancyPercent(ihop)
        test1.setMaxTenuring(maxTenuring)
        test1.test()
        time.sleep(2)

def test_max_tenuring():
    maxPause = 300
    for threshold in [0,1,2,3,4]:
        test1 = Test("test-tenuring-"+str(threshold)+"-31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
        test1.setMaxTenuring(threshold)
        test1.test()
        time.sleep(2)

def test_parallelRefProcEnabled():
    maxPause = 300
    test1 = Test("test-parallel_ref-disabled-31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.test()
    time.sleep(2)
    test1 = Test("test-parallel_ref-31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setParallelRefProcEnabled()
    test1.test()
    time.sleep(2)

def test_mixed_percent():
    maxPause = 300
    test1 = Test("test-mixed-percent-45-31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setMixedGCLiveThresholdPercent(45)
    test1.test()
    time.sleep(2)
    test1 = Test("test-mixed-percent-55-31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setMixedGCLiveThresholdPercent(55)
    test1.test()
    time.sleep(2)

def test_string_dedup():
    maxPause = 300
    test1 = Test("test-string-dedup-45-31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.enableStringDedup()
    test1.test()

def test_base():
    maxPause = 300
    test1 = Test("test-base-31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setRegionSize("16m")
    test1.test()


def test_base_zing():
    maxPause = 300
    test1 = Test("test-base-31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.useZing()
    test1.test()

def test_zing_heap():
    i=48
    test1 = Test("test-zing-heap-size-"+str(i)+"GB", str(i)+"G", str(i)+"G")
    test1.useZing()
    test1.test()
    # for i in range(8, 62, 8):
    #     test1 = Test("test-zing-heap-size-"+str(i)+"GB", str(i)+"G", str(i)+"G")
    #     test1.useZing()
    #     test1.test()
    #     time.sleep(2)

def test_zero_based_compression():
    maxPause=300
    test1 = Test("test-zero_based_compression-heap-30GB", "30G", "30G", G1MaxGCPauseMilli=maxPause)
    test1.setRegionSize("16m")
    test1.test()
    time.sleep(2)
    test1 = Test("test-zero_based_compression-heap-31GB", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setRegionSize("16m")
    test1.test()
    time.sleep(2)


def test_final():
    maxPause = 300
    test1 = Test("test-final-31GB-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setRegionSize("16m")
    test1.setNewSize("2500m")
    test1.setMaxTenuring(0)
    test1.setParallelGCThreads(32)
    test1.setParallelRefProcEnabled()

    #test1.useZing()
    test1.test()

def test_huge_page():
    maxPause = 300
    test1 = Test("test-huge-page-enabled-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setRegionSize("16m")
    test1.useLargPage()
    test1.test()
    test1 = Test("test-huge-page-disabled-"+str(maxPause)+"ms", "31G", "31G", G1MaxGCPauseMilli=maxPause)
    test1.setRegionSize("16m")
    test1.test()


test_huge_page()

#test_base()
# test_mixed_percent()
# test_string_dedup()
#test_string_dedup()
#test_zing_heap()
#test_zero_based_compression()
#test_heap_pause_200()

#test_pause_time_32()
# test_heap_pause_time()
# #test_parallelRefProcEnabled()
# test_new_size()
# test_parallel_gc_thread()
#test_32_31_simple()
# test_max_tenuring()
# test_ihop(0)
#test_ihop(1)


# test1 = Test("test-heap-size-32GB", "32G", "32G")
# test1.test()

#test1.resetDSE()
#test1.startGatlingTest()
#tar: test-heap-size-36GB-500ms-1522540732002/simulation.log: file changed as we read it
