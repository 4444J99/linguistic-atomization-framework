from __future__ import annotations

import argparse
import time

from nexus_babel.main import create_app


def run_worker(*, once: bool = False, max_jobs: int | None = None) -> int:
    app = create_app()
    processed = 0

    while True:
        session = app.state.db.session()
        did_work = False
        try:
            app.state.job_service.complete_stale_leases(session, app.state.settings.worker_name)
            job = app.state.job_service.process_next(session, app.state.settings.worker_name)
            if job:
                did_work = True
                processed += 1
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        if once:
            break
        if max_jobs is not None and processed >= max_jobs:
            break
        if not did_work:
            time.sleep(max(app.state.settings.worker_poll_seconds, 0.1))

    return processed


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexus Babel async worker")
    parser.add_argument("--once", action="store_true", help="Process at most one eligible job and exit")
    parser.add_argument("--max-jobs", type=int, default=None, help="Exit after processing N jobs")
    args = parser.parse_args()
    processed = run_worker(once=args.once, max_jobs=args.max_jobs)
    print(f"processed_jobs={processed}")


if __name__ == "__main__":
    main()
