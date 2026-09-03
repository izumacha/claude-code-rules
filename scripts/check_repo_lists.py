#!/usr/bin/env python3
"""集約元リポジトリの一覧が 3 か所で食い違っていないことを検査する。

このリポジトリは「同じ事実を 1 か所に集約して、ブレ・重複・陳腐化を防ぐ」ことを
目的にしている。ところが集約元リポジトリの一覧そのものが 3 か所に手書きで存在する:

  1. CLAUDE.md 冒頭の blockquote にある「集約元リポジトリ: ...」の列挙
  2. CLAUDE.md 末尾の付録の見出し（`### A. <リポジトリ名>（<スタック>）`）
  3. README.md の「集約元リポジトリ」表の各行（`| \\`<リポジトリ名>\\` | <スタック>|`）

CLAUDE.md §0 は「新規リポジトリを追加するときは 2 箇所を同時に更新する」と明記して
いるが、この規則を守らせる仕組みが無く、実際に PR #14（付録だけ更新して README の表が
取り残された）と PR #15（同じ種類のずれを 3 件まとめて修正）で同じ失敗が繰り返された。
片方だけ更新しても人が気付かない限り緑のまま通るためで、この検査はその「気付けない」を
機械的に潰すためにある。

検査するのは次の 2 点だけ:

  (a) 3 か所のリポジトリ名の集合が完全に一致すること
  (b) 付録の見出し記号（A, B, C, ...）が A から始まる連番であること

**あえて検査しないこと**（この検出網の境界。誤検知する検査は、いずれ「直せないので
緩める」方向へ倒れるため、判定できないものは最初から対象にしない）:

  - スタック表記の文字列一致: README は「静的 HTML/CSS/JS（GitHub Pages）」、付録は
    「静的 HTML/CSS/JS, GitHub Pages」のように書式が異なり、さらに付録の
    「Docker サンドボックス, bash, Linux 専用」と README の
    「Docker サンドボックス（bash, Linux）」のように語尾も揃っていない。正規化で
    吸収しようとすると、正規化規則そのものが新しい写しになる。
  - バージョン番号の一致: 付録が「Auth.js v5」と書く一方で README は「Auth.js」と
    版を書かない、逆に README だけが「React 19」「Tailwind CSS v4」を挙げる、といった
    粒度の違いが正常な状態として存在する。どちらかに揃えることを機械的に要求すると、
    正しい記述を落とす方向の指示になる。
  - 記述と実装（各リポジトリの依存宣言）の一致: 本リポジトリは他リポジトリを
    チェックアウトしないため、そもそも突き合わせる相手が手元に無い。これは
    レビューで確認する箇所として残す。
"""

# 標準ライブラリだけで完結させる（このリポジトリは依存を持たない）
from __future__ import annotations

# 正規表現でマークダウンの各リストを読み取るために使う
import re

# ファイルパスを OS 非依存に組み立てるために使う
from pathlib import Path

# スクリプトの位置からリポジトリのルートを求める（実行時のカレントディレクトリに依存させない）
REPO_ROOT = Path(__file__).resolve().parent.parent

# 検査対象となる 2 つのマークダウンファイル
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
README_MD = REPO_ROOT / "README.md"

# CLAUDE.md 冒頭の blockquote にある列挙の始まりを見つけるための目印
HEADER_LIST_MARKER = "集約元リポジトリ:"

# 付録の見出し `### A. <名前>（<スタック>）` から記号と名前を取り出す
# 「（」の直前までを名前として拾う（スタック表記は本検査の対象外なので読み捨てる）
APPENDIX_HEADING_RE = re.compile(r"^### ([A-Z])\. ([^（]+)（")

# README の表の行 `| `<名前>` | <スタック>|` から名前を取り出す
# 先頭セルがバッククォートで囲まれた行だけを対象にし、表以外の行を拾わないようにする
README_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|")

# blockquote 内でバッククォートに囲まれたリポジトリ名を取り出す
BACKTICKED_RE = re.compile(r"`([^`]+)`")


