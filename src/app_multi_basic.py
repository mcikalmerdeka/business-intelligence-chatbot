"""
Multi-table database chat application (Basic - without RAG)
"""

import os
import sys
import streamlit as st

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    DATABASE_URL,
    MODEL_OPTIONS, SHOW_DEBUG_INFO, DATASET_CONFIGS, setup_logger
)
from config.prompts import SQL_GENERATION_SYSTEM_PROMPT, RESPONSE_GENERATION_SYSTEM_PROMPT
from core import DatabaseConnection, execute_sql_query, LLMClient, load_schema_description

# Setup application logger - this initializes handlers
logger = setup_logger("bi_chatbot")

# Configure Streamlit
st.set_page_config(page_title="Chat with your database through LLMs")
st.header("Chat with your database through LLMs")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# App info
st.expander("ℹ️ About Multi-Table Database Chat").markdown(
    """
    - This app allows you to ask questions about a complex database with multiple related tables.
    - The AI assistant will convert your question into SQL, query the database, and provide a detailed analysis.
    - The system loads the full database schema to understand table relationships.
    - Choose an AI model and dataset from the sidebar to get started!
    - The chat has memory, so you can ask follow-up questions.
    """
)

_selected = st.session_state.get("dataset_choice", list(DATASET_CONFIGS.keys())[0])
if _selected == "Olist E-Commerce":
    st.expander("💡 Example Questions — Olist E-Commerce").markdown(
        """
        Copy any question below and paste it into the chat box to get started!

        **Orders & Customers**
        - What is the average monthly active user count for each year?
        - Show me the number of customers who made more than one purchase for each year
        - How many orders were delivered late compared to the estimated delivery date?
        - What is the average number of days between order purchase and delivery?

        **Revenue & Payments**
        - What are the top product categories by total revenue?
        - Show detailed information on the amount of usage for each payment type per year
        - What is the average order value by payment type?
        - Which states generate the most revenue?

        **Sellers & Products**
        - Which sellers have the highest number of orders?
        - What are the top 10 product categories by number of orders?
        - What is the average review score per product category?
        - Which states have the most active sellers?

        **Follow-up Examples** *(ask these after an initial question)*
        - Which one showed the most significant increase?
        - Break down those results by customer location.
        - Show me the same trend for the top 5 categories.
        - What was the year-over-year growth rate?
        """
    )
else:
    st.expander("💡 Example Questions — WRS EHR Healthcare").markdown(
        """
        Copy any question below and paste it into the chat box to get started!

        **Patients & Diagnoses**
        - How many patients were diagnosed with diabetes in 2024?
        - What are the most common diagnoses across all facilities?
        - How many active patients are registered per state?
        - What is the average age of patients by primary diagnosis?

        **Appointments & Providers**
        - Which providers have the highest patient appointment counts?
        - What is the average appointment duration by facility type?
        - How many appointments were cancelled or no-show in the last year?
        - Which specialties have the longest average appointment duration?

        **Prescriptions & Lab Results**
        - Show me the top 10 most prescribed medications
        - What percentage of lab results came back abnormal?
        - Which diagnosis types have the most associated prescriptions?
        - What is the average number of prescriptions per appointment?

        **Insurance**
        - What insurance plans are most frequently used by patients?
        - Which insurance plan type (HMO, PPO, etc.) has the highest average copay?

        **Follow-up Examples** *(ask these after an initial question)*
        - Which of them had the highest count?
        - Break that down by facility type.
        - Show me the same for active patients only.
        - What was the trend over the past 12 months?
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

    # Dataset selector
    st.subheader("Dataset")
    dataset_choice = st.selectbox(
        "Select a dataset",
        list(DATASET_CONFIGS.keys()),
        key="dataset_choice"
    )

    # When dataset changes: wipe chat and force a full rerun so the
    # correct schema is loaded before anything renders
    if st.session_state.get("active_dataset") != dataset_choice:
        st.session_state.chat_history = []
        st.session_state.active_dataset = dataset_choice
        logger.info(f"Dataset changed to {dataset_choice}, triggering rerun")
        st.rerun()

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
question = st.chat_input("Ask a question about your database")

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
        
        # Load schema for selected dataset and generate SQL
        cfg = DATASET_CONFIGS[st.session_state.dataset_choice]
        schema = load_schema_description(cfg["schema_path"])
        sql_query = llm_client.generate_response(
            question=question,
            system_prompt=SQL_GENERATION_SYSTEM_PROMPT.format(
                database_schema_description=schema,
                schema_prefix=cfg["schema_prefix"],
            ),
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
