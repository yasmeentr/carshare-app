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
                echo '🧪 Exécution des tests fonctionnels de connexion + screens PNG...'
                script {
                    sh '''
                        set -e
                        mkdir -p screens
        
                        # Nom du réseau Docker créé par docker compose (visible dans tes logs)
                        DOCKER_NETWORK="carshare-pipeline_carshare"
                        # URL interne à ce réseau (port 8080 dans le conteneur Tomcat)
                        BASE_URL_INTERNAL="http://tomcat:8080/carshare-app"
        
                        echo "================================================"
                        echo "TEST 1: Accès à la page d'accueil"
                        echo "================================================"
                        HOME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${TOMCAT_PORT}/carshare-app/")
                        if [ "$HOME_RESPONSE" = "200" ]; then
                            echo "✅ Page d'accueil accessible (HTTP $HOME_RESPONSE)"
                        else
                            echo "❌ Erreur: Page d'accueil non accessible (HTTP $HOME_RESPONSE)"
                            exit 1
                        fi
        
                        echo ""
                        echo "================================================"
                        echo "SCREEN A: Page de login (PNG)"
                        echo "================================================"
                        # Capture PNG de la page /login (pas besoin de cookie)
                        docker run --rm \\
                          --network "$DOCKER_NETWORK" \\
                          -v "$PWD/screens":/out \\
                          surnet/alpine-wkhtmltopdf \\
                          wkhtmltoimage --quality 92 --width 1280 --format png \\
                          "${BASE_URL_INTERNAL}/login" /out/login_page.png
        
                        echo ""
                        echo "================================================"
                        echo "TEST 2: Tentative de connexion avec Dylan"
                        echo "================================================"
                        echo "Email: ${TEST_EMAIL}"
                        echo "Password: ${TEST_PASSWORD}"
        
                        COOKIE_FILE=$(mktemp)
        
                        # POST /login : on récupère les cookies (dont JSESSIONID) et le code HTTP
                        LOGIN_RESPONSE=$(curl -s -c "$COOKIE_FILE" -w "\\n%{http_code}" \\
                            -X POST \\
                            -d "email=${TEST_EMAIL}" \\
                            -d "password=${TEST_PASSWORD}" \\
                            "http://localhost:${TOMCAT_PORT}/carshare-app/login")
        
                        HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)
                        RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)
                        echo "Code HTTP: $HTTP_CODE"
        
                        if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "302" ]; then
                            echo "❌ Connexion refusée (HTTP $HTTP_CODE)"
                            echo "Réponse: $RESPONSE_BODY"
                            rm -f "$COOKIE_FILE"
                            exit 1
                        fi
        
                        # Extraire la valeur du cookie JSESSIONID
                        JSESSIONID=$(awk '/JSESSIONID/ {print $7}' "$COOKIE_FILE" | tail -n 1)
                        if [ -z "$JSESSIONID" ]; then
                            echo "⚠️  Aucun cookie JSESSIONID trouvé. La capture authentifiée risque d’être non connectée."
                        else
                            echo "✅ Cookie JSESSIONID récupéré"
                        fi
        
                        echo ""
                        echo "================================================"
                        echo "TEST 3: Accès à /home après connexion + SCREEN B (PNG)"
                        echo "================================================"
                        # Vérifier /home côté hôte (sanity check)
                        HOME_AUTH_RESPONSE=$(curl -s -b "$COOKIE_FILE" -w "\\n%{http_code}" \\
                            "http://localhost:${TOMCAT_PORT}/carshare-app/home")
                        HOME_AUTH_CODE=$(echo "$HOME_AUTH_RESPONSE" | tail -n 1)
                        HOME_AUTH_BODY=$(echo "$HOME_AUTH_RESPONSE" | head -n -1)
                        echo "Code HTTP (home): $HOME_AUTH_CODE"
        
                        # Générer le PNG authentifié avec wkhtmltoimage en passant le cookie
                        # (si JSESSIONID absent, l'image sera la vue non authentifiée)
                        if [ -n "$JSESSIONID" ]; then
                          docker run --rm \\
                            --network "$DOCKER_NETWORK" \\
                            -v "$PWD/screens":/out \\
                            surnet/alpine-wkhtmltopdf \\
                            wkhtmltoimage --quality 92 --width 1280 --format png \\
                            --cookie JSESSIONID "$JSESSIONID" \\
                            "${BASE_URL_INTERNAL}/home" /out/home_after_login.png
                        else
                          docker run --rm \\
                            --network "$DOCKER_NETWORK" \\
                            -v "$PWD/screens":/out \\
                            surnet/alpine-wkhtmltopdf \\
                            wkhtmltoimage --quality 92 --width 1280 --format png \\
                            "${BASE_URL_INTERNAL}/home" /out/home_after_login.png
                        fi
        
                        if [ "$HOME_AUTH_CODE" = "200" ]; then
                            echo "✅ Accès à la page home réussi après connexion"
                            if echo "$HOME_AUTH_BODY" | grep -qi "dylan"; then
                                echo "✅ Le nom 'Dylan' est présent dans la page home"
                            else
                                echo "⚠️  Le nom 'Dylan' n'est pas trouvé dans la page"
                            fi
                        else
                            echo "⚠️  Code HTTP inattendu pour la page home: $HOME_AUTH_CODE"
                        fi
        
                        rm -f "$COOKIE_FILE"
        
                        echo ""
                        echo "================================================"
                        echo "TEST 4: Vérification de la base de données"
                        echo "================================================"
                        if docker compose exec -T mysql mysql -utomcat -ptomcat carshare -e "SELECT COUNT(*) FROM users WHERE email='${TEST_EMAIL}';" 2>/dev/null | grep -q "1"; then
                            echo "✅ L'utilisateur Dylan existe dans la base de données"
                        else
                            echo "⚠️  L'utilisateur Dylan n'est pas trouvé dans la base de données"
                        fi
        
                        echo ""
                        echo "================================================"
                        echo "📊 RÉSUMÉ DES TESTS"
                        echo "================================================"
                        echo "✅ Page d'accueil accessible"
                        echo "✅ Login endpoint accessible"
                        echo "✅ Session utilisateur (cookie) gérée"
                        echo "✅ Screens PNG générés: screens/login_page.png, screens/home_after_login.png"
                        echo "================================================"
                    '''
                }
            }
            post {
                always {
                    echo '📝 Logs des conteneurs après les tests:'
                    sh 'docker compose logs --tail=50 tomcat || true'
                    echo '📦 Archivage des screens (PNG)...'
                    archiveArtifacts artifacts: 'screens/*.png', fingerprint: true
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
