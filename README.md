# Chess Engine with ML-Based Move Filtering

A UCI-compatible chess engine written in Python, combining classical alpha-beta
search with a machine learning model trained on real games to guide move
selection, plus an opening book and quiescence search.

## Overview

This started as a standard minimax/alpha-beta engine with material +
piece-square-table (PST) evaluation. I then extended it with three additional
components, each targeting a specific weakness of naive minimax engines:

1. **ML move filtering** — a lightweight classifier that scores legal moves
   by how likely a strong human player would be to play them, and prunes
   the weakest half before the search even starts.
2. **Opening book** — a Polyglot book so the engine plays established theory
   in the opening instead of "reasoning" every move from scratch.
3. **Quiescence search** — extends the search at leaf nodes through capture
   sequences only, to avoid the classic horizon effect (missing a piece
   being recaptured one ply beyond the search depth).

## How the ML move filter works

The idea is adapted from Ethan Mai's article ["How I Coded My Own Python
Chess Engine"](https://towardsdatascience.com/machine-learning-how-i-coded-my-own-python-chess-engine-c4c81bcb2a9a/),
reimplemented with a lighter model:

- **Data**: PGN games from the [Lichess open database](https://database.lichess.org/)
  and the [Lichess Elite Database](https://database.nikonoel.fr/) (games
  between players rated 2200+/2400+).
- **Labeling**: for each position where the eventual winner was to move, the
  move they actually played is labeled "good" (1); a randomly sampled legal
  alternative from the same position is labeled "bad" (0).
- **Features**: 14 handcrafted features per move — captured material value,
  change in PST positional bonus, whether the move is a capture/check/castle/
  promotion, distance of the destination square from the center, and the
  piece type. All computed with [python-chess](https://python-chess.readthedocs.io/).
- **Model**: logistic regression (scikit-learn), trained offline. Weights are
  exported to a small JSON file, so the engine itself only needs plain
  arithmetic at inference time — no scikit-learn/pandas dependency at runtime.
- **Usage in search**: legal moves are scored by the model; the bottom half
  is discarded before minimax runs, except captures and checks, which are
  always kept regardless of score (safety net against missing tactics).
  The filter is only applied a few plies from the root — the last couple of
  plies before a leaf are searched in full, so late-game tactics aren't
  pruned away.

On a held-out test set, the classifier reaches **~66-68% accuracy / ~0.71-0.74
ROC-AUC** at distinguishing a strong player's move from a random legal
alternative — meaningfully better than chance, though this is a simple linear
model on a small feature set, not a claim of strong tactical understanding.

## Other components

- **Evaluation**: material values + piece-square tables (PST) per piece type.
- **Search**: alpha-beta pruning with MVV-LVA move ordering (capture the most
  valuable piece with the least valuable attacker first) to improve pruning
  efficiency.
- **Quiescence search**: at the search horizon, captures are played out until
  the position is "quiet" before returning a static evaluation.
- **Opening book**: Polyglot-format book (`chess.polyglot`), engine queries it
  first and only falls back to search once the position leaves the book.

## Project structure

```
engine.py               UCI loop, search, evaluation
move_filter.py           ML move-filtering logic (inference only)
features.py               Feature extraction shared by training and inference
config.json               Piece values and piece-square tables
move_filter_model.json    Trained logistic regression weights
build_dataset.py          Parses PGN games into a labeled move dataset
train_model.py            Trains the logistic regression model, exports weights
play.py                   Terminal game against the engine
requirements.txt          Runtime dependency (python-chess)
```

## Play a game against it

```bash
pip install -r requirements.txt
python play.py              # you are White, engine depth 3
python play.py --black      # you are Black
python play.py --depth 4    # stronger but slower engine (max 10)
```

Type moves like `e4`, `Nf3`, `O-O` or `e2e4`. Commands: `undo`, `resign`, `quit`.

Or load `engine.py` in any UCI GUI (Arena, En Croissant, Cute Chess) as an engine.

## Running it

The engine speaks the standard UCI protocol, so it works with any UCI-compatible
GUI (Arena, En Croissant, Cute Chess) or as a [Lichess bot](https://lichess.org/api#tag/Bot)
via [lichess-bot](https://github.com/lichess-bot-devs/lichess-bot).

```bash
pip install python-chess
python engine.py
```

To retrain the ML filter on your own PGN data:

```bash
pip install python-chess pandas scikit-learn
python build_dataset.py   # PGN -> dataset.csv
python train_model.py     # dataset.csv -> move_filter_model.json
```

## Motivation

I built this to go beyond a "textbook" minimax engine and explore where a
data-driven component can realistically help a classical search algorithm —
and, just as importantly, where it can't (a linear model on 14 features is
not going to develop positional understanding on its own; it's a pruning
heuristic, not a replacement for search or a strong evaluation function).

## Acknowledgements

- Opening book (`gm2001.bin`): [michaeldv/donna_opening_books](https://github.com/michaeldv/donna_opening_books)
- Training data: [Lichess open database](https://database.lichess.org/) and
  [Lichess Elite Database](https://database.nikonoel.fr/) by nikonoel
  (both released under CC0)
- ML move-filtering concept adapted from Ethan Mai's article on
  Towards Data Science
