"""Migrate local MariaDB -> Supabase Postgres (host-side, no Docker pgloader).

Uses Session pooler (IPv4). Does not print secrets.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pymysql
import psycopg2
from psycopg2.extras import execute_batch

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
BATCH = 500


def load_env(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        vals[k.strip()] = v
    return vals


def map_type(data_type: str, column_type: str, datetime_precision) -> str:
    dt = data_type.lower()
    ct = column_type.lower()
    if dt in ("tinyint",) and ct.startswith("tinyint(1)"):
        return "boolean"
    if dt in ("tinyint", "smallint"):
        return "smallint"
    if dt in ("mediumint", "int", "integer"):
        return "integer"
    if dt == "bigint":
        return "bigint"
    if dt in ("float",):
        return "real"
    if dt in ("double", "double precision"):
        return "double precision"
    if dt in ("decimal", "numeric"):
        return ct.replace("decimal", "numeric")
    if dt in ("char", "varchar"):
        return ct
    if dt in ("text", "mediumtext", "longtext", "tinytext"):
        return "text"
    if dt in ("json",):
        return "jsonb"
    if dt in ("date",):
        return "date"
    if dt in ("datetime", "timestamp"):
        return "timestamptz"
    if dt in ("time",):
        return "time"
    if dt in ("blob", "mediumblob", "longblob", "tinyblob", "binary", "varbinary"):
        return "bytea"
    if dt in ("enum", "set"):
        return "text"
    return "text"


def pg_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def main() -> int:
    vals = load_env(ENV_PATH)
    mysql_conn = pymysql.connect(
        host=vals.get("DB_HOST", "127.0.0.1"),
        port=int(vals.get("DB_PORT", "3306")),
        user=vals["DB_USER"],
        password=vals.get("DB_PASSWORD", ""),
        database=vals["DB_NAME"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    u = vals["SUPABASE_DB_URL"].strip()
    _, rest = u.split("://", 1)
    userinfo, hostpart = rest.rsplit("@", 1)
    _user, password = userinfo.split(":", 1)
    hostpart = hostpart.split("?", 1)[0]
    hostname = hostpart.split("/", 1)[0].rsplit(":", 1)[0]
    dbname = hostpart.split("/", 1)[1] if "/" in hostpart else "postgres"
    ref = hostname.removeprefix("db.").removesuffix(".supabase.co")

    # Project lives in ap-northeast-1 (Tokyo); direct db.* is IPv6-only from this network
    pg_conn = psycopg2.connect(
        host="aws-0-ap-northeast-1.pooler.supabase.com",
        port=5432,
        dbname=dbname,
        user=f"postgres.{ref}",
        password=password,
        sslmode="require",
        connect_timeout=20,
    )
    pg_conn.autocommit = False

    print(f"source: MariaDB {vals['DB_NAME']}")
    print(f"target: pooler ap-northeast-1 / postgres.{ref}")

    with mysql_conn.cursor() as mc, pg_conn.cursor() as pc:
        mc.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        key = f"Tables_in_{vals['DB_NAME']}"
        tables = [row[key] for row in mc.fetchall()]
        print(f"tables: {len(tables)}")

        for table in tables:
            print(f"→ {table}")
            mc.execute(
                """
                SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE,
                       COLUMN_DEFAULT, COLUMN_KEY, EXTRA, DATETIME_PRECISION
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s
                ORDER BY ORDINAL_POSITION
                """,
                (vals["DB_NAME"], table),
            )
            cols = mc.fetchall()
            if not cols:
                print("  skip (no columns)")
                continue

            col_defs = []
            pk_cols = []
            for c in cols:
                name = c["COLUMN_NAME"]
                pg_type = map_type(
                    c["DATA_TYPE"], c["COLUMN_TYPE"], c.get("DATETIME_PRECISION")
                )
                null_sql = "NULL" if c["IS_NULLABLE"] == "YES" else "NOT NULL"
                # skip MySQL defaults that don't translate cleanly
                col_defs.append(f"{pg_ident(name)} {pg_type} {null_sql}")
                if c["COLUMN_KEY"] == "PRI":
                    pk_cols.append(name)

            pc.execute(f"DROP TABLE IF EXISTS {pg_ident(table)} CASCADE")
            ddl = f"CREATE TABLE {pg_ident(table)} (\n  " + ",\n  ".join(col_defs)
            if pk_cols:
                ddl += ",\n  PRIMARY KEY (" + ", ".join(pg_ident(p) for p in pk_cols) + ")"
            ddl += "\n)"
            pc.execute(ddl)

            col_names = [c["COLUMN_NAME"] for c in cols]
            mc.execute(f"SELECT * FROM `{table}`")
            rows = mc.fetchall()
            if not rows:
                print("  0 rows")
                pg_conn.commit()
                continue

            placeholders = ",".join(["%s"] * len(col_names))
            insert_sql = (
                f"INSERT INTO {pg_ident(table)} ("
                + ",".join(pg_ident(n) for n in col_names)
                + f") VALUES ({placeholders})"
            )
            values = []
            for row in rows:
                tup = []
                for n, c in zip(col_names, cols):
                    val = row[n]
                    # tinyint(1) → bool
                    if (
                        c["DATA_TYPE"].lower() == "tinyint"
                        and c["COLUMN_TYPE"].lower().startswith("tinyint(1)")
                        and val is not None
                    ):
                        val = bool(val)
                    tup.append(val)
                values.append(tuple(tup))

            execute_batch(pc, insert_sql, values, page_size=BATCH)
            pg_conn.commit()
            print(f"  {len(values)} rows")

    mysql_conn.close()
    pg_conn.close()
    print("DONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print("ERROR", type(e).__name__ + ":", str(e).split("\n")[0][:200], file=sys.stderr)
        raise
