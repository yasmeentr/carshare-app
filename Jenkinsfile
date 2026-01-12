
pipeline {
  agent any

  options {
    timeout(time: 30, unit: 'MINUTES')
    disableConcurrentBuilds()
  }

  environment {
    APP_NAME             = "carshare-app"
    // Eviter l'interpolation au moment du parse: mettre une chaîne simple ici
    WAR_PATH             = "target/carshare-app.war"
    TOMCAT_WEBAPPS       = "/var/lib/tomcat10/webapps"
    // false => http://localhost:8090/carshare-app/ ; true => http://localhost:8090/
    DEPLOY_AS_ROOT       = "false"
    COMPOSE_FILE         = "docker-compose.yml"
    COMPOSE_PROJECT_NAME = "carshare"
    GIT_URL              = "https://github.com/yasmeentr/carshare-app.git"
    GIT_BRANCH           = "main"
  }

  stages {
    stage("Checkout") {
      steps {
        git branch: env.GIT_BRANCH, url: env.GIT_URL
      }
    }

    stage("Build WAR") {
      steps {
        sh """
          set -e
          mvn -B clean install -DskipTests
          ls -l target || true
        """
      }
      post {
        success {
          archiveArtifacts artifacts: "${env.WAR_PATH}", fingerprint: true
        }
      }
    }

    

    stage("Docker Compose DOWN") {
      steps {
        sh """
          set -e
          # Attention: -v --rmi all supprime volumes et images (destructif et lent)
          sudo docker compose -p ${env.COMPOSE_PROJECT_NAME} -f ${env.COMPOSE_FILE} down -v --rmi all || true
        """
      }
    }

    stage("Docker Compose UP") {
      steps {
        sh """
          set -e
          sudo docker compose -p ${env.COMPOSE_PROJECT_NAME} -f ${env.COMPOSE_FILE} up -d --build
        """
      }
    }
  }

  post {
    success {
      echo "Déploiement OK !"
      echo "URL : http://localhost:8090/${env.DEPLOY_AS_ROOT == 'true' ? '' : env.APP_NAME + '/'}"
    }
       failure {
      echo "Échec du pipeline."
    }
  }
}
