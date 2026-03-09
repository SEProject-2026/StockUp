import pytest
from tests.container import testing_container
from src.domain.user import User

# --- Tests ---

@pytest.mark.asyncio
async def test_save_and_get_user():
    """
    Verifies that a user can be successfully saved to the PostgreSQL DB
    and retrieved correctly using async calls.
    """
    # Arrange
    # Access the repo directly from the container (it is already initialized with the DB session)
    repo = testing_container.user_repo 
    new_user = User(
        email="integration_test@example.com", 
        hashed_password="hashed_secret", # Make sure this matches your Domain model field name
        name="Integration Tester"
    )

    # Act
    # We must await the save operation because it is an async function
    saved_user = await repo.save(new_user)

    # Assert
    assert saved_user.id is not None
    assert saved_user.email == "integration_test@example.com"

    # Verify retrieval from DB (also needs await)
    fetched_user = await repo.get_by_email("integration_test@example.com")
    assert fetched_user is not None
    assert fetched_user.id == saved_user.id
    assert fetched_user.name == "Integration Tester"

@pytest.mark.asyncio
async def test_duplicate_email_should_fail():
    """
    Verifies that the database enforces the unique constraint on the email field.
    """
    repo = testing_container.user_repo
    user1 = User(email="unique@example.com", hashed_password="123", name="User One")
    
    # First save must be awaited
    await repo.save(user1)

    user2 = User(email="unique@example.com", hashed_password="456", name="User Two")
    
    # Expect an exception when trying to save the duplicate
    with pytest.raises(Exception): 
        await repo.save(user2)