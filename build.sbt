import sbtassembly.PathList

name := "jvm_bench"

version := "0.1"

scalaVersion := "2.12.4"

libraryDependencies += "io.gatling" % "gatling-core" % "2.2.3"
libraryDependencies += "io.gatling" % "gatling-http" % "2.2.3"
libraryDependencies += "com.google.guava" % "guava" % "24.1-jre"



// resolvers += "Job Server Bintray" at "https://dl.bintray.com/spark-jobserver/maven"

assemblyMergeStrategy in assembly := {
  case PathList("javax", "servlet", xs @ _*) => MergeStrategy.last
  case PathList("javax", "activation", xs @ _*) => MergeStrategy.last
  case PathList("org", "apache", xs @ _*) => MergeStrategy.last
  case PathList("com", "google", xs @ _*) => MergeStrategy.last
  case PathList("com", "esotericsoftware", xs @ _*) => MergeStrategy.last
  case PathList("com", "codahale", xs @ _*) => MergeStrategy.last
  case PathList("com", "yammer", xs @ _*) => MergeStrategy.last
  case "about.html" => MergeStrategy.rename
  case "META-INF/ECLIPSEF.RSA" => MergeStrategy.last
  case "META-INF/mailcap" => MergeStrategy.last
  case "META-INF/mimetypes.default" => MergeStrategy.last
  case "plugin.properties" => MergeStrategy.last
  case "log4j.properties" => MergeStrategy.last
  case x if x.endsWith("io.netty.versions.properties") => MergeStrategy.first
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case x => MergeStrategy.first
  //  case x =>
  //    val oldStrategy = (assemblyMergeStrategy in assembly).value
  //    oldStrategy(x)
}

