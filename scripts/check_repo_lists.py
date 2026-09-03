#!/usr/bin/env python3
"""集約元リポジトリの一覧が 3 か所で食い違っていないことを検査する。

このリポジトリは「同じ事実を 1 か所に集約して、ブレ・重複・陳腐化を防ぐ」ことを
目的にしている。ところが集約元リポジトリの一覧そのものが 3 か所に手書きで存在する:

  1. CLAUDE.md 冒頭の blockquote にある「集約元リポジトリ: ...」の列挙
  2. CLAUDE.md 末尾の付録の見出し（`### A. <リポジトリ名>（<スタック>）`）
  3. README.md の「集約元リポジトリ」表の各行（`| \\`<リポジトリ名>\\` | <スタック>|`）

3 箇所とも手書きなので、1 つだけ更新して他が取り残されても人が気付かない限り緑のまま
通る。PR #14（付録 D の Next.js 15 → 16）と PR #15（付録 E の EF Core 8 → 9、および
README にだけあった実在しない「+ C# .NET 10」の削除）はどちらもこの形の修正だった。

検査するのは次の 4 点:

  (a) 3 か所のリポジトリ名の集合が完全に一致すること（重複が無いことを含む）
  (b) 3 か所の**並び順**も一致すること。付録は A, B, C... と記号を振り、本文が
      「§E の …」と記号で相互参照するので、並びがずれると読み手が別のリポジトリの
      説明にたどり着く
  (c) 付録の見出し記号が A から始まる連番であること
  (d) README の表と付録の見出しで、**バージョン番号の集合が一致すること**。
      #14 / #15 で実際に起きたのがこのずれで、`Next.js 15` と `16`、`EF Core 8` と
      `9`、README にだけある `.NET 10` は、いずれも数値の集合の差として現れる

**あえて検査しないこと**（この検出網の境界。誤検知する検査は、いずれ「直せないので
緩める」方向へ倒れるため、判定できないものは最初から対象にしない）:

  - **スタック表記そのものの文字列一致**。README と付録は書式の約束が異なり
    （README は「静的 HTML/CSS/JS（GitHub Pages）」、付録は
    「静的 HTML/CSS/JS, GitHub Pages」）、語尾も揃っていない（README の
    「Docker サンドボックス（bash, Linux）」に対し付録は
    「Docker サンドボックス, bash, Linux 専用」）。正規化して一致を求めると、
    正規化規則そのものが新しい写しになる。**数値だけを比べる (d) はこの問題を
    避けられる**——句読点や語尾の違いは数値を含まないため。
  - **記述と実装（各リポジトリの依存宣言）の一致**。(d) が見るのは「README と付録が
    互いに食い違っていないか」だけで、両方が揃って古い場合は検出できない。本
    リポジトリは他リポジトリをチェックアウトしないため突き合わせる相手が手元に無く、
    これはレビューで確認する箇所として残す。
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

# CLAUDE.md の付録が始まる見出しの前置き（`## 付録: リポジトリ別のルール（Appendix）`）
APPENDIX_SECTION_PREFIX = "## 付録"

# README.md で集約元リポジトリの表を含む節の見出しに必ず含まれる語
README_SECTION_KEYWORD = "集約元リポジトリ"

# 付録の見出し `### A. <名前>（<スタック>）` から記号・名前・スタックを取り出す
APPENDIX_HEADING_RE = re.compile(r"^### ([A-Z])\. ([^（]+)（(.*)）\s*$")

# README の表の行 `| `<名前>` | <スタック>|` から名前とスタックを取り出す
# 先頭セルがバッククォートで囲まれた行だけを対象にし、見出し行や区切り行を拾わない
README_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|(.*)\|\s*$")

# blockquote 内でバッククォートに囲まれたリポジトリ名を取り出す
BACKTICKED_RE = re.compile(r"`([^`]+)`")

# スタック表記に現れるバージョン番号を取り出す。
# 直前が英数字でないことを求めて、語の途中の数字（`HTML5` の 5 など）を拾わない。
# 先頭の "v" は書き方の揺れ（`Auth.js v5` と `Auth.js 5`）なので取り込んで捨てる。
VERSION_TOKEN_RE = re.compile(r"(?<![0-9A-Za-z])v?(\d+(?:\.\d+)*)")

# 付録の見出し記号に使えるアルファベットの数（A〜Z）
MAX_APPENDIX_LETTERS = 26


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


def read_header_repos(text: str) -> list[str]:
    """CLAUDE.md 冒頭の blockquote から集約元リポジトリ名を順に取り出す。"""
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
            # 列挙は blockquote の中にしか無い。blockquote 以外の行に同じ語が出てきても
            # 反応しないようにする（本文に「現在の集約元リポジトリ: 8 件」のような文が
            # あると、そこで読み取りを始めてしまい、続く行が列挙でないため即座に打ち切って
            # 空の一覧を返す。fail-closed で落ちはするが「書式を変えたなら読み取りも
            # 直せ」という誤った診断を出し、実際には無傷の blockquote を疑わせる）
            if not line.startswith(">") or HEADER_LIST_MARKER not in content:
                continue
            # 目印の行に来たら、目印より後ろだけを列挙の本体として扱う
            started = True
            content = content.split(HEADER_LIST_MARKER, 1)[1]
        # 空行に来たら列挙は終わり（blockquote 内の "> " だけの行もここに含まれる）
        elif not content:
            break
        # この行が「列挙の続き」でなければ、そこで列挙は終わったものとして読むのをやめる。
        # 終わりの判定を「先頭が > でなくなったら」にしないのは、Markdown では
        # blockquote の続きを > なしで書ける（lazy continuation）ため。表示は同じなのに
        # 読み取りだけが途中で止まり、画面に見えているリポジトリを「載っていません」と
        # 報告してしまう。中身が列挙かどうかで判定すれば、どちらの書き方でも正しく読める。
        elif not is_enumeration_segment(content):
            break
        # この行に含まれるバッククォート囲みをすべてリポジトリ名として拾う
        repos.extend(BACKTICKED_RE.findall(content))
    # 見つかった順のまま返す（呼び出し側で突き合わせる）
    return repos


def read_appendix_entries(text: str) -> list[tuple[str, str, str]]:
    """CLAUDE.md 末尾の付録から (見出し記号, リポジトリ名, スタック表記) を順に取り出す。

    走査は「## 付録」以降に限定する。このファイルは新規リポジトリへコピーして
    §1〜§3 を埋めるテンプレートなので、埋めた内容の中に
    `### A. 入力レイヤ（バリデーション）` のような同じ書式の見出しが現れうる。
    範囲を限定しないとそれをリポジトリ名として拾い、連番検査が
    「実際 A B A B / 期待 A B C D」という原因の分からない失敗を出す。
    """
    # 取り出した組を順番に貯める入れ物
    entries: list[tuple[str, str, str]] = []
    # 付録の節に入ったかどうかを覚えておくフラグ
    inside = False
    # ファイル全体を 1 行ずつ順番に見ていく
    for line in text.splitlines():
        # 見出し行に来たら、付録の節かどうかを判定し直す
        if line.startswith("## "):
            # 「## 付録」で始まる見出しなら、ここから読み取りを始める
            inside = line.startswith(APPENDIX_SECTION_PREFIX)
            # 見出し行そのものは付録の項目ではないので次の行へ進む
            continue
        # 付録の中にいるときだけ、項目の見出しかどうかを調べる
        if inside and (match := APPENDIX_HEADING_RE.match(line)):
            # 記号・名前・スタック表記の組にして貯める
            entries.append(
                (match.group(1), match.group(2).strip(), match.group(3).strip())
            )
    # 見つかった順のまま返す
    return entries


def read_readme_entries(text: str) -> list[tuple[str, str]]:
    """README.md の「集約元リポジトリ」表から (リポジトリ名, スタック表記) を順に取り出す。

    まず「## 集約元リポジトリ」節に範囲を限定し、そのうえで**表が終わった時点で**
    走査をやめる。節を限定するだけでは足りないのは、この節がファイル末尾まで続いており、
    後ろに説明文や別の表を足す編集が自然に起こるため（実際この節には検査の使い方の説明が
    足してある）。別の表まで拾うと、その 1 列目をリポジトリ名と誤認し、「`用語` が
    CLAUDE.md 冒頭の列挙 / 付録に載っていません」という実行してはいけない指示を出す。
    """
    # 対象の節に入ったかどうかを覚えておくフラグ
    inside = False
    # 表の行を読み始めたかどうかを覚えておくフラグ
    reading_table = False
    # 取り出した組を順番に貯める入れ物
    entries: list[tuple[str, str]] = []
    # ファイル全体を 1 行ずつ順番に見ていく
    for line in text.splitlines():
        # 見出し行に来たら、対象の節かどうかを判定し直す
        if line.startswith("## "):
            # 対象の語を含む見出しなら、ここから表の読み取りを始める
            inside = README_SECTION_KEYWORD in line
            # 見出し行そのものは表の行ではないので次の行へ進む
            continue
        # 対象の節の外にいる間は何も拾わない
        if not inside:
            continue
        # 表の行なら、名前とスタック表記を拾う
        if match := README_ROW_RE.match(line):
            # 1 行目を拾った時点で「表を読んでいる」状態にする
            reading_table = True
            # 先頭セルの名前と 2 列目のスタック表記を貯める
            entries.append((match.group(1), match.group(2).strip()))
        # 表を読んでいる途中で **表でない行**（空行や説明文）へ出たら、そこで表は終わり。
        # 打ち切りの条件を「行がパターンに一致しないこと」にしないのは、バッククォートを
        # 書き忘れた行が 1 つあるだけで以降の行がすべて読み飛ばされ、実際には表に載って
        # いるリポジトリまで「載っていません」と報告してしまうため（その指示に従うと
        # 行が二重になり、今度は重複検査で落ちる）。表の途中かどうかは行頭の | で見る。
        elif reading_table and not line.startswith("|"):
            break
    # 見つかった順のまま返す
    return entries


def version_tokens(stack: str) -> set[str]:
    """スタック表記に現れるバージョン番号の集合を返す。"""
    # 数値だけを取り出して集合にする（並び順や区切り記号の違いを無視するため）
    return set(VERSION_TOKEN_RE.findall(stack))


def find_problems(claude_text: str, readme_text: str) -> list[str]:
    """2 つのテキストを突き合わせ、見つかった問題を説明の一覧として返す。"""
    # 3 か所それぞれから読み取る
    header = read_header_repos(claude_text)
    appendix = read_appendix_entries(claude_text)
    readme = read_readme_entries(readme_text)

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
    # 1 つでも読めていなければ、この先の突き合わせは意味を持たないのでここで返す
    if problems:
        return problems

    # 付録と README から名前だけを取り出す（並びは読み取った順のまま保つ）
    appendix_names = [name for _, name, _ in appendix]
    readme_names = [name for name, _ in readme]

    # 「どこに何が書かれているか」を 1 か所だけで定義する。
    # 以降の検査はすべてここから導く。箇所の呼び名を 2 度書くと、表記を直したときに
    # 片方だけ残り、同じ実行の中で 1 つの場所が 2 通りの名前で報告されてしまう。
    sources: list[tuple[str, list[str]]] = [
        ("CLAUDE.md 冒頭の列挙", header),
        ("CLAUDE.md 末尾の付録", appendix_names),
        ("README.md の表", readme_names),
    ]

    # (a) 3 か所のいずれかに 1 度でも現れた名前をすべて集める
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

    # (b) 並び順の一致は、集合が揃っているときだけ意味を持つので、ここまで問題が
    # 無い場合に限って調べる（欠落があると並びの差はその巻き添えでしかない）
    if not problems:
        # 先頭の箇所を基準にして、残りの箇所と並びを突き合わせる
        base_where, base_names = sources[0]
        # 2 番目以降の箇所を順に比べる
        for where, names in sources[1:]:
            # 並びが違えば、両方の並びを添えて報告する
            if names != base_names:
                problems.append(
                    f"{where} の並びが {base_where} と違います。"
                    "付録は A, B, C... と記号を振り本文がその記号で相互参照するため、"
                    "並びがずれると読み手が別のリポジトリの説明にたどり着きます。"
                    f"（{base_where}: {' / '.join(base_names)}）"
                    f"（{where}: {' / '.join(names)}）"
                )

    # (c) 付録の見出し記号が A から始まる連番になっているかを調べる
    # 記号が飛んだり重複したりするのは、付録を編集したときの取りこぼしの兆候
    if len(appendix) > MAX_APPENDIX_LETTERS:
        # A〜Z を使い切ると連番を作れない。誤った案内を出す前に、ここで理由を示して落とす
        problems.append(
            f"付録の項目が {len(appendix)} 件あり、見出し記号に使える"
            f" A〜Z の {MAX_APPENDIX_LETTERS} 文字を超えました。"
            "記号の付け方を決め直し、本スクリプトの連番検査も併せて直してください。"
        )
    else:
        # 期待する記号の並び（A から順に項目数だけ）を組み立てる
        expected = [chr(ord("A") + i) for i in range(len(appendix))]
        # 実際に書かれている記号の並びを取り出す
        actual = [letter for letter, _, _ in appendix]
        # 期待と食い違っていれば、両方を並べて報告する
        if actual != expected:
            problems.append(
                "付録の見出し記号が A から始まる連番になっていません: "
                f"実際 {' '.join(actual)} / 期待 {' '.join(expected)}"
            )

    # (d) README の表と付録の見出しで、バージョン番号の集合が一致するかを調べる。
    # #14 / #15 で実際に起きたずれがこれで、句読点や語尾の違いは数値を含まないため
    # スタック表記そのものを比べなくても検出できる。
    # 名前からスタック表記を引けるようにしておく
    appendix_stacks = {name: stack for _, name, stack in appendix}
    # README の各行について、同じ名前が付録にもあれば数値を突き合わせる
    for name, readme_stack in readme:
        # 付録に無い名前は (a) が既に報告しているので、ここでは飛ばす
        if name not in appendix_stacks:
            continue
        # それぞれのスタック表記からバージョン番号の集合を作る
        readme_versions = version_tokens(readme_stack)
        appendix_versions = version_tokens(appendix_stacks[name])
        # 食い違っていれば、両方の表記をそのまま添えて報告する
        if readme_versions != appendix_versions:
            problems.append(
                f"`{name}` のバージョン表記が README.md の表と CLAUDE.md 末尾の付録で"
                "食い違っています。どちらが実装と合っているかを確かめて揃えてください。"
                f"（README.md の表: {readme_stack}）"
                f"（CLAUDE.md 末尾の付録: {appendix_stacks[name]}）"
            )

    # 見つかった問題をまとめて返す
    return problems


def main() -> int:
    """3 か所の一覧を突き合わせ、食い違いがあれば理由を表示して失敗する。"""
    # 検査対象のファイルを読み込む（明示的に UTF-8 を指定し、実行環境の既定に依存させない）
    claude_text = CLAUDE_MD.read_text(encoding="utf-8")
    readme_text = README_MD.read_text(encoding="utf-8")

    # 突き合わせを行い、見つかった問題を受け取る
    problems = find_problems(claude_text, readme_text)

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
    print(
        f"集約元リポジトリの一覧は 3 か所で一致しています"
        f"（{len(read_header_repos(claude_text))} 件）。"
    )
    return 0


# スクリプトとして直接実行されたときだけ main を呼ぶ（import されたときは実行しない）
if __name__ == "__main__":
    raise SystemExit(main())
