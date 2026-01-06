
pipeline {
  agent any

  options {
    timeout(time: 30, unit: 'MINUTES')
    disableConcurrentBuilds()
  }

  tools {
    maven "Maven-3.9"
  }

  environment {
    APP_NAME             = "carshare-app"
    // Evite l'interpolation dans environment: on met une chaîne simple
    WAR_PATH             = "target/carshare-app.war"
    // Tomcat natif (host)
    TOMCAT_WEBAPPS       = "/var/lib/tomcat10/webapps"

    // False => http://localhost:8090/carshare-app/
    // True  => http://localhost:8090/
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

    stage("Copy WAR into Tomcat native") {
      steps {
        script {
          // En bloc script, utilise env.VAR
          def targetName = (env.DEPLOY_AS_ROOT == "true") ? "ROOT.war" : "${env.APP_NAME}.war"
          sh """
            set -e
            test -f ${env.WAR_PATH}
            sudo rm -f ${env.TOMCAT_WEBAPPS}/${targetName} || true
            sudo cp ${env.WAR_PATH} ${env.TOMCAT_WEBAPPS}/${targetName}
          """
        }
      }
    }

    stage("Restart Tomcat") {
      steps {
        sh """
          set -e
          if systemctl status tomcat10 >/dev/null 2>&1; then
            sudo systemctl restart tomcat10
          else
            echo 'Service tomcat10 absent - étape ignorée.'
          fi
        """
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
