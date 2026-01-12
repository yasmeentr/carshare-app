pipeline {
    agent any

    environment {
        PROJECT_DIR = '.'  // Mettez à jour avec le chemin correct
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout du code à partir de votre dépôt Git
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Construire l'image Docker si nécessaire
                    sh 'docker-compose build'
                }
            }
        }

        stage('Start Containers') {
            steps {
                script {
                    // Démarrer les conteneurs Docker en mode détaché (en arrière-plan)
                    sh 'docker-compose up -d'
                }
            }
        }

        stage('Wait for Containers') {
            steps {
                script {
                    // Attendre que les services soient accessibles (vous pouvez ajuster le temps)
                    sleep 10
                }
            }
        }

        // stage de tests

        stage('Check if App is Accessible') {
            steps {
                script {
                    // Vérifiez que votre application est accessible en localhost
                    // Vous pouvez tester la disponibilité d'un port, comme 8090 pour Tomcat
                    def checkApp = sh(script: 'curl --silent --fail http://localhost:8090', returnStatus: true)
                    if (checkApp != 0) {
                        error "L'application n'est pas accessible sur localhost:8090"
                    } else {
                        echo "L'application est accessible sur localhost:8090"
                    }
                }
            }
        }

    }

   
}
