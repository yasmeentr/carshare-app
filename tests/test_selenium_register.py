import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8090/carshare-app")
EMAIL = os.getenv("TEST_EMAIL", "dylan@exemple.com")
PASSWORD = os.getenv("TEST_PASSWORD", "dylan")

SCREEN_DIR = Path("screenshots")
SCREEN_DIR.mkdir(parents=True, exist_ok=True)

def snap(driver, name: str):
    """Capture un screenshot PNG dans ./screenshots/NAME.png"""
    path = SCREEN_DIR / f"{name}.png"
    ok = driver.save_screenshot(str(path))
    print(f"[INFO] Screenshot {'OK' if ok else 'FAIL'}: {path}")

def make_driver():
    """Crée un driver Chrome headless robuste pour Jenkins."""
    opts = Options()
    # Mode headless stable (Chrome 109+)
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    # Réduit le bruit dans les logs
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver

def login_flow(driver):
    wait = WebDriverWait(driver, 12)

    # 1) Aller sur /login
    url = f"{BASE_URL}/login"
    print(f"[INFO] Ouverture: {url}")
    driver.get(url)
    snap(driver, "01_login_page_loaded")

    # 2) Trouver les champs email / password
    try:
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        snap(driver, "02_email_field_visible")
    except TimeoutException as e:
        print("[ERROR] Champ email introuvable sur /login")
        snap(driver, "ERROR_no_email_field")
        raise

    try:
        password_input = driver.find_element(By.NAME, "password")
    except NoSuchElementException:
        print("[ERROR] Champ password introuvable sur /login")
        snap(driver, "ERROR_no_password_field")
        raise

    # 3) Remplir le formulaire
    email_input.clear()
    email_input.send_keys(EMAIL)
    password_input.clear()
    password_input.send_keys(PASSWORD)
    snap(driver, "03_credentials_filled")

    # 4) Cliquer sur le bouton submit
    try:
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'],input[type='submit']")
    except NoSuchElementException:
        print("[WARN] Bouton submit non trouvé via CSS, tentative via texte.")
        # fallback simple (si boutons nommés différemment)
        try:
            submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Login') or contains(., 'Se connecter')]")
        except NoSuchElementException:
            snap(driver, "ERROR_no_submit_button")
            raise

    submit_btn.click()
    time.sleep(0.8)  # laisser la redirection démarrer
    snap(driver, "04_after_submit_click")

    # 5) Attendre d'être sur /home
    try:
        wait.until(EC.url_contains("/home"))
        snap(driver, "05_homepage_loaded")
        print("[SUCCESS] Connexion réussie, page /home chargée.")
    except TimeoutException:
        print(f"[ERROR] Redirection vers /home non détectée. URL actuelle: {driver.current_url}")
        snap(driver, "ERROR_home_not_reached")
        # Enrichir le diagnostic: vérifier un message d'erreur éventuel
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print("[DEBUG] Extrait de la page:", body_text[:500])
        except Exception:
            pass
        raise

def main():
    driver = make_driver()
    try:
        login_flow(driver)
    except Exception as e:
        # Capture finale d'erreur
        snap(driver, "ZZZ_FATAL_ERROR")
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
