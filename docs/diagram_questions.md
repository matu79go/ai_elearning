# 図形問題への図（SVG）付与ガイド

数学の**図形問題（体積・表面積・面積・角度など）には、ラベル付きの図を必ず付ける**。
図があると子供が問題を解きやすい。このドキュメントは、その標準アプローチをまとめたもの。

> 初出: Y7 Maths Unit 7「Volume of Cuboids」(material 283) /「Surface Area of a Prism」(material 284)。
> 今後、同種の図形マテリアルが来たら同じやり方で対応する。

---

## 1. 仕組み（表示パイプラインは完成済み）

- `questions` テーブルと `drill_questions` テーブルに **`chart_svg` カラム**がある。
- 子供画面 `templates/child/quiz.html`・`templates/child/drill.html` が `chart_svg` をそのまま描画する。
  （管理画面 `templates/admin/material_chunk_detail.html` 等でも表示）
- つまり「1問ごとにSVG文字列を持たせる」だけで図が出る。**新しい表示実装は不要**。

## 2. 作図モジュール `services/shape_svg.py`

立体図形のラベル付きSVGを生成する（依存なし・Python純正・斜投影でPDF風）。
グラフ系（円/棒/折れ線/関数）は別途 `services/chart_svg.py`。

| 関数 | 用途 |
|------|------|
| `cuboid_svg(w_label, h_label, d_label, *, wv, hv, dv, face_label=None)` | 直方体。**立方体**は `wv=hv=dv` で表現。`face_label` で前面に `V = 84 cm³` 等を表示 |
| `triangular_prism_svg(base_label, height_label, hyp_label, length_label, *, bv, hv, lv)` | 直角三角形を断面にもつ三角柱（直角マーク付き） |

- `*_label` は辺に表示する文字列（例 `'5 cm'`, `'? cm'`）。
- `*v`（`wv`/`hv`/`dv` 等）は**見た目の比率**に使う相対値。
- 新しい図形（円柱・角錐・複合図形など）が来たら、この方針で**描画関数を追加**する。

## 3. 生成の鉄則：数値と図をPythonで同時に決める

**LLM任せにしない。** 数値も図も**Pythonコードが同時に決める**ことで、図とテキストと正答が必ず一致する。
パラメトリックなテンプレートを書く（`batch/generate_shape_questions.py` が実例）。

各問題ビルダーの戻り値の形:
```python
{
  'question_text': '...',
  'options': [{'label':'A','text':'12 cm³'}, ...],   # A–D
  'correct_answer': 'B',
  'explanation': '...',
  'chart_svg': cuboid_svg(...),   # 図が不要な概念/文章題は None
}
```

### 誤答（distractor）の作り方
典型的なミスを選択肢に入れる:
- 体積問題 → 表面積 `2(lw+lh+wh)`、`l+w+h`、`l×w` など
- 表面積問題 → 体積 `l×w×h`、`lw+lh+wh`（×2忘れ）、`2(l+w+h)` など
- 三角柱の表面積 → 体積 `½ab×L`、`周×長さ`のみ（三角形2枚を忘れる）など

`build_mc(correct_val, distractors, unit_fmt)`（実装例参照）が、正答＋重複しない誤答3つを A–D にシャッフルして返す。

## 4. どの問題に図を付けるか

- **図を付ける**: 1つの立体の寸法から計算する問題（体積・表面積・欠けた辺・立方体の辺 など）。
- **テキストのまま**: 概念問題（「体積の単位は？」「公式は？」）、多段階/容量・単位換算の文章題、複合図形で作図が難しいもの。
- **テスト数は他のマテリアルと揃える**（例: KS3 は 15問/チャンク）。図付きに**差し替え**ても総数は維持する。

実績（material 283/284、各チャンク15問）: Volume 13・Missing/Cubes 14・Real-life Vol 7・SA Cuboid 13・SA Prism 14・Real-life SA 7 が図付き。

## 5. 投入前の検証（必須）

本番に入れる前に、**ローカルでビルダーだけを実行**して次を確認する:
- 各チャンクちょうど15問
- 選択肢は A–D で**テキスト重複なし**、`correct_answer` が選択肢に含まれる
- `chart_svg` が**整形式XML**（`xml.etree.ElementTree.fromstring` でパース）
- 必要なら Playwright で画像化して見た目を目視（`npx playwright screenshot`）

## 6. 本番反映の手順

本番 app は `.:/app` をマウントしているので、**ホストの該当ディレクトリへ scp すれば即コンテナ内で使える**（再ビルド不要）。

```bash
# 1) 作図モジュール & バッチを本番へ
scp -i ~/.ssh/github_matu79go services/shape_svg.py \
    ubuntu@153.126.192.71:/home/ubuntu/ai_elearning/services/
scp -i ~/.ssh/github_matu79go batch/generate_shape_questions.py \
    ubuntu@153.126.192.71:/home/ubuntu/ai_elearning/batch/

# 2) dry-run（インポート確認）→ 本実行
ssh -i ~/.ssh/github_matu79go ubuntu@153.126.192.71 \
  "cd ~/ai_elearning && sudo docker exec elearn_app python batch/generate_shape_questions.py --dry-run"
ssh -i ~/.ssh/github_matu79go ubuntu@153.126.192.71 \
  "cd ~/ai_elearning && sudo docker exec elearn_app python batch/generate_shape_questions.py"
```

注意:
- `questions.source` は ENUM（`llm_generated` / `rule_based` 等）。手組み問題は **`source='rule_based'`**、識別用に `template_id`（例 `'shape_svg'`）を付ける。
- 既存問題を入れ替える時は、先に `answer_history`（`models.material.AnswerHistory`）の該当行を削除してから `questions` を削除する。

## 7. 関連ファイル

- `services/shape_svg.py` — 立体の作図
- `batch/generate_shape_questions.py` — チャンク別に図付き問題を再生成（パラメトリックの実例）
- `batch/create_volume_materials.py` — マテリアル＋チャンク作成の型
- `services/chart_svg.py` — グラフ系SVG（円/棒/折れ線/関数）
