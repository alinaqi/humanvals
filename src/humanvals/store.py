"""SQLite persistence (ADR-0003). All access behind this class so alternative
stores can implement the same surface."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from humanvals.models import Case, Evaluation, Guideline, Metadata, new_id

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
  id TEXT PRIMARY KEY, agent TEXT, namespace TEXT, input TEXT, output TEXT,
  metadata TEXT, guidelines_injected TEXT, created_at REAL, reviewed INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS evaluations (
  id TEXT PRIMARY KEY, case_id TEXT, intent_ok INTEGER, output_ok INTEGER,
  context_ok INTEGER, tool_ok INTEGER DEFAULT 1, expected_tool_call TEXT DEFAULT '',
  notes TEXT, guideline_text TEXT, applies_when TEXT,
  reviewer TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS guidelines (
  id TEXT PRIMARY KEY, agent TEXT, namespace TEXT, intent_text TEXT, intent_vec TEXT,
  text TEXT, applies_when TEXT, origin TEXT, status TEXT, exposures INTEGER DEFAULT 0,
  wins INTEGER DEFAULT 0, validation_count INTEGER DEFAULT 0, superseded_by TEXT,
  source_case_id TEXT, created_at REAL, promoted_at REAL);
CREATE TABLE IF NOT EXISTS exposure_credits (
  case_id TEXT, guideline_id TEXT, PRIMARY KEY (case_id, guideline_id));
"""


SCHEMA_VERSION = 2

# version-gated ALTERs applied to databases created by older releases
_MIGRATIONS: dict[int, list[str]] = {
    2: ["ALTER TABLE evaluations ADD COLUMN tool_ok INTEGER DEFAULT 1",
        "ALTER TABLE evaluations ADD COLUMN expected_tool_call TEXT DEFAULT ''"],
}


