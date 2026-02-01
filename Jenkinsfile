pipeline {
    agent any
    
    tools {
        maven 'Maven 3.9.6' // Assurez-vous que ce nom correspond à votre configuration Maven dans Jenkins
        jdk 'JDK 21'        // Assurez-vous que ce nom correspond à votre configuration JDK dans Jenkins
    }
    
    environment {
        // Variables d'environnement Docker
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_IMAGE_NAME = 'carshare-app'
        DOCKER_COMPOSE_VERSION = '2.24.0'
        
        // Variables pour l'application
        TOMCAT_PORT = '8090'
        MYSQL_PORT = '3310'
        PHPMYADMIN_PORT = '8091'
        
        // Credentials de test
        TEST_EMAIL = 'dylan@exemple.com'
        TEST_PASSWORD = 'dylan'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Récupération du code source...'
                checkout scm
            }
        }
        
        stage('Vérification des prérequis') {
            steps {
                script {
                    echo 'Vérification de Maven...'
                    sh 'mvn --version'
                    
                    echo 'Vérification de Java...'
                    sh 'java -version'
                    
                    echo 'Vérification de Docker...'
                    sh 'docker --version'
                    
                    echo 'Vérification de Docker Compose...'
                    sh 'docker compose version'
                }
            }
        }
        
        stage('Clean') {
            steps {
                echo 'Nettoyage du projet...'
                sh 'mvn clean'
            }
        }
        
        stage('Compile') {
            steps {
                echo 'Compilation du projet...'
                sh 'mvn compile'
            }
        }
        
        stage('Test') {
            steps {
                echo 'Exécution des tests...'
                sh 'mvn test'
            }
            post {
                always {
                    // Publication des résultats de tests
                    junit allowEmptyResults: true, testResults: '**/target/surefire-reports/*.xml'
                }
            }
        }
        
        stage('Package') {
            steps {
                echo 'Packaging de l\'application...'
                sh 'mvn package -DskipTests'
            }
            post {
                success {
                    // Archivage du WAR généré
                    archiveArtifacts artifacts: 'target/*.war', fingerprint: true
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo 'Construction de l\'image Docker...'
                script {
                    sh 'docker build -t ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} .'
                    sh 'docker tag ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} ${DOCKER_IMAGE_NAME}:latest'
                }
            }
        }
        
        stage('Stop Previous Containers') {
            steps {
                echo 'Arrêt des conteneurs précédents...'
                script {
                    // Arrêt et suppression des conteneurs existants (ignore les erreurs si rien n'existe)
                    sh 'docker compose down -v || true'
                }
            }
        }
        
        stage('Deploy with Docker Compose') {
            steps {
                echo 'Déploiement avec Docker Compose...'
                script {
                    // Lancement des conteneurs
                    sh 'docker compose up -d --build'
                    
                    // Attendre que les services soient prêts
                    echo 'Attente du démarrage des services...'
                    sh 'sleep 30'
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo 'Vérification de la santé de l\'application...'
                script {
                    // Vérifier que Tomcat répond
                    sh '''
                        for i in {1..30}; do
                            if curl -f http://localhost:${TOMCAT_PORT}/carshare-app/ > /dev/null 2>&1; then
                                echo "✅ Application accessible !"
                                exit 0
                            fi
                            echo "Tentative $i/30..."
                            sleep 2
                        done
                        echo "❌ L'application n'est pas accessible après 60 secondes"
                        exit 1
                    '''
                }
            }
        }
        
        stage('Functional Tests - Register (Selenium)') {
            steps {
                echo '🧪 Exécution des tests Selenium d’inscription (dans un conteneur)...'
                sh '''
                  set -eux
        
                  docker run --rm --network=host \
                    -e WORKSPACE="$WORKSPACE" \
                    -e TOMCAT_PORT="${TOMCAT_PORT}" \
                    -e TEST_EMAIL="${TEST_EMAIL}" \
                    -e TEST_PASSWORD="${TEST_PASSWORD}" \
                    -e BUILD_NUMBER="${BUILD_NUMBER}" \
                    -e CHROME_BIN="/usr/bin/chromium" \
                    -v "$WORKSPACE":"$WORKSPACE" -w "$WORKSPACE" \
                    python:3.12-slim bash -lc '
                      set -eux
                      apt-get update
                      apt-get install -y --no-install-recommends chromium ca-certificates fonts-liberation
                      python -m pip install --upgrade pip
                      pip install selenium
                      python tests/functional_register.py
                    '
                '''
            }
            post {
                always {
                    echo '📝 Logs des conteneurs après les tests (register):'
                    sh 'docker compose logs --tail=50 tomcat || true'
        
                    archiveArtifacts artifacts: 'screenshots/register/*.png, functional_register_report.txt', allowEmptyArchive: true
                }
            }
        }

        
        stage('API Health Check') {
            steps {
                echo '🔍 Vérification des endpoints de l\'application...'
                script {
                    sh '''
                        echo "Endpoints disponibles:"
                        echo "- Page d'accueil: http://localhost:${TOMCAT_PORT}/carshare-app/"
                        echo "- Login: http://localhost:${TOMCAT_PORT}/carshare-app/login"
                        echo "- Register: http://localhost:${TOMCAT_PORT}/carshare-app/register"
                        echo "- PHPMyAdmin: http://localhost:${PHPMYADMIN_PORT}"
                        
                        # Tester quelques endpoints basiques
                        curl -s -o /dev/null -w "Login page: %{http_code}\\n" \
                            http://localhost:${TOMCAT_PORT}/carshare-app/login
                        
                        curl -s -o /dev/null -w "Register page: %{http_code}\\n" \
                            http://localhost:${TOMCAT_PORT}/carshare-app/register
                    '''
                }
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline terminé'
            // Nettoyage des images Docker non utilisées
            sh 'docker image prune -f || true'
        }
        success {
            echo '✅ Build et déploiement réussis !'
            echo "Application disponible sur : http://localhost:${TOMCAT_PORT}/carshare-app"
            echo "PHPMyAdmin disponible sur : http://localhost:${PHPMYADMIN_PORT}"
            echo ""
            echo "🧪 Tests de connexion réussis avec:"
            echo "   Email: ${TEST_EMAIL}"
            echo "   Password: ${TEST_PASSWORD}"
        }
        failure {
            echo '❌ Build ou déploiement échoué'
            // Afficher les logs en cas d'échec
            sh 'docker compose logs || true'
        }
    }
}
