import sqlparse
from sqlparse.tokens import DDL, Keyword

BLOCKED_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "INSERT",
    "TRUNCATE", "ALTER", "CREATE", "REPLACE"
}

def validate_query(sql: str) -> tuple[bool, str]:
    if not sql or not sql.strip():
        return False, "Empty query"

    parsed = sqlparse.parse(sql.strip())
    if not parsed:
        return False, "Could not parse SQL"

    # Reject stacked/multi-statement input outright. sqlparse.parse() splits on
    # ';' into separate Statement objects — validating only parsed[0] would let
    # a mutating statement smuggle through after a harmless leading SELECT
    # (e.g. "SELECT 1; DROP TABLE daily_sales;"), so every statement is checked.
    non_empty_statements = [s for s in parsed if s.token_first(skip_ws=True, skip_cm=True)]
    if len(non_empty_statements) > 1:
        return False, "Multiple statements are not allowed"

    statement = non_empty_statements[0]
    stmt_type = statement.get_type()

    if stmt_type != "SELECT":
        return False, f"Only SELECT allowed. Got: {stmt_type}"

    for token in statement.flatten():
        if token.ttype in (Keyword, DDL):
            if token.normalized.upper() in BLOCKED_KEYWORDS:
                return False, f"Blocked keyword: {token.normalized}"

    return True, "OK"
