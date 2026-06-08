# CLAUDE.md（原本 / マスターテンプレート）

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> このファイルは **CLAUDE.md の原本（Source of Truth）** です。`izumacha` の各リポジトリにある
> `CLAUDE.md` から、**プロジェクト固有でない共通の規約だけ**を重複を排除して集約したものです。
> 新規リポジトリを作るときはこのファイルをコピーし、`{{ }}` のプレースホルダ部分（プロジェクト概要・
> コマンド・アーキテクチャなど）だけを埋めてください。既存リポジトリの `CLAUDE.md` を見直すときは、
> この原本との差分を確認し、共通規約をここに合わせて統一します。原本そのものを更新したら、各リポジトリへ
> 反映する運用とします。
>
> 集約元リポジトリ: `profile-portfolio` / `my-task-manager` / `my-first-ai-app` /
> `helpdesk-hub` / `incident-insight` / `AI-Docker-Environment`

---

## 0. このテンプレートの使い方

- **共通規約（§4 以降）はそのまま全リポジトリで適用する。** 文言を勝手に薄めず、必要なら原本側を改訂してから各リポジトリへ反映する。
- **プロジェクト固有の章（§1〜§3）はリポジトリごとに書き換える。** ここに書ききれない詳細（ドメインルール・ファイル構成・特殊な運用）は各リポジトリの `CLAUDE.md` に追記してよい。
- **「正本（Source of Truth）」を必ず明示する。** 要件定義書や計画書（例: `docs/requirements.md`, `docs/smb-dx-pivot-plan.md`）がある場合、実装より仕様を優先し、衝突したら**先に仕様側を改訂してから実装を変更する**。同一 PR 内で仕様ドキュメントも更新する。

---

## 1. プロジェクト概要（リポジトリごとに記述）

{{ このリポジトリが何をするものか、技術スタック、UI 言語（多くは日本語）を 1〜3 段落で説明する。
   例: 「`my-task-manager` は Python + tkinter 製の GUI タスクプランナー」。
   UI テキスト・エラーメッセージ・テストセレクタが日本語の場合は、編集時にそれを保持する旨を明記する。 }}

## 2. コマンド（リポジトリごとに記述）

{{ セットアップ・実行・テストを「コピペで動くコマンド」として列挙する。README 冒頭にも同じ手順を置く。
   例:
   ```bash
   npm run dev          # 開発サーバー
   npm run build        # 本番ビルド
   npm run lint         # ESLint
   npm run typecheck    # tsc --noEmit
   npm run test         # ユニットテスト
   ```
   単体テストの実行例（特定ファイル・特定ケース）も書いておくと便利。 }}

## 3. アーキテクチャ（リポジトリごとに記述）

{{ スタック一覧と、ディレクトリ／レイヤ構成、主要ファイルの責務、再利用すべき既存実装
   （バリデーション・状態遷移テーブル・リポジトリ Port など）を記述する。
   ファイルを追加・改名・削除したら、この章と README を必ず同時に更新する（コードとドキュメントの乖離を許さない）。 }}

---

## 4. 実装フロー（プランモード必須）

コード変更を伴う作業に着手する前に、**必ず Claude Code のプランモード（Plan Mode）で計画を作成し、ユーザーの承認を得てから実装に移る**こと。

- 対象: 機能追加・改修・リファクタ・バグ修正など、ソースコード／スキーマ／設定ファイルを変更するすべての作業。
- 計画には以下を含める:
  1. **Context**: 何を、なぜ変更するのか。正本（要件定義書・計画書）のどの項目に対応するか。
  2. **変更対象ファイル**: 修正・追加するファイルの絶対パス（既存ファイルは行番号や関数名まで具体化）。
  3. **再利用する既存実装**: 既にある関数・モジュール・Port を優先して再利用する。新規作成する場合はその理由を明記。
  4. **検証方法**: lint / typecheck / test（必要に応じて E2E）と、画面確認の手順。
- **例外**: タイポ修正・コメントのみの変更・1 行以下の自明な修正は計画作成を省略してよい。それ以外は必ず `ExitPlanMode` でユーザー承認を得る。
- 計画と異なる実装が必要になったら、いったん手を止めてプランを更新（または `AskUserQuestion` で確認）してから続行する。

