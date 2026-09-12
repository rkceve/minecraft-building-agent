# 2 分デモ動画 撮影手順（提出 15:30）

準備: ゲーム内で時刻は昼固定済み。OBS か Windows ゲームバー（Win+G）で 1080p 録画。チャット欄が映る位置に。

| 秒 | 映すもの | 台詞（字幕でも可） |
|---|---|---|
| 0–10 | 画面: 大聖堂（あなたの litematic を貼るか、スクショ）→ タイトル | "A master builder's cathedral. Can an agent build like him?" |
| 10–30 | 比較用の素の Astra 版（原点）を一周 | "Same photos, same prompt. Plain GPT-6 Astra." |
| 30–55 | ハーネス版（x=-60）を一周。柱・窓・軒・土台に寄る | "Add two things: his principles as a system prompt, and his cathedral's placements as helper functions. Astra composes; the harness places blocks." |
| 55–85 | 塔を見ながら `!fix この尖塔をもっと高くして` を打つ → 待ち時間はカット → 差分が下から積み上がる様子 | "Look at something, say what to change. Only the diff is replaced, live." |
| 85–105 | 2 回目の `!fix`（窓の中央寄せ）の適用アニメーション | "Every element has a name, so 'this window' means this window." |
| 105–120 | ターミナル: bridge.log の 3 行（受信→Astra 完了→適用 +N -M）と README | "Chat in, code edit by Astra, voxel diff out. Repo and prompts are public." |

撮影のこつ:
- 待ち時間（Astra 1〜4 分）は必ずカット。適用アニメーション（10〜40 秒）は等速で見せる。
- `!fix` の前に `!status` で空いていることを確認。
- 失敗した時のために、`!undo` で直前に戻せる。

提出物: タイトル / 説明（README 冒頭 3 段落を流用）/ 公開 GitHub URL / 動画 / SNS 投稿（#AgentsEverywhere、AI Tinkerers とパートナーをタグ）。
