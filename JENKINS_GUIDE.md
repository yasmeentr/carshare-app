# Guide Complet : Configuration Jenkins pour Carshare App

## 🔍 Problèmes Courants et Solutions

### Problème 1 : Maven ou JDK non trouvé

**Symptômes :**
- `mvn: command not found`
- Erreur de compilation Java

**Solution :**

1. **Installer les outils dans Jenkins**
   - Aller dans `Manage Jenkins` → `Tools`
   - Configurer **Maven** :
     - Name : `Maven 3.9.6` (ou un autre nom, mais le même que dans le Jenkinsfile)
     - Install automatically : ✅
     - Version : 3.9.6 ou plus récente
   
   - Configurer **JDK** :
     - Name : `JDK 21` (ou un autre nom, mais le même que dans le Jenkinsfile)
     - Install automatically : ✅
     - Version : JDK 21 (requis car votre pom.xml utilise Java 21)

2. **Adapter le Jenkinsfile si vous utilisez d'autres noms**
   ```groovy
   tools {
       maven 'VotreNomMaven'
       jdk 'VotreNomJDK'
   }
   ```

---

### Problème 2 : Docker n'est pas accessible

**Symptômes :**
- `docker: command not found`
- `permission denied while trying to connect to the Docker daemon socket`

**Solution :**

1. **Installer Docker sur le serveur Jenkins**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install docker.io docker-compose-plugin
   
   # Démarrer Docker
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

2. **Ajouter l'utilisateur Jenkins au groupe Docker**
   ```bash
   sudo usermod -aG docker jenkins
   sudo systemctl restart jenkins
   ```

3. **Vérifier les permissions**
   ```bash
   # Se connecter en tant que jenkins
   sudo su - jenkins
   docker ps
   ```

---

### Problème 3 : Les ports sont déjà utilisés

**Symptômes :**
- `Error starting userland proxy: listen tcp4 0.0.0.0:8090: bind: address already in use`

**Solution :**

1. **Vérifier les ports occupés**
   ```bash
   sudo lsof -i :8090
   sudo lsof -i :3310
   sudo lsof -i :8091
   ```

2. **Modifier les ports dans docker-compose.yml**
   ```yaml
   ports:
     - "8095:8080"  # Au lieu de 8090:8080
     - "3315:3306"  # Au lieu de 3310:3306
     - "8096:80"    # Au lieu de 8091:80
   ```

3. **Ou arrêter les services qui utilisent ces ports**
   ```bash
   docker compose down -v
   ```

---

### Problème 4 : Le répertoire target/ n'existe pas

**Symptômes :**
- Docker ne trouve pas le WAR
- `ERROR: cannot mount /target/carshare-app`

**Solution :**

Le Jenkinsfile compile et génère le WAR avant le déploiement. Si le problème persiste :

1. **Vérifier que Maven package s'est bien exécuté**
   - Regarder les logs Jenkins
   - Le fichier `target/carshare-app.war` doit exister

2. **Modifier docker-compose.yml pour utiliser le WAR**
   ```yaml
   tomcat:
     volumes:
       - ./target/carshare-app.war:/usr/local/tomcat/webapps/carshare-app.war
   ```

---

### Problème 5 : Workspace permissions

**Symptômes :**
- Permission denied lors de l'écriture dans le workspace

**Solution :**

```bash
# Donner les permissions au workspace Jenkins
sudo chown -R jenkins:jenkins /var/lib/jenkins/workspace/
```

---

## 🚀 Configuration Complète Pas à Pas

### Étape 1 : Créer un nouveau Job Jenkins

1. Aller sur Jenkins Dashboard
2. Cliquer sur `New Item`
3. Choisir `Pipeline`
4. Nommer le projet : `carshare-app-pipeline`
5. Cliquer sur `OK`

### Étape 2 : Configurer le Pipeline

1. Dans la section **Pipeline** :
   - **Definition** : `Pipeline script from SCM`
   - **SCM** : `Git`
   - **Repository URL** : URL de votre dépôt Git
   - **Branches to build** : `*/main` ou `*/master`
   - **Script Path** : `Jenkinsfile`

