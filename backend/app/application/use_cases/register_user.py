from app.application.dto.auth import AuthResult
from app.core.security import create_access_token, hash_password
from app.infrastructure.db.repositories.user_repository import UserRepository


class EmailAlreadyRegisteredError(Exception):
    pass


async def register_user(repo: UserRepository, email: str, password: str) -> AuthResult:
    existing = await repo.get_by_email(email)
    if existing is not None:
        raise EmailAlreadyRegisteredError(email)

    user = await repo.create(email=email, hashed_password=hash_password(password))
    token = create_access_token(subject=str(user.id))
    return AuthResult(access_token=token, user_id=str(user.id), email=user.email, role=user.role)