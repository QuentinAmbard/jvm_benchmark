package jvm

import java.nio.ByteBuffer
import java.time.format.DateTimeFormatter
import java.time.{LocalDateTime, ZoneOffset}
import java.util
import java.util.{Date, UUID}

import com.datastax.driver.core._
import io.gatling.core.Predef.{constantUsersPerSec, feed, scenario, _}
import io.gatling.core.scenario.Simulation
import io.github.gatling.cql.Predef.{cql, _}

import scala.concurrent.duration.DurationInt
import scala.util.Random


class TestJVM extends Simulation {
  def getProperty(value: String, default: String = null): String = {
    System.getProperty(value) match {
      case null => default
      case c => c
    }
  }
  val contactPoint = getProperty("contactPoint", "localhost")

  val writePerSecPerQuery = getProperty("writePerSecPerQuery", "10000").toInt
  val readPerSecPerQuery = getProperty("readPerSecPerQuery", "10000").toInt
  val testDurationSec = getProperty("testDurationSec", "10").toInt
  val rampupDurationSec = getProperty("rampupDurationSec", "120").toInt
  val maxEntitiesPerTable = getProperty("maxEntitiesPerTable", "480000").toInt

  Random.setSeed(1321254L)
  val random = new Random()
  val subset: Array[Char] = "0123456789abcdefghijklmnopqrstuvwxyzAZERTYUIOPMLKJHGFDSQWXCVBN".toCharArray
  def getRandomStr(length: Int): String = {
    val buf = new Array[Char](length)
    for (i <- 0 to buf.length -1) {
      val index = random.nextInt(subset.length)
      buf(i) = subset(index)
    }
    new String(buf)
  }


  def getRandom[A](values: Array[A]): A = values(random.nextInt(values.length))

  val dates = (0 to 1000000).map(i => new Date(i)).toArray


  val cluster = Cluster.builder()
    .addContactPoints(contactPoint)
    .withPoolingOptions(new PoolingOptions()
      .setConnectionsPerHost(HostDistance.LOCAL, 20, 30)
      .setMaxRequestsPerConnection(HostDistance.LOCAL, 5000))
    .build()

  val session = cluster.connect() //Your C* session

  val firstnames = (0 to 100).map(_ => getRandomStr(30)).toArray
  val lastnames = (0 to 100).map(_ => getRandomStr(50)).toArray
  val cities = (0 to 100).map(_ => getRandomStr(10+random.nextInt(10))).toArray
  val addresses = (0 to 100).map(_ => getRandomStr(20+random.nextInt(50))).toArray
  val zipcodes = (0 to 100).map(_ => getRandomStr(7)).toArray
  val contents = (0 to 10).map(_ => getRandomStr(2000+random.nextInt(500))).toArray
  val smallContents = (0 to 10).map(i => {
    val b = new Array[Byte](random.nextInt(100) + 500)
    random.nextBytes(b)
    ByteBuffer.wrap(b)
  }).toArray


  val cqlConfig = cql.session(session) //Initialize Gatling DSL with your session

  var maxEntry = 8000 * 60
  var p = 0

  val insertPersonQ = session.prepare("""INSERT INTO jvm.person (id, firstname, lastname, age, city, address, zipcode, description) VALUES (?,?,?,?,?,?,?,?)""")
  val insertPerson = scenario("insert Person").repeat(1) {
    feed(Iterator.continually({
      p += 1
      //if(p>maxEntitiesPerTable) p = 0
      Map(
        "id" -> p ,
        "firstname" -> s"$p${getRandom(firstnames)}",
        "lastname"  -> s"$p${getRandom(lastnames)}",
        "age" -> p,
        "city" -> s"$p${getRandom(cities)}",
        "address" -> s"$p${getRandom(addresses)}",
        "zipcode" -> s"$p${getRandom(zipcodes)}",
        "description" -> s"$p${getRandom(contents)}"
      )
    })).exec(cql("insert person").execute(insertPersonQ)
      .withParams("${id}", "${firstname}", "${lastname}", "${age}", "${city}", "${address}", "${zipcode}", "${description}")
    )
  }

  var m = 0
  val insertMessageQ = session.prepare("""INSERT INTO jvm.message (person_id, id, header, content, content2, score) VALUES (?,?,?,?,?,?)""")
  val insertMessage = scenario("insert message").repeat(1) {
    feed(Iterator.continually({
      m += 1
      //if(m>maxEntitiesPerTable) m = 0
      Map(
        "person_id" -> p/10,
        "id" -> m ,
        "header"  -> getRandom(lastnames),
        "content" -> getRandom(smallContents),
        "content2" -> getRandom(smallContents),
        "score" -> random.nextFloat()
      )
    })).exec(cql("insert message").execute(insertMessageQ)
      .withParams("${person_id}", "${id}", "${header}", "${content}", "${content2}", "${score}")
    )
  }

