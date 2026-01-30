# Configuration Avancée Jenkins pour Carshare App

## 🔐 Utilisation de Credentials Jenkins

Si vous avez besoin de stocker des mots de passe de manière sécurisée :

### 1. Ajouter des Credentials dans Jenkins

1. Aller dans `Manage Jenkins` → `Credentials`
2. Cliquer sur `(global)` → `Add Credentials`
3. Choisir le type :
   - **Username with password** pour Git, Docker Hub, etc.
   - **Secret text** pour des tokens ou clés API
   - **SSH Username with private key** pour Git SSH

### 2. Utiliser les Credentials dans le Jenkinsfile

```groovy
pipeline {
    agent any
    
    environment {
        // Utiliser un credential de type "Username with password"
        DOCKER_HUB = credentials('dockerhub-credentials-id')
    }
    
    stages {
        stage('Docker Login') {
            steps {
                sh 'echo $DOCKER_HUB_PSW | docker login -u $DOCKER_HUB_USR --password-stdin'
            }
        }
        
        stage('Push Image') {
            steps {
                sh 'docker push moncompte/carshare-app:latest'
            }
        }
    }
}
```

---

## 🌍 Déploiement Multi-Environnements

### Jenkinsfile avec paramètres d'environnement

```groovy
pipeline {
    agent any
    
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging', 'production'],
            description: 'Environnement cible'
        )
        booleanParam(
            name: 'SKIP_TESTS',
            defaultValue: false,
            description: 'Ignorer les tests ?'
        )
    }
    
    tools {
        maven 'Maven 3.9.6'
        jdk 'JDK 21'
    }
    
    environment {
        // Variables en fonction de l'environnement
        TOMCAT_PORT = "${params.ENVIRONMENT == 'production' ? '8080' : '8090'}"
        MYSQL_PORT = "${params.ENVIRONMENT == 'production' ? '3306' : '3310'}"
    }
    
    stages {
        stage('Info') {
            steps {
                echo "Déploiement sur l'environnement : ${params.ENVIRONMENT}"
                echo "Port Tomcat : ${TOMCAT_PORT}"
                echo "Tests ignorés : ${params.SKIP_TESTS}"
            }
        }
        
        stage('Build') {
            steps {
                script {
                    if (params.SKIP_TESTS) {
                        sh 'mvn clean package -DskipTests'
                    } else {
                        sh 'mvn clean package'
                    }
                }
            }
        }
        
        stage('Deploy') {
            when {
                expression { params.ENVIRONMENT == 'production' }
            }
            steps {
                echo 'Déploiement en PRODUCTION !'
                // Actions spécifiques à la production
            }
        }
    }
}
```

---

## 📧 Notifications Email

### Configurer les notifications

```groovy
pipeline {
    agent any
    
    tools {
        maven 'Maven 3.9.6'
        jdk 'JDK 21'
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }
    }
    
    post {
        success {
            emailext (
                subject: "✅ Build SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                    <h2>Build réussi !</h2>
                    <p>Job: ${env.JOB_NAME}</p>
                    <p>Build: ${env.BUILD_NUMBER}</p>
                    <p>URL: ${env.BUILD_URL}</p>
                """,
                to: 'votre-email@example.com',
                mimeType: 'text/html'
            )
        }
        failure {
            emailext (
                subject: "❌ Build FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                    <h2>Build échoué !</h2>
                    <p>Job: ${env.JOB_NAME}</p>
                    <p>Build: ${env.BUILD_NUMBER}</p>
                    <p>URL: ${env.BUILD_URL}</p>
                    <p>Logs: ${env.BUILD_URL}console</p>
                """,
                to: 'votre-email@example.com',
                mimeType: 'text/html'
            )
        }
    }
}
```

**Configuration requise :**
1. Installer le plugin `Email Extension`
2. Configurer SMTP dans `Manage Jenkins` → `Configure System` → `E-mail Notification`

---

## 📊 Rapports et Métriques

### Ajouter des rapports de tests et de couverture

```groovy
pipeline {
    agent any
    
    tools {
        maven 'Maven 3.9.6'
        jdk 'JDK 21'
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }
        
        stage('Tests') {
            steps {
                sh 'mvn test'
            }
        }
        
        stage('Code Coverage') {
            steps {
                sh 'mvn jacoco:report'
            }
        }
    }
    
    post {
        always {
            // Publier les résultats de tests
            junit allowEmptyResults: true, testResults: '**/target/surefire-reports/*.xml'
            
            // Publier le rapport de couverture (nécessite le plugin JaCoCo)
            jacoco(
                execPattern: 'target/jacoco.exec',
                classPattern: 'target/classes',
                sourcePattern: 'src/main/java'
            )
            
            // Archiver les artifacts
            archiveArtifacts artifacts: 'target/*.war', fingerprint: true
        }
    }
}
```

---

## 🔄 Déploiement Continu (CD)

### Pipeline avec déploiement automatique

```groovy
pipeline {
    agent any
    
    tools {
        maven 'Maven 3.9.6'
        jdk 'JDK 21'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build & Test') {
            steps {
                sh 'mvn clean package'
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("carshare-app:${env.BUILD_NUMBER}")
                    docker.build("carshare-app:latest")
                }
            }
        }
        
        stage('Push to Registry') {
            when {
                branch 'main'
            }
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'dockerhub-credentials') {
                        docker.image("carshare-app:${env.BUILD_NUMBER}").push()
                        docker.image("carshare-app:latest").push()
                    }
                }
            }
        }
        
        stage('Deploy to Dev') {
            steps {
                sh 'docker compose down -v'
                sh 'docker compose up -d'
            }
        }
        
        stage('Approval for Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Déployer en production ?', ok: 'Déployer'
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                echo 'Déploiement en production...'
                // Commandes pour déployer sur serveur de production
            }
        }
    }
}
```

