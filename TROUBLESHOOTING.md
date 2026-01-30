# 🚨 Problèmes Courants Jenkins - Solutions Rapides

## 1. "mvn: command not found"

### Cause
Maven n'est pas installé ou pas configuré dans Jenkins.

### Solution
**Dans Jenkins :**
1. `Manage Jenkins` → `Tools`
2. Section `Maven installations`
3. Cliquer sur `Add Maven`
4. Nom : `Maven 3.9.6` (utilisez exactement ce nom dans le Jenkinsfile)
5. ✅ Cocher `Install automatically`
6. Choisir une version (3.9.6 recommandée)
7. Sauvegarder

**OU installer Maven sur le serveur :**
```bash
sudo apt update
sudo apt install maven -y
```

---

## 2. "Java version mismatch" ou erreur de compilation

### Cause
Mauvaise version de Java ou JDK non configuré.

### Solution
**Dans Jenkins :**
1. `Manage Jenkins` → `Tools`
2. Section `JDK installations`
3. Cliquer sur `Add JDK`
4. Nom : `JDK 21` (utilisez exactement ce nom dans le Jenkinsfile)
5. ✅ Cocher `Install automatically`
6. Choisir Java 21
7. Sauvegarder

**OU installer Java 21 sur le serveur :**
```bash
sudo apt install openjdk-21-jdk -y
```

---

## 3. "docker: command not found"

### Cause
Docker n'est pas installé sur le serveur Jenkins.

### Solution
```bash
# Installer Docker
sudo apt update
sudo apt install docker.io docker-compose-plugin -y

# Démarrer Docker
sudo systemctl start docker
sudo systemctl enable docker

# Ajouter jenkins au groupe docker
sudo usermod -aG docker jenkins

# Redémarrer Jenkins
sudo systemctl restart jenkins

# Vérifier
sudo su - jenkins -s /bin/bash
docker ps
```

---

## 4. "Permission denied" avec Docker

### Cause
L'utilisateur Jenkins n'a pas les permissions Docker.

### Solution
```bash
# Ajouter jenkins au groupe docker
sudo usermod -aG docker jenkins

# Appliquer les changements
sudo systemctl restart jenkins

# OU redémarrer le serveur
sudo reboot
```

---

## 5. "Port already in use" (8090, 3310, 8091)

### Cause
Un autre service utilise ces ports.

### Solution A - Libérer les ports
```bash
# Voir ce qui utilise le port
sudo lsof -i :8090
sudo lsof -i :3310
sudo lsof -i :8091

# Arrêter les anciens conteneurs
docker compose down -v
```

### Solution B - Changer les ports
Modifier `docker-compose.yml` :
```yaml
services:
  tomcat:
    ports:
      - "8095:8080"  # Changez 8090 en 8095
  mysql:
    ports:
      - "3315:3306"  # Changez 3310 en 3315
  phpmyadmin:
    ports:
      - "8096:80"    # Changez 8091 en 8096
```

---

## 6. "target directory not found" ou "No such file or directory"

### Cause
Le build Maven n'a pas réussi ou le workspace n'est pas bon.

### Solution
1. Vérifier que l'étape Maven s'exécute avec succès dans Jenkins
2. Regarder les logs Jenkins pour voir où le WAR est généré
3. Si nécessaire, modifier le Jenkinsfile :
```groovy
stage('Verify WAR') {
    steps {
        sh 'ls -la target/'
        sh 'ls -la target/carshare-app.war'
    }
}
```

---

## 7. Échec du Health Check

### Cause
L'application ne démarre pas correctement.

### Solution
```bash
# Voir les logs Tomcat
docker compose logs tomcat

# Voir les logs MySQL
docker compose logs mysql

# Entrer dans le conteneur pour débugger
docker compose exec tomcat bash
cd /usr/local/tomcat/logs
cat catalina.out
```

---

## 8. "Workspace permission denied"

### Cause
Jenkins n'a pas les permissions d'écriture.

### Solution
```bash
# Donner les permissions au workspace
sudo chown -R jenkins:jenkins /var/lib/jenkins/workspace/

# Ou pour un projet spécifique
sudo chown -R jenkins:jenkins /var/lib/jenkins/workspace/carshare-app-pipeline/
```

---

## 9. Jenkins ne trouve pas le Jenkinsfile

### Cause
Le fichier n'est pas à la racine ou mal nommé.

### Solution
1. Vérifier que le fichier s'appelle exactement `Jenkinsfile` (avec J majuscule)
2. Vérifier qu'il est à la racine du dépôt Git
3. Dans la config Jenkins, vérifier que "Script Path" = `Jenkinsfile`

---

## 10. Problèmes de connexion à la base de données

### Cause
MySQL n'est pas prêt ou problème de configuration.

### Solution
1. Augmenter le temps d'attente dans le Jenkinsfile :
```groovy
stage('Wait for MySQL') {
    steps {
        sh 'sleep 60'  // Augmenter à 60 secondes
    }
}
```

2. Vérifier les credentials MySQL dans `conf/context.xml`
3. Vérifier que MySQL est accessible :
```bash
docker compose exec mysql mysql -utomcat -ptomcat -e "SHOW DATABASES;"
```

---

## 🔍 Commandes de Debug Utiles

```bash
# Voir l'état des conteneurs
docker ps -a

# Voir les logs en temps réel
docker compose logs -f

# Entrer dans un conteneur
docker compose exec tomcat bash
docker compose exec mysql bash

# Redémarrer tout
docker compose restart

# Supprimer et recréer tout
docker compose down -v
docker compose up -d --build

# Voir les images Docker
docker images

# Nettoyer les images non utilisées
docker image prune -a

# Voir l'utilisation du disque
docker system df
```

---

## 📝 Checklist Avant de Lancer Jenkins

- [ ] Docker installé et fonctionnel
- [ ] Jenkins peut utiliser Docker (permissions)
- [ ] Maven configuré dans Jenkins Tools
- [ ] JDK 21 configuré dans Jenkins Tools
- [ ] Ports 8090, 3310, 8091 disponibles
- [ ] Jenkinsfile présent à la racine
- [ ] Git configuré (si dépôt privé : credentials ajoutés)

---

## 🆘 Toujours pas résolu ?

1. **Exécutez le script de vérification :**
   ```bash
   cd /chemin/vers/carshare-app
   ./check-prerequisites.sh
   ```

2. **Regardez les logs Jenkins :**
   - Dans Jenkins, cliquez sur le build échoué
   - Cliquez sur `Console Output`
   - Cherchez les messages d'erreur en rouge

3. **Testez en local d'abord :**
   ```bash
   # Test Maven
   mvn clean package -DskipTests
   
   # Test Docker
   docker compose up -d --build
   ```

4. **Commencez avec le Jenkinsfile simple :**
   - Renommez `Jenkinsfile` en `Jenkinsfile.full`
   - Renommez `Jenkinsfile.simple` en `Jenkinsfile`
   - Lancez un build pour tester juste Maven
   - Une fois que ça marche, repassez au Jenkinsfile complet

---

## 💡 Astuce Finale

90% des problèmes Jenkins viennent de :
1. **Permissions** (docker, workspace)
2. **Outils non configurés** (Maven, JDK)
3. **Ports occupés**

Vérifiez ces trois points en premier ! 🎯
