# Blog #005: 子供用UI刷新・クイズフロー再設計・自由回答NLP/LLM採点

**Date:** 2026-03-15

## Overview

子供用学習画面のUI全面刷新と、クイズの回答→採点フローを根本から再設計した。自由回答の採点には spaCy（NLP）+ GPT-5 Nano（LLM）のハイブリッド方式を導入し、コスト0.005円/問で実用的な精度を実現した。

---

## 1. UI刷新: 2カラムレイアウト

### Before

各画面（subjects, units, section, quiz, result）がバラバラなデザインで、灰色背景 `#f0f0f5` に白カード。サイドバーなし。

### After

`study.html` のプロトタイプを参考に、**全画面を統一した2カラムレイアウト**に刷新：

- **背景**: 紫グラデーション `linear-gradient(135deg, #667eea, #764ba2)`
- **PC/タブレット (768px+)**: glassmorphicサイドバー (280px→320px) + 白コンテンツカード
- **スマホ**: 1カラム + アコーディオンパネル

### 共通ベーステンプレート

`templates/child/child_base.html` を新規作成。全子供画面がこれを継承：

```
child_base.html (extends base.html)
  ├── subjects.html     サイドバー: プロフィール+統計
  ├── units.html        サイドバー: 教科ナビゲーション
  ├── section.html      サイドバー: セクションナビゲーション
  ├── quiz.html         サイドバー: セッション統計+問題ナビ
  └── quiz_result.html  サイドバー: スコア+問題結果
```

### サイドバーのコンテキスト適応

各画面でサイドバーの内容が変わる設計：

| 画面 | サイドバー内容 |
|------|---------------|
| Subjects | 子供プロフィール（アバター+名前）+ ポイント/レベル/ストリーク |
| Units | 全教科リスト（現在の教科をハイライト） |
| Section | 同ユニット内のセクション一覧（現在のセクションをハイライト） |
| Quiz | セッション統計 + 問題ナビゲーション（確定/正解/不正解の色分け） |
| Result | スコアサマリー + 問題別結果リスト |

### 教科の絵文字・色マッピング

`child_base.html` で `SUBJ` 辞書を定義し、全テンプレートで共有：

```python
SUBJ = {
    'Science':   {'emoji': '🔬', 'bg': '#dbeafe', 'color': '#1d4ed8'},
    'Maths':     {'emoji': '🔢', 'bg': '#fef3c7', 'color': '#92400e'},
    'English':   {'emoji': '📖', 'bg': '#ede9fe', 'color': '#6d28d9'},
    ...
}
```

### ルート変更

サイドバーに必要なデータを追加でテンプレートに渡すよう `child_learn.py` を修正：

- `child_units`: `all_subjects`（サイドバーの教科ナビ用）
- `child_section`: `all_chunks`（サイドバーのセクションナビ用）

---

## 2. クイズフロー再設計

### 旧設計の問題点

旧設計は「1問ずつサーバーに即時送信して採点」方式だった：

- 回答した瞬間にDB書き込み → 取り消し不可
- 問題間を移動するとJS状態がリセット
- 「答え合わせ」という概念がなく、学習体験として不自然

### 新設計: 確定→答え合わせ方式

Duolingo等の一般的なe-learningに倣い、2フェーズに分離：

```
【フェーズ1: 回答フェーズ（JSのみ、サーバー通信なし）】

  Q1: 選択 → [Confirm] → JSに保存、ロック表示 → 自動で次へ
  Q2: 選択 → [Confirm] → JSに保存、ロック表示 → 自動で次へ
  ...
  ・サイドバーで任意の問題にジャンプ可能
  ・ロック済みの問題 → [Change] でロック解除 → 再回答可能
  ・全問ロック → [Check Answers!] ボタンが出現

【フェーズ2: 答え合わせ（一括サーバー送信）】

  [Check Answers!] クリック
    ↓
  全回答をまとめて POST /child/quiz/<chunk_id>/check
    ↓
  サーバーで一括採点 → JSON レスポンス
    ↓
  各問題に正誤・解説・ポイント表示
    ↓
  [See Results →] で結果画面へ
```

