stage('Selenium E2E Tests') {
    steps {
        echo '🧪 Exécution des tests E2E Selenium (avec screenshots)...'
        sh '''
            set -euxo pipefail

            # Préparer l'environnement Python dans le workspace
            python3 -V
            python3 -m venv .venv
            . .venv/bin/activate
            python -m pip install --upgrade pip

            # Dépendances Selenium (pas besoin de ChromeDriver si le conteneur Jenkins a Chrome/Chromium)
            pip install "selenium>=4.20.0" webdriver-manager

            # Variables pour le test (mêmes valeurs que dans ton pipeline)
            export E2E_BASE_URL="http://localhost:${TOMCAT_PORT}/carshare-app"
            export TEST_EMAIL="${TEST_EMAIL}"
            export TEST_PASSWORD="${TEST_PASSWORD}"

            # Lancer le test Python
            python tests/test_selenium_register.py
        '''
    }
    post {
        always {
            echo '[INFO] Archivage des screenshots Selenium...'
            archiveArtifacts artifacts: 'screenshots/*.png', fingerprint: true, allowEmptyArchive: true
        }
    }
}