  val categories = (0 to 1000).map(i => {
    val c = new util.HashMap[String, String]()
    c.put(random.nextString(10), random.nextString(10))
    c.put(random.nextString(10), random.nextString(10))
    c.put(random.nextString(10), random.nextString(10))
    c
  }).toArray


  var c = 0
  val insertCommentQ = session.prepare("""INSERT INTO jvm.comment (id, time, content, like, categories) VALUES (?,?,?,?,?)""")
  val insertComment = scenario("insert comment").repeat(1) {
    feed(Iterator.continually({
      c += 1
      //if(c>maxEntitiesPerTable) c = 0
      Map(
        "id" -> c/10 ,
        "time" -> getRandom(dates),
        "content"  -> getRandom(contents),
        "like" -> random.nextInt(),
        "categories" -> getRandom(categories)
      )
    })).exec(cql("insert comment").execute(insertCommentQ)
      .withParams("${id}", "${time}", "${content}", "${like}", "${categories}")
    )
  }

  var rp = 0
  val readPersonQ = session.prepare("""SELECT * from jvm.person where id=? """)
  val readPerson = scenario("read person").repeat(1) {
    feed(Iterator.continually({
//      rp+=1
//      if(rp>p){
//        rp = 0
//      }
      Map("id" -> random.nextInt(p))
    })).exec(cql("read person").execute(readPersonQ)
      .withParams("${id}")
    )
  }

  var rm = 0
  val readMessageQ = session.prepare("""SELECT * from jvm.message where person_id=? """)
  val readMessage = scenario("read message").repeat(1) {
    feed(Iterator.continually({
//      rm+=1
//      if(rm>m){
//        rm = 0
//      }
      Map("person_id" -> random.nextInt(p))
    })).exec(cql("read message").execute(readMessageQ)
      .withParams("${person_id}")
      .consistencyLevel(ConsistencyLevel.ONE)
    )
  }


  var rc = 0
  val readCommentQ = session.prepare("""SELECT * from jvm.comment where id=? """)
  val readComment = scenario("read comment").repeat(1) {
    feed(Iterator.continually({
//      rc+=1
//      if(rc>c){
//        rc = 0
//      }
      Map("id" -> random.nextInt(c))
    })).exec(cql("read comment").execute(readCommentQ)
      .withParams("${id}")
      .consistencyLevel(ConsistencyLevel.ONE)
    )
  }


  setUp(
    insertPerson.inject(smalRampup(), normalRampup(writePerSecPerQuery), constantUsersPerSec(writePerSecPerQuery) during (testDurationSec seconds), endRampup(writePerSecPerQuery))
    ,insertMessage.inject(smalRampup(), normalRampup(writePerSecPerQuery), constantUsersPerSec(writePerSecPerQuery) during (testDurationSec seconds), endRampup(writePerSecPerQuery))
    ,insertComment.inject(smalRampup(), normalRampup(writePerSecPerQuery), constantUsersPerSec(writePerSecPerQuery) during (testDurationSec seconds), endRampup(writePerSecPerQuery))

    ,readPerson.inject(smalRampup(), normalRampup(readPerSecPerQuery), constantUsersPerSec(readPerSecPerQuery) during (testDurationSec seconds), endRampup(readPerSecPerQuery))
    ,readMessage.inject(smalRampup(), normalRampup(readPerSecPerQuery), constantUsersPerSec(readPerSecPerQuery) during (testDurationSec seconds), endRampup(readPerSecPerQuery))
    ,readComment.inject(smalRampup(), normalRampup(readPerSecPerQuery), constantUsersPerSec(readPerSecPerQuery) during (testDurationSec seconds), endRampup(readPerSecPerQuery))
  ).protocols(cqlConfig)

//  session.execute("delete from jvm.test where name='gatling'")

  private def normalRampup(target: Int) = {
    rampUsersPerSec(500) to target during (rampupDurationSec seconds)
  }

  private def endRampup(target: Int) = {
    rampUsersPerSec(target) to 10 during (30 seconds)
  }

  private def smalRampup() = {
    rampUsersPerSec(1) to 500 during (20 seconds)
  }
}