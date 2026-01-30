# tests/test_selenium_register.py
import os
import time
import random
import string

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = os.getenv("BASE_URL", "http://localhost:8090")
CONTEXT = os.getenv("CONTEXT_PATH", "/carshare-app")
REGISTER_URL = f"{BASE_URL}{CONTEXT}/register"

def random_suffix(k=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))

def main():
    # --- Chrome headless options ---
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 15)

    username = f"bob{random_suffix()}"
    email = f"{username}@example.com"
    password = "P@ssw0rd-Example"

    try:
        driver.get(REGISTER_URL)

        # Attendre le formulaire
        wait.until(EC.presence_of_element_located((By.ID, "username")))
        wait.until(EC.presence_of_element_located((By.ID, "email")))
        wait.until(EC.presence_of_element_located((By.ID, "password")))
        submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')

        # Remplir
        driver.find_element(By.ID, "username").clear()
        driver.find_element(By.ID, "username").send_keys(username)

        driver.find_element(By.ID, "email").clear()
        driver.find_element(By.ID, "email").send_keys(email)

        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys(password)

        submit_btn.click()

        # Petit délai post-submit
        time.sleep(0.5)

        # Critères de succès :
        # 1) message de succès (bloc vert)
        # 2) redirection (URL ne se termine plus par /register)
        redirected = not driver.current_url.rstrip("/").endswith("/register")

        success_block = None
        try:
            success_block = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".bg-green-100.text-green-700")
                )
            )
        except Exception:
            success_block = None

        if redirected or success_block:
            print("[OK] Inscription considérée comme réussie.")
            print(f"  - Username : {username}")
            print(f"  - Email    : {email}")
            print(f"  - URL fin  : {driver.current_url}")
            if success_block:
                print(f"  - Message  : {success_block.text.strip() or '(vide)'}")
            return

        # Sinon : récupérer les erreurs éventuelles pour debug
        error_block_text = ""
        try:
            error_block = driver.find_element(By.CSS_SELECTOR, ".bg-red-100.text-red-700")
            error_block_text = error_block.text.strip()
        except Exception:
            pass

        raise AssertionError(
            "Aucun indicateur de succès détecté après la soumission.\n"
            f"URL actuelle : {driver.current_url}\n"
            f"Message d'erreur (si présent) : {error_block_text}"
        )

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
