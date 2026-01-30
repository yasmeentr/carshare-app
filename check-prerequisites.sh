#!/bin/bash

# Script de vérification des prérequis Jenkins pour Carshare App
# Ce script vérifie que tous les outils nécessaires sont installés

echo "=========================================="
echo "Vérification des prérequis Jenkins"
echo "=========================================="
echo ""

# Couleurs pour l'affichage
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteur d'erreurs
ERRORS=0

# Fonction pour vérifier une commande
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 est installé"
        $1 --version 2>&1 | head -n 1
    else
        echo -e "${RED}✗${NC} $1 n'est PAS installé"
        ((ERRORS++))
    fi
    echo ""
}

# Fonction pour vérifier un port
check_port() {
    PORT=$1
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} Port $PORT est déjà utilisé"
        lsof -Pi :$PORT -sTCP:LISTEN
        ((ERRORS++))
    else
        echo -e "${GREEN}✓${NC} Port $PORT est disponible"
    fi
    echo ""
}

# Vérification Java
echo "1. Vérification de Java..."
check_command java

# Vérification Maven
echo "2. Vérification de Maven..."
check_command mvn

# Vérification Docker
echo "3. Vérification de Docker..."
check_command docker

# Vérification Docker Compose
echo "4. Vérification de Docker Compose..."
if docker compose version &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose est installé"
    docker compose version
else
    echo -e "${RED}✗${NC} Docker Compose n'est PAS installé"
    ((ERRORS++))
fi
echo ""

# Vérification Git
echo "5. Vérification de Git..."
check_command git

# Vérification des permissions Docker pour l'utilisateur courant
echo "6. Vérification des permissions Docker..."
if docker ps &> /dev/null; then
    echo -e "${GREEN}✓${NC} L'utilisateur $(whoami) peut utiliser Docker"
else
    echo -e "${RED}✗${NC} L'utilisateur $(whoami) ne peut PAS utiliser Docker"
    echo "Solution : sudo usermod -aG docker $(whoami)"
    ((ERRORS++))
fi
echo ""

# Vérification des ports nécessaires
echo "7. Vérification des ports..."
check_port 8090
check_port 3310
check_port 8091

# Vérification de l'espace disque
echo "8. Vérification de l'espace disque..."
DISK_SPACE=$(df -h / | awk 'NR==2 {print $4}' | sed 's/G//')
if (( $(echo "$DISK_SPACE > 5" | bc -l) )); then
    echo -e "${GREEN}✓${NC} Espace disque suffisant : ${DISK_SPACE}G disponible"
else
    echo -e "${YELLOW}⚠${NC} Espace disque faible : ${DISK_SPACE}G disponible"
    echo "Il est recommandé d'avoir au moins 5G d'espace libre"
fi
echo ""

# Vérification de la présence des fichiers nécessaires
echo "9. Vérification des fichiers du projet..."
FILES=("pom.xml" "Dockerfile" "docker-compose.yml" "Jenkinsfile")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file existe"
    else
        echo -e "${RED}✗${NC} $file n'existe PAS"
        ((ERRORS++))
    fi
done
echo ""

# Vérification de la version Java requise
echo "10. Vérification de la version Java..."
JAVA_VERSION=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}' | cut -d'.' -f1)
if [ "$JAVA_VERSION" -ge 21 ]; then
    echo -e "${GREEN}✓${NC} Java $JAVA_VERSION est compatible (requis : Java 21+)"
else
    echo -e "${RED}✗${NC} Java $JAVA_VERSION n'est PAS compatible (requis : Java 21+)"
    ((ERRORS++))
fi
echo ""

# Résumé
echo "=========================================="
echo "Résumé de la vérification"
echo "=========================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Tous les prérequis sont satisfaits !${NC}"
    echo "Vous pouvez lancer le pipeline Jenkins."
    exit 0
else
    echo -e "${RED}✗ $ERRORS erreur(s) détectée(s)${NC}"
    echo "Veuillez corriger les erreurs avant de lancer le pipeline Jenkins."
    echo ""
    echo "Aide rapide :"
    echo "- Pour installer Docker : https://docs.docker.com/engine/install/"
    echo "- Pour ajouter l'utilisateur au groupe docker : sudo usermod -aG docker \$USER"
    echo "- Pour installer Maven : sudo apt install maven"
    echo "- Pour installer Java 21 : sudo apt install openjdk-21-jdk"
    exit 1
fi