## 5. コメント規約（最優先・本方針はプロジェクト固有）

- **1 行ごとに初心者でも意味がわかるコメントを書く。** コード 1 行ごとに、プログラミング初心者でも処理内容が理解できる日本語コメントを付ける。変数宣言・条件分岐・関数呼び出し・ループ・`return` など、すべての実行行に対して「何をしているか」を説明するコメントを必ず添える（型定義の単純な再エクスポートなど明らかに自明な行は除く）。
- コメントは行の直前または行末に記述し、専門用語を使うときは平易な言い換えを併記する。
  - 例: `var x = users.Where(u => u.IsActive); // アクティブなユーザーだけを抜き出す`
- このルールは本方針固有であり、汎用的な「コメントは最小限に」というガイダンスよりも**優先**する。
- 言語別コメント記法: C# / JS / TS は `//`、Razor (`.cshtml`) は `@* *@`、JSON など非対応形式は対象外。

## 6. コーディング規約（共通）

- **既存コードのスタイルに合わせる。** インデント・命名・ファイル構成は周囲の慣習を踏襲する。
- **自己説明的な構成にする。** モジュールは単一責務に分割し、ファイル名・関数名から役割が推測できるようにする。公開関数には docstring / コメントで意図を残す。
- **設計判断を残す。** 非自明な実装やトレードオフには「なぜそうしたか」をコメントで残す。
- **定数・ラベルは一元管理する。** 配色・フォント・余白・UI 文言・enum ラベルなどは単一の参照元（例: `theme.py`, `constants.ts`, `EnumLabels.cs`, CSS の `:root` 変数）に集約し、各所に直書きしない。新しい値を追加したら参照元をすべて更新する。
- **マジックナンバー・マジック文字列を避ける。** 意味のある値（しきい値・キー名・パスなど）は名前付き定数にし、上記の一元管理に従って単一の参照元に置く。意図が読み取れない裸の数値・文字列をコードに散らさない。
- **重複を避ける（DRY）。** 同じロジックを書き写す前に既存の関数・モジュール・Port を探して再利用する（§4 のプラン段階で確認）。ただし将来を見越した過度な抽象化は避け、実際に 2〜3 箇所目で重複したら共通化する。
- **エラーを握り潰さない。** 例外は黙って捨てず、文脈を付けて再送出するかログに残す。空の `catch` / 裸の `except:` を作らない。回復不能な失敗は安全側に倒し（§7 の fail-closed）、ユーザーには内部詳細を含まない安全なメッセージを返す。
- **デッドコードを残さない。** 使われない import・変数・関数や、コメントアウトしただけの旧コードは削除する（履歴は Git に残る）。
- **変更は最小スコープに保つ。** 1 つの変更は単一の目的に絞り、無関係なリファクタや整形を同じ差分に混ぜない（§10 の「1 コミット = 1 論理変更」と整合）。レビューしやすい粒度を保つ。
- 言語別の補足:
  - **TypeScript**: `strict: true` を維持。`any` は禁止（不明なら `unknown`）。Props は `interface` で定義。パスエイリアス `@/*` → `src/*`。Server Component をデフォルトにし、必要時のみ `'use client'`。
  - **Python**: `from __future__ import annotations` を先頭に。公開関数に docstring。入力検証は「範囲外→クランプ、非数値→デフォルト」パターン。定数は `UPPER_SNAKE_CASE`。
  - **Bash**: 先頭で `set -euo pipefail`。ログは stderr。インデント 4 スペース。

## 7. セキュリティ（共通・必達）

