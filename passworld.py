from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = "gamelist1990s"  # ここに設定したいパスワードを入力
hashed_password = pwd_context.hash(password)
print(f"hash passworld: {hashed_password}")