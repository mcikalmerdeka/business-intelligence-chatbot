"""
Single-table database chat application (Basic - without RAG)
"""

import os
import sys
import streamlit as st

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    DATABASE_URL,
    MODEL_OPTIONS, SHOW_DEBUG_INFO, setup_logger
)
from config.prompts import SQL_GENERATION_SYSTEM_PROMPT_SINGLE_TABLE, RESPONSE_GENERATION_SYSTEM_PROMPT
from core import DatabaseConnection, execute_sql_query, LLMClient

# Setup application logger - this initializes handlers
logger = setup_logger("bi_chatbot")

# Configure Streamlit
st.set_page_config(page_title="Chat with your database through LLMs")
st.header("Chat with your database through LLMs")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# App info
st.expander("ℹ️ About Single-Table Database Chat").markdown(
    """
    - This app allows you to ask questions about your sales database in natural language.
    - The AI assistant will convert your question into SQL, query the database, and provide a friendly response.
    - Choose an AI model from the sidebar and connect to your database to get started!
    - The chat has memory, so you can ask follow-up questions.
    """
)

st.expander("💡 Example Questions").markdown(
    """
    Copy any question below and paste it into the chat box to get started!

    **Sales & Revenue**
    - What were the total sales in 2003 and 2004?
    - Which product line has the highest average order value?
    - What is the total revenue by country?
    - What are the top 5 products by total sales amount?

    **Customers**
    - Show me the top 5 customers by revenue
    - What is the phone number of customer Toys of Finland, Co.?
    - Which countries have the most customers?

    **Orders & Products**
    - How many orders were placed in each quarter of 2004?
    - What is the distribution of deal sizes (Small, Medium, Large)?
    - Which product line had the most orders shipped in 2003?
    - What is the average order quantity per product line?

    **Follow-up Examples** *(ask these after an initial question)*
    - What about for 2005?
    - Which of them had the highest growth?
    - Break that down by product line.
    - Show me the same for the top 3 countries.
    """
)

# Sidebar
with st.sidebar:
    # Model settings
    st.subheader("Model Settings")
    model_choice = st.selectbox(
        "Select a model",
        list(MODEL_OPTIONS.keys()),
        key="model_choice"
    )
    
    # Database settings
    st.subheader("Database Settings")
    if st.button("Test Connection"):
        with st.spinner("Testing database connection..."):
            db_conn = DatabaseConnection(dsn=DATABASE_URL)
            db_conn.test_connection()
    
    # Chat controls
    st.subheader("Chat Controls")
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.success("Chat history cleared!")

# Display chat history
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

# User input
question = st.chat_input("Ask a question about your sales data")

if question:
    logger.info(f"User question received: {question}")
    # Display user message
    st.chat_message("user").write(question)
    st.session_state.chat_history.append({"role": "user", "content": question})
    
    with st.spinner("Processing your query..."):
        logger.info("Starting query processing pipeline")
        # Initialize LLM client and database connection
        llm_client = LLMClient(st.session_state.model_choice)
        db_conn = DatabaseConnection(dsn=DATABASE_URL)
        
        # Get conversation history
        model_history = st.session_state.chat_history[:-1] if len(st.session_state.chat_history) > 1 else None
        
        # Generate SQL
        sql_query = llm_client.generate_response(
            question=question,
            system_prompt=SQL_GENERATION_SYSTEM_PROMPT_SINGLE_TABLE,
            history=model_history
        )
        
        if sql_query:
            if SHOW_DEBUG_INFO:
                st.subheader("Generated SQL Query:")
                st.code(sql_query, language="sql")
            
            # Execute query
            result = execute_sql_query(db_conn, sql_query)
            
            if result:
                if SHOW_DEBUG_INFO:
                    st.subheader("Query Results:")
                    for row in result:
                        st.write(row)
                
                # Generate human-friendly response
                humane_response = llm_client.generate_response(
                    question=question,
                    system_prompt=RESPONSE_GENERATION_SYSTEM_PROMPT.format(
                        question=question,
                        result=result
                    ),
                    history=model_history
                )
                
                st.chat_message("assistant").write(humane_response)
                st.session_state.chat_history.append({"role": "assistant", "content": humane_response})
            else:
                error_message = "No results returned from the query."
                st.error(error_message)
                st.session_state.chat_history.append({"role": "assistant", "content": error_message})
        else:
            error_message = "Failed to generate SQL query."
            logger.error("SQL generation failed")
            st.error(error_message)
            st.session_state.chat_history.append({"role": "assistant", "content": error_message})

# Footer
st.markdown(
    """
    <style>
    .footer {position: fixed;left: 0;bottom: 0;width: 100%;background-color: #000;color: white;text-align: center;}
    </style>
    <div class='footer'>
        <p>mcikalmerdeka@gmail.com</p>
    </div>
    """,
    unsafe_allow_html=True,
)
