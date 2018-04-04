kill -9 $(pgrep -f cassandra)
rm -rf /home/cassandra/5.1.7/cassandra/commitlog/*
rm -rf /home/cassandra/5.1.7/cassandra/data/jvm/*
