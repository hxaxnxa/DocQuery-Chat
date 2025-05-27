import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_documents(file_paths):
    documents = []
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist.")
            continue
        try:
            if file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif file_path.endswith(".docx"):
                loader = Docx2txtLoader(file_path)
                documents.extend(loader.load())
            elif file_path.endswith(".txt"):
                print(f"Loading text file: {file_path}")
                loader = TextLoader(file_path, encoding="utf-8")
                docs = loader.load()
                print(f"Successfully loaded {len(docs)} documents from {file_path}")
                documents.extend(docs)
            else:
                print(f"Error: Unsupported file type for {file_path}. Supported types: .pdf, .docx, .txt")
        except Exception as e:
            print(f"Failed to load {file_path}: {str(e)}")
            raise Exception(f"Error loading {file_path}: {str(e)}")
    return documents

def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    return chunks