---

## 🔍 Scan de Sécurité

### Ajouter un scan de vulnérabilités

```groovy
pipeline {
    agent any
    
    tools {
        maven 'Maven 3.9.6'
        jdk 'JDK 21'
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }
        
        stage('Security Scan') {
            steps {
                // Scan des dépendances Maven
                sh 'mvn dependency-check:check'
                
                // Scan de l'image Docker avec Trivy
                sh 'trivy image carshare-app:latest'
            }
        }
    }
    
    post {
        always {
            // Publier le rapport de sécurité
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'target/dependency-check-report',
                reportFiles: 'dependency-check-report.html',
                reportName: 'Security Report'
            ])
        }
    }
}
```

---

## 🎯 Triggers Automatiques

### Déclencher le build automatiquement

```groovy
pipeline {
    agent any
    
    // Déclencheurs
    triggers {
        // Build toutes les nuits à 2h du matin
        cron('0 2 * * *')
        
        // Build dès qu'il y a un push sur Git (nécessite webhook GitHub/GitLab)
        pollSCM('H/5 * * * *')  // Vérifier toutes les 5 minutes
    }
    
    tools {
        maven 'Maven 3.9.6'
        jdk 'JDK 21'
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }
    }
}
```

---

## 📦 Versioning Automatique

### Incrémenter automatiquement la version

```groovy
pipeline {
    agent any
    
    tools {
        maven 'Maven 3.9.6'
        jdk 'JDK 21'
    }
    
    stages {
        stage('Version') {
            steps {
                script {
                    // Lire la version actuelle du pom.xml
                    def pom = readMavenPom file: 'pom.xml'
                    def version = pom.version
                    echo "Version actuelle : ${version}"
                    
                    // Incrémenter la version (exemple simple)
                    def newVersion = version.replace('-SNAPSHOT', ".${env.BUILD_NUMBER}")
                    echo "Nouvelle version : ${newVersion}"
                    
                    // Mettre à jour la version dans pom.xml
                    sh "mvn versions:set -DnewVersion=${newVersion}"
                }
            }
        }
        
        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }
    }
}
```

---

## 🔒 Bonnes Pratiques de Sécurité

1. **Ne jamais committer de mots de passe** dans le code
2. **Utiliser Jenkins Credentials** pour tous les secrets
3. **Scanner les vulnérabilités** régulièrement
4. **Limiter les permissions** des utilisateurs Jenkins
5. **Utiliser HTTPS** pour Jenkins
6. **Mettre à jour Jenkins** régulièrement
7. **Sauvegarder** la configuration Jenkins

---

## 📝 Variables d'Environnement Utiles

```groovy
environment {
    // Variables Jenkins par défaut
    BUILD_NUMBER = "${env.BUILD_NUMBER}"
    BUILD_ID = "${env.BUILD_ID}"
    BUILD_TAG = "${env.BUILD_TAG}"
    JOB_NAME = "${env.JOB_NAME}"
    WORKSPACE = "${env.WORKSPACE}"
    
    // Variables Git
    GIT_BRANCH = "${env.GIT_BRANCH}"
    GIT_COMMIT = "${env.GIT_COMMIT}"
    
    // Variables personnalisées
    APP_NAME = 'carshare-app'
    APP_VERSION = '1.0'
    DEPLOY_ENV = 'production'
}
```

---

## 🎨 Exemple Complet : Pipeline Production-Ready

```groovy
pipeline {
    agent any
    
    parameters {
        choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'production'])
        booleanParam(name: 'SKIP_TESTS', defaultValue: false)
        booleanParam(name: 'DEPLOY', defaultValue: true)
    }
    
    tools {
        maven 'Maven 3.9.6'
        jdk 'JDK 21'
    }
    
    environment {
        APP_NAME = 'carshare-app'
        DOCKER_REGISTRY = credentials('docker-registry')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                script {
                    if (params.SKIP_TESTS) {
                        sh 'mvn clean package -DskipTests'
                    } else {
                        sh 'mvn clean package'
                    }
                }
            }
        }
        
        stage('Tests') {
            when {
                expression { !params.SKIP_TESTS }
            }
            steps {
                sh 'mvn test'
            }
        }
        
        stage('Security Scan') {
            steps {
                sh 'mvn dependency-check:check || true'
            }
        }
        
        stage('Docker Build') {
            steps {
                sh "docker build -t ${APP_NAME}:${BUILD_NUMBER} ."
                sh "docker tag ${APP_NAME}:${BUILD_NUMBER} ${APP_NAME}:latest"
            }
        }
        
        stage('Deploy') {
            when {
                expression { params.DEPLOY }
            }
            steps {
                sh 'docker compose down -v'
                sh 'docker compose up -d'
            }
        }
    }
    
    post {
        always {
            junit allowEmptyResults: true, testResults: '**/target/surefire-reports/*.xml'
            archiveArtifacts artifacts: 'target/*.war', fingerprint: true
            cleanWs()
        }
        success {
            echo '✅ Pipeline réussi !'
        }
        failure {
            echo '❌ Pipeline échoué'
        }
    }
}
```

---

Cette configuration avancée vous permettra de gérer des déploiements complexes avec Jenkins ! 🚀