- **入力は信用しない。** 外部入力（ユーザー入力・設定ファイル・JSON・環境変数）は必ず検証する。Web ではスキーマ検証（例: Zod の `safeParse`）を通してから永続化・API へ渡す。壊れたデータでクラッシュさせず、不正値はフォールバックする。
- **秘密情報をコミットしない。** 認証情報・トークン・API キー・個人情報をコード・ログ・コミットに含めない。`.env` / `.env.local` はコミットせず、`.env.example` にキー名だけ記載する。
- **API キーをフロントエンドに露出させない。** 外部 API はサーバー側（API ルート / Server Action）経由で呼ぶ。モデル名やエンドポイントは定数・環境変数で管理し、ハードコードしない。
- **認可はサーバー側で強制する。** UI を隠すだけに頼らず、Server Action / コントローラの冒頭で認証・ロールチェックを行う。マルチテナントではクエリに必ずテナント条件（`where.tenantId = session.user.tenantId`）を差し込み、クロステナント漏洩を防ぐ。
- **危険な実行を避ける。** `eval` / `exec` / `pickle` / `shell=True` を使わない。外部コマンドは引数配列で実行し、ユーザー入力を文字列連結でシェルに渡さない。
- **失敗しても安全側に倒す（fail-safe / fail-closed）。** 例外時はクラッシュや権限昇格ではなく機能を縮退して継続する。権限・ネットワーク・パスの判定は「不明なら拒否」をデフォルトにする。
- **最小権限・最小公開。** 読み書きするファイルは想定パス配下に限定し、外部由来の値をそのままパスに連結しない（パストラバーサル防止）。
- **出力もエスケープする（インジェクション対策）。** SQL は ORM／パラメータ化クエリで組み立て、ユーザー値を文字列連結で SQL に混ぜない。HTML はフレームワークの自動エスケープに任せ、`dangerouslySetInnerHTML` / `v-html` / `innerHTML` などの生 HTML 挿入は原則避ける（やむを得ない場合はサニタイズしてから）。OS コマンド・パス・LDAP なども同様に値を直接連結しない。
- **状態変更リクエストを保護する。** フォーム送信や書き込み系 API には CSRF トークン（またはダブルサブミットクッキー）を必須とする。`SameSite` クッキーはそれを置き換えるものではなく、多層防御として併用する（OWASP 準拠。登録ドメインを他サービスと共有する場合、サブドメイン経由や `Lax` のトップレベル遷移では `SameSite` だけでは防げない）。副作用のある操作を GET で行わない。
- **機密情報・PII・スタックトレースをログやエラー応答に漏らさない。** 外部にはサニタイズした安全なメッセージだけを返し、詳細はサーバ内ログに限定する。ログに残す前にトークン・個人情報はマスク／伏字化する。
- **暗号・認証情報は自前実装しない。** パスワードは平文・可逆形式で保存せず bcrypt / argon2 等でハッシュ化する。暗号化は標準ライブラリを使い、自前の暗号方式を発明しない。署名・擬似匿名化に使うソルトや鍵は環境変数から取得し、未設定なら起動を失敗させる（fail-closed）。
- **依存（サプライチェーン）を管理する。** ロックファイルをコミットし、新規依存は最小限に絞って出所・メンテ状況を確認する。`npm audit` / Dependabot 等で既知脆弱性を定期的に確認し、放置しない。
- **公開エンドポイントを保護する。** レート制限と、リクエストサイズ・タイムアウト・ページネーション上限を設けて DoS とリソース枯渇を防ぐ。

## 8. 移植性・プラットフォーム差異ゼロ設計（共通）

- **ロジックと UI を分離する。** ビジネスロジックは表示層に依存しない純粋関数として保ち、Web / デスクトップ / モバイルで共有できる状態を維持する。
- **プラットフォーム差を 1 か所に閉じ込める。** OS / 実行環境固有の処理は分岐（例: `platform.system()`）で局所化し、必ずフォールバックを用意する。
- **移植可能な書き方をする。** 特定 OS でしか動かない記述（例: `strftime` の `%-d`）を持ち込まない。同じ操作はどの環境でも同じ結果になるよう、判定ロジックは共有層に置きテストで担保する。
- **契約（contract）で同一性を保証する。** 言語・プラットフォーム非依存の入力→期待出力ケース（例: JSON の契約ファイル）を真実の源とし、各実装はそれに従う。

## 9. テスト（共通）

