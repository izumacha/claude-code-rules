"""`scripts/check_repo_lists.py` が主張どおりに検出できることを固定するテスト。

**このテストが必要な理由**: 検査スクリプト本体は「一覧が一致していれば緑」を出すだけ
なので、**検査の中身を消しても実ファイルに対しては緑のまま通る**。実際、3 か所の
突き合わせ（`union` を回すブロック）をまるごと削っても、README の読み取り範囲を
節に限定する条件を外しても、`python3 scripts/check_repo_lists.py` は
「一致しています（N 件）」と表示して 0 で終わる。つまり本体だけでは
「検出網が働いている」と「検出網が骨抜きになった」を区別できない。

そこでここでは**合成した入力**（実ファイルではなく、テスト内で組み立てた文字列）に
対して「壊した入力なら落ちること」「正しい入力なら通ること」の両方を固定する。
実ファイルを書き換えて確かめる形にしないのは、テストが失敗した途中で
リポジトリのファイルが壊れたまま残るのを避けるため。

CLAUDE.md §11 の配置規約（Python は `tests/test_<module>.py`）に従う。
標準ライブラリの unittest だけを使い、依存を増やさない。
"""

# 型注釈を実行時に評価させない（前方参照を素直に書けるようにする）
from __future__ import annotations

# 検査対象のスクリプトをモジュールとして読み込むために使う
import importlib.util

# 標準のテストランナーを使う（外部依存を増やさないため）
import unittest

# ファイルパスを OS 非依存に組み立てるために使う
from pathlib import Path

# このテストファイルの位置からリポジトリのルートを求める
REPO_ROOT = Path(__file__).resolve().parent.parent

# 検査対象スクリプトの場所
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_repo_lists.py"


def load_checker():
    """`scripts/check_repo_lists.py` をモジュールとして読み込んで返す。

    ファイル名がハイフンを含まないので import でも読めるが、`scripts/` を
    パッケージにしないためファイルパス指定で読み込む。
    """
    # ファイルパスから読み込み方（spec）を組み立てる
    spec = importlib.util.spec_from_file_location("check_repo_lists", SCRIPT_PATH)
    # 空のモジュールオブジェクトを作る
    module = importlib.util.module_from_spec(spec)
    # モジュールの中身を実際に実行して関数を定義させる
    spec.loader.exec_module(module)
    # 出来上がったモジュールを呼び出し側へ返す
    return module


# テストの各ケースで使い回す、正しく揃った状態の CLAUDE.md 相当のテキスト
VALID_CLAUDE = """# CLAUDE.md

> このファイルは原本です。
>
> 集約元リポジトリ: `alpha` / `beta` /
> `gamma`

## 0. 使い方

---

## 付録: リポジトリ別のルール（Appendix）

### A. alpha（静的 HTML）

- 何らかの規約。

### B. beta（Python + tkinter, GUI）

- 何らかの規約。

### C. gamma（Java 21 / Maven）

- 何らかの規約。
"""

# 正しく揃った状態の README.md 相当のテキスト
VALID_README = """# README

## 集約元リポジトリ

| リポジトリ | スタック |
|---|---|
| `alpha` | 静的 HTML（GitHub Pages）|
| `beta` | Python + tkinter（GUI）|
| `gamma` | Java 21 / Maven（バッチ）|

※ `delta` は private のため未収録。
"""


