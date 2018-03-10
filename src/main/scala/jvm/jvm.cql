drop table jvm.person ;
drop table jvm.comment ;
drop table jvm.message ;
create keyspace jvm with replication = {'class': 'SimpleStrategy', 'replication_factor': 1} ;
create table jvm.person (id int, firstname text, lastname text, age int, city text, address text, zipcode text, description text, primary key (id));
create table jvm.message (person_id int, id int, header text, content blob, content2 blob, score float, primary key ((person_id), id));
create table jvm.comment (id int, time timestamp, content text, like int, categories map<text, text>, primary key ((id), time));