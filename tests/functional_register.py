#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from pathlib import Path

# --- Selenium imports ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------------------------------------------------------
# Configuration depuis l'environnement Jenkins
# ---------------------------------------------------------
WORKSPACE = os.environ.get("WORKSPACE", os.getcwd())
SCREEN_DIR = Path(WORKSPACE) / "screenshots" / "register"
REPORT_FILE = Path(WORKSPACE) / "functional_register_report.txt"

TOMCAT_PORT = os.environ.get("TOMCAT_PORT", "8090")
BASE_URL = f"http://localhost:{TOMCAT_PORT}/carshare-app"
REGISTER_URL = f"{BASE_URL}/register"
LOGIN_URL = f"{BASE_URL}/login"
HOME_URL = f"{BASE_URL}/home"

# Données de test
DEFAULT_TEST_EMAIL = os.environ.get("TEST_EMAIL", "dylan@exemple.com")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "dylan")
REGISTER_USERNAME = os.environ.get("REGISTER_USERNAME", "dylan")

# Email d'inscription: unique si non fourni explicitement
BUILD_NUMBER = os.environ.get("BUILD_NUMBER")
REGISTER_EMAIL = os.environ.get("REGISTER_EMAIL")
if not REGISTER_EMAIL:
    # Générer un email unique basé sur TEST_EMAIL
    try:
        local, domain = DEFAULT_TEST_EMAIL.split("@", 1)
    except ValueError:
        local, domain = ("dylan", "exemple.com")
    suffix = BUILD_NUMBER or str(int(time.time()))
    REGISTER_EMAIL = f"{local}.reg{suffix}@{domain}"

# ---------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------
step_counter = 0
def take_screenshot(driver, label: str):
    """Capture une screenshot numérotée dans screenshots/register/."""
    global step_counter
    step_counter += 1
    SCREEN_DIR.mkdir(parents=True, exist_ok=True)
    filename = SCREEN_DIR / f"{step_counter:02d}_{label}.png"
    try:
        driver.save_screenshot(str(filename))
        print(f"[📸] Screenshot enregistré: {filename}")
    except Exception as e:
        print(f"[WARN] Impossible d'enregistrer la capture '{label}': {e}")

def write_report(lines):
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[📝] Rapport écrit dans: {REPORT_FILE}")