### JS状態管理

```javascript
const answers = {};       // idx → { answer: string, locked: boolean }
let checkResults = null;  // 答え合わせ前: null, 後: サーバーレスポンス
```

### UIの3状態

| 状態 | 選択肢の見た目 | ボタン |
|------|---------------|--------|
| **Open** (未回答/変更中) | クリック可能、選択時に青ボーダー | [Confirm] |
| **Locked** (確定済み) | 選択済みが青、他はdisabled | [Change] + (全問確定時 [Check Answers!]) |
| **Checked** (採点済み) | 正解=緑、不正解=赤、正答=緑 | [See Results →] |

### サイドバー/モバイルの色分け

| 状態 | サイドバー数字 | モバイルピル |
|------|--------------|-------------|
| 未回答 | グレー | グレー |
| 確定済み | インディゴ (#6366f1) | インディゴ |
| 正解 | グリーン (#10b981) | グリーン |
| 不正解 | レッド (#ef4444) | レッド |

### スコアバナー

答え合わせ後、クイズカードの上にスコアバナーを表示：

```
🎉 5 / 7 correct!
71%
+3 pts
```

---

## 3. 自由回答の採点システム

### 設計の経緯

自由回答の採点は3段階で進化した：

#### 第1世代: 完全一致

```python
is_correct = (user_answer.lower() == correct_answer.lower())
```

問題: `correct_answer` が空の問題が多数（模範解答は `reference_answer` に格納）。少しでも表現が違うと不正解。

#### 第2世代: spaCy NLPキーワードマッチ

```python
pip install spacy
python -m spacy download en_core_web_sm
```

spaCyで以下を実装：
- レンマ化（moving → move, processes → process）
- ストップワード除去（a, the, is, does...）
- トークン単位のマッチング（レンマ+原形の両方で比較）
- カスタムストップワードリスト（spaCyはmove等を除外するため独自定義）

**問題点**: 模範解答が長い場合、キーワードカバー率で評価するとしきい値の調整が困難。短い正解は通らず、曖昧な回答が通る境界ケースが多発。

#### 第3世代（現行）: GPT-5 Nano LLM採点 + spaCyフォールバック

LLMに「模範解答との一致率を0-100で返す」だけの簡単なタスクを与える：

```python
prompt = """You are grading a Year 7 student's answer.
Return ONLY a number 0-100.

Scoring guide:
- 100: Covers all key concepts with explanation
- 70: Covers the main idea AND gives specific reasons/details
- 40: States the main idea AND at least one supporting reason
- 20: Only states the conclusion without any reasoning or detail
- 0: Completely wrong or irrelevant

IMPORTANT: Just stating a fact without explaining WHY scores only 20.
The student must show reasoning.

Reference: {reference_answer}
Student: {user_answer}

Score:"""
```

### 採点フロー（3段階フォールバック）

```
1) correct_answer と完全一致？ → 正解
2) reference_answer にカンマ区切り代替回答？ → いずれかと一致で正解
3) 10文字以上の長文回答？
   → GPT-5 Nano で一致率判定 → 30%以上で正解
   → API障害時 → spaCy キーワードマッチにフォールバック
```

### プロンプト設計のポイント

LLMに「スコアをつけろ」ではなく「一致率を返せ」と指示する理由：

| 方式 | LLM負荷 | 精度 | コスト |
|------|---------|------|--------|
| 「この回答を0-10で採点して」 | 高い（理解+判断） | モデル依存 | 高い |
| **「模範解答との一致率を返して」** | **低い（比較だけ）** | **安定** | **安い** |

安いモデル（GPT-5 Nano）でも安定した出力が得られるのは、「比較」という単純タスクだから。

### しきい値の決定

テストで確認したスコア分布：

| 回答内容 | LLMスコア | 判定 |
|---------|-----------|------|
| 完全コピー | 100 | 正解 |
| 主要概念+理由あり | 40-70 | 正解 |
| 結論だけ（理由なし） | 20 | **不正解** |
| 的外れ | 0 | 不正解 |

→ **30以上で正解** に設定。「結論だけ書いて理由を書かない」回答は不正解になる。

### コスト

- **GPT-5 Nano**: Input $0.05/1M tokens, Output $0.40/1M tokens
- 1問あたり: 入力~500トークン + 出力~20トークン ≈ **0.005円**
- 1000問採点しても**5円**

### API呼び出し: GPT-5 Responses API

GPT-5からは新しい Responses API を使用（Chat Completions APIからの移行）：

```python
from openai import OpenAI

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

response = client.responses.create(
    model='gpt-5-nano',
    input=prompt,
)

score = response.output_text  # "50" のような数値テキスト
```

**注意**: `gpt-5-nano` は `temperature` パラメータ非対応。指定するとエラーになる。

### spaCyフォールバックの設計

API障害時に自動的にspaCyに切り替わる：

```python
def _grade_free_response(user_answer, correct_answer, reference_answer):
    ...
    score = _llm_grade(user_answer, match_target)
    if score is not None:
        return score >= 30
    # LLM失敗時 → spaCy フォールバック
    return _fuzzy_match(user, match_target.lower())
```

spaCyの判定ロジック：
- カスタムストップワード除去（spaCyデフォルトは `move` 等を除外するため独自リスト使用）
- トークン単位マッチング（レンマ+原形テキストの両方で比較）
- 判定: 3語以上一致 & precision >= 50%、または 2語以上 & 5単語以上の文

### Docker対応

`Dockerfile` に spaCy モデルのダウンロードを追加：

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm
```

spaCyモデルはプロセス内でキャッシュし、毎回ロードしない：

```python
_nlp_model = None

def _get_nlp():
    global _nlp_model
    if _nlp_model is None:
        import spacy
        _nlp_model = spacy.load('en_core_web_sm')
    return _nlp_model
```

---

## 4. バグ修正

### QuestionMastery.attempts が None

新規 `QuestionMastery` レコードの `attempts` カラムがデフォルト `None` のため、`+= 1` で `TypeError`。`(mastery.attempts or 0) + 1` に修正。

### correct_answer が空の自由回答問題

Oak National Academyからインポートした自由回答問題の多くで `correct_answer` が空文字。模範解答は `reference_answer` に格納されている。`correct_answer` が空なら `reference_answer` にフォールバックするよう修正。

### 不正解時の模範解答表示

答え合わせ後、不正解の問題で模範解答が表示されていなかった。`Reference: ...` として全文表示するよう修正。

---

## 5. テスト結果

### 穴埋め問題 (Q146)

| 入力 | 判定 | 方式 |
|------|------|------|
| "life cycle" (正解) | ✅ | 完全一致 |
| "life" (代替回答) | ✅ | カンマ区切り候補マッチ |
| "life processes" (代替) | ✅ | カンマ区切り候補マッチ |
| "death" | ❌ | - |

### 長文自由回答 (Q288: 車はなぜ生物でないか)

| 入力 | LLMスコア | 判定 |
|------|-----------|------|
| 模範解答全文コピー | 100 | ✅ |
| 「because it does not carry out all the life processes」 | 40 | ✅ |
| 「A car is not a living organism」(結論だけ) | 20 | ❌ |
| 「Cars are fast」(的外れ) | 0 | ❌ |

### 長文自由回答 (Q289: 生徒の誤りを訂正)

| 入力 | LLMスコア | 判定 |
|------|-----------|------|
| 「Both wrong. Plants do move but slowly」 | 70 | ✅ |
| 「Plants are living organisms」(結論だけ) | 20 | ❌ |
| 「I like plants」 | 0 | ❌ |

---

## 6. 次回TODO

- [ ] ポイント配分テスト（正解済み再回答で0pt、不正解→正解で1pt）
- [ ] 4択選択肢のランダム並び替え
- [ ] publish/unpublish機能（管理画面）
- [ ] 全教科を publish して子供画面に反映
- [ ] セクション要約のLLM生成・キャッシュ
