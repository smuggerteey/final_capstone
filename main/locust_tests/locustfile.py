from locust import HttpUser, task, between, TaskSet, tag
import random
from faker import Faker
import os
from datetime import datetime

# ========== CONFIGURATION ==========
class TestConfig:
    BASE_URL = "http://localhost:5000"  # Update for your environment
    WAIT_TIME = (1, 5)                  # Min/max seconds between tasks
    USER_CREDENTIALS = {
        "admin": {"username": "cicada", "password": "57sfafgh@As6t"},
        "regular": {"username": "cicada", "password": "57sfafgh@As6t"}
    }
    TEST_FILES = {
        "images": ["test_image.jpg"],
        "max_upload_size": 2 * 1024 * 1024  # 2MB
    }

# ========== UTILITIES ==========
class TestUtils:
    fake = Faker()
    
    @staticmethod
    def generate_artwork_data():
        return {
            "title": TestUtils.fake.sentence(),
            "description": TestUtils.fake.text(),
            "price": random.randint(10, 1000),
            "tags": ", ".join(TestUtils.fake.words(3)),
            "category": random.choice(["Painting", "Sculpture", "Digital"])
        }
    
    @staticmethod
    def validate_response(response, success_codes=[200, 201, 302]):
        if response.status_code not in success_codes:
            response.failure(f"Unexpected status {response.status_code}")
            return False
        return True

# ========== TEST BEHAVIORS ==========
class AuthBehavior(TaskSet):
    def on_start(self):
        """Executed when a user starts before any tasks"""
        self.client.cookies.clear()
        if random.random() < 0.1:  # 10% chance admin
            self.login(TestConfig.USER_CREDENTIALS["admin"])
        else:
            if random.random() < 0.3:  # 30% register new users
                new_user = self.register_new_user()
                if new_user:
                    self.login(new_user)
                else:
                    raise Exception("User registration failed")
            else:
                self.login(TestConfig.USER_CREDENTIALS["regular"])

    def register_new_user(self):
        user_data = {
            "username": TestUtils.fake.user_name(),
            "password": "LocustTest123!",
            "email": TestUtils.fake.email()
        }
        with self.client.post("/registration", data={
            "username": user_data["username"],
            "firstName": TestUtils.fake.first_name(),
            "lastName": TestUtils.fake.last_name(),
            "phone": TestUtils.fake.phone_number(),
            "role": "Artist" if random.random() < 0.5 else "Regular User",
            "address": TestUtils.fake.address(),
            "email": user_data["email"],
            "password": user_data["password"],
            "confirmPassword": user_data["password"]
        }, catch_response=True) as response:
            if not TestUtils.validate_response(response):
                return None
        return user_data

    def login(self, credentials):
        with self.client.post("/login", data={
            "username": credentials["username"],
            "password": credentials["password"]
        }, catch_response=True) as response:
            if not TestUtils.validate_response(response):
                raise Exception("Login failed")

    @task(3)
    @tag("auth")
    def view_profile(self):
        with self.client.get("/profile", catch_response=True) as response:
            TestUtils.validate_response(response)

    @task(1)
    @tag("auth")
    def logout(self):
        with self.client.get("/logout", catch_response=True) as response:
            TestUtils.validate_response(response)

class ArtworkBehavior(TaskSet):
    @task(5)
    @tag("artwork")
    def browse_gallery(self):
        with self.client.get("/virtual_gallery", catch_response=True) as response:
            TestUtils.validate_response(response)

    @task(3)
    @tag("artwork")
    def view_artwork_detail(self):
        artwork_id = random.randint(1, 100)  # Replace with dynamic ID retrieval if needed
        with self.client.get(f"/artwork/{artwork_id}", name="/artwork/[id]", 
                             catch_response=True) as response:
            if response.status_code == 404:
                response.success()  # 404s are okay if ID doesn't exist
            else:
                TestUtils.validate_response(response)

    @task(2)
    @tag("artwork")
    def upload_artwork(self):
        image_path = TestConfig.TEST_FILES["images"][0]
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Missing test image: {image_path}")

        if os.path.getsize(image_path) > TestConfig.TEST_FILES["max_upload_size"]:
            raise Exception("Test image exceeds max_upload_size")

        with open(image_path, "rb") as f:
            data = TestUtils.generate_artwork_data()
            files = {
                "media": (image_path, f, "image/jpeg")
            }

            with self.client.post("/upload", files=files, data=data, catch_response=True) as response:
                TestUtils.validate_response(response)

class MarketplaceBehavior(TaskSet):
    @task(4)
    @tag("marketplace")
    def browse_marketplace(self):
        with self.client.get("/marketplace", catch_response=True) as response:
            TestUtils.validate_response(response)

    @task(2)
    @tag("marketplace")
    def simulate_purchase(self):
        artwork_id = random.randint(1, 100)
        with self.client.post(f"/checkout/{artwork_id}", 
                              data={
                                  "payment_method": random.choice(["paypal", "momo"]),
                                  "agree_terms": "on"
                              },
                              name="/checkout/[id]",
                              catch_response=True) as response:
            TestUtils.validate_response(response)

# ========== MAIN USER CLASS ==========
class WebsiteUser(HttpUser):
    host = TestConfig.BASE_URL
    wait_time = between(*TestConfig.WAIT_TIME)

    tasks = {
        AuthBehavior: 3,
        ArtworkBehavior: 4,
        MarketplaceBehavior: 2
    }

    def on_start(self):
        self.start_time = datetime.now()

    def on_stop(self):
        elapsed = datetime.now() - self.start_time
        print(f"User session duration: {elapsed}")
        self.client.cookies.clear()
