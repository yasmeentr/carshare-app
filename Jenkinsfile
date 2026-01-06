
pipeline {
  agent any

  environment {
    APP_NAME = "carshare-app"
    WAR_PATH = "target/${APP_NAME}.war"

    // Tomcat natif (host)
    TOMCAT_WEBAPPS = "/var/lib/tomcat10/webapps"

    // False => http://localhost:8090/carshare-app/
    // True  => http://localhost:8090/
    DEPLOY_AS_ROOT = "false"

    COMPOSE_FILE = "docker-compose.yml"
    COMPOSE_PROJECT_NAME = "carshare"
  }

  tools {
    maven "Maven-3.9"
  }

  stages {

    stage("Checkout") {
      steps {
        git branch: 'main', url: 'https://github.com/yasmeentr/carshare-app.git'
      }
    }

    stage("Build WAR") {
      steps {
        sh """
          mvn clean install -DskipTests
          ls -l target
        """
      }
      post {
        success {
          archiveArtifacts artifacts: "${WAR_PATH}", fingerprint: true
        }
      }
    }

    stage("Copy WAR into Tomcat native") {
      steps {
        script {
          def targetName = (DEPLOY_AS_ROOT == "true") ? "ROOT.war" : "${APP_NAME}.war"

          sh """
            sudo rm -f ${TOMCAT_WEBAPPS}/${targetName} || true
            sudo cp ${WAR_PATH} ${TOMCAT_WEBAPPS}/${targetName}
          """
        }
      }
    }

    stage("Restart Tomcat") {
      steps {
        sh """
          sudo systemctl restart tomcat10
        """
      }
    }

    stage("Docker Compose DOWN") {
      steps {
        sh """
          sudo docker compose -p ${COMPOSE_PROJECT_NAME} -f ${COMPOSE_FILE} down -v --rmi all || true
        """
      }
    }

    stage("Docker Compose UP") {
      steps {
        sh """
          sudo docker compose -p ${COMPOSE_PROJECT_NAME} -f ${COMPOSE_FILE} up -d --build
        """
      }
    }
  }

  post {
    success {
      echo "Déploiement OK !"
      echo "URL : http://localhost:8090/${DEPLOY_AS_ROOT == 'true' ? '' : APP_NAME + '/'}"
    }
   }
