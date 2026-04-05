# 🚀 StockUp Testing Framework

This suite provides a comprehensive testing environment for the StockUp backend, combining high-speed unit logic validation with robust API integration testing.

## 🏗️ Folder Structure & Layering

The suite is organized into two primary layers, each with its own configuration to balance speed and reliability:

* **`tests/unit/`**: Validates Domain Entities and Service logic. These tests are isolated from external dependencies (repositories, notification services) using **Mocks**.
* **`tests/integration/`**: Full-cycle API tests. They interact with a live PostgreSQL instance (Port 5433) to verify the synergy between FastAPI routes, Services, and Database models.
* **`tests/factories.py`**: Centralized data generation layer using the **Factory Pattern** to ensure consistent object creation across all testing layers.

## ⚙️ Configuration & Fixtures

We use a hierarchical `conftest.py` structure to manage the testing environment effectively:

### 1. Global Context-Aware Helpers (`tests/conftest.py`)
This file defines dynamic fixtures (`any_user`, `any_home`, `any_product`, etc.) that intelligently adapt to the test environment:
* **Database Integration**: These fixtures detect if a `db_session` is active in the current test. If it is (Integration), they automatically persist the generated entity to the DB. If not (Unit), they return a pure in-memory domain object.
* **Boilerplate Reduction**: They serve as the primary entry point for tests, abstracting away the complexity of the underlying `factories.py`.

### 2. Integration Infrastructure (`tests/integration/conftest.py`)
This file handles the heavy lifting for API and Database lifecycle management:
* **Clean-Slate Strategy**: Manages a dedicated PostgreSQL session. To ensure total isolation, it utilizes a **Cascade Truncate** strategy after every test execution, wiping all tables while respecting foreign key constraints.
* **FastAPI Overrides**: Automatically injects the isolated `db_session` into the application's dependencies and bypasses real authentication by overriding `get_current_user_id` with a fixed `auth_user` UUID.

## 🛠️ Maintenance & Best Practices

To maintain the suite's integrity, please follow these engineering guidelines:

### Grouping & Structure
Group tests within classes named after the feature or method being validated. This ensures clean reporting and easy navigation.
```python
class TestStockService:
    async def test_add_product_success(self, stock_service, auth_setup, ...):
        # Use auth_setup for a pre-linked home and user
```

### Development Guidelines
1.  **Flush, don't Commit**: In integration tests, use `db_session.flush()`. This makes data visible to the API while allowing the global rollback/truncate mechanism to handle cleanup.
2.  **Mock Side-Effects**: Always mock services with external side effects (e.g., FCM push notifications or external catalog providers) in the unit layer to keep tests fast and deterministic.
3.  **Leverage Factories**: Use the existing factory methods in `conftest.py` to seed data. This ensures that changes to model schemas only require a single update in the factory layer.

## 🚀 Execution Commands
* **Setup docker container `docker compose up -d`
* **Run the full suite**: `pytest`
* **Unit layer only**: `pytest tests/unit`
* **Integration layer only**: `pytest tests/integration`
* **Generate Coverage Report**: `pytest --cov=src --cov-report=html`