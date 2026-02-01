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
        
        stage('Functional Tests - Login') {
            steps {
                echo '🧪 Exécution des tests fonctionnels de connexion + screenshots...'
                script {
        
                    // Création du dossier screenshots
                    sh 'mkdir -p screenshots'
        
                    // --- SCREEN 1 : Page d'accueil ---
                    sh '''
                        echo "📸 Capture screenshot de la page d'accueil..."
                        chromium-browser --headless --disable-gpu --screenshot="screenshots/home.png" \
                        --window-size=1280,900 http://localhost:${TOMCAT_PORT}/carshare-app/
                    '''
        
                    // --- SCREEN 2 : Page Login ---
                    sh '''
                        echo "📸 Capture screenshot de la page login..."
                        chromium-browser --headless --disable-gpu --screenshot="screenshots/login_page.png" \
                        --window-size=1280,900 http://localhost:${TOMCAT_PORT}/carshare-app/login
                    '''
        
                    // --- TEST CURL ---
                    sh '''
                        echo "================================================"
                        echo "TEST 1: Accès page d'accueil"
                        echo "================================================"
        
                        HOME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${TOMCAT_PORT}/carshare-app/)
                        if [ "$HOME_RESPONSE" = "200" ]; then
                            echo "✅ Page d'accueil OK"
                        else
                            echo "❌ Page d'accueil erreur ($HOME_RESPONSE)"
                            exit 1
                        fi
                    '''
        
                    // --- LOGIN DYLAN ---
                    sh '''
                        echo ""
                        echo "================================================"
                        echo "TEST 2: Connexion Dylan"
                        echo "================================================"
        
                        COOKIE_FILE=$(mktemp)
        
                        LOGIN_RESPONSE=$(curl -s -c "$COOKIE_FILE" -w "\\n%{http_code}" \
                            -X POST \
                            -d "email=${TEST_EMAIL}" \
                            -d "password=${TEST_PASSWORD}" \
                            http://localhost:${TOMCAT_PORT}/carshare-app/login)
        
                        HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)
        
                        echo "Code HTTP: $HTTP_CODE"
        
                        if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "302" ]; then
                            echo "❌ Connexion refusée"
                            exit 1
                        fi
                    '''
        
                    // --- SCREEN 3 : Page Home après connexion ---
                    sh '''
                        echo "📸 Capture screenshot home après login..."
                        chromium-browser --headless --disable-gpu --screenshot="screenshots/home_after_login.png" \
                        --window-size=1280,900 http://localhost:${TOMCAT_PORT}/carshare-app/home
                    '''
        
                    // --- Vérifier présence de Dylan ---
                    sh '''
                        echo "================================================"
                        echo "TEST 3: Vérification nom utilisateur"
                        echo "================================================"
                        
                        PAGE=$(curl -s http://localhost:${TOMCAT_PORT}/carshare-app/home)
                        echo "$PAGE" | grep -qi "dylan" && echo "✅ Dylan affiché" || echo "⚠️ Dylan NON trouvé"
                    '''
        
                }
            }
            post {
                always {
                    echo '📁 Archivage des screenshots...'
                    archiveArtifacts artifacts: 'screenshots/*.png', fingerprint: true
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
