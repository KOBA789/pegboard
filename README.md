# pegboard

> [!NOTE]
> このリポジトリは、Claude Opus 5.5 の空間認識能力のベンチマークも兼ねている。
> ここにあるデータ（build123d のスクリプトと、そこから生成した STL / STEP）は、すべて Claude がモデリングしたもの。

KOBA789 が自宅で使っている、ニトリの有孔ボード（Nポルダ、φ6 穴・25 mm ピッチ・板厚 5.5 mm）用の
3D プリントフック集。形状はすべて [build123d](https://github.com/gumyr/build123d) の Python スクリプトで作っている。

自分の家の物に合わせて作ったものなので、そのままでは他の家では使えないかもしれない。それでも、
同じボードを持っていて自分でパラメータをいじれる人なら再利用できるので公開している。
フックとペグなどの取付部分は `src/pegboard` にまとめてあるので、新しいフックを作るときの土台にも使える。

## フック一覧

| フック | 用途 | 出力 |
|---|---|---|
| [trackpoint_keyboard](hooks/trackpoint_keyboard/) | ThinkPad TrackPoint Keyboard II を掛ける。縦置き（A）と棚置き（B） | `cradle.stl` ×2 または `shelf.stl` ×2 |
| [switchbot_meter](hooks/switchbot_meter/) | SwitchBot 温湿度計を立てて入れるポケット | `pocket.stl` ×1 |
| [ipad_pro_11](hooks/ipad_pro_11/) | iPad Pro 11（M1）を横向きでボードの近くに置き、右から抜き差しする。USB-C は右に出る | `stop.stl` ×1、`rail.stl` ×数個 |
| [plate](hooks/plate/) | ボードと支柱の間に挟むスペーサー板（デスクライトのクランプ用）。ボス 2 個で穴に位置決め | `plate.stl` ×1 |

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

## 印刷と寸法合わせ

- 作者は Bambu Lab A1 mini と Bambu PLA Matte で印刷している。`write_stl` は A1 mini のベッド（180 mm 角）に
  収まらない形を書き出さない。もっと大きいプリンタなら `src/pegboard/export.py` の `BED` を変える。
- 穴径は、カタログ上は約 5 mm だが、作者のボードの実測では φ6.0 だった。圧入ペグ（φ6.1）や位置決めボスは
  この値に合わせてある。ボードのロットやプリンタによってきつさが変わるので、まずフック 1 個を試し刷りする。
  ペグがきつすぎたり緩すぎたりしたら、各モジュールの `P` の `peg_d` を変える。穴径そのものが違えば
  `src/pegboard/board.py` の `NPOLDA` を直す。直したら `make` で作り直し、`make test` を通す。

## 構成

```
src/pegboard/     共通ライブラリ（ボード寸法、フック/ペグ、出力）
hooks/<name>/     フックごとのパッケージ（build.py ほか）、README.md（寸法・設計・印刷設定）、output/
tests/            pytest
tools/            insertion_sim.py（フックが差し込めるかの 2D シミュレーション）
docs/             ボードの仕様と、実績のある取付部品の説明
```

ボードの寸法と取付部品は [docs/nitori_npolda.md](docs/nitori_npolda.md) を参照。

## ライセンス

[MIT](LICENSE)。生成済みの STL / STEP も含む。
