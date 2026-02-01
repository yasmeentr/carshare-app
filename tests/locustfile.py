# locustfile.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    host = "http://localhost:8090"  
    wait_time = between(1, 3)

    @task
    def home(self):
        self.client.get("/carshare-app")

    @task(3)
    def login_fake(self):
        self.client.post("/carshare-app/login", data={
            "email": "bob@example.com",
            "password": "12345"
        })
