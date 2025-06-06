import uuid
import os
import logging
from langsmith import Client
from agno.agent import Agent
from agno.models.google import Gemini

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QueryRewritingAgent:
    def __init__(self):
        """Initialize the Query Rewriting Agent with an Agno Agent using Gemini 1.5 Flash."""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            logger.error("GOOGLE_API_KEY environment variable is not set.")
            raise ValueError("GOOGLE_API_KEY environment variable is not set.")
        
        self.agno_agent = Agent(
            model=Gemini(id="gemini-1.5-flash"),
            instructions=[
                "You are an expert query rewriter. Your task is to rewrite the user query to make it more precise, clear, and optimized for retrieving relevant information from a document database.",
                "Always produce a rewritten query that differs from the input while preserving its core intent. Output only the rewritten query, with no additional text, explanations, or markdown formatting.",
                "For example, if the user query is 'What’s new in HTML5?', rewrite it as 'HTML5 new features and specifications'.",
                "For example, if the user query is 'what is the basics of engineering economics?', rewrite it as 'Fundamental principles of engineering economics'.",
                "For example, if the user query is 'How do you make a form?', rewrite it as 'Steps to create an HTML form'.",
                "For example, if the user query is 'Tell me about machine learning', rewrite it as 'Overview of machine learning concepts and techniques'.",
                "For example, if the user query is 'What is blockchain?', rewrite it as 'Fundamentals and applications of blockchain technology'.",
                "For example, if the user query is 'How to code a website?', rewrite it as 'Steps to develop a website using HTML and CSS'.",
                "For example, if the user query is 'What is the latest version of Python?', rewrite it as 'Current version of Python'."
            ],
            markdown=False,
        )
        logger.info("Initialized Agno Agent with Gemini 1.5 Flash model.")
        
        # Initialize LangSmith client only if API key is set
        self.langsmith_client = Client() if os.getenv("LANGCHAIN_API_KEY") else None
        if not self.langsmith_client:
            logger.warning("LANGCHAIN_API_KEY not set. LangSmith feedback logging will be disabled.")

    def rewrite_query(self, query, run_id=None):
        """Rewrite the user query using the Agno Agent and log to LangSmith."""
        try:
            logger.info(f"Rewriting query: {query}")
            # Use agent.run() to get the rewritten query
            logger.debug("Using agent.run() to rewrite query...")
            response = self.agno_agent.run(query)

            # Extract the rewritten query from the response
            if hasattr(response, 'content') and response.content:
                rewritten_query = response.content.strip()
                logger.debug(f"Response content: '{rewritten_query}'")
            elif isinstance(response, str) and response.strip():
                rewritten_query = response.strip()
                logger.debug(f"String response: '{rewritten_query}'")
            elif hasattr(response, 'messages') and response.messages:
                last_message = response.messages[-1]
                if hasattr(last_message, 'content') and last_message.content:
                    rewritten_query = last_message.content.strip()
                    logger.debug(f"Message content: '{rewritten_query}'")
                else:
                    raise ValueError("No valid content in response messages")
            else:
                raise ValueError(f"Unexpected response type: {type(response)}")

            # Finalize and return the response
            return self._finalize_response(rewritten_query, query, run_id)

        except Exception as e:
            logger.error(f"Error rewriting query with Agno: {e}")
            logger.error(f"Response details: {dir(response) if 'response' in locals() else 'No response'}")
            return query  # Fallback to original query if rewriting fails

    def _finalize_response(self, rewritten_query, original_query, run_id):
        if not rewritten_query or rewritten_query.lower() == original_query.lower():
            logger.warning(f"Rewritten query is empty or unchanged: '{rewritten_query}'")
            return original_query
        
        logger.info(f"Final rewritten query: {rewritten_query}")
        
        # Log to LangSmith if client is initialized and run_id is provided
        if self.langsmith_client and run_id:
            try:
                self.langsmith_client.create_feedback(
                    run_id=run_id,
                    key="query-rewrite",
                    score=1,
                    comment=f"Rewritten query: {rewritten_query}"
                )
                logger.info("Logged feedback to LangSmith")
            except Exception as e:
                logger.error(f"Error logging feedback to LangSmith: {e}")
        
        return rewritten_query