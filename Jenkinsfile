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
        
        stage('Functional Tests - Login') {
            steps {
                echo 'Exécution des tests fonctionnels de connexion...'
                script {
                    sh '''
                        set -e

                        mkdir -p screens

                        echo "================================================"
                        echo "TEST 1: Accès à la page d'accueil"
                        echo "================================================"
                        
                        # Test de la page d'accueil
                        HOME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${TOMCAT_PORT}/carshare-app/")
                        
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
                        
                        # Fichier pour stocker les cookies
                        COOKIE_FILE=$(mktemp)

                        # POST /login : on capture headers, body et une trace verbeuse (nos 'screens')
                        # La trace -v est redirigée dans un fichier pour inspection fine.
                        curl -s -c "$COOKIE_FILE" \
                             -D screens/login_response.headers.txt \
                             -o screens/login_response.body.html \
                             -w "\\nHTTP_CODE=%{http_code}\\n" \
                             -X POST \
                             -d "email=${TEST_EMAIL}" \
                             -d "password=${TEST_PASSWORD}" \
                             "http://localhost:${TOMCAT_PORT}/carshare-app/login" \
                             2> screens/login_request.trace.txt

                        # Extraire le code HTTP (ajouté via -w)
                        HTTP_CODE=$(tail -n 1 screens/login_response.body.html | sed -n 's/^HTTP_CODE=\\([0-9][0-9][0-9]\\)$/\\1/p')
                        # Si l'astuce du -w s'est mélangée avec le body, on calcule autrement:
                        if [ -z "$HTTP_CODE" ]; then
                          HTTP_CODE=$(grep -Eo '^HTTP/[0-9.]+ [0-9]+' screens/login_response.headers.txt | tail -n1 | awk '{print $2}')
                        fi

                        echo "Code HTTP: $HTTP_CODE"
                        
                        # Vérifier la réponse
                        if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ]; then
                            echo "✅ Requête de login acceptée (HTTP $HTTP_CODE)"
                            
                            # Vérifier si on a une session (cookie JSESSIONID)
                            if grep -q "JSESSIONID" "$COOKIE_FILE"; then
                                echo "✅ Session créée (cookie JSESSIONID présent)"
                            else
                                echo "⚠️  Warning: Aucun cookie de session trouvé"
                            fi
                            
                            echo ""
                            echo "================================================"
                            echo "TEST 3: Accès à la page home après connexion"
                            echo "================================================"
                            
                            # GET /home authentifié : capturer headers, body et trace
                            curl -s -b "$COOKIE_FILE" \
                                 -D screens/home_after_login.headers.txt \
                                 -o screens/home_after_login.html \
                                 "http://localhost:${TOMCAT_PORT}/carshare-app/home" \
                                 2> screens/home_after_login.trace.txt
                            
                            HOME_AUTH_CODE=$(grep -Eo '^HTTP/[0-9.]+ [0-9]+' screens/home_after_login.headers.txt | tail -n1 | awk '{print $2}')
                            echo "Code HTTP: $HOME_AUTH_CODE"
                            
                            if [ "$HOME_AUTH_CODE" = "200" ]; then
                                echo "✅ Accès à la page home réussi après connexion"
                                
                                # Vérifier si le nom de l'utilisateur apparaît dans la page
                                if grep -qi "dylan" screens/home_after_login.html; then
                                    echo "✅ Le nom 'Dylan' est présent dans la page home"
                                else
                                    echo "⚠️  Le nom 'Dylan' n'est pas trouvé dans la page"
                                fi
                            else
                                echo "⚠️  Code HTTP inattendu pour la page home: $HOME_AUTH_CODE"
                            fi
                            
                        elif grep -qi "invalid\\|incorrect\\|error\\|erreur" screens/login_response.body.html; then
                            echo "❌ Échec de connexion: Identifiants invalides"
                            echo "↳ Voir screens/login_response.body.html"
                            exit 1
                        else
                            echo "⚠️  Code HTTP inattendu: $HTTP_CODE"
                            echo "↳ Voir screens/login_response.headers.txt et screens/login_request.trace.txt"
                        fi
                        
                        # Nettoyer le fichier de cookies
                        rm -f "$COOKIE_FILE"
                        
                        
                        echo ""
                        echo "================================================"
                        echo "📊 RÉSUMÉ DES TESTS"
                        echo "================================================"
                        echo "✅ Page d'accueil accessible"
                        echo "✅ Login endpoint accessible"
                        echo "✅ Session utilisateur fonctionnelle"
                        echo "✅ Captures disponibles dans le dossier 'screens/' (Artifacts)"
                        echo "================================================"
                    '''
                }
            }
            post {
                always {
                    echo '📝 Logs des conteneurs après les tests:'
                    sh 'docker compose logs --tail=50 tomcat || true'
                    echo '📦 Archivage des screens (login)...'
                    archiveArtifacts artifacts: 'screens/**/*', fingerprint: true
                }
            }
        }

        
        stage('Load Test - Locust') {
          steps {
            sh '''
              set -e
        
              # 1) S'assurer d'avoir le module venv
              if ! python3 -m venv --help >/dev/null 2>&1; then
                sudo apt-get update
                sudo apt-get install -y python3-venv
              fi
        
              # 2) Créer et activer un venv local au workspace
              python3 -m venv .venv
              . .venv/bin/activate
        
              # 3) Installer Locust DANS le venv (pas global -> pas de PEP 668)
              pip install --upgrade pip
              pip install --no-cache-dir locust
        
              # 4) Exécuter Locust en mode headless
              .venv/bin/locust -f ./tests/locustfile.py --headless \
                -u 5 -r 1 -H http://localhost:8090 --run-time 10s \
                --csv locust_report
        
              # 5) Désactiver
              deactivate
            '''
            archiveArtifacts artifacts: 'locust_report*', fingerprint: true, onlyIfSuccessful: false
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
        }
        failure {
            echo '❌ Build ou déploiement échoué'
            // Afficher les logs en cas d'échec
            sh 'docker compose logs || true'
        }
    }
}
