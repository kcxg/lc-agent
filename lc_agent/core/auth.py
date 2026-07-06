import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt


class AuthService:
    def __init__(self, secret: str, token_expire_days: int = 7):
        if len(secret) < 16:
            raise ValueError("Auth secret must be at least 16 characters")
        self._secret = secret
        self._token_expire_days = token_expire_days

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

    def create_token(self, *, user_id: str, username: str, role: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=self._token_expire_days)
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": expire,
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def decode_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            return payload
        except JWTError:
            return None

    def generate_random_password(self, length: int = 16) -> str:
        return secrets.token_urlsafe(length)[:length]
