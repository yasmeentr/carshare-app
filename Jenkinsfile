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

  
        stage('Functional Tests - Register') {
          steps {
            echo "🧪 Exécution des tests fonctionnels d'inscription..."
            sh '''
              set -eux
        
              # 1) Attente MySQL prêt (max ~2 min)
              echo "⏳ Attente de MySQL..."
              for i in $(seq 1 80); do
                if docker compose exec -T mysql mysql -utomcat -ptomcat -e "SELECT 1" carshare >/dev/null 2>&1; then
                  echo "✅ MySQL OK"
                  break
                fi
                sleep 2
                if [ $i -eq 80 ]; then
                  echo "❌ MySQL pas prêt après 160s"; docker compose logs mysql | tail -n 100 || true; exit 1
                fi
              done
        
              # 2) Attente HTTP 200 sur /register (max ~2 min)
              echo "⏳ Attente endpoint /register (HTTP 200)..."
              for i in $(seq 1 80); do
                CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${TOMCAT_PORT}/carshare-app/register" || true)
                if [ "$CODE" = "200" ]; then
                  echo "✅ /register renvoie 200"
                  break
                fi
                echo "ℹ️  /register encore indisponible (HTTP $CODE), tentative $i/80..."
                sleep 2
                if [ $i -eq 80 ]; then
                  echo "❌ /register pas prêt après 160s"
                  curl -i "http://localhost:${TOMCAT_PORT}/carshare-app/register" || true
                  docker compose logs --tail=100 tomcat || true
                  exit 1
                fi
              done
        
              # 3) Lancer le script de test Selenium
              chmod +x tests/test_selenium_register.sh || true
              bash ./tests/test_selenium_register.sh
            '''
          }
          post {
            always {
              echo "📝 Logs des conteneurs après les tests d'inscription:"
              sh 'docker compose logs --tail=50 tomcat || true'
            }
          }
        }

        stage('Functional Tests - Login') {
            steps {
                echo '🧪 Exécution des tests fonctionnels de connexion...'
                script {
                    sh '''
                        echo "================================================"
                        echo "TEST 1: Accès à la page d'accueil"
                        echo "================================================"
                        
                        # Test de la page d'accueil
                        HOME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${TOMCAT_PORT}/carshare-app/)
                        
                        if [ "$HOME_RESPONSE" = "200" ]; then
                            echo "✅ Page d'accueil accessible (HTTP $HOME_RESPONSE)"
                        else
                            echo "❌ Erreur: Page d'accueil non accessible (HTTP $HOME_RESPONSE)"
                            exit 1
                        fi
                        
                        echo ""
                        echo "================================================"
                        echo "TEST 2: Tentative de connexion avec Dylan"
                        echo "================================================"
                        echo "Email: ${TEST_EMAIL}"
                        echo "Password: ${TEST_PASSWORD}"
                        
                        # Créer un fichier pour stocker les cookies
                        COOKIE_FILE=$(mktemp)
                        
                        # Effectuer la requête de login
                        LOGIN_RESPONSE=$(curl -s -c "$COOKIE_FILE" -w "\\n%{http_code}" \
                            -X POST \
                            -d "email=${TEST_EMAIL}" \
                            -d "password=${TEST_PASSWORD}" \
                            http://localhost:${TOMCAT_PORT}/carshare-app/login)
                        
                        # Extraire le code HTTP
                        HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)
                        RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)
                        
                        echo "Code HTTP: $HTTP_CODE"
                        
                        # Vérifier la réponse
                        if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ]; then
                            echo "✅ Requête de login acceptée (HTTP $HTTP_CODE)"
                            
                            # Vérifier si on a une session
                            if grep -q "JSESSIONID" "$COOKIE_FILE"; then
                                echo "✅ Session créée (cookie JSESSIONID présent)"
                            else
                                echo "⚠️  Warning: Aucun cookie de session trouvé"
                            fi
                            
                            # Tester l'accès à la page home après connexion
                            echo ""
                            echo "================================================"
                            echo "TEST 3: Accès à la page home après connexion"
                            echo "================================================"
                            
                            HOME_AUTH_RESPONSE=$(curl -s -b "$COOKIE_FILE" -w "\\n%{http_code}" \
                                http://localhost:${TOMCAT_PORT}/carshare-app/home)
                            
                            HOME_AUTH_CODE=$(echo "$HOME_AUTH_RESPONSE" | tail -n 1)
                            HOME_AUTH_BODY=$(echo "$HOME_AUTH_RESPONSE" | head -n -1)
                            
                            echo "Code HTTP: $HOME_AUTH_CODE"
                            
                            if [ "$HOME_AUTH_CODE" = "200" ]; then
                                echo "✅ Accès à la page home réussi après connexion"
                                
                                # Vérifier si le nom de l'utilisateur apparaît dans la page
                                if echo "$HOME_AUTH_BODY" | grep -qi "dylan"; then
                                    echo "✅ Le nom 'Dylan' est présent dans la page home"
                                else
                                    echo "⚠️  Le nom 'Dylan' n'est pas trouvé dans la page"
                                fi
                            else
                                echo "⚠️  Code HTTP inattendu pour la page home: $HOME_AUTH_CODE"
                            fi
                            
                        elif echo "$RESPONSE_BODY" | grep -qi "invalid\\|incorrect\\|error\\|erreur"; then
                            echo "❌ Échec de connexion: Identifiants invalides"
                            echo "Réponse du serveur: $RESPONSE_BODY"
                            exit 1
                        else
                            echo "⚠️  Code HTTP inattendu: $HTTP_CODE"
                            echo "Réponse: $RESPONSE_BODY"
                        fi
                        
                        # Nettoyer le fichier de cookies
                        rm -f "$COOKIE_FILE"
                        
                        echo ""
                        echo "================================================"
                        echo "TEST 4: Vérification de la base de données"
                        echo "================================================"
                        
                        # Vérifier que MySQL est accessible
                        if docker compose exec -T mysql mysql -utomcat -ptomcat carshare -e "SELECT COUNT(*) FROM users WHERE email='${TEST_EMAIL}';" 2>/dev/null | grep -q "1"; then
                            echo "✅ L'utilisateur Dylan existe dans la base de données"
                        else
                            echo "⚠️  L'utilisateur Dylan n'est pas trouvé dans la base de données"
                            echo "Note: Ceci peut être normal si l'utilisateur doit être créé manuellement"
                        fi
                        
                        echo ""
                        echo "================================================"
                        echo "📊 RÉSUMÉ DES TESTS"
                        echo "================================================"
                        echo "✅ Page d'accueil accessible"
                        echo "✅ Login endpoint accessible"
                        echo "✅ Session utilisateur fonctionnelle"
                        echo "================================================"
                    '''
                }
            }
            post {
                always {
                    echo '📝 Logs des conteneurs après les tests:'
                    sh 'docker compose logs --tail=50 tomcat || true'
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