- **テストは必ず通過させること。** 変更前後で lint / typecheck / test を通す。
- テストファイルは専用ディレクトリ（`tests/`）に、対象モジュール単位（`test_<module>.py` / `*.test.ts`）で配置する。
- **純粋ロジックはユニットテスト、DB / 外部依存は E2E or 契約テストに寄せる。** ユニットテストに DB アクセスを持ち込まない。外部 API はモックして実際には呼ばない。
- 境界値（0・最大・空文字列・非数値など）を重視する。OS 依存処理は `@patch` 等でモックし、特定 OS でしか通らないテストを作らない。
- DB を破壊的に扱う契約テストは、専用 DB を明示フラグで起動したときだけ走らせ、開発 DB を指さない。共有 DB を `TRUNCATE` するテストは直列実行する。

## 10. Git 規約（共通）

- コミットメッセージ形式: `type(scope): 日本語の説明`
  - type: `feat` / `fix` / `refactor` / `test` / `docs` / `chore`
  - scope: 変更領域（例: `chat`, `api`, `ui`, `tickets`, `reminder`）
  - 例: `feat(chat): ストリーミング応答の実装`
- **1 コミット = 1 論理変更。** スキーマ変更とマイグレーションは同一コミットに含める。
- 開発は機能ブランチで行い、`main`（デフォルトブランチ）への直 push は避ける。

## 11. PR・レビュー運用（共通）

- **PR は draft ではなく open（ready）で作成する。** harness のデフォルトが draft の場合は、作成直後に ready 化してから次の手順に進む。
- **Codex 自動レビュー**: PR を ready 化して open にしたあと、および PR ブランチへ push したあとに、その PR へ `@codex review` コメントを投稿してレビューを起動する（順序は「ready 化 → open → `@codex review`」）。
  - コメントは接続済みアカウント（OWNER 名義）で投稿する。`github-actions[bot]` など bot 名義の `@codex review` は拒否されるため、ワークフローからの自動投稿は使わない。
  - 質問返信やレビュー不要な状況報告には付けない。差分を push するたび（初回 PR 作成時を含む）に投稿する。
- **CI の成否（グリーン）はチャット上で報告する。** GitHub MCP（check-runs / status）で取得して報告し、PR コメントでの自動検証・要約はワークフロー側に委ねる。

## 12. CI（共通）

- GitHub Actions（`.github/workflows/ci.yml`）で **lint → typecheck → test → E2E** を実行する。PR を出す前にローカルで `lint && typecheck && test` を通す。
- DB / ブラウザ依存のジョブはサービスコンテナ（PostgreSQL 等）や chromium を使う。ローカルでは `docker compose up` で依存を起動してから実行する。

---

## 付録: リポジトリ別の固有ルール（Appendix）

各リポジトリの `CLAUDE.md` から、**§4〜§12 の共通規約と重複しない固有ルールだけ**を抜き出したカタログ。
新規リポジトリが似た技術スタックの場合、該当ブロックを §1〜§3 の具体化や追補として流用できる。
（出典の `CLAUDE.md` には、ここに載らないプロジェクト固有のアーキテクチャ詳細も含まれる。詳細は各リポジトリを参照。）

### A. profile-portfolio（静的 HTML/CSS/JS, GitHub Pages）

- ビルドツール・パッケージマネージャを使わない。確認は `open index.html` または `python -m http.server 8000`。
- ファイル構成: `index.html`（ダークテーマ）/ `resume.html`（ライトテーマ・印刷対応）。
- 色の変更は `:root` の CSS 変数（`--primary`, `--accent`, `--bg-dark` 等）経由。個別要素にカラーコードを直書きしない。
- レスポンシブ: ブレークポイント 968px（タブレット）・768px（モバイル）。グリッドは `auto-fit, minmax()` でメディアクエリを最小化。フォントは `clamp()` で流体タイポグラフィを適用。
- HTML はセマンティックタグ、CSS は BEM 風命名（`.section-header` 等）、JS は Vanilla のみ（外部ライブラリを追加しない）。画像に `alt`、外部リンクに `rel="noopener noreferrer"`、`lang="ja"`。
- セクション追加時は Intersection Observer の `.observe()` 対象に追加し、ナビリンク・768px 表示・`resume.html` 反映を確認する。

### B. my-task-manager（Python + tkinter, GUI）

