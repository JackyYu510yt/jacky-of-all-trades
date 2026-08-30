# note.py tests

Every test here exists because an independent reviewer found a real defect.
They are not illustrative — each one FAILED before its fix landed.

    test_note_reviewers.py        14 checks — FnReview r1/r2, Refuter r1, RED-TEAM
    test_note_refuter2.py          8 checks — Refuter r2 (BLOCKER 1, BLOCKER 2, C2, C3)
    test_note_concurrency.py       the gate: 6 procs x 150 findings, twice.
                                   Asserts BOTH the record and the global index
                                   reach 900 — the index assert was added after a
                                   reviewer noticed the gate proved only half of it.
    test_note_reconcile_race.py    6 concurrent `--recent` reconciles must not
                                   double-append.

RUN ALL FOUR AFTER ANY EDIT TO note.py. The concurrency gate especially: a
lock change invalidates every earlier pass, and two separate bugs in this
file's history were invisible until the gate ran on the shipped binary.

Baseline on 2026-08-30: 14/14, 8/8, 900/900 twice (record AND index), clean.
