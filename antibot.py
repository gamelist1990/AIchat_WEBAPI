import time
from datetime import datetime, timedelta

# ユーザーのブロック状態を管理する辞書
blocked_users = {}

# リクエスト間隔（秒）
request_interval = 1

# ユーザーIDと最後のリクエスト時間のマッピング
last_request = {}

# ユーザーIDとリクエストカウントのマッピング
request_count = {}

# 1秒あたりの最大リクエスト数
max_requests_per_second = 8

# BANの持続時間（時間）
ban_duration = timedelta(hours=1)

# BAN履歴を保持するリスト
ban_history = []

def check_and_ban(user_id: str, request):
    """ユーザーがボットかどうかチェックし、必要に応じてBANします。

    Args:
        user_id (str): ユーザーID。
        request: FastAPIのリクエストオブジェクト。

    Returns:
        tuple: (bool, str): 
            - True: ユーザーがBANされた場合。
            - False: ユーザーがBANされなかった場合。
            - str: BANされた場合の理由。
    """

    # 最後のリクエスト時間を更新
    last_request[user_id] = datetime.now()

    # リクエストカウントを更新
    if user_id in request_count:
        request_count[user_id] += 1
    else:
        request_count[user_id] = 1

    # 1秒あたりのリクエスト数が最大値を超えた場合、またはBANされている場合
    if (datetime.now() - last_request[user_id] < timedelta(seconds=request_interval) and request_count[user_id] > max_requests_per_second) or (user_id in blocked_users and datetime.now() < blocked_users[user_id]):
        # BANの理由を設定
        reason = "短時間に大量のリクエストを検知しました。1時間はアクセスできません。"

        # ユーザーをBAN
        ban_user(user_id)

        return True, reason

    return False, ""

def ban_user(user_id: str):
    """ユーザーをBANします。

    Args:
        user_id (str): ユーザーID。
    """
    blocked_users[user_id] = datetime.now() + ban_duration
    ban_history.append({"user_id": user_id, "ban_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

def unban_user(user_id: str):
    """ユーザーのBANを解除します。

    Args:
        user_id (str): ユーザーID。
    """
    if user_id in blocked_users:
        del blocked_users[user_id]  # blocked_users から user_id を削除

    # ban_history から user_id に対応する履歴を削除
    global ban_history
    ban_history = [entry for entry in ban_history if entry["user_id"] != user_id] 

def get_ban_history():
    """BAN履歴を取得します。

    Returns:
        list: BAN履歴のリスト。
    """
    return ban_history

def get_banned_count():
    """現在のBAN人数を取得します。

    Returns:
        int: 現在のBAN人数。
    """
    return len(blocked_users)