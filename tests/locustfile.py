# locustfile.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)

    @task(4)
    def home_page(self):
        self.client.get("/")

    @task(2)
    def login_fake(self):
        self.client.post("/login", data={
            "email": "fake@example.com",
            "password": "wrong"
        })
