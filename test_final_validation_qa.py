"""Smoke test for final QA validation runner artifacts."""

from pathlib import Path

from src.modules.operations.qa import FinalValidationRunner, ValidationConfig


def test_final_validation_runner_exports_artifacts() -> None:
    output_dir = "./qa-results-test"
    runner = FinalValidationRunner(
        ValidationConfig(
            pilot_site="school-a",
            dataset_snapshot="snapshot-test",
            reviewer="tester",
            output_dir=output_dir,
        )
    )

    payload = runner.run()

    assert payload["summary"]["total_cases"] >= 1
    assert "results" in payload

    output_path = Path(output_dir)
    json_files = list(output_path.glob("validation_school-a_*.json"))
    csv_files = list(output_path.glob("validation_school-a_*.csv"))

    assert json_files
    assert csv_files
