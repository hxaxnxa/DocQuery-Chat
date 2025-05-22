import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_documents(file_paths):

    documents = []

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist.")
            continue
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())
        elif file_path.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
            documents.extend(loader.load())
        elif file_path.endswith(".txt"):
            loader = TextLoader(file_path)
            documents.extend(loader.load())
        else:
            print(f"Error: Unsupported file type for {file_path}. Supported types: .pdf, .docx, .txt")
    return documents

def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    return chunks