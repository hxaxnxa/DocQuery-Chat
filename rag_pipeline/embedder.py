from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
     
def initialize_embeddings():
         try:
             embeddings = GoogleGenerativeAIEmbeddings(
                 model="models/text-embedding-004",
                 google_api_key=os.getenv("GOOGLE_API_KEY")
             )
             return embeddings
         except Exception as e:
             print(f"Error initializing Gemini embeddings: {e}")
             raise
     
def initialize_llm():
         try:
             llm = ChatGoogleGenerativeAI(
                 model="gemini-1.5-flash",  # Updated to a valid model
                 temperature=0,
                 google_api_key=os.getenv("GOOGLE_API_KEY")
             )
             return llm
         except Exception as e:
             print(f"Error initializing Gemini LLM: {e}")
             raise