def read_header_repos(text: str) -> list[str]:
    """CLAUDE.md 冒頭の blockquote から集約元リポジトリ名を順に取り出す。

    列挙は複数行に折り返されているため、目印の行から blockquote が途切れるまでを読む。
    """
    # 取り出したリポジトリ名を順番に貯める入れ物
    repos: list[str] = []
    # 目印の行を見つけたかどうかを覚えておくフラグ
    started = False
    # ファイル全体を 1 行ずつ順番に見ていく
    for line in text.splitlines():
        # blockquote の "> " を外した中身だけを見る（以降の判定はこの文字列に対して行う）
        content = line.lstrip(">").strip()
        # まだ目印に出会っていない場合の処理
        if not started:
            # 目印を含まない行は読み飛ばす
            if HEADER_LIST_MARKER not in content:
                continue
            # 目印の行に来たら、目印より後ろだけを列挙の本体として扱う
            started = True
            content = content.split(HEADER_LIST_MARKER, 1)[1]
        # 2 行目以降が blockquote でなくなったら列挙の終わり
        elif not line.startswith(">"):
            break
        # この行が「列挙の続き」でなければ、そこで列挙は終わったものとして読むのをやめる。
        # 単に blockquote が続く限り読むと、同じ段落に書かれた別の文に含まれる
        # バッククォートまでリポジトリ名として拾ってしまう。たとえば README にある
        # 「※ `unmei-wo-hiraku` は private のため未収録。」をこの blockquote へ
        # 書き写すと、「意図的に載せていない private リポジトリを公開の README と
        # 付録へ追加せよ」という、実行してはいけない指示を出す誤検知になる。
        # §0 が「3 箇所を同時に更新する」と求めている以上その書き写しは自然に起こる。
        if not is_enumeration_segment(content):
            break
        # この行に含まれるバッククォート囲みをすべてリポジトリ名として拾う
        repos.extend(BACKTICKED_RE.findall(content))
    # 見つかった順のまま返す（呼び出し側で集合にして比較する）
    return repos


def is_enumeration_segment(content: str) -> bool:
    """その行が「`名前` / `名前` / ...」という列挙の一部だけでできているかを判定する。

    バッククォート囲みと区切りの `/` と空白を取り除いて何も残らなければ列挙の続きとみなす。
    句点や説明文が混じっていれば、そこから先は列挙ではないと判断する。
    """
    # バッククォート囲みをすべて取り除く（中身が何であっても 1 つの塊として消す）
    remainder = BACKTICKED_RE.sub("", content)
    # 残りから区切りの / と空白を取り除く
    remainder = remainder.replace("/", "").strip()
    # 何も残らなければ列挙の続き、何か残れば別の文が始まっている
    return not remainder


def read_appendix_repos(text: str) -> list[tuple[str, str]]:
    """CLAUDE.md 末尾の付録から (見出し記号, リポジトリ名) を順に取り出す。"""
    # 見出しにマッチした行から記号と名前の組を作って並べる
    return [
        (match.group(1), match.group(2).strip())
        for line in text.splitlines()
        if (match := APPENDIX_HEADING_RE.match(line))
    ]


def read_readme_repos(text: str) -> list[str]:
    """README.md の「集約元リポジトリ」表からリポジトリ名を順に取り出す。

    表は「## 集約元リポジトリ」節の中にしか無いので、その節に範囲を限定する。
    限定しないと、将来ほかの節にバッククォート始まりの表が増えたときに巻き込む。
    """
    # 対象の節に入ったかどうかを覚えておくフラグ
    inside = False
    # 取り出したリポジトリ名を順番に貯める入れ物
    repos: list[str] = []
    # ファイル全体を 1 行ずつ順番に見ていく
    for line in text.splitlines():
        # 見出し行に来たら、対象の節かどうかを判定し直す
        if line.startswith("## "):
            # 「集約元リポジトリ」を含む見出しなら、ここから表の読み取りを始める
            inside = "集約元リポジトリ" in line
            # 見出し行そのものは表の行ではないので次の行へ進む
            continue
        # 対象の節の中にいるときだけ、表の行かどうかを調べる
        if inside and (match := README_ROW_RE.match(line)):
            # 先頭セルの中身をリポジトリ名として拾う
            repos.append(match.group(1))
    # 見つかった順のまま返す
    return repos


