from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordEncoder:
    @staticmethod
    def validate(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @staticmethod
    def encode(password: str) -> str: # שיניתי מ-hash ל-encode שיתאים לשם
        return pwd_context.hash(password)