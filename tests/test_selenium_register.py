# tests/test_selenium_register.py
# Test de CONNEXION (login) avec l'utilisateur dylan (email: dylan@exemple.com, mdp: dylan)
# - Ouvre /login (fallback /login.jsp)
# - Remplit le formulaire
# - Valide la connexion via redirection, message de succès, ou lien Déconnexion
# - Sauvegarde HTML/PNG de debug en cas d'échec (archivables par Jenkins)

import os
import time
import string
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- Config via variables d'environnement (aligné avec ton Jenkinsfile) ---
BASE_URL = os.getenv("BASE_URL", "http://localhost:8090")
CONTEXT = os.getenv("CONTEXT_PATH", "/carshare-app")

LOGIN_URL = f"{BASE_URL}{CONTEXT}/login"
LOGIN_JSP_URL = f"{BASE_URL}{CONTEXT}/login.jsp"

# Compte à tester
LOGIN_EMAIL = os.getenv("TEST_LOGIN_EMAIL", "dylan@exemple.com")
LOGIN_PASSWORD = os.getenv("TEST_LOGIN_PASSWORD", "dylan")

# Chrome args en CI (prend ceux fournis par Jenkins si présents)
SELENIUM_CHROME_ARGS = os.getenv(
    "SELENIUM_CHROME_ARGS",
    "--headless=new --no-sandbox --disable-dev-shm-usage --window-size=1280,900"
)


def make_driver():
    opts = Options()
    for arg in SELENIUM_CHROME_ARGS.split():
        if arg.strip():
            opts.add_argument(arg)
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(60)
    return driver


def wait_doc_ready(driver, timeout=45):
    W(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def dump_artifacts(driver, prefix="login_debug"):
    try:
        html = driver.page_source
        with open(f"{prefix}.html", "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        print(f"[WARN] Failed to save HTML: {e}", file=sys.stderr)
    try:
        driver.save_screenshot(f"{prefix}.png")
    except Exception as e:
        print(f"[WARN] Failed to save screenshot: {e}", file=sys.stderr)
    try:
        print(f"[DEBUG] Current URL: {driver.current_url}")
        print(f"[DEBUG] Title: {driver.title}")
        print(f"[DEBUG] Page length: {len(driver.page_source)}")
    except Exception:
        pass


def find_first(driver, selectors, wait_time=20):
    for by, sel in selectors:
        try:
            el = W(driver, wait_time).until(EC.presence_of_element_located((by, sel)))
            if el:
                return el, (by, sel)
        except TimeoutException:
            continue
    return None, None


def maybe_switch_into_iframe(driver):
    # Si le formulaire est éventuellement dans un iframe (peu probable ici, mais safe)
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            driver.switch_to.frame(iframes[0])
            return True
    except Exception:
        pass
    return False


def consider_login_success(driver):
    """
    Critères de succès :
      - Redirection : l'URL ne se termine plus par /login ou login.jsp
      - Message de succès visible (classes Tailwind/alerts)
      - Présence d'un lien 'Déconnexion' / 'Se déconnecter' / '/logout'
    """
    url = driver.current_url
    if not (url.rstrip("/").endswith("/login") or url.endswith("login.jsp")):
        return True, "redirected"

    # message de succès
    try:
        success_block = W(driver, 3).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".bg-green-100.text-green-700, .alert-success, .text-green-700")
            )
        )
        if success_block:
            return True, f"success_message:{success_block.text.strip() if success_block.text else ''}"
    except Exception:
        pass

    # lien / bouton de déconnexion
    try:
        # différents patterns possibles
        logout_candidates = driver.find_elements(
            By.XPATH,
            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'déconnexion') or "
            "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'se déconnecter') or "
            "contains(@href, '/logout')]"
        )
        if logout_candidates:
            return True, "logout_link_present"
    except Exception:
        pass

    return False, ""


def try_login_flow(driver, url):
    print(f"[INFO] Navigating to: {url}")
    driver.get(url)
    wait_doc_ready(driver, timeout=45)

    print(f"[INFO] Effective URL after navigation: {driver.current_url}")
    print(f"[INFO] Page length: {len(driver.page_source)}")

    # Localiser champs email/password
    email_el, used_email_sel = find_first(driver, [
        (By.ID, "email"),
        (By.NAME, "email"),
        (By.CSS_SELECTOR, "input#email"),
        (By.CSS_SELECTOR, "input[name='email']")
    ], wait_time=20)

    password_el, used_pwd_sel = find_first(driver, [
        (By.ID, "password"),
        (By.NAME, "password"),
        (By.CSS_SELECTOR, "input#password"),
        (By.CSS_SELECTOR, "input[name='password']")
    ], wait_time=20)

    # Si introuvable, tenter un iframe
    if not (email_el and password_el):
        switched = maybe_switch_into_iframe(driver)
        if switched:
            print("[INFO] Switched into first iframe and retrying locators…")
            email_el, used_email_sel = find_first(driver, [
                (By.ID, "email"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "input#email"),
                (By.CSS_SELECTOR, "input[name='email']")
            ], wait_time=10)
            password_el, used_pwd_sel = find_first(driver, [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input#password"),
                (By.CSS_SELECTOR, "input[name='password']")
            ], wait_time=10)

    if not email_el:
        dump_artifacts(driver, "login_missing_email")
        raise TimeoutException("Email field not found on login page.")
    if not password_el:
        dump_artifacts(driver, "login_missing_password")
        raise TimeoutException("Password field not found on login page.")

    print(f"[INFO] Found email field with selector: {used_email_sel}")
    print(f"[INFO] Found password field with selector: {used_pwd_sel}")

    # Bouton submit
    try:
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    except NoSuchElementException:
        dump_artifacts(driver, "login_missing_submit")
        raise TimeoutException("Submit button not found on login page.")

    # Remplir
    email_el.clear();    email_el.send_keys(LOGIN_EMAIL)
    password_el.clear(); password_el.send_keys(LOGIN_PASSWORD)

    # Scroll + click
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    submit_btn.click()

    # Laisse le serveur traiter
    time.sleep(1.0)
    wait_doc_ready(driver, timeout=30)

    ok, reason = consider_login_success(driver)
    if ok:
        print("[OK] Connexion considérée comme réussie.")
        print(f"  - Email    : {LOGIN_EMAIL}")
        print(f"  - URL fin  : {driver.current_url}")
        if reason:
            print(f"  - Indice   : {reason}")
        return True

    # Sinon, log d'une éventuelle erreur
    try:
        error_block = driver.find_element(By.CSS_SELECTOR, ".bg-red-100.text-red-700, .alert-danger, .text-red-700")
        print(f"[ERROR] Message d'erreur: {error_block.text.strip()}")
    except Exception:
        pass

    dump_artifacts(driver, "login_after_submit_no_success")
    raise AssertionError("Aucun indicateur de succès détecté après tentative de connexion.")


def main():
    driver = make_driver()
    try:
        # 1) Essaye /login
        try:
            return try_login_flow(driver, LOGIN_URL)
        except TimeoutException as e:
            print(f"[WARN] /login failed with: {e}. Trying /login.jsp ...")

        # 2) Fallback /login.jsp
        driver.switch_to.default_content()
        return try_login_flow(driver, LOGIN_JSP_URL)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
