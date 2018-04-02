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
        self.java = "alternatives --set java "+options.zingJdkPath

    def setHeapWastePercent(self, percent):
        self.params["g1HeapWastePercent"] = str(percent)

    def setRegionSizePercent(self, percent):
        self.params["g1NewSizePercent"] = str(percent)

    def setRegionSize(self, regionSize):
        self.params["g1RegionSize"] = regionSize

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

    def setInitiatingHeapOccupancyPercent(self, milli):
        self.params["g1InitiatingHeapOccupancyPercent"] = "-XX:InitiatingHeapOccupancyPercent="+str(percent)

    def setParallelGCThreads(self, threads):
        self.params["g1ParallelGCThreads"] = "-XX:ParallelGCThreads="+str(threads)

    def setConcGCThreads(self, threads):
        self.params["g1ConcGCThreads"] = "-XX:ConcGCThreads="+str(threads)

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
        command = self.sshCommand("kill -9 $(pgrep -f cassandra)")
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
            session.execute("create table if not exists jvm.person (id int, firstname text, lastname text, age int, city text, address text, zipcode text, description text, primary key (id)) ") #WITH compaction= { 'class': 'MemoryOnlyStrategy' } AND compression = {'sstable_compression' : ''} AND caching = {'keys':'NONE', 'rows_per_partition':'NONE'}
            session.execute("create table if not exists jvm.message (person_id int, id int, header text, content blob, content2 blob, score float, primary key ((person_id), id)) ") #WITH compaction= { 'class': 'MemoryOnlyStrategy' } AND compression = {'sstable_compression' : ''} AND caching = {'keys':'NONE', 'rows_per_partition':'NONE'}
            session.execute("create table if not exists jvm.comment (id int, time timestamp, content text, like int, categories map<text, text>, primary key ((id), time)) ") #WITH compaction= { 'class': 'MemoryOnlyStrategy' } AND compression = {'sstable_compression' : ''} AND caching = {'keys':'NONE', 'rows_per_partition':'NONE'}
            session.execute("truncate table jvm.person")
            session.execute("truncate table jvm.comment")
            session.execute("truncate table jvm.message")
            print("Tables truncated, DSE is ready")
        except:
            time.sleep(1)
            print("trying to connect to"+options.dseHost)
            if count > 120:
                print("ERROR, DSE hasn't restarted, something is wrong...")
            else:
                self.resetDSE(count+1)


    def startGatlingTest(self):
        print("Warming up jvm, (60 sec gatling stress)")
        #from time to time Zing won't start if it can't allocate the required heap memory (even if it's only used by buffers). drop all cache before starting gatling.
        process = subprocess.Popen(self.clean_memory_command + """alternatives --set java """+options.oracleJdkPath+""" && export JAVA_OPTS="-DcontactPoint="""+options.dseHost+""" -DtestDurationSec=60 -DwritePerSecPerQuery=5000 -DreadPerSecPerQuery=5000" && """+options.gatlingFolder+"""/bin/gatling.sh -m -nr > """+self.name+"""-warmup.log.txt 2>&1 """, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process.wait()
        time.sleep(20)
        print("Running "+self.name)
        command = self.clean_memory_command + """alternatives --set java """+options.zingJdkPath+""" && export JAVA_OPTS="-DcontactPoint=%s -DtestDurationSec=%d -DwritePerSecPerQuery=%d -DreadPerSecPerQuery=%d" && %s/bin/gatling.sh -m -nr -rf %s -on %s > %s 2>&1 """ % (options.dseHost, testDurationSec, writePerSecPerQuery, readPerSecPerQuery, options.gatlingFolder, outputFolder, self.name, self.name+".log.txt")
        print(command)
        process_injector = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        command_sar = self.sshCommand(options.sarViewFolder+"/data_collector.sh -n %d -i 1 && /root/dump_jvm.sh " % (testDurationSec + 80))
        print(command_sar)
        process_sar = subprocess.Popen(command_sar, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process_injector.wait()
        process_sar.wait()
        command_copy_sar = "mkdir -p "+outputFolder+"/"+self.name+"-sar "
        if options.ssh == "":
            command_copy_sar += "&& cp -r "+options.sarViewFolder+"/graphs/* "+outputFolder+"/"+self.name+"-sar/"
            command_copy_sar += "&& cp -r /var/log/cassandra/gc.log* "+outputFolder+"/"+self.name+"-sar/"
        else:
            command_copy_sar += "&& scp -r "+options.ssh+":"+options.sarViewFolder+"/graphs/* "+outputFolder+"/"+self.name+"-sar"
            command_copy_sar += "&& scp -r "+options.ssh+":/var/log/cassandra/gc.log* "+outputFolder+"/"+self.name+"-sar/"
            command_copy_sar += "&& for i in "+outputFolder+"/"+self.name+"* ; do tar -I pigz -cvf $i.tar.gz $i  --remove-files; done"

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



# plt.plot([1,2,3,4])
# plt.ylabel('some numbers')
# plt.savefig('foo.png', dpi=200)

test1 = Test("test-heap-size-36GB-500ms", "36G", "36G", G1MaxGCPauseMilli=500)
test1.test()
time.sleep(2)

test1 = Test("test-heap-size-12GB-400ms", "12G", "12G", G1MaxGCPauseMilli=400)
test1.test()
time.sleep(2)

for maxPause in [50]:#[400, 500, 600, 200, 100, 50]:
    for i in range(16, 82, 4):
        test1 = Test("test-heap-size-"+str(i)+"GB-"+str(maxPause)+"ms", str(i)+"G", str(i)+"G", G1MaxGCPauseMilli=maxPause)
        test1.test()
        time.sleep(2)

# test1 = Test("test-heap-size-32GB", "32G", "32G")
# test1.test()

#test1.resetDSE()
#test1.startGatlingTest()
#tar: test-heap-size-36GB-500ms-1522540732002/simulation.log: file changed as we read it
