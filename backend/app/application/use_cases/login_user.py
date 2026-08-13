from app.application.dto.auth import AuthResult
from app.core.security import create_access_token, verify_password
from app.infrastructure.db.repositories.user_repository import UserRepository


class InvalidCredentialsError(Exception):
    pass


async def login_user(repo: UserRepository, email: str, password: str) -> AuthResult:
    user = await repo.get_by_email(email)
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()

    token = create_access_token(subject=str(user.id))
    return AuthResult(access_token=token, user_id=str(user.id), email=user.email, role=user.role)