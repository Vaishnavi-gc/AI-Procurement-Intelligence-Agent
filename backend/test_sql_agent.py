from sql_agent import generate_sql


question = "Which vendors have on-time delivery above 95%?"

sql = generate_sql(question)

print("\nGenerated SQL:\n")
print(sql)