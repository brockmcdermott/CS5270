# consumer.py
import argparse
import logging
import sys
from typing import Optional

from poller_s3 import S3RequestPoller
from storage_s3 import S3WidgetStore
from storage_dynamodb import DynamoWidgetStore
from router import handle_request


def setup_logging(log_path: str) -> logging.Logger:
    """Configure root logger to write to both file and stdout.

    Important for tests: we always (re)create the FileHandler for the requested
    log_path, removing any prior FileHandlers that may point elsewhere.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove any existing FileHandlers so we can guarantee the target path
    for h in list(logger.handlers):
        if isinstance(h, logging.FileHandler):
            try:
                h.flush()
                h.close()
            except Exception:
                pass
            logger.removeHandler(h)

    # Fresh file handler for the requested path
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(fh)

    # Ensure there is exactly one console handler
    has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    if not has_stream:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(sh)

    return logging.getLogger("consumer")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="CS5270 HW6 Consumer")
    p.add_argument("--bucket2", required=True, help="S3 bucket name for incoming Widget Requests (Bucket 2).")
    p.add_argument("--target", choices=("s3", "dynamodb"), required=True, help="Storage backend for widgets.")
    p.add_argument("--bucket3", help="S3 bucket name for widgets (Bucket 3) if --target=s3.")
    p.add_argument("--table", help="DynamoDB table name if --target=dynamodb.")
    p.add_argument("--sleep-ms", type=int, default=100, help="Poll sleep when no requests are found (default: 100).")
    p.add_argument("--stop-after", type=int, default=0, help="Stop after N processed requests (0 = run forever).")
    p.add_argument("--log-file", default="consumer.log", help="Path to the log file (default: consumer.log).")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    log = setup_logging(args.log_file)

    # Validate resource combo
    if args.target == "s3" and not args.bucket3:
        log.error("--bucket3 is required when --target=s3")
        _flush_logs()
        return 2
    if args.target == "dynamodb" and not args.table:
        log.error("--table is required when --target=dynamodb")
        _flush_logs()
        return 2

    # Build poller + store
    poller = S3RequestPoller(bucket2_name=args.bucket2, sleep_ms=args.sleep_ms)
    if args.target == "s3":
        store = S3WidgetStore(bucket3_name=args.bucket3)
    else:
        store = DynamoWidgetStore(table_name=args.table)

    processed = 0
    log.info(
        f"Consumer starting: bucket2={args.bucket2}, target={args.target}, "
        f"bucket3={args.bucket3 or '-'}, table={args.table or '-'}, sleep_ms={args.sleep_ms}"
    )

    try:
        while True:
            req = poller.get_next_request()
            if req is None:
                # poller already slept; just continue
                continue

            handle_request(req, store, log)
            processed += 1

            if args.stop_after and processed >= args.stop_after:
                log.info(f"Stop-after reached ({processed}). Exiting.")
                break

    except KeyboardInterrupt:
        log.info("Interrupted by user. Shutting down gracefully.")
    except Exception as e:
        log.exception(f"Fatal error in consumer loop: {e}")
        _flush_logs()
        return 1

    log.info(f"Consumer stopped. Total processed: {processed}")
    _flush_logs()
    return 0


def _flush_logs():
    """Ensure file handlers are flushed/closed (important for tests)."""
    root = logging.getLogger()
    # Flush all handlers
    for h in list(root.handlers):
        try:
            if hasattr(h, "flush"):
                h.flush()
        except Exception:
            pass
    # Close and remove to avoid duplicates on subsequent runs
    for h in list(root.handlers):
        try:
            h.close()
        except Exception:
            pass
        root.removeHandler(h)


if __name__ == "__main__":
    raise SystemExit(main())
