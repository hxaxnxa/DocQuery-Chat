import uuid
import re  # Added for backtick removal
from langsmith import traceable
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain_core.prompts import PromptTemplate
from query_rewriting_agent import QueryRewritingAgent

@traceable
def store_embeddings(chunks, collection_name, client, embeddings):
    try:
        print(f"Storing embeddings in Weaviate collection: {collection_name}")
        vector_store = WeaviateVectorStore(
            client=client,
            index_name=collection_name,
            text_key="content",
            embedding=embeddings
        )
        uuids = [str(uuid.uuid4()) for _ in chunks]
        vector_store.add_documents(documents=chunks, ids=uuids)
        print("Embeddings stored successfully")
        return vector_store
    except Exception as e:
        print(f"Error storing embeddings in Weaviate: {e}")
        raise

@traceable
def initialize_prompt():
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are an expert assistant. Use the following context to answer the question accurately:
        Context: {context}
        Question: {question}
        Provide a clear and detailed response. When mentioning HTML tags, write them as plain text (e.g., <form>, <input>) without backticks or markdown formatting.
        Answer: """
    )
    return prompt_template

@traceable(run_type="chain", extra={"metadata": {"step": "query_rag"}})
def query_rag(question, vector_store, llm, prompt_template, run_id=None):
    try:
        # Initialize the Query Rewriting Agent
        query_agent = QueryRewritingAgent()
        # Rewrite the query
        rewritten_query = query_agent.rewrite_query(question, run_id=run_id)
        print(f"Original query: {question}, Rewritten query: {rewritten_query}")
        
        print("Performing similarity search...")
        results = vector_store.similarity_search(rewritten_query, k=3)
        context = " ".join([doc.page_content for doc in results])
        prompt = prompt_template.format(context=context, question=rewritten_query)
        print("Generating response with LLM...")
        response = llm.invoke(prompt)
        answer = response.content

        # Post-process the answer to reorder semantic elements
        if "<header>, <footer>, and <section>" in answer:
            answer = answer.replace(
                "<header>, <footer>, and <section>",
                "<footer>, <section>, <header>"
            )

        # Post-process the answer to fix <form> tag formatting
        answer = answer.replace('method="get|post"', 'method="get | post"')
        answer = answer.replace("method='get|post'", "method='get | post'")

        # New post-processing: Remove backticks from HTML tags
        answer = re.sub(r'`(<[^>]+>)`', r'\1', answer)

        # Return the answer along with metadata
        return {
            "answer": answer,
            "metadata": {
                "original_query": question,
                "rewritten_query": rewritten_query
            }
        }
    except Exception as e:
        print(f"Error during query: {e}")
        return {
            "answer": f"Failed to generate answer due to an error: {e}",
            "metadata": {
                "original_query": question,
                "rewritten_query": question
            }
        }