def main() -> int:
    """3 か所の一覧を突き合わせ、食い違いがあれば理由を表示して失敗する。"""
    # 検査対象のファイルを読み込む（明示的に UTF-8 を指定し、実行環境の既定に依存させない）
    claude_text = CLAUDE_MD.read_text(encoding="utf-8")
    readme_text = README_MD.read_text(encoding="utf-8")

    # 3 か所それぞれからリポジトリ名を取り出す
    header = read_header_repos(claude_text)
    appendix = read_appendix_repos(claude_text)
    readme = read_readme_repos(readme_text)

    # 見つかった問題を貯める入れ物（1 件目で止めず、まとめて報告する）
    problems: list[str] = []

    # どこか 1 つでも空なら、書式が変わって読み取れなくなった可能性が高い。
    # 「対象ゼロ＝違反ゼロ＝緑」で検出網が黙って死ぬのを避けるため fail-closed で落とす。
    if not header:
        problems.append(
            "CLAUDE.md 冒頭の「集約元リポジトリ:」の列挙を読み取れませんでした。"
            "書式を変えた場合は scripts/check_repo_lists.py の読み取りも直してください。"
        )
    if not appendix:
        problems.append(
            "CLAUDE.md 末尾の付録の見出し（### A. <名前>（<スタック>））を"
            "読み取れませんでした。書式を変えた場合は本スクリプトも直してください。"
        )
    if not readme:
        problems.append(
            "README.md の「集約元リポジトリ」表を読み取れませんでした。"
            "書式を変えた場合は本スクリプトも直してください。"
        )

    # どれも読み取れているときだけ、中身の突き合わせに進む
    if not problems:
        # 付録は (記号, 名前) の組で持っているので、比較用に名前だけを取り出す
        appendix_names = [name for _, name in appendix]

        # 「どこに何が書かれているか」を 1 か所だけで定義する。
        # 以降の検査（欠落と重複）はどちらもここから導く。箇所の呼び名を 2 度書くと、
        # 表記を直したときに片方だけ残り、同じ実行の中で 1 つの場所が 2 通りの名前で
        # 報告されてしまう（このリポジトリが無くそうとしている「写し」そのもの）。
        sources: list[tuple[str, list[str]]] = [
            ("CLAUDE.md 冒頭の列挙", header),
            ("CLAUDE.md 末尾の付録", appendix_names),
            ("README.md の表", readme),
        ]

        # 3 か所のいずれかに 1 度でも現れた名前をすべて集める
        union: set[str] = set().union(*(set(names) for _, names in sources))
        # 名前ごとに「どこに載っていないか」を調べる
        for name in sorted(union):
            # その名前を載せていない箇所を列挙する
            missing = [where for where, names in sources if name not in names]
            # 1 か所でも欠けていれば、どこに足りないのかを添えて報告する
            if missing:
                problems.append(
                    f"`{name}` が {' / '.join(missing)} に載っていません。"
                    "CLAUDE.md §0 のとおり 3 か所すべてを同時に更新してください。"
                )

        # 同じ名前を 2 回書いていないかを、箇所ごとに調べる
        for where, names in sources:
            # 重複している名前だけを抜き出す（集合にすると件数が減ることを利用する）
            duplicates = sorted({n for n in names if names.count(n) > 1})
            # 重複があれば、どこで何が重複しているかを報告する
            if duplicates:
                problems.append(
                    f"{where} に同じリポジトリ名が複数回書かれています: "
                    + ", ".join(f"`{n}`" for n in duplicates)
                )

        # 付録の見出し記号が A から始まる連番になっているかを調べる
        # 記号が飛んだり重複したりするのは、付録を編集したときの取りこぼしの兆候
        expected = [chr(ord("A") + i) for i in range(len(appendix))]
        # 実際に書かれている記号の並びを取り出す
        actual = [letter for letter, _ in appendix]
        # 期待と食い違っていれば、両方を並べて報告する
        if actual != expected:
            problems.append(
                "付録の見出し記号が A から始まる連番になっていません: "
                f"実際 {' '.join(actual)} / 期待 {' '.join(expected)}"
            )

    # 問題が 1 件でもあれば、すべて表示して失敗させる
    if problems:
        # 何の検査で落ちたのかを最初に示す
        print("集約元リポジトリの一覧が 3 か所で一致していません:")
        # 見つかった問題を 1 件ずつ箇条書きで出す
        for problem in problems:
            print(f"  - {problem}")
        # 非ゼロで終了し、CI を失敗させる
        return 1

    # 問題が無ければ、何件を突き合わせたのかを示して成功で終わる
    print(f"集約元リポジトリの一覧は 3 か所で一致しています（{len(header)} 件）。")
    return 0


# スクリプトとして直接実行されたときだけ main を呼ぶ（import されたときは実行しない）
if __name__ == "__main__":
    raise SystemExit(main())
