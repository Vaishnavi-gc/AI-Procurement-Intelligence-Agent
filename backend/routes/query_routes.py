import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from guardrails import validate_sql
from sql_agent import generate_sql, generate_answer


router = APIRouter(
    prefix="/api",
    tags=["SQL Agent"]
)


# =========================================
# DESTRUCTIVE INTENT CHECK
# =========================================

def is_destructive_intent(question: str) -> bool:

    text_question = question.lower().strip()

    destructive_patterns = [
        "delete all",
        "delete everything",
        "remove all",
        "remove everything",
        "erase all",
        "erase everything",
        "wipe all",
        "wipe everything",
        "destroy all",
        "drop table",
        "drop database",
        "truncate",
        "delete vendors",
        "remove vendors",
        "delete all vendors",
        "remove all vendors",
        "update all vendors",
        "modify all vendors",
        "change all vendors"
    ]

    for pattern in destructive_patterns:

        if pattern in text_question:
            return True

    return False


# =========================================
# API
# =========================================

@router.post("/query")
def execute_query(
    question: str,
    history: str = "[]",
    db: Session = Depends(get_db)
):

    # =========================================
    # 1. VALIDATE QUESTION
    # =========================================

    if not question.strip():

        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )


    # =========================================
    # 2. DESTRUCTIVE INTENT CHECK
    # =========================================

    if is_destructive_intent(question):

        print(
            f"[BLOCKED INTENT] {question}"
        )

        return {
            "success": False,
            "blocked": True,
            "error_type": "destructive_intent",
            "message": (
                "I can't perform delete, update, "
                "or other destructive operations. "
                "I can only provide read-only "
                "procurement analysis."
            )
        }


    # =========================================
    # 3. PARSE CONVERSATION HISTORY
    # =========================================

    try:

        conversation_history = json.loads(history)

        if not isinstance(
            conversation_history,
            list
        ):
            conversation_history = []

    except Exception as e:

        print(
            f"[HISTORY ERROR] {e}"
        )

        conversation_history = []


    # =========================================
    # 4. GEMINI #1 — SQL GENERATION
    # =========================================

    try:

        generated_sql = generate_sql(
            question,
            conversation_history
        )

    except Exception as e:

        print(
            f"[SQL GENERATION ERROR] "
            f"{type(e).__name__}: {e}"
        )

        return {
            "success": False,
            "blocked": False,
            "error_type": "ai_unavailable",
            "message": (
                "I'm temporarily unable to "
                "process your request. "
                "Please try again later."
            )
        }


    # =========================================
    # 5. SQL GUARDRAILS
    # =========================================

    try:

        is_valid, result = validate_sql(
            generated_sql
        )

    except Exception as e:

        print(
            f"[GUARDRAIL ERROR] "
            f"{type(e).__name__}: {e}"
        )

        return {
            "success": False,
            "blocked": True,
            "error_type": "validation_error",
            "message": (
                "I couldn't safely process "
                "that request."
            )
        }


    # =========================================
    # 6. BLOCK UNSAFE SQL
    # =========================================

    if not is_valid:

        print(
            f"[BLOCKED SQL] {result}"
        )

        return {
            "success": False,
            "blocked": True,
            "error_type": "unsafe_query",
            "message": (
                "I can only perform safe, "
                "read-only procurement searches."
            )
        }


    safe_sql = result


    # =========================================
    # 7. EXECUTE SQL
    # =========================================

    try:

        print(
            "Executing SQL..."
        )

        query_result = db.execute(
            text(safe_sql)
        )


        columns = list(
            query_result.keys()
        )


        rows = [
            dict(row._mapping)
            for row in query_result.fetchall()
        ]


        print(
            f"Database returned {len(rows)} rows."
        )


    except Exception as e:

        print(
            f"[DATABASE ERROR] "
            f"{type(e).__name__}: {e}"
        )

        return {
            "success": False,
            "blocked": False,
            "error_type": "database_error",
            "message": (
                "I couldn't retrieve the "
                "requested information."
            )
        }


    # =========================================
    # 8. GEMINI #2 — EXPLANATION
    # =========================================

    try:

        print(
            "Gemini #2: Generating explanation..."
        )

        answer = generate_answer(
            question,
            safe_sql,
            columns,
            rows,
            conversation_history
        )

        print(
            f"Gemini #2 answer: {answer}"
        )


    except Exception as e:

        print(
            f"[ANSWER GENERATION ERROR] "
            f"{type(e).__name__}: {e}"
        )

        answer = (
            "I found the requested information, "
            "but I couldn't generate the explanation "
            "right now."
        )


    # =========================================
    # 9. RETURN RESPONSE
    # =========================================

    return {
        "success": True,
        "blocked": False,
        "answer": answer,
        "columns": columns,
        "rows": rows
    }