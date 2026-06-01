"""
Locust load test configuration for Nexopus Finance Ops API
Run with: locust -f locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between
import random


class NexopusUser(HttpUser):
    """
    Simulates a user interacting with the Nexopus API.
    """
    wait_time = between(1, 5)

    def on_start(self):
        """Login on start to get auth token."""
        self.client.post("/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })

    @task(3)
    def view_dashboard(self):
        """View dashboard data."""
        self.client.get("/reports/dre/1/2024")

    @task(2)
    def view_documents(self):
        """View documents list."""
        self.client.get("/documents")

    @task(1)
    def view_compliance(self):
        """View compliance data."""
        self.client.get("/compliance")

    @task(1)
    def view_audit(self):
        """View audit data."""
        self.client.post("/ai/audit", json={
            "company_id": "1",
            "year": 2024
        })

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health")


class AdminUser(HttpUser):
    """
    Simulates an admin user with higher privileges.
    """
    wait_time = between(2, 10)

    def on_start(self):
        """Login as admin."""
        self.client.post("/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })

    @task(2)
    def view_users(self):
        """View users list."""
        self.client.get("/admin/users")

    @task(1)
    def view_audit_logs(self):
        """View audit logs."""
        self.client.get("/admin/audit-logs")

    @task(1)
    def view_companies(self):
        """View companies list."""
        self.client.get("/companies")
