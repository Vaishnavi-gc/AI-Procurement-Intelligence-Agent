import sqlglot
from sqlglot import exp


ALLOWED_TABLES = {
    "vendors",
    "quotations"
}


def validate_sql(sql: str):

    # Remove unnecessary whitespace
    sql = sql.strip()

    if not sql:
        return False, "SQL query cannot be empty."

    try:
        # Parse SQL
        parsed = sqlglot.parse_one(sql, dialect="postgres")
    except Exception as e:
        return False, f"Invalid SQL syntax: {str(e)}"

    # ------------------------------------------------
    # 1. SELECT ONLY
    # ------------------------------------------------

    if not isinstance(parsed, exp.Select):
        return False, "Only SELECT queries are allowed."

    # ------------------------------------------------
    # 2. CHECK TABLES
    # ------------------------------------------------

    tables = parsed.find_all(exp.Table)

    for table in tables:

        table_name = table.name.lower()

        if table_name not in ALLOWED_TABLES:
            return False, (
                f"Access to table '{table_name}' is not allowed."
            )

    # ------------------------------------------------
    # 3. BLOCK DANGEROUS KEYWORDS
    # ------------------------------------------------

    dangerous_keywords = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE",
        "GRANT",
        "REVOKE"
    ]

    sql_upper = sql.upper()

    for keyword in dangerous_keywords:

        if keyword in sql_upper:

            return False, (
                f"Dangerous SQL operation detected: {keyword}"
            )

    # ------------------------------------------------
    # 4. LIMIT RESULTS
    # ------------------------------------------------

    if not parsed.args.get("limit"):

        sql = sql.rstrip(";")

        sql = f"{sql} LIMIT 100"

    return True, sql