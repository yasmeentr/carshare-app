# tests/test_selenium_register.py
import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Si tu préfères laisser Chrome/Chromium système, commente ces 2 lignes:
from webdriver_manager.chrome import ChromeDriverManager  # auto-installe le bon driver

# --- Configuration depuis Jenkins (ou valeurs par défaut locales) ---
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8090/carshare-app")
EMAIL = os.getenv("TEST_EMAIL", "dylan@exemple.com")
PASSWORD = os.getenv("TEST_PASSWORD", "dylan")
USERNAME = os.getenv("TEST_USERNAME", "dylan")  # utile si le formulaire d'inscription le demande

# Dossier des captures
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
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    # Utilise webdriver-manager pour disposer d’un chromedriver compatible
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(30)
    return driver


def wait_find(wait: WebDriverWait, candidates):
    """
    Essaie une liste de sélecteurs (locators) et retourne le premier trouvé.
    candidates = [(By.NAME, "email"), (By.ID, "email"), ...]
    """
    last_err = None
    for locator in candidates:
        try:
            return wait.until(EC.presence_of_element_located(locator))
        except TimeoutException as e:
            last_err = e
            continue
    raise TimeoutException(f"Élément introuvable. Tentatives: {candidates}") from last_err


def click_submit(driver):
    """Clique sur le bouton submit (robuste)."""
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'],input[type='submit']")
    except NoSuchElementException:
        # Fallback: bouton par texte
        try:
            btn = driver.find_element(
                By.XPATH,
                "//button[contains(., 'Inscription') or contains(., 'S’inscrire') or "
                "contains(., 'Register') or contains(., 'Se connecter') or contains(., 'Login')]"
            )
        except NoSuchElementException as e:
            snap(driver, "ERROR_no_submit_button")
            raise e
    btn.click()


def register_flow(driver) -> str:
    """
    Tente de s'inscrire via /register avec (USERNAME, EMAIL, PASSWORD).
    Retourne "profile" si déjà connecté après l’inscription,
            "login" si redirigé vers la page de login,
            "stay" si on reste sur la page (erreur/validation).
    """
    url = f"{BASE_URL}/register"
    print(f"[INFO] Ouverture (register): {url}")
    driver.get(url)
    snap(driver, "00_register_page_loaded")

    wait = WebDriverWait(driver, 12)

    # Certains formulaires n'ont pas "username". On essaie mais on tolère l'absence.
    try:
        username_input = wait_find(wait, [
            (By.NAME, "username"),
            (By.ID, "username"),
            (By.NAME, "name"),
            (By.ID, "name"),
        ])
        username_input.clear()
        username_input.send_keys(USERNAME)
    except TimeoutException:
        print("[WARN] Champ 'username' non trouvé (ok si non requis).")

    # Email
    email_input = wait_find(wait, [
        (By.NAME, "email"),
        (By.ID, "email"),
    ])
    email_input.clear()
    email_input.send_keys(EMAIL)

    # Password (principal)
    pwd_input = wait_find(wait, [
        (By.NAME, "password"),
        (By.ID, "password"),
    ])
    pwd_input.clear()
    pwd_input.send_keys(PASSWORD)

    # Confirm password (si présent)
    try:
        confirm_input = wait_find(wait, [
            (By.NAME, "confirm_password"),
            (By.ID, "confirm_password"),
            (By.NAME, "passwordConfirm"),
            (By.ID, "passwordConfirm"),
            (By.NAME, "confirm"),
            (By.ID, "confirm"),
        ])
        confirm_input.clear()
        confirm_input.send_keys(PASSWORD)
    except TimeoutException:
        print("[WARN] Champ de confirmation de mot de passe non trouvé (ok si non requis).")

    snap(driver, "01_register_form_filled")
    click_submit(driver)
    time.sleep(1.0)
    snap(driver, "02_register_after_submit")

    # Scénarios possibles après inscription :
    wait_short = WebDriverWait(driver, 5)
    # a) Redirection vers /profile (déjà connecté)
    try:
        wait_short.until(EC.url_contains("/profile"))
        snap(driver, "03_register_redirect_profile")
        return "profile"
    except TimeoutException:
        pass
    # b) Redirection vers /login (inscription OK mais il faut se connecter)
    try:
        wait_short.until(EC.url_contains("/login"))
        snap(driver, "03_register_redirect_login")
        return "login"
    except TimeoutException:
        pass

    # c) On est resté sur la page /register, vérifier un éventuel message d'erreur/succès
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").getText()
    except Exception:
        body_text = driver.page_source

    if any(x in body_text.lower() for x in ["existe déjà", "déjà utilisé", "already exists", "duplicate"]):
        print("[INFO] L'adresse e-mail semble déjà utilisée. On tentera simplement le login.")
    else:
        print("[INFO] Inscription : pas de redirection détectée. On poursuit avec un login standard.")
    return "stay"


def login_flow(driver):
    """Se connecte avec (EMAIL, PASSWORD) et attend la page /profile."""
    wait = WebDriverWait(driver, 12)

    url = f"{BASE_URL}/login"
    print(f"[INFO] Ouverture (login): {url}")
    driver.get(url)
    snap(driver, "10_login_page_loaded")

    email_input = wait_find(wait, [
        (By.NAME, "email"),
        (By.ID, "email"),
    ])
    pwd_input = wait_find(wait, [
        (By.NAME, "password"),
        (By.ID, "password"),
    ])

    email_input.clear()
    email_input.send_keys(EMAIL)
    pwd_input.clear()
    pwd_input.send_keys(PASSWORD)
    snap(driver, "11_login_form_filled")

    click_submit(driver)
    time.sleep(0.8)
    snap(driver, "12_login_after_submit")

    try:
        wait.until(EC.url_contains("/profile"))
        snap(driver, "13_profile_loaded")
        print("[SUCCESS] Connexion réussie, page /profile chargée.")
    except TimeoutException:
        print(f"[ERROR] Redirection vers /profile non détectée. URL actuelle: {driver.current_url}")
        snap(driver, "ERROR_profile_not_reached")
        # Affiner le diagnostic
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print("[DEBUG] Extrait de la page:", body_text[:600])
        except Exception:
            pass
        raise


def main():
    driver = make_driver()
    try:
        outcome = register_flow(driver)
        # Si déjà connecté suite à l'inscription → on s'assure d'être bien sur /profile
        if outcome == "profile":
            print("[INFO] Déjà connecté après inscription. Vérification finale …")
            WebDriverWait(driver, 8).until(EC.url_contains("/profile"))
            snap(driver, "14_profile_after_register")
        else:
            # Sinon on tente le login standard
            login_flow(driver)

    except Exception as e:
        snap(driver, "ZZZ_FATAL_ERROR")
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
