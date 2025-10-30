# rand2payload

## Requirements

- Python 3.12+
- Node.js (used to mirror Chrome's `Math.random()` sequence)
- `z3-solver` Python package

### Suggested setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install z3-solver
```

## Tests

The Chrome/Node regression test spawns Node.js to capture a `Math.random()` sequence, feeds the first five values into `predict_sequence`, and checks the predicted values against the subsequent numbers from Node.

Run the test with:

```
python3 -m unittest tests/test_chrome_node.py
```

## CLI usage

`./rand2payload` exposes a small CLI wrapper around `predict_sequence`. Only the Chrome path is covered by automated tests; Firefox and Safari modes are experimental and not tested yet.

Example:

```
./rand2payload --count 15 0.9695987786633904 0.28071711843620584 0.17303127964472753 0.9884694323895107 0.5292326613492848
```

Use `--json` to print the predictions as a JSON array instead of one value per line.
Run the command from an environment where `z3-solver` is installed (activate the virtualenv created above).

## Static web server

`./web_server.py` serves files from the `public/` directory (default) with permissive CORS headers and optional verbose logging of request headers and bodies.

Example:

```
./web_server.py --host 0.0.0.0 --port 8080 --verbose
```

Visit `http://localhost:8080/` to load the sample `public/index.html` page. The `--verbose` flag prints incoming headers and body payloads in addition to the method and URL.

### Predict endpoint

When the server is running, it also exposes a POST `/predict` endpoint that wraps `predict_sequence`.

Body fields:

- `kind`: `"double"` for raw `Math.random()` observations, or `"round"` when you only have the rounded integers (e.g. `Math.round(Math.random() * 10000)`).
- `observations`: non-empty array of your observed values (ints for `round`, floats for `double`).
- `count`: how many future random values you want.
- `scale` (optional): only for `kind: "round"`. If omitted, the server infers a decimal scale from the maximum observation.

Example request:

```js
fetch('http://localhost:8000/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    kind: 'round',
    observations: [9415, 1920, 3442, 3584, 3390, 7138, 6626, 6473, 3740, 1409],
    count: 10,
    scale: 10000
  }),
})
  .then((res) => res.json())
  .then(({ predictions }) => console.log(predictions));
```