class ReadersTest(unittest.TestCase):
    """3 か所それぞれの読み取りが、意図した範囲だけを拾うことを固定する。"""

    def setUp(self):
        """各テストの前に検査スクリプトを読み込む。"""
        # 検査対象のモジュールを取得してテストから使えるようにする
        self.checker = load_checker()

    def test_header_reads_wrapped_enumeration(self):
        """冒頭の列挙が複数行に折り返されていても全件読めること。"""
        # 折り返された列挙から 3 件すべてを拾えることを確かめる
        self.assertEqual(
            self.checker.read_header_repos(VALID_CLAUDE), ["alpha", "beta", "gamma"]
        )

    def test_header_stops_before_unrelated_sentence(self):
        """列挙の後ろに別の文が続いても、その中のバッククォートを拾わないこと。

        README にある「※ `delta` は private のため未収録。」を冒頭の blockquote へ
        書き写す編集は自然に起こりうる。ここで拾ってしまうと「意図的に載せていない
        private リポジトリを公開の README と付録へ追加せよ」という、実行しては
        いけない指示を出す誤検知になる。
        """
        # 列挙のすぐ後ろに注記を足した入力を組み立てる
        text = VALID_CLAUDE.replace(
            "> `gamma`", "> `gamma`\n>\n> ※ `delta` は private のため未収録。"
        )
        # 注記の中の `delta` を拾わず、列挙の 3 件だけを返すことを確かめる
        self.assertEqual(
            self.checker.read_header_repos(text), ["alpha", "beta", "gamma"]
        )

    def test_appendix_reads_letter_and_name(self):
        """付録の見出しから記号と名前の組を順に読めること。"""
        # 見出し記号と名前が想定どおりに取り出せることを確かめる
        self.assertEqual(
            self.checker.read_appendix_entries(VALID_CLAUDE),
            [
                ("A", "alpha", "静的 HTML"),
                ("B", "beta", "Python + tkinter, GUI"),
                ("C", "gamma", "Java 21 / Maven"),
            ],
        )

    def test_readme_reads_only_the_target_section(self):
        """README の読み取りが「集約元リポジトリ」節の表だけに限定されること。

        節を限定していないと、別の節に増えた表まで巻き込む。
        """
        # 対象節より後ろに、同じ書式の別の表を持つ節を足した入力を組み立てる
        text = VALID_README + "\n## 別の表\n\n| 項目 | 値 |\n|---|---|\n| `noise` | x |\n"
        # 別の節の `noise` を拾わず、対象節の 3 件だけを返すことを確かめる
        self.assertEqual(
            [name for name, _ in self.checker.read_readme_entries(text)],
            ["alpha", "beta", "gamma"],
        )

    def test_readme_stops_after_the_first_table(self):
        """同じ節の中に別の表が続いても、最初の表だけを読むこと。

        対象節はファイル末尾まで続くため、節を限定するだけでは足りない。実際この節には
        検査の使い方の説明が足してあり、そこに表を書く編集は自然に起こる。拾うと
        「`用語` が CLAUDE.md 冒頭の列挙 / 付録に載っていません」という、実行しては
        いけない指示を出す誤検知になる。
        """
        # 同じ節の中に、説明文と 2 つ目の表を足した入力を組み立てる
        text = VALID_README + "\n用語の対応表:\n\n| 用語 | 意味 |\n|---|---|\n| `用語` | x |\n"
        # 2 つ目の表の `用語` を拾わず、最初の表の 3 件だけを返すことを確かめる
        self.assertEqual(
            [name for name, _ in self.checker.read_readme_entries(text)],
            ["alpha", "beta", "gamma"],
        )

    def test_header_stops_at_prose_on_the_next_line(self):
        """空行を挟まずに別の文が続く場合も、その中のバッククォートを拾わないこと。

        空行での打ち切りだけに頼ると、列挙の直後の行に注記を書いた場合をすり抜ける。
        """
        # 空行を挟まずに注記を続けた入力を組み立てる
        text = VALID_CLAUDE.replace(
            "> `gamma`", "> `gamma`\n> ※ `delta` は private のため未収録。"
        )
        # 注記の中の `delta` を拾わず、列挙の 3 件だけを返すことを確かめる
        self.assertEqual(
            self.checker.read_header_repos(text), ["alpha", "beta", "gamma"]
        )

    def test_header_reads_lazy_continuation_without_marker(self):
        """列挙の続きが `>` なしで書かれていても読めること。

        Markdown では blockquote の続きを `>` なしで書ける（lazy continuation）。
        表示は同じなのに読み取りだけが途中で止まると、画面に見えているリポジトリを
        「載っていません」と報告してしまう。
        """
        # 2 行目の `>` を外した入力を組み立てる
        text = VALID_CLAUDE.replace("> `gamma`", "`gamma`")
        # `>` の有無にかかわらず 3 件すべてを読めることを確かめる
        self.assertEqual(
            self.checker.read_header_repos(text), ["alpha", "beta", "gamma"]
        )

    def test_readme_row_without_backticks_does_not_swallow_later_rows(self):
        """バッククォートを書き忘れた行があっても、後続の行を読み飛ばさないこと。

        打ち切りの条件を「パターンに一致しない行」にすると、1 行の書き忘れで以降が
        すべて読まれず、実際には表に載っているリポジトリまで「載っていません」と
        報告する。その指示に従うと行が二重になり、今度は重複検査で落ちる。
        """
        # 2 行目のバッククォートだけを外した入力を組み立てる
        text = VALID_README.replace(
            "| `beta` | Python + tkinter（GUI）|", "| beta | Python + tkinter（GUI）|"
        )
        # 書き忘れた行だけが落ち、その後ろの gamma は読めていることを確かめる
        self.assertEqual(
            [name for name, _ in self.checker.read_readme_entries(text)],
            ["alpha", "gamma"],
        )

    def test_header_marker_outside_blockquote_is_ignored(self):
        """blockquote の外にある同じ語では読み取りを始めないこと。

        本文に「現在の集約元リポジトリ: 8 件」のような文があると、そこで読み始めて
        しまい、続く行が列挙でないため空の一覧を返す。fail-closed で落ちはするが
        「書式を変えたなら読み取りも直せ」という誤った診断になり、実際には無傷の
        blockquote を疑わせる。
        """
        # 本物の blockquote より前に、同じ語を含む本文の行を足した入力を組み立てる
        text = VALID_CLAUDE.replace(
            "# CLAUDE.md", "# CLAUDE.md\n\n現在の集約元リポジトリ: 3 件（詳細は付録）。"
        )
        # 本文の行に反応せず、blockquote の列挙 3 件を返すことを確かめる
        self.assertEqual(
            self.checker.read_header_repos(text), ["alpha", "beta", "gamma"]
        )

    def test_appendix_reads_only_the_appendix_section(self):
        """付録の読み取りが「## 付録」以降に限定されること。

        このファイルは新規リポジトリへコピーして §1〜§3 を埋めるテンプレートなので、
        埋めた内容に同じ書式の見出しが現れうる。拾うと連番検査が
        「実際 A B A B / 期待 A B C D」という原因の分からない失敗を出す。
        """
        # 付録より前の節に、同じ書式の見出しを足した入力を組み立てる
        text = VALID_CLAUDE.replace(
            "## 0. 使い方",
            "## 3. アーキテクチャ\n\n### A. 入力レイヤ（バリデーション）\n\n- 説明。\n",
        )
        # 付録の外の見出しを拾わず、付録の 3 件だけを返すことを確かめる
        self.assertEqual(
            self.checker.read_appendix_entries(text),
            [
                ("A", "alpha", "静的 HTML"),
                ("B", "beta", "Python + tkinter, GUI"),
                ("C", "gamma", "Java 21 / Maven"),
            ],
        )


