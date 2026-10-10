# CLAUDE.md

ニトリ Nポルダ有孔ボード（φ6 穴、25 mm ピッチ、板厚 5.5 mm）用のフックを build123d で作るリポジトリ。
詳しい構成と使い方は README.md、ボード仕様と取付部品の根拠は docs/nitori_npolda.md を参照。

## コマンド

- `make` — 全フックの出力を再生成する（`uv run hooks/<name>/build.py` を順に実行）
- `make test` / `make lint` — pytest / ruff（line-length 100）
- `uv run python tools/insertion_sim.py '<json>'` — フックが差し込めるかの 2D シミュレーション

## 約束ごと

- **座標系**（`src/pegboard/board.py`）: x はボードに沿って右、y は上、z はボードから部屋側。
  z = 0 がボードの表面、原点は基準にする穴の中心。フックやペグは -z 側に伸びる。単位は mm。
- 取付部品（`bent_hook` / `straight_peg` / `press_fit_peg`）は穴の中心を原点として作り、
  `Pos(NPOLDA.hole(i, j)) * part` で配置する。新しい取付形状を作るのではなく、まずこれらを使う。
  フック形状を変えたら、必ず `tools/insertion_sim.py` で挿入性を確認する。
- フックごとに `hooks/<name>/` を作り、次のものを置く。
  - `build.py`: 冒頭の `P = dict(...)` にパラメータ、`main()` で出力
  - `README.md`: 対象物の寸法と出典、設計の意図、印刷設定、取り付け方
  - `output/`
- **出力**: STEP はボード座標、STL は印刷の向き（`pegboard.export.lay_on_side` / `on_bed`）。
  `write_stl` は、単一の valid なソリッドで A1 mini（180 mm 角）に収まるものしか書き出さない。
  STEP のタイムスタンプは固定してあるので、形状が変わらなければ出力は同一になる。
- **生成物（STL/STEP）もコミットする**。形状を変えたら、`make` で再生成して一緒にコミットする。
- テストは `tests/test_<name>.py`。最低限、次を確認する。
  - 単一の valid なソリッドである
  - ベッドに収まる
  - 装着した状態でボードと干渉しない（交差体積がほぼ 0）
  - 載せる物と干渉しない
- 見た目: 見える稜線は丸める。ただし、ボードに接する面は平らで角のまま残す（丸めると隙間が見えて不格好になる）。
  ベッドに置く面の稜線は、45° 以下のオーバーハングになるようにする。
- 寸法は、公称値か実測値か推定値かをコメントで区別する。
- 参考: 取付部品は、FreeCAD 時代に作った HUB75 パネル用レール（非公開）から移植したもの。
  `tests/test_mount.py` で、移植した形状が当時のものと一致することを確認している。
