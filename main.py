from app.db.schema import init_db
from app.repositories.user_repository import UserRepository
from app.repositories.admin_repository import AdminRepository
from app.repositories.customer_repository import CustomerRepository
from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    InvalidCredentialsError,
)
from app.services.role_service import RoleService


def main():
    # Initialize database schema (safe to call multiple times)
    init_db()

    user_repo = UserRepository()
    auth_service = AuthService(user_repo)

    # --------- REGISTER ---------
    try:
        user = auth_service.register(
            username="radoslav",
            email="radoslav@example.com",
            name="Radoslav Velkov",
            password="secret123",
        )
        print("Registered:", user)
    except (EmailAlreadyExistsError, UsernameAlreadyExistsError) as e:
        print("Register skipped:", e)

    # --------- LOGIN ---------
    try:
        logged_user = auth_service.login(
            email="radoslav@example.com",
            password="secret123",
        )
        print("Logged in:", logged_user)
    except InvalidCredentialsError as e:
        print("Login failed:", e)
        return

    # --------- ROLES ---------
    role_service = RoleService(
        AdminRepository(),
        CustomerRepository(),
    )

    # Make the user a CUSTOMER (comment out if already done)
    role_service.make_customer(logged_user.id, currency="BGN")

    # Uncomment if you want to test admin role
    # role_service.make_admin(logged_user.id)

    logged_user = role_service.enrich_user_role(logged_user)
    print("User role:", logged_user.role)


if __name__ == "__main__":
    main()
