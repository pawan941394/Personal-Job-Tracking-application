import google.generativeai as genai
import streamlit as st
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent
llm = ChatGoogleGenerativeAI(model="gemini-1.0-pro", google_api_key=st.secrets["firebase"]["gen_api_key"], temperature=0.2)

def gen_ai(df, prompt):
    retries = 3
    for attempt in range(retries):
        try:
            agent_executor = create_pandas_dataframe_agent(
                llm,
                df,
                agent_type="zero-shot-react-description",
                verbose=True,
                return_intermediate_steps=True,
                allow_dangerous_code=True
            )
            formatted_prompt = prompt + '''
            Please format the output as follows:
            For each row in the DataFrame, output the values in this format:

            &
                company: value
                date: value
                phone: value
                comments: value
                followup: value
                email: value
                name: value

            &
                company: value
                date: value
                phone: value
                comments: value
                followup: value
                email: value
                name: value

            And so on for each row.
            '''
            ans = agent_executor.invoke(formatted_prompt)
            return ans
        except genai.ResourceExhaustedError as e:
            st.error(f'Quota exceeded: {e}. Retrying in 60 seconds...')
            time.sleep(60)  # Wait before retrying
        except Exception as e:
            st.error(f'An error occurred: {e}')
            break
