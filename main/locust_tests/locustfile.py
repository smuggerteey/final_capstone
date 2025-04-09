from locust import HttpUser, task, between
import random
import string

class QuickstartUser(HttpUser):
    wait_time = between(1, 5)  # Simulate realistic user think time

    def on_start(self):
        """Executed when a simulated user starts."""
        self.auth_token = ""
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.login()

    def login(self):
        credentials = {
            "username": "cicada",
            "password": "57sfafgh@As6t"
        }
        with self.client.post("/login", json=credentials, catch_response=True) as response:
            if response.status_code == 200:
                self.auth_token = response.json().get("token", "")
                self.headers["Authorization"] = f"Bearer {self.auth_token}"
            else:
                response.failure("Login failed")

    @task(1)
    def register_user(self):
        """Test user registration endpoint"""
        user_data = {
            "username": "user_" + ''.join(random.choices(string.ascii_lowercase, k=5)),
            "email": ''.join(random.choices(string.ascii_lowercase, k=5)) + "@example.com",
            "password": "Test@1234"
        }
        self.client.post("/register", json=user_data)

    @task(3)
    def view_homepage(self):
        self.client.get("/")

    @task(2)
    def view_virtual_gallery(self):
        self.client.get("/virtual_gallery")

    @task(2)
    def view_marketplace(self):
        self.client.get("/marketplace")

    @task(2)
    def view_artwork_detail(self):
        artwork_id = random.randint(1, 100)  # Assuming 1–100 are valid
        self.client.get(f"/artwork/{artwork_id}")

    @task(1)
    def view_dashboard(self):
        self.client.get("/dashboard", headers=self.headers)

    @task(1)
    def view_profile(self):
        self.client.get("/profile", headers=self.headers)

    @task(1)
    def upload_artwork(self):
        artwork_data = {
            "title": "Test Artwork " + ''.join(random.choices(string.ascii_letters, k=5)),
            "description": "This is a test artwork upload",
            "price": random.randint(10, 1000),
            "tags": "test,locust",
            "category": random.choice(["painting", "digital", "sculpture", "photography"])
        }
        self.client.post("/upload", json=artwork_data, headers=self.headers)

    @task(1)
    def send_message(self):
        message_data = {
            "room": "general",
            "message": "Test message from load test",
            "username": "test_user"
        }
        self.client.post("/send_message", json=message_data, headers=self.headers)

    @task(1)
    def comment_on_artwork(self):
        artwork_id = random.randint(1, 30)
        comment_data = {
            "artwork_id": artwork_id,
            "comment": "This is a test comment",
            "username": "test_user"
        }
        self.client.post("/artwork/comment", json=comment_data, headers=self.headers)

    @task(1)
    def view_leaderboard(self):
        self.client.get("/leaderboard")

    @task(1)
    def view_insights(self):
        self.client.get("/insights", headers=self.headers)

    @task(1)
    def chat_with_bot(self):
        questions = [
            "What is this platform about?",
            "How do I upload artwork?",
            "Tell me about the challenges",
            "What payment methods do you accept?",
            "How can I contact support?"
        ]
        question = random.choice(questions)
        self.client.post("/predict", json={"input_text": question}, headers=self.headers)

    @task(1)
    def logout(self):
        self.client.get("/logout", headers=self.headers)
        self.auth_token = ""