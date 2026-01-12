pipeline {
    agent any
    
    environment {
        // Set any environment variables if needed
        PROJECT_DIR = 'carshare-dev'
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout the code from your repository (assuming it's using git)
                checkout scm
            }
        }
        
        stage('Build Docker Image') {
            steps {
                // Build the Docker image if needed
                script {
                    // Assuming Dockerfile is in the root directory
                    sh 'docker build -t carshare-dev .'
                }
            }
        }
        
        stage('Build with Maven') {
            steps {
                // Build the Java project using Maven
                script {
                    sh 'mvn clean install'
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                // Run the tests if applicable
                script {
                    sh 'mvn test'
                }
            }
        }
        
        stage('Deploy') {
            steps {
                // Deploy the application, e.g., using Docker Compose
                script {
                    // Run docker-compose to deploy the application
                    sh 'docker-compose up -d'
                }
            }
        }
        
        stage('Cleanup') {
            steps {
                // Clean up resources after deployment
                script {
                    sh 'docker-compose down'
                }
            }
        }
    }

    post {
        always {
            // Always clean up any resources, e.g., stopping Docker containers
            sh 'docker-compose down'
        }
    }
}
