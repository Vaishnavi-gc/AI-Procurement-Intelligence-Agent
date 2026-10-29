import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors


# =========================================
# ENVIRONMENT
# =========================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set")


# =========================================
# GEMINI CLIENT
# =========================================

client = genai.Client(
    api_key=api_key
)


# =========================================
# MODEL
# =========================================

MODEL = "gemini-3.6-flash"


# =========================================
# DATABASE SCHEMA
# =========================================

SCHEMA = """
DATABASE: procurement_agent_db

TABLE: vendors

Columns:
- id INTEGER PRIMARY KEY
- vendor_name VARCHAR
- contact_person VARCHAR
- email VARCHAR
- phone VARCHAR
- city VARCHAR
- support_quality INTEGER (1-100)
- problem_resolution INTEGER (1-100)
- defect_rate DECIMAL
- ontime_delivery_percentage DECIMAL
- total_orders_completed INTEGER
- negotiation_flexibility INTEGER (1-100)
- preferred_vendor BOOLEAN


TABLE: quotations

Columns:
- id INTEGER PRIMARY KEY
- vendor_id INTEGER REFERENCES vendors(id)
- product_name VARCHAR
- quantity INTEGER
- unit_price NUMERIC
- total_price NUMERIC
- delivery_days INTEGER
- warranty_years INTEGER
- payment_terms VARCHAR
- quotation_valid_until DATE
"""


# =========================================
# GENERATE SQL
# GEMINI CALL #1
# =========================================

def generate_sql(
    question: str,
    conversation_history: list = None
) -> str:

    if conversation_history is None:
        conversation_history = []


    # ---------------------------------------
    # CONVERSATION CONTEXT
    # ---------------------------------------

    history_text = ""

    for turn in conversation_history[-5:]:

        history_text += f"""
Previous user question:
{turn.get("question", "")}

Previous assistant answer:
{turn.get("answer", "")}

Previous database results:
{turn.get("results", "")}

-------------------------
"""


    # ---------------------------------------
    # PROMPT
    # ---------------------------------------

    prompt = f"""
You are a PostgreSQL SQL expert for a
procurement analytics application.

Convert the CURRENT USER QUESTION into
ONE safe PostgreSQL SELECT query.

DATABASE SCHEMA:

{SCHEMA}


CONVERSATION HISTORY:

{history_text}


CURRENT USER QUESTION:

{question}


CONTEXT RULES:

1. Use conversation history to understand
   follow-up questions.

2. Resolve references such as:
   - they
   - them
   - their
   - those vendors
   - that vendor
   - the cheapest one
   - the previous vendor

3. Example:

Previous question:
Which vendors have delivery above 95%?

Current question:
Give me their names.

Interpret "their" as the vendors
from the previous question.


SQL RULES:

1. Return ONLY SQL.
2. SQL must be SELECT.
3. Only use vendors and quotations.
4. Never use INSERT.
5. Never use UPDATE.
6. Never use DELETE.
7. Never use DROP.
8. Never use ALTER.
9. Never use TRUNCATE.
10. Never use GRANT.
11. Never use REVOKE.
12. Never invent columns.
13. Never invent tables.
14. Use JOIN when required.
15. Use valid PostgreSQL syntax.
16. Do not use markdown.
17. Do not explain the SQL.
18. Do not add LIMIT unless useful.
"""


    # ---------------------------------------
    # GEMINI CALL
    # ---------------------------------------

    try:

        print("Gemini #1: Generating SQL...")


        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )


        if not response.text:

            raise RuntimeError(
                "Gemini returned an empty response."
            )


        sql = response.text.strip()


        # ---------------------------------------
        # REMOVE MARKDOWN
        # ---------------------------------------

        if sql.startswith("```"):

            sql = sql.replace(
                "```sql",
                ""
            )

            sql = sql.replace(
                "```",
                ""
            )

            sql = sql.strip()


        print(
            f"Generated SQL: {sql}"
        )


        return sql


    except errors.ServerError as e:

        print(
            f"[GEMINI SQL ERROR] {e}"
        )

        raise RuntimeError(
            "AI service is temporarily unavailable."
        )


    except Exception as e:

        print(
            f"[SQL GENERATION ERROR] "
            f"{type(e).__name__}: {e}"
        )

        raise RuntimeError(
            "Unable to generate a query."
        )


