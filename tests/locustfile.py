from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    host = "http:localhost:8090"
    wait_time = between(1, 3)

    @task
    def index(self):
        with self.client.get("/carshare-app", name="GET /carshare-app", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"Homepage HTTP {r.status_code}")

    @task(3)
    def login(self):
        # Si ton backend attend un formulaire, préfère data=... ; sinon garde json=...
        payload = {"email": "bob@example.com", "password": "12345"}
        with self.client.post("/carshare-app/login", data=payload, name="POST /carshare-app/login", catch_response=True) as r:
            if r.status_code in (401, 403):
                r.success()  # Échec d'auth attendu → succès du test fonctionnel
            elif r.status_code == 200:
                txt = (r.text or "").lower()
                # Adapte aux messages de ton app (ex: "invalid", "erreur", "incorrect")
                if "invalid" in txt or "erreur" in txt or "incorrect" in txt:
                    r.success()  # Login refusé → attendu
                else:
                    r.failure("Login semble accepté avec de faux identifiants")
            elif 300 <= r.status_code < 400:
                # Redirection fréquente après login (succès ou échec)
                loc = r.headers.get("Location", "").lower()
                if "error" in loc or "login" in loc:
                    r.success()  # redirection vers /login?error → attendu
                else:
                    r.failure(f"Redirection inattendue vers {loc}")
            else:
                r.failure(f"HTTP {r.status_code}")
``
