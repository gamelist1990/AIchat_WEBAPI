from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = "test"  # ここに設定したいパスワードを入力
hashed_password = pwd_context.hash(password)
print(f"hash passworld: {hashed_password}")

pas = " $2b$12$0TsIwyv50SLpZRc4SSMjQeFWPxGKFhTvVx1RCAKLNTk5HFUMlqqnq"