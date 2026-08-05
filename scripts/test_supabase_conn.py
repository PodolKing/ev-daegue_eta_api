"""Probe Supabase connection options (no secrets printed)."""
from pathlib import Path

import psycopg2


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


def try_conn(label: str, **kwargs) -> bool:
    try:
        conn = psycopg2.connect(connect_timeout=12, sslmode="require", **kwargs)
        cur = conn.cursor()
        cur.execute("select 1")
        print("OK", label)
        conn.close()
        return True
    except Exception as e:
        msg = " | ".join(str(e).strip().splitlines())[:180]
        print("FAIL", label, msg)
        return False


def main() -> None:
    vals = load_env(Path(__file__).resolve().parents[1] / ".env")
    u = vals["SUPABASE_DB_URL"].strip()
    _, rest = u.split("://", 1)
    userinfo, hostpart = rest.rsplit("@", 1)
    user, password = userinfo.split(":", 1)
    hostpart = hostpart.split("?", 1)[0]
    host_port = hostpart.split("/", 1)[0]
    dbname = hostpart.split("/", 1)[1] if "/" in hostpart else "postgres"
    hostname = host_port.rsplit(":", 1)[0]
    port = int(host_port.rsplit(":", 1)[1]) if ":" in host_port else 5432
    ref = hostname.removeprefix("db.").removesuffix(".supabase.co")

    try_conn("direct_dns", host=hostname, port=port, dbname=dbname, user=user, password=password)

    ipv6 = "2406:da14:1d4f:7402:318a:5172:1d9d:7235"
    try_conn("direct_ipv6", host=ipv6, port=5432, dbname=dbname, user=user, password=password)

    for region in (
        "ap-northeast-2",
        "ap-northeast-1",
        "ap-southeast-1",
        "us-east-1",
    ):
        host = f"aws-0-{region}.pooler.supabase.com"
        for p in (5432, 6543):
            try_conn(
                f"pooler_{region}_{p}",
                host=host,
                port=p,
                dbname=dbname,
                user=f"postgres.{ref}",
                password=password,
            )


if __name__ == "__main__":
    main()