class DetectionTest(unittest.TestCase):
    """「壊した入力なら落ちる／正しい入力なら通る」を固定する。

    検査本体を骨抜きにする改変（突き合わせのブロックごと削る等）を入れると、
    このクラスのどれかが失敗するようにしてある。
    """

    def setUp(self):
        """各テストの前に検査スクリプトを読み込み、実ファイルの代わりに合成入力を使わせる。"""
        # 検査対象のモジュールを取得する
        self.checker = load_checker()

    def run_check(self, claude_text: str, readme_text: str) -> tuple[int, str]:
        """合成した 2 つのテキストに対して検査を走らせ、(終了コード, 出力) を返す。

        実ファイルを書き換えずに済ませるため、読み込み先だけを一時的に差し替える。
        出力も返すのは、終了コードだけでは「どの分岐で落ちたか」を固定できないため
        （たとえば読み取り不能のときは、専用の案内を出さなくても欠落として報告され
        1 にはなる。案内の有無まで見ないと、その分岐を消しても気付けない）。
        """
        # 標準出力を横取りするために使う
        import contextlib

        # 出力を貯めるための入れ物として使う
        import io

        # 一時ディレクトリを作り、その中に合成したファイルを書き出す
        import tempfile

        # with を抜けると一時ディレクトリごと自動で消える
        with tempfile.TemporaryDirectory() as tmp:
            # 合成した CLAUDE.md を書き出す
            claude_path = Path(tmp) / "CLAUDE.md"
            claude_path.write_text(claude_text, encoding="utf-8")
            # 合成した README.md を書き出す
            readme_path = Path(tmp) / "README.md"
            readme_path.write_text(readme_text, encoding="utf-8")
            # モジュールが見に行く先を、この一時ファイルへ差し替える
            self.checker.CLAUDE_MD = claude_path
            self.checker.README_MD = readme_path
            # 検査の出力を受け取るバッファを用意する
            buffer = io.StringIO()
            # print の出力先をバッファへ切り替えたうえで検査を実行する
            with contextlib.redirect_stdout(buffer):
                code = self.checker.main()
            # 終了コードと出力の組を返す（0 = 問題なし、1 = 問題あり）
            return code, buffer.getvalue()

    def test_valid_input_passes(self):
        """揃っている入力では 0 で通ること（誤検知しないこと）。"""
        # 正しい入力に対しては問題を報告しないことを確かめる
        code, _ = self.run_check(VALID_CLAUDE, VALID_README)
        self.assertEqual(code, 0)

    def test_missing_row_in_readme_fails(self):
        """README の表から 1 行落とすと落ちること。"""
        # README の表から gamma の行を取り除いた入力を作る
        broken = VALID_README.replace("| `gamma` | Java 21 / Maven（バッチ）|\n", "")
        # 欠落を検出して 1 を返すことを確かめる
        code, output = self.run_check(VALID_CLAUDE, broken)
        self.assertEqual(code, 1)
        # 欠けている名前と、**どこに足りないのか**まで名指しできていることを確かめる。
        # 終了コードだけを見ると、報告先のラベルを取り違えても（たとえば冒頭の列挙と
        # README の表を入れ替えても）通ってしまい、直す場所を誤って案内する
        self.assertIn("`gamma`", output)
        self.assertIn("README.md の表", output)
        # 実際には揃っている箇所を「載っていない」と言わないことも確かめる
        self.assertNotIn("CLAUDE.md 冒頭の列挙", output)
        self.assertNotIn("CLAUDE.md 末尾の付録", output)

    def test_missing_from_two_places_names_both(self):
        """2 箇所に足りないときは 2 箇所とも名指しすること。

        報告先を先頭 1 件に切り詰めても終了コードは 1 のままなので、
        件数まで固定しないと「片方だけ直して再び落ちる」案内になる。
        """
        # README の表にだけ delta を足し、CLAUDE.md 側には足さない入力を作る
        broken = VALID_README.replace(
            "| `gamma` | Java 21 / Maven（バッチ）|",
            "| `gamma` | Java 21 / Maven（バッチ）|\n| `delta` | 何か |",
        )
        # 欠落を検出して 1 を返すことを確かめる
        code, output = self.run_check(VALID_CLAUDE, broken)
        self.assertEqual(code, 1)
        # CLAUDE.md 側の 2 箇所がどちらも名指しされることを確かめる
        self.assertIn("CLAUDE.md 冒頭の列挙", output)
        self.assertIn("CLAUDE.md 末尾の付録", output)
        # 実際に載っている README を「載っていない」と言わないことも確かめる
        self.assertNotIn("README.md の表", output)

    def test_missing_entry_in_header_fails(self):
        """冒頭の列挙から 1 件落とすと落ちること。"""
        # 冒頭の列挙から beta を取り除いた入力を作る
        broken = VALID_CLAUDE.replace("`alpha` / `beta` /", "`alpha` /")
        # 欠落を検出して 1 を返すことを確かめる
        code, _ = self.run_check(broken, VALID_README)
        self.assertEqual(code, 1)

    def test_missing_appendix_heading_fails(self):
        """付録の見出しが 1 つ欠けると落ちること。"""
        # 付録から gamma の見出しを取り除いた入力を作る
        broken = VALID_CLAUDE.replace("### C. gamma（Java 21 / Maven）", "")
        # 欠落を検出して 1 を返すことを確かめる
        code, _ = self.run_check(broken, VALID_README)
        self.assertEqual(code, 1)

    def test_duplicate_row_fails(self):
        """同じリポジトリ名を 2 回書くと落ちること。"""
        # README の表に beta の行を重ねた入力を作る
        broken = VALID_README.replace(
            "| `beta` | Python + tkinter（GUI）|",
            "| `beta` | Python + tkinter（GUI）|\n| `beta` | Python + tkinter（GUI）|",
        )
        # 重複を検出して 1 を返すことを確かめる
        code, output = self.run_check(VALID_CLAUDE, broken)
        self.assertEqual(code, 1)
        # 重複として報告されることまで確かめる。終了コードだけを見ると、重複検査を
        # 消しても並び順の検査が別の理由で 1 を返すため、素通りしてしまう
        self.assertIn("複数回", output)
        self.assertIn("`beta`", output)

    def test_non_sequential_appendix_letter_fails(self):
        """付録の見出し記号が連番から外れると落ちること。"""
        # 付録の記号を C から Z へ飛ばした入力を作る
        broken = VALID_CLAUDE.replace("### C. gamma", "### Z. gamma")
        # 連番の乱れを検出して 1 を返すことを確かめる
        code, _ = self.run_check(broken, VALID_README)
        self.assertEqual(code, 1)

    def test_unreadable_header_fails_closed(self):
        """冒頭の列挙を読み取れなくなったら fail-closed で落ちること。

        書式が変わって読めなくなったときに「対象ゼロ＝違反ゼロ＝緑」で
        検出網が黙って死ぬのを防ぐ。
        """
        # 目印の文字列を変えて読み取れなくした入力を作る
        broken = VALID_CLAUDE.replace("集約元リポジトリ:", "集約もとリポジトリ:")
        # 読み取り不能を検出して 1 を返すことを確かめる
        code, output = self.run_check(broken, VALID_README)
        self.assertEqual(code, 1)
        # 「欠落が 8 件」ではなく、書式が読めなくなった旨の案内が出ることまで確かめる。
        # ここを見ないと、専用の分岐を消しても（欠落として報告されるため）1 のまま通る。
        self.assertIn("読み取れませんでした", output)

    def test_version_drift_between_readme_and_appendix_fails(self):
        """README の表と付録でバージョン番号が食い違うと落ちること。

        #14（Next.js 15 → 16）と #15（EF Core 8 → 9）で実際に起きたずれがこれ。
        句読点や語尾の書式差は数値を含まないので、スタック表記そのものを比べなくても
        数値の集合だけで検出できる。
        """
        # 付録が「Java 21」のまま、README の表だけを「Java 17」に変えた入力を作る
        broken = VALID_README.replace(
            "| `gamma` | Java 21 / Maven（バッチ）|",
            "| `gamma` | Java 17 / Maven（バッチ）|",
        )
        # ずれを検出して 1 を返すことを確かめる
        code, output = self.run_check(VALID_CLAUDE, broken)
        self.assertEqual(code, 1)
        # どのリポジトリのどの表記が食い違っているかを示すことを確かめる
        self.assertIn("`gamma`", output)
        self.assertIn("バージョン表記", output)

    def test_extra_version_only_in_readme_fails(self):
        """README にだけ余分な版が書かれている場合も落ちること。

        #15 が削除した実在しない「+ C# .NET 10」がこの形（付録には無い数値が
        README にだけある）だった。
        """
        # README の表にだけ、付録に無い版を足した入力を作る
        broken = VALID_README.replace(
            "| `beta` | Python + tkinter（GUI）|",
            "| `beta` | Python + tkinter（GUI）+ C# .NET 10 |",
        )
        # ずれを検出して 1 を返すことを確かめる
        code, output = self.run_check(VALID_CLAUDE, broken)
        self.assertEqual(code, 1)
        # 対象のリポジトリ名が示されることを確かめる
        self.assertIn("`beta`", output)

    def test_formatting_difference_alone_does_not_fail(self):
        """句読点や語尾だけが違う場合は落ちないこと（誤検知しないこと）。

        README の「（GitHub Pages）」対 付録の「, GitHub Pages」、README の
        「（bash, Linux）」対 付録の「, bash, Linux 専用」のような差は正常な状態。
        ここで落とすと、正しい記述を直せという指示になる。
        """
        # 語尾だけを変えた（数値は同じ）入力を作る
        readme = VALID_README.replace(
            "| `beta` | Python + tkinter（GUI）|",
            "| `beta` | Python + tkinter（GUI・デスクトップ）|",
        )
        # 書式の差だけでは問題として報告しないことを確かめる
        code, _ = self.run_check(VALID_CLAUDE, readme)
        self.assertEqual(code, 0)

    def test_order_mismatch_fails(self):
        """3 箇所の並び順がずれると落ちること。

        付録は A, B, C... と記号を振り本文がその記号で相互参照するため、並びが
        ずれると読み手が別のリポジトリの説明にたどり着く。
        """
        # README の表で 2 行目と 3 行目を入れ替えた入力を作る
        broken = VALID_README.replace(
            "| `beta` | Python + tkinter（GUI）|\n| `gamma` | Java 21 / Maven（バッチ）|",
            "| `gamma` | Java 21 / Maven（バッチ）|\n| `beta` | Python + tkinter（GUI）|",
        )
        # 並びのずれを検出して 1 を返すことを確かめる
        code, output = self.run_check(VALID_CLAUDE, broken)
        self.assertEqual(code, 1)
        # 並びの問題であることが分かる文言が出ることを確かめる
        self.assertIn("並び", output)

    def test_more_than_26_entries_reports_the_letter_limit(self):
        """付録が 26 件を超えたら、連番の乱れではなく上限の超過として報告すること。

        A〜Z を使い切ると連番を作れない。そのまま連番検査に掛けると
        「付録に載っていません」という、既に書いてある見出しを足せという
        誤った案内になる。
        """
        # 27 件のリポジトリ名を用意する
        names = [f"repo{i:02d}" for i in range(27)]
        # 冒頭の列挙・付録・README の 3 箇所を 27 件で組み立てる
        claude = (
            "# CLAUDE.md\n\n> 集約元リポジトリ: "
            + " / ".join(f"`{n}`" for n in names)
            + "\n\n## 付録: リポジトリ別のルール（Appendix）\n\n"
            + "".join(
                f"### {chr(ord('A') + i % 26)}. {n}（スタック）\n\n- 規約。\n\n"
                for i, n in enumerate(names)
            )
        )
        readme = (
            "# README\n\n## 集約元リポジトリ\n\n| リポジトリ | スタック |\n|---|---|\n"
            + "".join(f"| `{n}` | スタック |\n" for n in names)
        )
        # 上限の超過として 1 を返すことを確かめる
        code, output = self.run_check(claude, readme)
        self.assertEqual(code, 1)
        # 連番の乱れではなく、記号を使い切った旨を伝えることを確かめる
        self.assertIn("A〜Z", output)

    def test_unreadable_appendix_fails_closed(self):
        """付録の見出しを読み取れなくなったら fail-closed で落ちること。"""
        # 見出しの階層を 1 段深くして、付録として認識できなくした入力を作る
        broken = VALID_CLAUDE.replace("### ", "#### ")
        # 読み取り不能を検出して 1 を返すことを確かめる
        code, output = self.run_check(broken, VALID_README)
        self.assertEqual(code, 1)
        # 同上。専用の案内が出ることまで固定する
        self.assertIn("読み取れませんでした", output)

    def test_unreadable_readme_table_fails_closed(self):
        """README の表を読み取れなくなったら fail-closed で落ちること。"""
        # 節の見出しを変えて表を見つけられなくした入力を作る
        broken = VALID_README.replace("## 集約元リポジトリ", "## 対象リポジトリ")
        # 読み取り不能を検出して 1 を返すことを確かめる
        code, output = self.run_check(VALID_CLAUDE, broken)
        self.assertEqual(code, 1)
        # 同上。専用の案内が出ることまで固定する
        self.assertIn("読み取れませんでした", output)


class RealFilesTest(unittest.TestCase):
    """実際の CLAUDE.md / README.md が現時点で一致していることを固定する。"""

    def test_repository_files_are_consistent(self):
        """リポジトリ同梱のファイルに対して検査が通ること。"""
        # 読み込み先を差し替えずにそのまま実行する
        self.assertEqual(load_checker().main(), 0)


# ファイルを直接実行したときにもテストを走らせられるようにする
if __name__ == "__main__":
    unittest.main()
