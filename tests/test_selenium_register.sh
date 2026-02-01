#!/bin/bash

# Script de test d'inscription pour l'application CarShare
# Ce script teste le processus d'inscription avec différents scénarios

echo "================================================"
echo "🧪 TESTS D'INSCRIPTION - CarShare App"
echo "================================================"
echo ""

# Récupération des variables d'environnement (définies par Jenkins)
TOMCAT_PORT=${TOMCAT_PORT:-8090}
BASE_URL="http://localhost:${TOMCAT_PORT}/carshare-app"
REGISTER_URL="${BASE_URL}/register"

# Générer un timestamp pour des utilisateurs uniques
TIMESTAMP=$(date +%s)
TEST_USERNAME="testuser_${TIMESTAMP}"
TEST_EMAIL="testuser_${TIMESTAMP}@test.com"
TEST_PASSWORD="TestPassword123!"

# Compteurs de tests
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Fonction pour afficher les résultats de test
test_result() {
    local test_name=$1
    local result=$2
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$result" -eq 0 ]; then
        echo "✅ PASS: $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "❌ FAIL: $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# ================================================
# TEST 1: Accès à la page d'inscription
# ================================================
############################################################
# TEST 1: Accès à la page d'inscription (attente 200)
############################################################
echo "================================================"
echo "TEST 1: Accès à la page d'inscription"
echo "================================================"

BASE="http://localhost:8090/carshare-app"
REGISTER_URL="$BASE/register"

max_tries=40   # ~80s
ok=0
for i in $(seq 1 $max_tries); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$REGISTER_URL" || true)
  if [ "$CODE" = "200" ]; then
    echo "✅ /register accessible (HTTP 200)"
    ok=1
    break
  fi
  echo "⏳ /register non prêt (HTTP $CODE) - tentative $i/$max_tries..."
  sleep 2
done

if [ "$ok" -ne 1 ]; then
  echo "❌ FAIL: /register ne renvoie pas 200 après attente"
  echo "----- Réponse actuelle -----"
  curl -i "$REGISTER_URL" || true
  exit 1
fi

# ================================================
# TEST 2: Inscription avec tous les champs vides
# ================================================
echo "================================================"
echo "TEST 2: Inscription avec champs vides"
echo "================================================"

EMPTY_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -d "username=" \
    -d "email=" \
    -d "password=" \
    "$REGISTER_URL")

EMPTY_HTTP_CODE=$(echo "$EMPTY_RESPONSE" | tail -n 1)
EMPTY_BODY=$(echo "$EMPTY_RESPONSE" | head -n -1)

if echo "$EMPTY_BODY" | grep -qi "obligatoires\|required"; then
    test_result "Message d'erreur pour champs vides" 0
else
    test_result "Message d'erreur pour champs vides" 1
fi

echo ""

# ================================================
# TEST 3: Inscription avec email invalide
# ================================================
echo "================================================"
echo "TEST 3: Inscription avec email invalide"
echo "================================================"

INVALID_EMAIL_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -d "username=testuser" \
    -d "email=invalidemail" \
    -d "password=TestPassword123" \
    "$REGISTER_URL")

INVALID_EMAIL_CODE=$(echo "$INVALID_EMAIL_RESPONSE" | tail -n 1)
INVALID_EMAIL_BODY=$(echo "$INVALID_EMAIL_RESPONSE" | head -n -1)

# Note: Le navigateur valide le format email côté client, 
# mais le test curl contourne cette validation
echo "ℹ️  Test avec email invalide (validation HTML5 contournée par curl)"
echo "   Code HTTP: $INVALID_EMAIL_CODE"

echo ""

# ================================================
# TEST 4: Inscription réussie avec nouvel utilisateur
# ================================================
echo "================================================"
echo "TEST 4: Inscription réussie"
echo "================================================"
echo "Username: $TEST_USERNAME"
echo "Email: $TEST_EMAIL"
echo "Password: $TEST_PASSWORD"

REGISTER_RESPONSE=$(curl -s -L -w "\n%{http_code}" \
    -X POST \
    -d "username=$TEST_USERNAME" \
    -d "email=$TEST_EMAIL" \
    -d "password=$TEST_PASSWORD" \
    "$REGISTER_URL")

REGISTER_HTTP_CODE=$(echo "$REGISTER_RESPONSE" | tail -n 1)
REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | head -n -1)

echo "Code HTTP: $REGISTER_HTTP_CODE"

if [ "$REGISTER_HTTP_CODE" = "200" ]; then
    if echo "$REGISTER_BODY" | grep -qi "inscription réussie\|success"; then
        test_result "Inscription réussie - Message de succès" 0
    else
        test_result "Inscription réussie - Message de succès" 1
        echo "⚠️  Aucun message de succès détecté dans la réponse"
    fi
else
    test_result "Inscription réussie (HTTP $REGISTER_HTTP_CODE)" 1
fi

echo ""

# ================================================
# TEST 5: Vérification dans la base de données
# ================================================
echo "================================================"
echo "TEST 5: Vérification dans la base de données"
echo "================================================"

# Attendre un peu pour la propagation
sleep 2

