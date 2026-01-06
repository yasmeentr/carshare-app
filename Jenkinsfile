
pipeline {
  agent any

  options {
    timeout(time: 30, unit: 'MINUTES')
    disableConcurrentBuilds()
  }

  environment {
    APP_NAME             = "carshare-app"
    WAR_PATH             = "target/${APP_NAME}.war"

    // Chemin Tomcat natif (Debian/Ubuntu)
    TOMCAT_WEBAPPS       = "/var/lib/tomcat10/webapps"

    // False => http://localhost:8090/carshare-app/
    // True  => http://localhost:8090/
    DEPLOY_AS_ROOT       = "false"

    COMPOSE_FILE         = "docker-compose.yml"
    COMPOSE_PROJECT_NAME = "carshare"
  }

  tools {
    maven "Maven-3.9"
  }

  stages {
    stage('Checkout') {
      steps {
        git branch: 'main', url: 'https://github.com/yasmeentr/carshare-app.git'
      }
    }

    stage('Build WAR (Maven)') {
      steps {
        sh '''
          set -e
          mvn -B clean install -DskipTests
          ls -l target || true
        '''
      }
      post {
        success {
          archiveArtifacts artifacts: "${WAR_PATH}", fingerprint: true
        }
      }
    }

    stage('Copie du WAR vers Tomcat (host)') {
      steps {
        script {
          def targetName = (env.DEPLOY_AS_ROOT == "true") ? "ROOT.war" : "${env.APP_NAME}.war"
          sh """
            set -e
            test -f ${WAR_PATH}
            sudo rm -f ${TOMCAT_WEBAPPS}/${targetName} || true
            sudo cp ${WAR_PATH} ${TOMCAT_WEBAPPS}/${targetName}
          """
        }
      }
    }

    stage('Restart Tomcat') {
      steps {
        sh '''
          set -e
          if systemctl status tomcat10 >/dev/null 2>&1; then
            sudo systemctl restart tomcat10
          else
            echo "Tomcat10 non détecté, étape ignorée."
          fi
        '''
      }
    }

    stage('Docker Compose DOWN') {
      steps {
        sh """
          set -e
          # Attention: -v --rmi all supprime volumes et images (lent et destructif)
          sudo docker compose -p ${COMPOSE_PROJECT_NAME} -f ${COMPOSE_FILE} down -v --rmi all || true
        """
      }
    }

    stage('Docker Compose UP') {
      steps {
        sh """
          set -e
          sudo docker compose -p ${COMPOSE_PROJECT_NAME} -f ${COMPOSE_FILE} up -d --build
        """
      }
    }
  }

  post {
    success {
      echo "✅ Déploiement terminé."
      echo "URL : http://localhost:8090/${env.DEPLOY_AS_ROOT == 'true' ? '' : env.APP_NAME + '/'}"
    }
       failure {
      echo "❌ Échec du pipeline."
    }
  }