- ビジネスロジックは GUI 非依存の純粋関数に保つ（`timeline.py` / `stats.py` / `recurrence.py` / `task.py`）。表示層を差し替えてもロジックを共有できる状態を維持。
- デザイントークン（配色・フォント・余白・カレンダー寸法）は `theme.py` に一元化。見た目の値をコードに直書きしない。
- 繰り返しタスクは「完了した時点」を起点に日/週/月/年で再スケジュール（月末日・うるう年はクランプ）。
- 言語・プラットフォーム非依存の繰り返し契約は `contract/recurrence_cases.json` を真実の源とし、契約駆動テスト（`test_recurrence_contract.py`）で検証。Web/スマホ版も同一契約に従う。
- tkinter の `StringVar` / `IntVar` はテスト用 `_DummyVar` で代替し、`_create_app()` ファクトリでモック済みインスタンスを生成（Tk 無しでテスト可能）。
- 入力検証は `_coerce_int()` パターン（範囲外→クランプ、非数値→デフォルト）。
- 今日のタスクは Treeview でなく `tk.Canvas` の「デイビュー」で描画し、位置・高さは分→px 換算（`HOUR_HEIGHT`）で Canvas 実サイズに依存させない。
- クロスプラットフォーム: 音/通知は macOS(`afplay`)・Windows(`winsound`)・Linux(`notify-send`+`tk.bell()`)を `platform.system()` で分岐。`cairosvg` はオプション依存で `ImportError` 時 graceful degradation。

### C. my-first-ai-app（Next.js 15 + Claude API）

- システムプロンプトは `src/lib/prompts.ts` に集約し、コンポーネントやルートハンドラに直接書かない。プロンプトは日本語で記述。
- モデル名（`claude-sonnet-4-6` 等）は環境変数または定数で管理しハードコードしない。`max_tokens` 既定 1024、長文が必要なカテゴリは `prompts.ts` で個別設定。
- `POST /api/chat` が唯一の API。Claude へのストリーミングプロキシで、`ANTHROPIC_API_KEY` はサーバ側環境変数から取得しフロントに露出させない。
- API ルートに簡易レート制限（IP ベース、1 分あたり 20 リクエスト目安）。
- API ルートのエラーは HTTP ステータスを使い分け: 401（キー未設定/無効）/ 429（レート制限超過）/ 500（その他）。フロントはユーザーフレンドリーな日本語メッセージを表示。

### D. helpdesk-hub（Next.js 15 / Prisma / Auth.js v5）

- 正本は `docs/smb-dx-pivot-plan.md`。Lite/Pro 二層・マルチテナント化・用語簡素化等の方針に反する変更をしない。Phase 0→1→2→3→4 の順序を尊重し、後フェーズ機能を前フェーズに混ぜない。
- Prisma クライアントは `src/generated/prisma` に出力される。型/enum は必ず `@/generated/prisma` から import（`@prisma/client` ではない）。クローン後やスキーマ変更後は `npm run db:generate` を実行。
- ロールは実質 requester と agent/admin の 2 種。`isAgent(role)`（`src/lib/role.ts`）を使い、`role === 'admin'` を直接比較しない（admin 限定の意図がある場合を除く）。
- Mutation（Server Action）の定型: `auth()`＋ロール表明 → `findUniqueOrThrow` → 状態変更は `isValidTransition(from,to)` でゲート → Prisma で更新 → `recordHistory(...)` → `createNotification(...)` → `revalidatePath(...)`。
- 状態遷移テーブル `ALLOWED_TRANSITIONS`（`src/domain/ticket-status.ts`）が唯一の真実の源。バイパスせず、ブロックされたら表とテストを更新する。
- Data 層は Ports & Adapters。Port を `src/data/ports/` に定義し、本番は `adapters/prisma/`、テストは `adapters/memory/`。Prisma を直接 import するのは Adapter 内のみ。
- 未読通知数は SSE（`/api/notifications/stream`）＋ `unstable_cache` で配信。`sse-subscribers.ts` はインプロセス Map のため、水平スケール前に要注意。
- 契約テストは `*.contract.prisma.test.ts` 命名。`RUN_PRISMA_CONTRACT=1` のときだけ走り、`beforeEach` で全テーブル `TRUNCATE` するため**開発 DB を指さない**。`--no-file-parallelism` で直列実行。

