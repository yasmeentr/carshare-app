pipeline {
    agent any

    environment {
        PROJECT_DIR = '/path/to/your/project'  // Mettez à jour avec le chemin correct
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
                    // Vous pouvez tester la disponibilité d'un port, comme 8080 pour Tomcat
                    def checkApp = sh(script: 'curl --silent --fail http://localhost:8080', returnStatus: true)
                    if (checkApp != 0) {
                        error "L'application n'est pas accessible sur localhost:8080"
                    } else {
                        echo "L'application est accessible sur localhost:8080"
                    }
                }
            }
        }

        stage('Cleanup') {
            steps {
                script {
                    // Arrêter et supprimer les conteneurs Docker après le test
                    sh 'docker-compose down'
                }
            }
        }
    }

    post {
        always {
            // Nettoyage final, garantir que les conteneurs sont toujours arrêtés
            sh 'docker-compose down'
        }
    }
}
