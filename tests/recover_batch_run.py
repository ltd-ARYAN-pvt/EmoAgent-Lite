import argparse

from batch.runner import recover_stale_runs


def main():
    parser = argparse.ArgumentParser(
        description="Inspect or recover stale EmoAgent batch runs."
    )

    parser.add_argument(
        "--config-id",
        required=True,
        help="Experiment configuration ID.",
    )

    parser.add_argument(
        "--stale-minutes",
        type=int,
        default=60,
        help="Minimum run age before recovery. Default: 60.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually mark stale runs as failed.",
    )

    args = parser.parse_args()

    if args.apply:
        print("RECOVERY MODE: database records may be modified.")
        print("Make sure no other runner is executing this experiment.")
    else:
        print("DRY-RUN MODE: database will not be modified.")

    recover_stale_runs(
        config_id=args.config_id,
        stale_after_minutes=args.stale_minutes,
        dry_run=not args.apply,
    )


if __name__ == "__main__":
    main()