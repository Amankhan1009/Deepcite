from dataclasses import dataclass


@dataclass
class AuthResult:
    """What a use case hands back to the router — plain data, no
    framework types, so use cases stay testable without FastAPI/Pydantic."""

    access_token: str
    user_id: str
    email: str
    role: str