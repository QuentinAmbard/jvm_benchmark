import com.google.common.base.Joiner;
import com.google.common.base.Splitter;
import scala.collection.mutable.StringBuilder;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.*;

public class Test {


    public static void main(String[] args) throws IOException {
        String logFile = args.length>0 ? args[0] : "/home/quentin/Downloads/jvm_bench/test-32-31GB-300ms-rs-32-1522861280706/simulation.log";
        String outputFile = args.length>1 ? args[1] : "/home/quentin/Downloads/jvm_bench/test-32-31GB-300ms-rs-32-1522861280706/result.csv";
        Integer timeToMeasureInSec = (args.length>2 ? Integer.valueOf(args[2]) : 1200)*1000;
        System.out.println("logFile="+logFile);
        System.out.println("outputFile="+outputFile);
        String testName = logFile.substring(0,logFile.lastIndexOf("/"));
        testName = logFile.substring(testName.lastIndexOf("/")+1, testName.length());
        Long startTime = null;
        int control = 0;
        long t1 = System.currentTimeMillis();
//        List<Long> timeOK = new ArrayList<>(48 * 1400);
//        List<Long> timeKO = new ArrayList<>(48 * 1400);
        List<Long> timeALL = new ArrayList<>(48 * 1400);
        Splitter splitter = Splitter.on("\t");
        try (BufferedReader br = new BufferedReader(new FileReader(logFile))) {
            String line;
            while ((line = br.readLine()) != null) {
//                if (control % 10000000 == 0) {
//                    System.out.println(control);
//                }
//                control++;
                if (line.startsWith("RE")) { //REQUEST
                    Iterator<String> cols = splitter.split(line).iterator(); //15% faster than a string.split?
                    Long start = null;
                    Long end = null;
                    for(int i =0;i<=6;i++){
                        String cell = cols.next();
                        if(i==5) start = Long.valueOf(cell);
                        else if(i==6) end = Long.valueOf(cell);
                    }
                    if(startTime == null){
                        startTime = start;
                    }
                    if(start > startTime + timeToMeasureInSec){
                        System.out.println("stop at"+start);
                        break;
                    }
                    timeALL.add(end-start);
                }
            }
        }
        long t2 = System.currentTimeMillis();
        System.out.println("took "+(t2-t1)+". sorting...");
        Collections.sort(timeALL);
        System.out.println("sorting ok");

        Map<Integer, Long> percentiles = new LinkedHashMap<>();
        for(int i = 1; i<=10000;i++){
            percentiles.put(i, getPercentile(timeALL, i));
        }
        String csvLine = testName + "," + Joiner.on(",").join(percentiles.values());
        System.out.println(csvLine);
        Files.write(Paths.get(outputFile), csvLine.getBytes(), StandardOpenOption.APPEND);

//        for(Map.Entry<Integer, Long> e : percentiles.entrySet()){
//            sb.append(e.getValue()+",");
//            System.out.println(e.getKey()+"=>"+e.getValue());
//        }
    }

    public static long getPercentile(List<Long> latencies, double percentile) {
        int index = (int) Math.ceil((percentile / 10000.0) * (double) latencies.size());
        return latencies.get(index - 1);
    }
}

// Guava percentile lib is dead slow...
//        System.out.println("Computing quantiles1");
//        Map<Integer, Double> results1 = Quantiles.scale(1000).indexes(500).compute(timeOK);

//        System.out.println("Computing quantiles"+results1.size());
//        ArrayList<Integer> percentiles = new ArrayList();
//        for(int i = 500; i<799;i+=100){
//            percentiles.add(i);
//        }
//        for(int i = 800; i<989;i+=10){
//            percentiles.add(i);
//        }
//        for(int i = 990; i<=1000;i++){
//            percentiles.add(i);
//        }
//        Map<Integer, Double> results = Quantiles.scale(1000).indexes(percentiles).compute(timeOK);
//        ArrayList<Integer> keys = new ArrayList<Integer>(results.keySet());
//        Collections.sort(keys);
//        for(int i : keys){
//            System.out.println(i+" -> "+results.get(i));
//        }
