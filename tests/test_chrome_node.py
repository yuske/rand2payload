import json
import subprocess
import unittest

from extensions import constraint_rounded
from xs128p import predict_sequence


class ChromeNodePredictionTest(unittest.TestCase):
    def _generate_node_randoms(
        self,
        count,
        expression='value'
    ):
        script = f"""
const count = {count};
const values = [];
const modified = [];
const compute = (value) => {expression};
for (let i = 0; i < count; i++) {{
  const value = Math.random();
  values.push(value);
  modified.push(compute(value));
}}
console.log(JSON.stringify({{values, modified}}));
"""
        result = subprocess.run(
            ['node', '-e', script],
            check=True,
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        return data['values'], data['modified']

    def test_predict_sequence_matches_node_math_random(self):
        total_numbers = 64
        observations = 5
        values, _ = self._generate_node_randoms(total_numbers)

        observed = values[:observations]
        expected = values[observations:]

        predicted = predict_sequence(observed, len(expected), browser='chrome')

        self.assertEqual(len(predicted), len(expected))
        for index, (pred, exp) in enumerate(zip(predicted, expected)):
            self.assertEqual(
                pred,
                exp,
                msg=f'mismatch at predicted index {index}',
            )

    def test_predict_sequence_matches_node_math_random_that_skip_first_nums(self):
        # total_numbers = 68
        # observations = 20
        # skip = 45

        total_numbers = 64
        observations = 20
        skip = 10
        values, _ = self._generate_node_randoms(total_numbers)

        observed = values[skip:observations+skip]
        expected = values[observations+skip:]

        predicted = predict_sequence(observed, len(expected), browser='chrome')

        self.assertEqual(len(predicted), len(expected))
        for index, (pred, exp) in enumerate(zip(predicted, expected)):
            self.assertEqual(
                pred,
                exp,
                msg=f'mismatch at predicted index {index}',
            )


    def test_predict_sequence_with_rounded_constraint(self):
        total_numbers = 64
        observations = 12
        scale = 10000
        values, modified = self._generate_node_randoms(
            total_numbers,
            expression=f'Math.round(value * {scale})'
        )

        observed = modified[:observations]
        expected = values[observations:]

        predicted = predict_sequence(
            observed,
            len(expected),
            browser='chrome',
            constraint_fn=constraint_rounded(scale),
        )

        self.assertEqual(len(predicted), len(expected))
        for index, (pred, exp) in enumerate(zip(predicted, expected)):
            self.assertEqual(
                pred,
                exp,
                msg=f'mismatch at predicted index {index}',
            )


    def test_predict_sequence_backward_recovers_prior_values(self):
        total_numbers = 65
        observations = 5
        start_index = 59
        values, _ = self._generate_node_randoms(total_numbers)

        observed = values[start_index:start_index + observations]
        expected = list(reversed(values[:start_index]))

        predicted = predict_sequence(
            observed,
            start_index, # 59 elements to go back
            browser='chrome',
            direction='backward',
        )

        self.assertEqual(len(predicted), len(expected))
        for index, (pred, exp) in enumerate(zip(predicted, expected)):
            self.assertEqual(
                pred,
                exp,
                msg=f'mismatch at backward predicted index {index}',
            )


if __name__ == '__main__':
    unittest.main()
