"""
LLM API レートリミッター

メモリ内カウンターで実装（Redis不要、単一プロセス向け）
アプリ再起動でリセットされるが、コスト保護には十分。
"""

import time
import threading
from collections import defaultdict

# ---- 設定 ----
# ユーザー別リミット
USER_HOURLY_LIMIT = 20      # 1ユーザー/1時間
USER_DAILY_LIMIT = 50       # 1ユーザー/1日

# グローバルリミット
GLOBAL_DAILY_LIMIT = 500    # 全体/1日

# ヒントチャット: 1問あたりの会話数上限
HINT_CHAT_LIMIT = 5         # 1問につきAIチャット5回まで


class RateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        # user_id -> [(timestamp, ...), ...]
        self._user_calls = defaultdict(list)
        # [(timestamp, ...), ...]
        self._global_calls = []
        # (user_id, question_id) -> count
        self._hint_chat_counts = defaultdict(int)

    def _cleanup(self):
        """古いエントリを削除"""
        now = time.time()
        one_hour_ago = now - 3600
        one_day_ago = now - 86400

        # ユーザー別: 24時間以上前を削除
        for uid in list(self._user_calls.keys()):
            self._user_calls[uid] = [
                t for t in self._user_calls[uid] if t > one_day_ago
            ]
            if not self._user_calls[uid]:
                del self._user_calls[uid]

        # グローバル: 24時間以上前を削除
        self._global_calls = [
            t for t in self._global_calls if t > one_day_ago
        ]

    def check_and_record(self, user_id):
        """
        LLM呼び出し可否をチェックし、OKなら記録してTrueを返す。
        NGならエラーメッセージ文字列を返す。
        """
        with self._lock:
            self._cleanup()
            now = time.time()
            one_hour_ago = now - 3600

            # グローバル日次チェック
            if len(self._global_calls) >= GLOBAL_DAILY_LIMIT:
                return 'Daily limit reached. AI hints are temporarily unavailable. Please try again tomorrow!'

            # ユーザー時間別チェック
            user_ts = self._user_calls.get(user_id, [])
            hourly = sum(1 for t in user_ts if t > one_hour_ago)
            if hourly >= USER_HOURLY_LIMIT:
                return 'You have used too many hints this hour. Take a break and try again later!'

            # ユーザー日次チェック
            if len(user_ts) >= USER_DAILY_LIMIT:
                return 'You have reached your daily hint limit. Come back tomorrow for more help!'

            # OK — 記録
            self._user_calls[user_id].append(now)
            self._global_calls.append(now)
            return True

    def check_hint_chat(self, user_id, question_id):
        """
        1問あたりのAIチャット回数をチェック。
        OKならカウントしてTrueを返す。NGならエラーメッセージ。
        """
        with self._lock:
            key = (user_id, question_id)
            if self._hint_chat_counts[key] >= HINT_CHAT_LIMIT:
                return f'You can ask up to {HINT_CHAT_LIMIT} questions per problem. Try solving it with the hints you have!'
            self._hint_chat_counts[key] += 1
            return True

    def get_stats(self):
        """現在の統計情報（管理画面用）"""
        with self._lock:
            self._cleanup()
            now = time.time()
            one_hour_ago = now - 3600
            return {
                'global_daily': len(self._global_calls),
                'global_daily_limit': GLOBAL_DAILY_LIMIT,
                'active_users': len(self._user_calls),
                'global_hourly': sum(1 for t in self._global_calls if t > one_hour_ago),
            }


# シングルトンインスタンス
llm_limiter = RateLimiter()
