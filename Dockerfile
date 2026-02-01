# Tomcat version stable (JDK 21 recommandé)
FROM tomcat:10.1-jdk21-temurin

# Initialisation robuste (chemins absolus + nettoyage)
RUN rm -rf /usr/local/tomcat/webapps/* \
    && cp -r /usr/local/tomcat/webapps.dist/* /usr/local/tomcat/webapps/

# Driver JDBC
COPY conf/mysql-connector-j-9.3.0.jar /usr/local/tomcat/lib/

# Confs
COPY conf/context.xml /usr/local/tomcat/conf/context.xml
COPY conf/tomcat-users.xml /usr/local/tomcat/conf/tomcat-users.xml

# Désactiver la RemoteAddrValve pour accéder au manager/host-manager depuis l’extérieur
RUN sed -i 's/^\(.*RemoteAddrValve.*\)$/<!-- \1 -->/' /usr/local/tomcat/webapps/manager/META-INF/context.xml && \
    sed -i 's/^\(.*RemoteAddrValve.*\)$/<!-- \1 -->/' /usr/local/tomcat/webapps/host-manager/META-INF/context.xml

# (Optionnel mais recommandé) Déployer ton WAR si tu buildes en dehors de Docker
COPY target/carshare-app.war /usr/local/tomcat/webapps/carshare-app.war