DB_CHECK=$(docker compose exec -T mysql mysql -utomcat -ptomcat carshare \
    -e "SELECT username, email FROM users WHERE email='$TEST_EMAIL';" 2>/dev/null)

if echo "$DB_CHECK" | grep -q "$TEST_USERNAME"; then
    test_result "Utilisateur créé dans la base de données" 0
    echo "✅ Détails: $(echo "$DB_CHECK" | grep "$TEST_USERNAME")"
else
    test_result "Utilisateur créé dans la base de données" 1
    echo "❌ L'utilisateur n'a pas été trouvé dans la base"
fi

echo ""

# ================================================
# TEST 6: Tentative d'inscription avec email existant
# ================================================
echo "================================================"
echo "TEST 6: Inscription avec email déjà utilisé"
echo "================================================"

DUPLICATE_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -d "username=autreuser" \
    -d "email=$TEST_EMAIL" \
    -d "password=AutrePassword123" \
    "$REGISTER_URL")

DUPLICATE_HTTP_CODE=$(echo "$DUPLICATE_RESPONSE" | tail -n 1)
DUPLICATE_BODY=$(echo "$DUPLICATE_RESPONSE" | head -n -1)

if echo "$DUPLICATE_BODY" | grep -qi "existe déjà\|already exists"; then
    test_result "Message d'erreur pour email existant" 0
else
    test_result "Message d'erreur pour email existant" 1
    echo "⚠️  Le système devrait rejeter les emails en double"
fi

echo ""

# ================================================
# TEST 7: Vérification du hachage du mot de passe
# ================================================
echo "================================================"
echo "TEST 7: Vérification du hachage Argon2"
echo "================================================"

PASSWORD_HASH=$(docker compose exec -T mysql mysql -utomcat -ptomcat carshare \
    -e "SELECT password FROM users WHERE email='$TEST_EMAIL';" 2>/dev/null | grep -v "password")

if echo "$PASSWORD_HASH" | grep -q '\$argon2'; then
    test_result "Mot de passe haché avec Argon2" 0
    echo "✅ Hash détecté: ${PASSWORD_HASH:0:30}..."
else
    test_result "Mot de passe haché avec Argon2" 1
    echo "❌ Le mot de passe ne semble pas être haché correctement"
fi

echo ""

# ================================================
# TEST 8: Connexion avec le nouveau compte
# ================================================
echo "================================================"
echo "TEST 8: Connexion avec le compte créé"
echo "================================================"

COOKIE_FILE=$(mktemp)

LOGIN_RESPONSE=$(curl -s -c "$COOKIE_FILE" -w "\n%{http_code}" \
    -X POST \
    -d "email=$TEST_EMAIL" \
    -d "password=$TEST_PASSWORD" \
    "${BASE_URL}/login")

LOGIN_HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)

if [ "$LOGIN_HTTP_CODE" = "302" ] || [ "$LOGIN_HTTP_CODE" = "200" ]; then
    if grep -q "JSESSIONID" "$COOKIE_FILE"; then
        test_result "Connexion réussie avec le nouveau compte" 0
    else
        test_result "Connexion réussie avec le nouveau compte" 1
    fi
else
    test_result "Connexion réussie avec le nouveau compte (HTTP $LOGIN_HTTP_CODE)" 1
fi

rm -f "$COOKIE_FILE"

echo ""

# ================================================
# TEST 9: Redirection si déjà connecté
# ================================================
echo "================================================"
echo "TEST 9: Redirection si utilisateur déjà connecté"
echo "================================================"

# Se connecter d'abord
COOKIE_FILE=$(mktemp)
curl -s -c "$COOKIE_FILE" \
    -X POST \
    -d "email=$TEST_EMAIL" \
    -d "password=$TEST_PASSWORD" \
    "${BASE_URL}/login" > /dev/null

# Essayer d'accéder à la page d'inscription en étant connecté
REDIRECT_RESPONSE=$(curl -s -b "$COOKIE_FILE" -w "\n%{http_code}" "$REGISTER_URL")
REDIRECT_CODE=$(echo "$REDIRECT_RESPONSE" | tail -n 1)

if [ "$REDIRECT_CODE" = "302" ]; then
    test_result "Redirection vers profile si déjà connecté" 0
else
    # Si pas de redirection, vérifier si on est sur la page register quand même
    test_result "Redirection vers profile si déjà connecté (HTTP $REDIRECT_CODE)" 1
fi

rm -f "$COOKIE_FILE"

echo ""

# ================================================
# RÉSUMÉ DES TESTS
# ================================================
echo "================================================"
echo "📊 RÉSUMÉ DES TESTS D'INSCRIPTION"
echo "================================================"
echo "Total de tests: $TOTAL_TESTS"
echo "Tests réussis: $PASSED_TESTS"
echo "Tests échoués: $FAILED_TESTS"
echo "================================================"

if [ $FAILED_TESTS -eq 0 ]; then
    echo "✅ TOUS LES TESTS SONT PASSÉS !"
    echo "================================================"
    exit 0
else
    echo "❌ CERTAINS TESTS ONT ÉCHOUÉ"
    echo "Taux de réussite: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    echo "================================================"
    exit 1
fi