### E. incident-insight（ASP.NET Core 8 MVC + EF Core 8）

- DB プロバイダ非依存。SQLite（既定）/ SQL Server / PostgreSQL を `Database:Provider` で切替。プロバイダ固有 SQL・列型をコードに持ち込まない。
- 楽観的同時実行制御: 編集 POST は `FindAsync` で再読込後、クライアントの編集前 `ConcurrencyToken` を `OriginalValue` に明示ピンして保存し、`DbUpdateConcurrencyException` を捕捉。トークンは hidden field で round-trip。
- 時刻は常に注入された `IClock`（JST）。`DateTime.Now/Today/UtcNow` を直接呼ばない。
- 監査ログは `AuditSaveChangesInterceptor` が唯一の源。`AuditLog` に直接書かない。`SaveChanges` 経由で更新し、`ExecuteUpdate`/`ExecuteDelete` を使わない（変更追跡を迂回し監査漏れになるため）。
- PHI 保護: 自由記述・個人名カラムには `[Sensitive(Mask.Redact)]` か `[Sensitive(Mask.Hash)]` を付与（`[REDACTED]` か HMAC-SHA256 擬似匿名化）。新カラム追加時も必ず annotate。本番で `Audit:HashSalt` 空は起動失敗。
- ビジネスルール `HasAtLeastOneValidMeasure`（インシデントは予防策が最低 1 件ないと登録不可）をバイパスしない。
- Enum（重症度・部署・インシデント種別）は `Incident` クラスの `static readonly` 辞書/配列が真実の源（DB ではない）。`EnumLabels.cs` に日本語ラベル＋Bootstrap カラーを集約。
- `SameDepartmentHandler` は `Incident` の eager-load（`.Include(x => x.Incident)`）が前提で fail-closed（null なら拒否）。
- 新規 POST アクション時チェック: `[Authorize]` / `[ValidateAntiForgeryToken]` / `ConcurrencyToken` ピン / 必要なら `.Include(Incident)` / `SaveChangesAsync` 使用 / `TempData["Success"|"Warning"]` / 新 PHI カラムに `[Sensitive]` / 対応テスト追加。テストは InMemory DbContext を優先（Mock より）。

### F. AI-Docker-Environment（Docker サンドボックス, bash, Linux 専用）

- 正本は `docs/requirements.md`。実装・新機能はすべて要件定義書に従い、衝突したら先に要件を改訂してから実装変更（同一 PR 内で §3/§4/§6 を更新）。
- すべて `bin/aidock` 経由で実行（`build`/`login`/`run`/`shell`/`firewall-refresh`/`logout`）。`guard_workspace()` の `/` および `$HOME` をマウント拒否するガードを削除しない。
- セキュリティ不変条件（変更禁止 or 影響必須検討）:
  - `compose.yaml`: `cap_drop: ALL`（必要 cap のみ add）/ `no-new-privileges:true` / `read_only: true`＋最小 `tmpfs` / メモリ・CPU・PID 上限 / ホストパスの追加 bind mount 原則禁止（`~/.ssh` 等）。
  - `HOST_WORKSPACE` に既定値を付けない（`${HOST_WORKSPACE:?...}`）。`bin/aidock` 非経由の直接 `docker compose run` を fail-closed にする。
  - `Dockerfile`/`entrypoint.sh`: `sudo` を含めず、root 起動 → firewall 初期化後に `gosu agent` で降格。ワークロードは `agent` で実行。
  - `init-firewall.sh`: `iptables -P OUTPUT DROP` と `ip6tables -P OUTPUT DROP`（IPv4/IPv6 両方 default-deny）を維持。許可ホスト追加は最小限・理由を PR に明記。DNS は許可 nameserver 限定。
- OAuth トークンは名前付きボリューム `claude-home` に置き、ホスト FS や Docker イメージ層に書き出さない。
- Linux 専用（iptables/ipset/cap_add 依存。macOS Docker Desktop 非対応）。スクリプトは Bash・先頭で `set -euo pipefail`、ログは stderr、インデント 4 スペース。
- このリポジトリのコミットメッセージは英語・命令形・1 行要約（既存履歴に倣う。§10 の日本語コミット規約より優先する例外）。