def run_cmd(cmd, cwd=None, timeout=30):
    """Exécute une commande shell et retourne (code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "Timeout"

def setup_chrome():
    """Configure Chrome/Chromium headless. Selenium Manager gère le driver."""
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,768")

    chrome_bin = os.environ.get("CHROME_BIN")
    if chrome_bin and Path(chrome_bin).exists():
        options.binary_location = chrome_bin

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver

# ---------------------------------------------------------
# Test principal
# ---------------------------------------------------------
def main():
    ok = True
    report = []
    driver = None

    try:
        print("=== Configuration (Register) ===")
        print(f"WORKSPACE: {WORKSPACE}")
        print(f"REGISTER_URL: {REGISTER_URL}")
        print(f"LOGIN_URL: {LOGIN_URL}")
        print(f"HOME_URL: {HOME_URL}")
        print(f"REGISTER_USERNAME: {REGISTER_USERNAME}")
        print(f"REGISTER_EMAIL:   {REGISTER_EMAIL}")

        driver = setup_chrome()
        wait = WebDriverWait(driver, 30)

        # 1) Accès à la page /register
        print("\n[TEST] Accès à la page d'inscription")
        driver.get(REGISTER_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        take_screenshot(driver, "register_page_open")

        # 2) Localiser les champs (#username, #email, #password)
        print("\n[TEST] Localisation des champs du formulaire")
        username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
        email_input    = wait.until(EC.presence_of_element_located((By.ID, "email")))
        pwd_input      = wait.until(EC.presence_of_element_located((By.ID, "password")))
        take_screenshot(driver, "form_located")

        # 3) Saisie des valeurs
        print("\n[TEST] Saisie username / email / password")
        username_input.clear(); username_input.send_keys(REGISTER_USERNAME)
        email_input.clear();    email_input.send_keys(REGISTER_EMAIL)
        pwd_input.clear();      pwd_input.send_keys(TEST_PASSWORD)
        take_screenshot(driver, "form_filled")

        # 4) Soumettre (Enter sur password puis fallback bouton submit)
        print("\n[TEST] Soumission du formulaire")
        pwd_input.send_keys(Keys.ENTER)
        # Si pas de navigation, cliquer explicitement le submit
        try:
            WebDriverWait(driver, 3).until(EC.staleness_of(pwd_input))
        except Exception:
            # Bouton submit (selon ta JSP, bouton type='submit')
            try:
                submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                submit_btn.click()
            except Exception:
                pass
        take_screenshot(driver, "after_submit")

        # 5) Attendre le message de succès ou un message d'erreur
        print("\n[TEST] Vérification du message de succès/erreur")
        success_detected = False
        error_detected = False
        try:
            # Succès: "Inscription réussie ! Veuillez vous connecter."
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(),'Inscription réussie')] | //*[contains(@class,'bg-green') and contains(text(),'Inscription réussie')]")
                )
            )
            success_detected = True
        except Exception:
            # Chercher un message d'erreur courant
            try:
                wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(),'Un compte avec cet email existe déjà')] | //*[contains(text(),'Erreur serveur')] | //*[contains(text(),'Tous les champs sont obligatoires')]")
                    )
                )
                error_detected = True
            except Exception:
                pass

        take_screenshot(driver, "post_feedback")

        if success_detected:
            report.append("✅ Inscription: message de succès détecté")
        elif error_detected:
            ok = False
            # Préciser quel type d'erreur a été vu (simplement dans le body)
            body_text = driver.page_source
            if "Un compte avec cet email existe déjà" in body_text:
                report.append("❌ Inscription refusée: email déjà utilisé")
            elif "Tous les champs sont obligatoires" in body_text:
                report.append("❌ Inscription refusée: champs manquants")
            else:
                report.append("❌ Inscription échouée: erreur serveur")
        else:
            ok = False
            report.append("❌ Aucun indicateur de succès/erreur détecté après soumission")

        # 6) Vérification DB (OPTIONNEL mais utile)
        print("\n[TEST] Vérification en base MySQL (optionnelle)")
        # Escape simple quote pour SQL
        safe_email = REGISTER_EMAIL.replace("'", "''")
        cmd = f"docker compose exec -T mysql mysql -utomcat -ptomcat carshare -e \"SELECT COUNT(*) FROM users WHERE email='{safe_email}';\""
        code, out, err = run_cmd(cmd, cwd=WORKSPACE, timeout=30)
        take_screenshot(driver, "db_check_context")
        if code == 0:
            # Heuristique simple: dernière ligne contient le count
            try:
                last = out.splitlines()[-1].strip()
                if last == "1":
                    report.append("✅ DB: utilisateur présent (COUNT=1)")
                elif last.isdigit() and int(last) >= 1:
                    report.append(f"⚠️ DB: multiple rows pour {REGISTER_EMAIL} (COUNT={last})")
                else:
                    report.append(f"⚠️ DB: utilisateur non confirmé (sortie='{last}')")
            except Exception:
                report.append(f"⚠️ DB: sortie inattendue ({out})")
        else:
            report.append(f"⚠️ DB: commande MySQL a échoué (code={code}) - {err or out}")

        # 7) (Optionnel) Tenter un login avec le compte créé
        print("\n[TEST] Login (optionnel) avec le compte créé")
        try:
            driver.get(LOGIN_URL)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            take_screenshot(driver, "login_page")

            login_email = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#email, input[name='email']")))
            login_pwd   = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#password, input[name='password']")))
            login_email.clear(); login_email.send_keys(REGISTER_EMAIL)
            login_pwd.clear();   login_pwd.send_keys(TEST_PASSWORD)
            take_screenshot(driver, "login_filled")

            login_pwd.send_keys(Keys.ENTER)
            take_screenshot(driver, "login_after_submit")

            # Attendre un indicateur de succès (URL /home ou “Déconnexion”)
            logged_in = False
            try:
                WebDriverWait(driver, 15).until(
                    lambda d: "/home" in d.current_url or "logout" in d.page_source.lower() or "déconnexion" in d.page_source.lower()
                )
                logged_in = True
            except Exception:
                pass
            take_screenshot(driver, "home_after_login")

            if logged_in:
                report.append("✅ Login OK avec le compte nouvellement créé")
            else:
                report.append("⚠️ Login non confirmé (peut dépendre du flow de l’app)")
        except Exception as e:
            report.append(f"⚠️ Login optionnel non exécuté correctement: {e}")

    except Exception as e:
        ok = False
        print(f"[ERROR] {e}")
        # Essayer une capture finale si possible
        try:
            if driver:
                take_screenshot(driver, "error")
        except Exception:
            pass
        report.append(f"❌ Exception: {e}")

    finally:
        if driver:
            try:
                take_screenshot(driver, "final_state")
            except Exception:
                pass
            driver.quit()

        # Écrire rapport
        write_report(report)

    # Sortie process
    if not ok:
        print("\n=== RÉSULTAT GLOBAL: ÉCHEC (Register) ===")
        sys.exit(1)
    else:
        print("\n=== RÉSULTAT GLOBAL: SUCCÈS (Register) ===")

if __name__ == "__main__":
    main()
