import unittest

from research_demo.evaluation import evaluate_labels


class EvaluationTests(unittest.TestCase):
    def test_agreement_and_kappa_example(self):
        human = ["trust", "price", "trust", "habit", "other", "price", "trust", "habit", "price", "trust"]
        model = ["trust", "price", "trust", "habit", "price", "price", "trust", "habit", "price", "other"]
        result = evaluate_labels(human, model)
        self.assertEqual(result["agreement"], 0.8)
        self.assertEqual(result["cohen_kappa"], 0.718)
        self.assertEqual(result["confusion_matrix_human_rows_model_columns"]["other"]["price"], 1)

    def test_rejects_unknown_labels(self):
        with self.assertRaisesRegex(ValueError, "labels must be"):
            evaluate_labels(["trust"], ["unknown"])
