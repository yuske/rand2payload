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
