from batch.config import BatchConfig
from batch.matrix import (
    generate_experiment_matrix,
    validate_matrix,
)

from data.persona_loader import load_batch_personas


def test_small_experiment_matrix():

    config = BatchConfig(
        persona_count=2,
    )
    personas = [
            {"id": f"test-{i:03d}"}
            for i in range(1, 3)
    ]

    matrix = generate_experiment_matrix(config, personas)

    validate_matrix(matrix, config)
    print(len(matrix))
    assert len(matrix) == 48  #--> 2 persona x 4 character x 2 style x 3 replica = 48 pairs

    total_runs = sum(
        len(pair["runs"])
        for pair in matrix
    )

    assert total_runs == 96 #--> for both on and off  48 x 2= 96 runs

    print("Small matrix test passed!")
    print(f"Pairs: {len(matrix)}")
    print(f"Runs: {total_runs}")


def test_full_experiment_matrix():

    config = BatchConfig()
    personas = load_batch_personas(
        persona_count=config.persona_count
    )
    matrix = generate_experiment_matrix(config, personas)

    validate_matrix(matrix, config)
    # print(len(matrix))
    assert len(matrix) == 2400 #--> 100 persona x 4 character x 2 style x 3 replica = 48 pairs

    total_runs = sum(
        len(pair["runs"])
        for pair in matrix
    )

    # print(total_runs)
    assert total_runs == 4800

    print("Full matrix test passed!")
    print(f"Pairs: {len(matrix)}")
    print(f"Runs: {total_runs}")


if __name__ == "__main__":
    test_small_experiment_matrix()
    test_full_experiment_matrix()