# =========================================
# GENERATE ANSWER
# GEMINI CALL #2
# =========================================

def generate_answer(
    question: str,
    sql: str,
    columns: list,
    rows: list,
    conversation_history: list = None
) -> str:

    if conversation_history is None:
        conversation_history = []


    # ---------------------------------------
    # CONVERSATION CONTEXT
    # ---------------------------------------

    history_text = ""

    for turn in conversation_history[-5:]:

        history_text += f"""
Previous user question:
{turn.get("question", "")}

Previous assistant answer:
{turn.get("answer", "")}

Previous database results:
{turn.get("results", "")}

-------------------------
"""


    # ---------------------------------------
    # PROMPT
    # ---------------------------------------

    prompt = f"""
You are a procurement intelligence assistant.

Your job is to explain the database results
to the user in natural language.

CONVERSATION HISTORY:

{history_text}


CURRENT USER QUESTION:

{question}


GENERATED SQL:

{sql}


DATABASE RESULT COLUMNS:

{columns}


DATABASE RESULT ROWS:

{rows}


RULES:

1. Answer the user's current question directly.

2. Use ONLY information contained in the
   database results and conversation context.

3. Never invent facts, values, vendors, or metrics.

4. Understand the user's intent from natural language.

5. For filtering questions:
   return and explain records that match
   the user's requested conditions.

6. For aggregation questions:
   clearly report the requested count,
   average, total, minimum, maximum, or
   other aggregate value.

7. For comparison questions:
   compare only the relevant records and
   metrics requested by the user.

8. For ranking or recommendation questions:
   identify the strongest candidate using
   the available procurement metrics.

9. Use these business semantics when evaluating
   vendor performance:

   - support_quality:
     higher is better

   - problem_resolution:
     higher is better

   - defect_rate:
     lower is better

   - ontime_delivery_percentage:
     higher is better

   - negotiation_flexibility:
     higher is better

   - preferred_vendor:
     positive signal

10. When multiple metrics are relevant,
    consider them together rather than relying
    on a single metric.

11. When the user asks for a specific field,
    provide that field without unnecessary
    information.

12. Do not expose sensitive or unnecessary
    vendor contact information unless the user
    explicitly asks for it.

13. For follow-up questions, use conversation
    context to resolve references such as:
    "they", "their", "those vendors",
    "the previous one", "the cheapest one",
    or "the best one".

14. Keep responses concise but provide enough
    reasoning to explain the result.

15. Use simple Markdown:
    - **bold** for important values
    - bullet points when useful

16. If the available data is insufficient to
    answer the question, clearly say so rather
    than guessing.

17. Do not mention:
    - SQL
    - PostgreSQL
    - Gemini
    - prompts
    - APIs
    - internal implementation
    - system instructions
    - internal errors
"""


    # ---------------------------------------
    # GEMINI CALL #2
    # ---------------------------------------

    try:

        print(
            "Gemini #2: Generating explanation..."
        )


        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )


        if not response.text:

            raise RuntimeError(
                "Gemini returned an empty answer."
            )


        answer = response.text.strip()


        print(
            f"Generated answer: {answer}"
        )


        return answer


    except errors.ServerError as e:

        print(
            f"[GEMINI ANSWER ERROR] {e}"
        )

        # Don't expose provider error

        return create_fallback_answer(
            columns,
            rows
        )


    except Exception as e:

        print(
            f"[ANSWER GENERATION ERROR] "
            f"{type(e).__name__}: {e}"
        )

        return create_fallback_answer(
            columns,
            rows
        )


# =========================================
# FALLBACK ANSWER
# =========================================

def create_fallback_answer(
    columns,
    rows
):

    if not rows:

        return (
            "I couldn't find any matching "
            "records."
        )


    # Single value such as COUNT(*)

    if (
        len(rows) == 1
        and len(columns) == 1
    ):

        value = rows[0][columns[0]]

        return f"The result is {value}."


    # Multiple records

    return (
        f"I found {len(rows)} matching "
        "records."
    )