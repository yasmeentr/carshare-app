pipeline {

    agent {
        docker {
            image 'python:3.13'
            args '--memory=4g --cpus=2 --shm-size=2g'
        }
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        ansiColor('xterm')
    }

    environment {
        E2E_BASE_URL = "http://localhost:8090/carshare-app"     // ajuster si besoin
        SELENIUM_HEADLESS = "1"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare Environment') {
            steps {
                sh """
                python -m venv .venv
                . .venv/bin/activate
                pip install --upgrade pip wheel
                pip install -r requirements.txt
                """
            }
        }

        stage('Start Docker Services') {
            steps {
                sh """
                echo '[INFO] Starting docker-compose...'
                docker compose down --remove-orphans || true
                docker compose build --parallel

                # Start containers
                docker compose up -d

                echo '[INFO] Waiting for DB readiness...'
                docker compose exec db bash -c '
                    until pg_isready -U postgres; do
                        echo "DB not ready, waiting..."
                        sleep 2
                    done
                '

                echo '[INFO] Waiting for backend API...'
                for i in {1..30}; do
                    curl -sf ${E2E_BASE_URL}/health && break
                    echo "Backend not ready, waiting..."
                    sleep 2
                done
                """
            }
        }

        stage('Run Selenium Tests') {
            steps {
                sh """
                . .venv/bin/activate

                export SELENIUM_CHROME_ARGS="--headless=new --disable-gpu --no-sandbox --disable-dev-shm-usage --window-size=1920,1080"

                python -c "import selenium; print('[INFO] Selenium version:', selenium.__version__)"
                
                echo '[INFO] Running Selenium tests...'
                python tests/test_selenium_register.py || EXIT=\$?

                exit \${EXIT:-0}
                """
            }
            post {
                always {
                    echo "[INFO] Archiving artifacts…"
                    archiveArtifacts artifacts: '**/*.png, **/*.html', allowEmptyArchive: true
                }
            }
        }

    }

    post {
        always {
            echo "[INFO] Cleaning Docker..."
            sh "docker compose down --remove-orphans || true"
        }
        success {
            echo "🎉 Pipeline success"
        }
        failure {
            echo "❌ Pipeline failed – artifacts saved"
        }
    }
}
