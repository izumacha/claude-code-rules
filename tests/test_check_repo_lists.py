"""`scripts/check_repo_lists.py` が主張どおりに検出できることを固定するテスト。

**このテストが必要な理由**: 検査スクリプト本体は「一覧が一致していれば緑」を出すだけ
なので、**検査の中身を消しても実ファイルに対しては緑のまま通る**。実際、3 か所の
突き合わせ（`union` を回すブロック）をまるごと削っても、README の読み取り範囲を
節に限定する条件を外しても、`python3 scripts/check_repo_lists.py` は
「一致しています（8 件）」と表示して 0 で終わる。つまり本体だけでは
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
            self.checker.read_appendix_repos(VALID_CLAUDE),
            [("A", "alpha"), ("B", "beta"), ("C", "gamma")],
        )

    def test_readme_reads_only_the_target_section(self):
        """README の読み取りが「集約元リポジトリ」節の表だけに限定されること。

        節を限定していないと、別の節に増えた表まで巻き込む。
        """
        # 対象節より後ろに、同じ書式の別の表を持つ節を足した入力を組み立てる
        text = VALID_README + "\n## 別の表\n\n| 項目 | 値 |\n|---|---|\n| `noise` | x |\n"
        # 別の節の `noise` を拾わず、対象節の 3 件だけを返すことを確かめる
        self.assertEqual(
            self.checker.read_readme_repos(text), ["alpha", "beta", "gamma"]
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
        code, _ = self.run_check(VALID_CLAUDE, broken)
        self.assertEqual(code, 1)

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
        code, _ = self.run_check(VALID_CLAUDE, broken)
        self.assertEqual(code, 1)

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
