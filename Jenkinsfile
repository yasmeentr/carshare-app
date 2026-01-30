pipeline {
  agent any

  options {
    timeout(time: 30, unit: 'MINUTES')
    // no ansiColor here to avoid compilation on older controllers
    // timestamps() // tu peux décommenter si le plugin Timestamps est présent
  }

  environment {
    // Ajuste si ton backend écoute ailleurs (ex: http://localhost:3000 ou http://localhost:8000)
    E2E_BASE_URL = "http://localhost:8000"
    // Utilisé par tes tests pour activer headless
    SELENIUM_HEADLESS = "1"
    // Arguments Chrome pour CI lente
    SELENIUM_CHROME_ARGS = "--headless=new --disable-gpu --no-sandbox --disable-dev-shm-usage --window-size=1920,1080"
    // Active un cache pip local au workspace pour accélérer les réinstallations
    PIP_CACHE_DIR = ".pip-cache"
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
          which python3 || true

          # Venv
          python3 -m venv .venv
          . .venv/bin/activate

          python -m pip install --upgrade pip wheel
          # Cache pip local
          mkdir -p "$PIP_CACHE_DIR"

          if [ -f requirements.txt ]; then
            PIP_CACHE_DIR="$PIP_CACHE_DIR" \
            pip install --cache-dir "$PIP_CACHE_DIR" -r requirements.txt
          fi

          # Affiche version Selenium si installée dans requirements.txt
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

          echo "[INFO] Wait for DB readiness (PostgreSQL)..."
          # NOTE: adapte le service 'db' et l'utilisateur si nécessaire
          docker compose exec -T db bash -lc '
            for i in $(seq 1 30); do
              if pg_isready -U postgres; then
                echo "DB is ready."
                exit 0
              fi
              echo "DB not ready, waiting..."
              sleep 2
            done
            echo "DB failed to become ready in time."
            exit 1
          '

          echo "[INFO] Wait for backend health endpoint..."
          for i in $(seq 1 30); do
            if curl -sf "$E2E_BASE_URL/health" > /dev/null; then
              echo "Backend is ready."
              break
            fi
            echo "Backend not ready, waiting..."
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

          # Expose Chrome args to tests; tes tests doivent les consommer (via env)
          export SELENIUM_CHROME_ARGS="$SELENIUM_CHROME_ARGS"
          export SELENIUM_HEADLESS="$SELENIUM_HEADLESS"
          export E2E_BASE_URL="$E2E_BASE_URL"

          echo "[INFO] Running Selenium tests..."
          # Si tu as plusieurs tests, tu peux lancer pytest -q
          # Ici on suit ton fichier existant:
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
