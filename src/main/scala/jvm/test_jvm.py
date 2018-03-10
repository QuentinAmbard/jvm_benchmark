#!/usr/bin/env python
import sys
import subprocess
import time
from cassandra.cluster import Cluster
import matplotlib.pyplot as plt

#sudo apt-get install python-matplotlib
#https://github.com/juliojsb/sarviewer
#apt-get install sysstat gnuplot
#pip install cassandra-driver

gatlingFolder = "/home/quentin/tools/gatling-charts-highcharts-bundle-2.2.2"
outputFolder =  gatlingFolder+"/results/"+time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
dseFolder = "/home/quentin/dse/dse-5.1.4"
dseHost = "127.0.0.1"
testDurationSec = 20
writePerSecPerQuery = 1000
readPerSecPerQuery = 1000

class Test:
    def __init__(self, name, xmx, xms, G1MaxGCPauseMilli = 300, xss=256):
        self.name = name
        self.params = {}
        self.params["xmx"] = "-Xmx"+xmx
        self.params["xms"] = "-Xms"+xms
        self.setG1MaxGCPauseMilli(G1MaxGCPauseMilli)
        self.setXss(xss)

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
        self.params["g1"] = "-XX:+UseG1GC"

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
        #TODO scp instead
        subprocess.call("cp jvm.options "+dseFolder+"/resources/cassandra/conf/jvm.options", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def archiveResults(self):
        print("archive results")

    def restartDSE(self):
        print("killing DSE")
        subprocess.call("kill -9 $(pgrep -f cassandra)", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        time.sleep(1)
        print("Restarting DSE")
        subprocess.call(dseFolder+"/bin/dse cassandra", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        time.sleep(30)

    def resetDSE(self, count = 0):
        try:
            cluster = Cluster(['dseHost'])
            session = cluster.connect()
            session.execute("create keyspace if not exists jvm with replication = {'class': 'SimpleStrategy', 'replication_factor': 1} AND durable_writes = false ")
            session.execute("create table if not exists jvm.person (id int, firstname text, lastname text, age int, city text, address text, zipcode text, description text, primary key (id))")
            session.execute("create table if not exists jvm.message (person_id int, id int, header text, content blob, content2 blob, score float, primary key ((person_id), id))")
            session.execute("create table if not exists jvm.comment (id int, time timestamp, content text, like int, categories map<text, text>, primary key ((id), time))")
            session.execute("create table if not exists jvm.test (name text primary key, state text)")
            session.execute("truncate table jvm.person")
            session.execute("truncate table jvm.comment")
            session.execute("truncate table jvm.message")
            print("Tables truncated, DSE is ready")
        except:
            time.sleep(1)
            if count > 60:
                print("ERROR, DSE hasn't restarted, something is wrong...")
            else:
                self.resetDSE(count+1)


    def startGatlingTest(self):
        print("Warming up jvm, (10 sec gatling stress)")
        process = subprocess.Popen("""export JAVA_OPTS="-DtestDurationSec=10 -DwritePerSecPerQuery=1000 -DreadPerSecPerQuery=1000" && """+gatlingFolder+"""/bin/gatling.sh -m -nr""", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process.wait()
        time.sleep(2)
        print("Running "+self.name)
        process = subprocess.Popen("""export JAVA_OPTS="-DtestDurationSec=%d -DwritePerSecPerQuery=%d -DreadPerSecPerQuery=%d" && %s/bin/gatling.sh -m -rf %s -on %s""" % (testDurationSec, writePerSecPerQuery, readPerSecPerQuery, gatlingFolder, outputFolder, self.name), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process.wait()
        print("test done")



plt.plot([1,2,3,4])
plt.ylabel('some numbers')
plt.savefig('foo.png', dpi=200)


#test1 = Test("test-witTLAB", "8G", "8G")

# test1.enableTlab()
# test1.loadConfigurationFile()
#test1.restartDSE()
# test1.resetDSE()
#test1.startGatlingTest()
