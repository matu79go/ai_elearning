#!/bin/bash

# requirements.txtのハッシュ値を保存するファイル
HASH_FILE="/tmp/requirements.hash"
CURRENT_HASH=$(md5sum /app/requirements.txt | awk '{print $1}')

# 前回のハッシュ値を読み込む
if [ -f "$HASH_FILE" ]; then
    PREVIOUS_HASH=$(cat "$HASH_FILE")
else
    PREVIOUS_HASH=""
fi

# ハッシュ値が変わっている場合のみインストール
if [ "$CURRENT_HASH" != "$PREVIOUS_HASH" ]; then
    echo "requirements.txt has changed. Installing dependencies..."
    pip install --no-cache-dir -r /app/requirements.txt
    echo "$CURRENT_HASH" > "$HASH_FILE"
    echo "Dependencies installed."
else
    echo "Dependencies are up to date."
fi

# 引数で渡されたコマンドを実行
exec "$@"