class SQLiteStore:
    def __init__(self, db: str) -> None:
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA busy_timeout=5000')
        self._migrate()
        self.conn.executescript(_SCHEMA)
        self.conn.execute(f'PRAGMA user_version={SCHEMA_VERSION}')

    def _migrate(self) -> None:
        version: int = self.conn.execute('PRAGMA user_version').fetchone()[0]
        has_tables = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name='evaluations'").fetchone()
        if version == 0 or not has_tables:
            return  # fresh database: _SCHEMA creates everything current
        for target in sorted(_MIGRATIONS):
            if version < target:
                for stmt in _MIGRATIONS[target]:
                    self.conn.execute(stmt)
        self.conn.commit()

    # -- cases ---------------------------------------------------------------

    def add_case(self, case: Case) -> None:
        self.conn.execute(
            'INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?)',
            (case.id, case.agent, case.namespace, case.input, case.output,
             json.dumps(case.metadata), json.dumps(case.guidelines_injected),
             case.created_at, int(case.reviewed)))
        self.conn.commit()

    def get_case(self, case_id: str) -> Case:
        row = self.conn.execute('SELECT * FROM cases WHERE id=?', (case_id,)).fetchone()
        if row is None:
            raise KeyError(f'no case {case_id}')
        return _case(row)

    def list_cases(self, agent: str | None, unreviewed_only: bool) -> list[Case]:
        sql, args = 'SELECT * FROM cases', []
        clauses = []
        if agent is not None:
            clauses.append('agent=?')
            args.append(agent)
        if unreviewed_only:
            clauses.append('reviewed=0')
        if clauses:
            sql += ' WHERE ' + ' AND '.join(clauses)
        rows = self.conn.execute(sql + ' ORDER BY rowid', args).fetchall()
        return [_case(r) for r in rows]

    def mark_reviewed(self, case_id: str) -> None:
        self.conn.execute('UPDATE cases SET reviewed=1 WHERE id=?', (case_id,))
        self.conn.commit()

    # -- evaluations ---------------------------------------------------------

    def add_evaluation(self, ev: Evaluation) -> str:
        eid = new_id()
        self.conn.execute(
            'INSERT INTO evaluations (id, case_id, intent_ok, output_ok, context_ok,'
            ' tool_ok, expected_tool_call, notes, guideline_text, applies_when,'
            ' reviewer, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (eid, ev.case_id, int(ev.intent_ok), int(ev.output_ok), int(ev.context_ok),
             int(ev.tool_ok), ev.expected_tool_call,
             ev.notes, ev.guideline_text, ev.applies_when, ev.reviewer, time.time()))
        self.conn.commit()
        return eid

    def list_case_evaluations(self, case_id: str) -> list[sqlite3.Row]:
        return list(self.conn.execute(
            'SELECT * FROM evaluations WHERE case_id=? ORDER BY rowid', (case_id,)))

    def list_evaluations(self, agent: str | None = None) -> list[sqlite3.Row]:
        sql = ('SELECT e.* FROM evaluations e JOIN cases c ON c.id = e.case_id')
        args: list[Any] = []
        if agent is not None:
            sql += ' WHERE c.agent=?'
            args.append(agent)
        return list(self.conn.execute(sql + ' ORDER BY e.rowid', args).fetchall())

    # -- guidelines ----------------------------------------------------------

    def add_guideline(self, g: Guideline, intent_vec: list[float]) -> None:
        self.conn.execute(
            'INSERT INTO guidelines VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (g.id, g.agent, g.namespace, g.intent_text, json.dumps(intent_vec), g.text,
             g.applies_when, g.origin, g.status, g.exposures, g.wins, g.validation_count,
             g.superseded_by, g.source_case_id, g.created_at, g.promoted_at))
        self.conn.commit()

    def list_guidelines(self, agent: str | None = None, namespace: str | None = None,
                        status: str | None = None) -> list[Guideline]:
        sql, args = 'SELECT * FROM guidelines', []
        clauses = []
        for col, val in (('agent', agent), ('namespace', namespace), ('status', status)):
            if val is not None:
                clauses.append(f'{col}=?')
                args.append(val)
        if clauses:
            sql += ' WHERE ' + ' AND '.join(clauses)
        rows = self.conn.execute(sql + ' ORDER BY rowid', args).fetchall()
        return [_guideline(r) for r in rows]

    def get_guideline(self, gid: str) -> Guideline:
        row = self.conn.execute('SELECT * FROM guidelines WHERE id=?', (gid,)).fetchone()
        if row is None:
            raise KeyError(f'no guideline {gid}')
        return _guideline(row)

    def intent_vec(self, gid: str) -> list[float]:
        row = self.conn.execute('SELECT intent_vec FROM guidelines WHERE id=?', (gid,)).fetchone()
        vec: list[float] = json.loads(row['intent_vec'])
        return vec

    def set_guideline_status(self, gid: str, status: str, origin: str | None = None,
                             promoted_at: float | None = None,
                             superseded_by: str | None = None,
                             reset_evidence: bool = False) -> None:
        sets: list[str] = ['status=?']
        args: list[Any] = [status]
        for col, val in (('origin', origin), ('promoted_at', promoted_at),
                         ('superseded_by', superseded_by)):
            if val is not None:
                sets.append(f'{col}=?')
                args.append(val)
        if reset_evidence:
            sets.append('exposures=0')
            sets.append('wins=0')
        self.conn.execute(f'UPDATE guidelines SET {", ".join(sets)} WHERE id=?', (*args, gid))
        self.conn.commit()

    def reinforce(self, gid: str) -> None:
        self.conn.execute(
            'UPDATE guidelines SET validation_count = validation_count + 1 WHERE id=?', (gid,))
        self.conn.commit()

    def credit_exposure(self, case_id: str, gid: str, win: bool) -> None:
        """Idempotent per (case, guideline): a re-review never double-counts."""
        cur = self.conn.execute(
            'INSERT OR IGNORE INTO exposure_credits VALUES (?,?)', (case_id, gid))
        if cur.rowcount == 1:
            self.conn.execute(
                'UPDATE guidelines SET exposures = exposures + 1, wins = wins + ? WHERE id=?',
                (int(win), gid))
        self.conn.commit()


def _case(row: sqlite3.Row) -> Case:
    return Case(id=row['id'], agent=row['agent'], namespace=row['namespace'],
                input=row['input'], output=row['output'],
                metadata=_meta(row['metadata']),
                guidelines_injected=json.loads(row['guidelines_injected']),
                created_at=row['created_at'], reviewed=bool(row['reviewed']))


def _meta(raw: str) -> Metadata:
    data: Metadata = json.loads(raw)
    return data


def _guideline(row: sqlite3.Row) -> Guideline:
    return Guideline(id=row['id'], agent=row['agent'], namespace=row['namespace'],
                     intent_text=row['intent_text'], text=row['text'],
                     applies_when=row['applies_when'], origin=row['origin'],
                     status=row['status'], exposures=row['exposures'], wins=row['wins'],
                     validation_count=row['validation_count'],
                     superseded_by=row['superseded_by'],
                     source_case_id=row['source_case_id'], created_at=row['created_at'],
                     promoted_at=row['promoted_at'])
