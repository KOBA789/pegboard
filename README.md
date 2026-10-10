# pegboard

家にあるニトリの有孔ボード（Nポルダ、φ6 穴・25 mm ピッチ・板厚 5.5 mm）に掛ける
3D プリント用のフック集。形状はすべて [build123d](https://github.com/gumyr/build123d)
の Python スクリプトで作る。

## フック一覧

| フック | 用途 | 出力 |
|---|---|---|
| [trackpoint_keyboard](hooks/trackpoint_keyboard/) | ThinkPad TrackPoint Keyboard II を掛ける。縦置き（A）と棚置き（B） | `cradle.stl` ×2 または `shelf.stl` ×2 |

## 使い方

```sh
uv sync          # 初回のみ
make             # 全フックの STEP / STL を hooks/<name>/output/ に再生成
make test        # pytest（形状の妥当性、ボードとの干渉、ベッドに収まるか）
make lint        # ruff
uv run python -m hooks.trackpoint_keyboard.build   # 1 つだけ作る
```

- `*.stl` は印刷する向きに置いてあるので、そのままスライサーに読み込める（Bambu Lab A1 mini、180 mm 角）。
- `*.step` はボード座標で出力する（確認用。`*_assembly.step` はボード・キーボードとの組み図）。

## 構成

```
src/pegboard/     共通ライブラリ（ボード寸法、フック/ペグ、出力）
hooks/<name>/     フックごとのパッケージ（build.py ほか）、README.md（寸法・設計・印刷設定）、output/
tests/            pytest
tools/            insertion_sim.py（フックが差し込めるかの 2D シミュレーション）
docs/             ボードの仕様と、実績のある取付部品の説明
```

ボードの寸法と取付部品は [docs/nitori_npolda.md](docs/nitori_npolda.md) を参照。
