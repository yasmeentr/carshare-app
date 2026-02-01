FROM tomcat:11.0.14-jdk21

# Supprimer les applications par défaut (optionnel)
RUN rm -rf /usr/local/tomcat/webapps/ROOT

# Copier le WAR directement dans webapps
COPY target/carshare-app.war /usr/local/tomcat/webapps/

# Copier le driver JDBC
COPY conf/mysql-connector-j-9.3.0.jar /usr/local/tomcat/lib/

# Copier context et tomcat-users
COPY conf/context.xml /usr/local/tomcat/conf/context.xml
COPY conf/tomcat-users.xml /usr/local/tomcat/conf/tomcat-users.xml

# Désactiver RemoteAddrValve dans manager/host-manager
#RUN sed -i 's/^\(.*RemoteAddrValve.*\)$/<!-- \1 -->/' \
 #   /usr/local/tomcat/webapps/manager/META-INF/context.xml && \
 #   sed -i 's/^\(.*RemoteAddrValve.*\)$/<!-- \1 -->/' \
 #   /usr/local/tomcat/webapps/host-manager/META-INF/context.xml
