UPDATE languages
SET compile_cmd = '/usr/local/openjdk13/bin/javac -J-XX:MaxMetaspaceSize=256m -J-Xms64m -J-Xmx256m %s Main.java',
    run_cmd = '/usr/local/openjdk13/bin/java -XX:MaxMetaspaceSize=256m -Xms64m -Xmx256m Main'
WHERE id = 62;
