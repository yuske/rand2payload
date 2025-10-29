import json
import subprocess
import unittest

from xs128p import predict_sequence


class ChromeNodePredictionTest(unittest.TestCase):
    def _generate_node_randoms(self, count):
        script = f"""
const count = {count};
const values = [];
for (let i = 0; i < count; i++) values.push(Math.random());
console.log(JSON.stringify(values));
"""
        result = subprocess.run(
            ['node', '-e', script],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_predict_sequence_matches_node_math_random(self):
        total_numbers = 20
        observations = 5
        numbers = self._generate_node_randoms(total_numbers)

        observed = numbers[:observations]
        expected = numbers[observations:]

        predicted = predict_sequence(observed, len(expected), browser='chrome')

        self.assertEqual(len(predicted), len(expected))
        for index, (pred, exp) in enumerate(zip(predicted, expected)):
            self.assertEqual(
                pred,
                exp,
                msg=f'mismatch at predicted index {index}',
            )


if __name__ == '__main__':
    unittest.main()
