pipeline {
  agent any

  options {
    timeout(time: 30, unit: 'MINUTES')
    // timestamps() // décommente si le plugin est installé
  }

  environment {
    // Base URL de l'app servie par Tomcat. Ajuste si ton app est sous /monapp
    APP_BASE_URL       = "http://localhost:8080"
    APP_HEALTH_PATH    = "/"                 // ex: "/monapp/health" si tu as un endpoint
    // Pour tes tests Selenium :
    E2E_BASE_URL       = "http://localhost:8080"
    SELENIUM_HEADLESS  = "1"
    SELENIUM_CHROME_ARGS = "--headless=new --disable-gpu --no-sandbox --disable-dev-shm-usage --window-size=1920,1080"
    // Cache pip local pour accélérer
    PIP_CACHE_DIR      = ".pip-cache"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Python Env') {
      steps {
        sh '''
          set -euxo pipefail

          python3 -V

          # Crée l'environnement virtuel Python
          python3 -m venv .venv
          . .venv/bin/activate

          python -m pip install --upgrade pip wheel
          mkdir -p "$PIP_CACHE_DIR"

          if [ -f requirements.txt ]; then
            PIP_CACHE_DIR="$PIP_CACHE_DIR" \
            pip install --cache-dir "$PIP_CACHE_DIR" -r requirements.txt
          fi

          # Info Selenium
          python - <<'PY'
import importlib
try:
    s = importlib.import_module("selenium")
    print("[INFO] Selenium version:", s.__version__)
except Exception as e:
    print("[WARN] Selenium not found in venv:", e)
PY
        '''
      }
    }

    stage('Docker Compose Up') {
      steps {
        sh '''
          set -euxo pipefail

          echo "[INFO] Docker version:"
          docker --version

          echo "[INFO] Bring down leftovers..."
          docker compose down --remove-orphans || true

          echo "[INFO] Build images (using cache if available)..."
          docker compose build --parallel

          echo "[INFO] Start services..."
          docker compose up -d

          echo "[INFO] Waiting for MySQL service readiness..."
          # Nom du service: "mysql" (vu dans tes logs). Si différent, adapte-le.
          # On tente d'abord avec mot de passe, sinon sans.
          docker compose exec -T mysql bash -lc '
            set -e
            tries=30
            wait_sec=2
            echo "Checking MySQL readiness inside container..."
            for i in $(seq 1 $tries); do
              if [ -n "$MYSQL_ROOT_PASSWORD" ]; then
                if mysqladmin ping -h 127.0.0.1 -u root -p"$MYSQL_ROOT_PASSWORD" --silent; then
                  echo "MySQL is ready (with password)."
                  exit 0
                fi
              else
                if mysqladmin ping -h 127.0.0.1 -u root --silent; then
                  echo "MySQL is ready (no password)."
                  exit 0
                fi
              fi
              echo "MySQL not ready yet... ($i/$tries)"
              sleep $wait_sec
            done
            echo "ERROR: MySQL failed to become ready in time."
            exit 1
          '

          echo "[INFO] Waiting for Tomcat (HTTP ${APP_BASE_URL}${APP_HEALTH_PATH}) ..."
          # On attend que Tomcat réponde au moins 200/3xx sur la racine (ou chemin santé)
          for i in $(seq 1 60); do
            if curl -sf "${APP_BASE_URL}${APP_HEALTH_PATH}" > /dev/null; then
              echo "Tomcat/App is ready."
              break
            fi
            echo "Tomcat not ready yet... ($i/60)"
            sleep 2
          done
        '''
      }
    }

    stage('Run Selenium Tests') {
      steps {
        sh '''
          set -euxo pipefail
          . .venv/bin/activate

          export SELENIUM_CHROME_ARGS="$SELENIUM_CHROME_ARGS"
          export SELENIUM_HEADLESS="$SELENIUM_HEADLESS"
          export E2E_BASE_URL="$E2E_BASE_URL"

          echo "[INFO] Running Selenium tests..."
          # Exemple minimal : lance ton test existant
          python tests/test_selenium_register.py
        '''
      }
      post {
        always {
          echo "[INFO] Archiving screenshots and html artifacts (if any)..."
          archiveArtifacts artifacts: '**/*.png, **/*.html', allowEmptyArchive: true
        }
      }
    }
  }

  post {
    always {
      echo "[INFO] Cleaning up docker..."
      sh 'docker compose down --remove-orphans || true'
    }
    success {
      echo '🎉 Pipeline SUCCESS'
    }
    failure {
      echo '❌ Pipeline FAILED — check archived artifacts and console logs'
    }
  }
}