2. Ou utiliser **Pipeline script** directement :
   - Coller le contenu du Jenkinsfile directement

### Étape 3 : Installer les Plugins Nécessaires

`Manage Jenkins` → `Plugins` → `Available plugins`

Plugins requis :
- ✅ Docker Pipeline
- ✅ Maven Integration
- ✅ Git
- ✅ Pipeline
- ✅ JUnit

### Étape 4 : Configurer les Credentials (si nécessaire)

Si votre dépôt Git est privé :
1. `Manage Jenkins` → `Credentials`
2. Ajouter des credentials Git (username/password ou SSH key)

### Étape 5 : Lancer le Build

1. Cliquer sur `Build Now`
2. Observer les logs dans `Console Output`

---

## 📋 Checklist de Vérification

Avant de lancer le build, vérifiez :

- [ ] Docker est installé sur le serveur Jenkins
- [ ] L'utilisateur jenkins est dans le groupe docker
- [ ] Maven est configuré dans Jenkins Tools
- [ ] JDK 21 est configuré dans Jenkins Tools
- [ ] Les ports 8090, 3310, 8091 sont libres
- [ ] Le Jenkinsfile est à la racine du projet
- [ ] Le fichier pom.xml est présent
- [ ] Le Dockerfile est présent
- [ ] Le docker-compose.yml est présent

---

## 🔧 Jenkinsfile Alternatif (Sans Docker)

Si vous voulez déployer sans Docker Compose dans Jenkins :

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
        
        stage('Build') {
            steps {
                sh 'mvn clean package -DskipTests'
            }
        }
        
        stage('Test') {
            steps {
                sh 'mvn test'
            }
        }
        
        stage('Deploy to Tomcat') {
            steps {
                // Copier le WAR vers un Tomcat externe
                sh 'cp target/carshare-app.war /path/to/tomcat/webapps/'
            }
        }
    }
}
```

---

## 🐛 Debug : Commandes Utiles

```bash
# Voir les logs des conteneurs
docker compose logs -f

# Voir les conteneurs en cours
docker ps

# Entrer dans le conteneur Tomcat
docker compose exec tomcat bash

# Voir les logs Tomcat
docker compose exec tomcat cat /usr/local/tomcat/logs/catalina.out

# Redémarrer les conteneurs
docker compose restart

# Reconstruire les images
docker compose build --no-cache
```

---

## 📝 Variables d'Environnement Jenkins

Vous pouvez ajouter des variables dans Jenkins :

1. `Manage Jenkins` → `Configure System`
2. Section `Global properties`
3. Cocher `Environment variables`
4. Ajouter :
   - `TOMCAT_PORT` = 8090
   - `MYSQL_PORT` = 3310
   - etc.

---

## 🔐 Sécurité

Pour un environnement de production :

1. **Ne pas committer les credentials** dans Git
2. **Utiliser Jenkins Credentials** pour les mots de passe
3. **Changer les mots de passe par défaut** (tomcat/tomcat)
4. **Restreindre l'accès aux ports** avec un firewall

---

## ✅ Test Final

Une fois le pipeline réussi :

1. Ouvrir un navigateur
2. Aller sur `http://votre-serveur-jenkins:8090/carshare-app`
3. Vous devriez voir l'application

---

## 💡 Conseils

1. **Commencer simple** : Testez d'abord le build Maven seul
2. **Logs** : Toujours regarder les logs en cas d'erreur
3. **Permissions** : 90% des problèmes viennent des permissions
4. **Isolation** : Utilisez des ports différents pour éviter les conflits

---

## 📞 Support

Si vous avez encore des problèmes :
1. Vérifiez les logs Jenkins (`Console Output`)
2. Vérifiez les logs Docker (`docker compose logs`)
3. Vérifiez les permissions système
4. Vérifiez que tous les outils sont bien installés

Bonne chance ! 🚀
