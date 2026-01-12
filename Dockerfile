FROM tomcat


# Nettoyer les apps par défaut
RUN rm -rf /usr/local/tomcat/webapps/*
# Copier ton WAR en ROOT
COPY target/carshare-app.war /usr/local/tomcat/webapps/ROOT.war


# Initialisation de tomcat
RUN cp -R webapps.dist/* webapps/

# Copie du driver JDBC
COPY conf/mysql-connector-j-9.3.0.jar /usr/local/tomcat/lib/

# Copie du fichier context.xml pour activer le JNDI
COPY conf/context.xml /usr/local/tomcat/conf/context.xml

# Copie du fichier tomcat-users.xml pour accéder au manager app
COPY conf/tomcat-users.xml /usr/local/tomcat/conf/tomcat-users.xml

RUN sed -i 's/^\(.*RemoteAddrValve.*\)$/<!-- \1 -->/' /usr/local/tomcat/webapps/manager/META-INF/context.xml
RUN sed -i 's/^\(.*RemoteAddrValve.*\)$/<!-- \1 -->/' /usr/local/tomcat/webapps/host-manager/META-INF/context.xml
