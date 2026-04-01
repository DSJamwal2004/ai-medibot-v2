from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.utils.logger import get_logger

logger = get_logger("auth_service")


class AuthError(Exception):
    pass


def register_user(db: Session, email: str, password: str) -> User:
    if db.query(User).filter(User.email == email).first():
        raise AuthError("Email already registered")

    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("user_registered", user_id=user.id)
    return user


def login_user(db: Session, email: str, password: str) -> str:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise AuthError("Invalid credentials")
    if not user.is_active:
        raise AuthError("Account inactive")

    token = create_access_token(subject=str(user.id))
    logger.info("user_authenticated", user_id=user.id)
    return token
