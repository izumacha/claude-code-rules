# claude-code-rules

CLAUDE.md の**原本（マスター）**を集約するリポジトリ。
A repository that consolidates the **master (source-of-truth) `CLAUDE.md`**.

## これは何 / What this is

各リポジトリに散らばっている `CLAUDE.md` の規約を 1 箇所に集約し、**原本（Source of Truth）**として管理します。
この原本（[`CLAUDE.md`](./CLAUDE.md)）を基準に、新しいリポジトリへ `CLAUDE.md` を追加したり、既存リポジトリの `CLAUDE.md` を統一したりします。

This repo gathers the coding/agent conventions that were scattered across each project's `CLAUDE.md` into a single **source-of-truth master** ([`CLAUDE.md`](./CLAUDE.md)). Use it to add a `CLAUDE.md` to new repositories and to unify the `CLAUDE.md` files of existing ones.

## なぜ作るか / Why

- 同じ規約を各リポジトリで書き直すと**ブレ・重複・陳腐化**が起きる。原本に一本化して解消する。
- 新規リポジトリで毎回ゼロから `CLAUDE.md` を書く手間をなくす。
- 既存リポジトリ間で**規約をそろえる**基準点（single source of truth）を持つ。

- Rewriting the same rules in every repo causes **drift, duplication, and staleness** — a single master fixes that.
- Removes the effort of writing a `CLAUDE.md` from scratch for each new repository.
- Provides one reference point to **align conventions** across existing repositories.

## 使い方 / How to use

**新規リポジトリ / New repository**

1. [`CLAUDE.md`](./CLAUDE.md) をコピーする / Copy `CLAUDE.md`.
2. `{{ }}` のプレースホルダ（§1 プロジェクト概要・§2 コマンド・§3 アーキテクチャ）をそのリポジトリ向けに埋める / Fill in the `{{ }}` placeholders (overview, commands, architecture).
3. 共通規約（§4 以降）はそのまま使う / Keep the shared conventions (§4 onward) as-is.

**既存リポジトリ / Existing repository**

1. その `CLAUDE.md` を原本と突き合わせる / Diff the repo's `CLAUDE.md` against this master.
2. 共通規約は原本の文言に合わせて統一する / Align shared rules to the master's wording.
3. 必要な固有ルールは付録（Appendix）を参考に各リポジトリ側へ残す / Keep needed project-specific rules per repo, using the Appendix as reference.

> 原本そのものを更新したら、各リポジトリへ反映する運用とします。
> When the master itself changes, propagate the update to each repository.

## 原本の構成 / Structure of the master

- **§0–§3**: 使い方とプロジェクト固有の章（プレースホルダ） / Usage and project-specific sections (placeholders).
- **§4–§14**: 重複排除した共通規約 / Deduplicated shared conventions.
  - 実装フロー（プランモード必須）/ Plan-mode-first workflow
  - 1 行ごとの初心者向けコメント / Beginner-friendly per-line comments
  - 正本優先 / Source-of-truth-first
  - アクセシビリティ（a11y）・パフォーマンス / Accessibility (a11y) and performance
  - セキュリティ・移植性・テスト・Git・PR/Codex・CI / Security, portability, testing, Git, PR/Codex, CI
- **付録 / Appendix**: リポジトリ別の固有ルール（共通規約と重複しない分のみ）/ Per-repository specific rules (only those not already in the shared section).

## 集約元リポジトリ / Source repositories

以下のリポジトリの `CLAUDE.md` を参照し、重複を排除して集約しています。
The master is consolidated from the `CLAUDE.md` files of:

| リポジトリ / Repository | スタック / Stack |
|---|---|
| `profile-portfolio` | 静的 HTML/CSS/JS（GitHub Pages）|
| `my-task-manager` | Python + tkinter（GUI）|
| `my-first-ai-app` | Next.js 16 + Claude API |
| `helpdesk-hub` | Next.js 15 / Prisma / Auth.js v5 |
| `incident-insight` | ASP.NET Core 8 MVC + EF Core 8 |
| `AI-Docker-Environment` | Docker サンドボックス（bash, Linux）|
| `batch-schduler` | Java 21 / Maven（バッチ実行マネージャ）|
| `Expense-Management-Rest-API` | Java 21 / Spring Boot + C# .NET 10（REST API）|

※ `unmei-wo-hiraku` は private のため未収録。
`unmei-wo-hiraku` is private and not included.
