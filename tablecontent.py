import sqlite3
import streamlit as st
import pandas as pd

# Connect to SQLite database
conn = sqlite3.connect('question_QA_response.db')

# Read the contents of the 'questions' table into a Pandas DataFrame
query = "SELECT * FROM questions"
df = pd.read_sql(query, conn)

# Close the connection
conn.close()

# Display the DataFrame using Streamlit
st.write("Contents of the 'questions' table:")
st.dataframe(df)
