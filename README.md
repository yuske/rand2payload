# rand2payload

## Requirements

- Python 3.12+
- Node.js (used to mirror Chrome's `Math.random()` sequence)
- `z3-solver` Python package

### Suggested setup

```
python3 -m venv .venv
.venv/bin/pip install z3-solver
```

## Tests

The Chrome/Node regression test spawns Node.js to capture a `Math.random()` sequence, feeds the first five values into `predict_sequence`, and checks the predicted values against the subsequent numbers from Node.

Run the test with:

```
.venv/bin/python -m unittest tests/test_chrome_node.py
```

## CLI usage

`./rand2payload` exposes a small CLI wrapper around `predict_sequence`. Only the Chrome path is covered by automated tests; Firefox and Safari modes are experimental and not tested yet.

Example:

```
./rand2payload --count 15 0.9695987786633904 0.28071711843620584 0.17303127964472753 0.9884694323895107 0.5292326613492848
```

Use `--json` to print the predictions as a JSON array instead of one value per line.
Run the command from an environment where `z3-solver` is installed (activate the virtualenv created above).
