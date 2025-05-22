import uuid
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain_core.prompts import PromptTemplate

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

def initialize_prompt():
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are an expert assistant. Use the following context to answer the question accurately:
        Context: {context}
        Question: {question}
        Answer: """
    )
    return prompt_template

def query_rag(question, vector_store, llm, prompt_template):
    try:
        print("Performing similarity search...")
        results = vector_store.similarity_search(question, k=3)
        context = " ".join([doc.page_content for doc in results])
        prompt = prompt_template.format(context=context, question=question)
        print("Generating response with LLM...")
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"Error during query: {e}")
        return "Failed to generate answer due to an error."