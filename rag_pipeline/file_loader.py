import os
import re
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
                raw_docs = loader.load()
                for doc in raw_docs:
                    # Extract page number
                    page_num = doc.metadata.get("page", 0) + 1
                    # Extract surrounding headings (heuristic: look for all-caps or bold-like lines)
                    content = doc.page_content
                    lines = content.split("\n")
                    heading = None
                    for line in lines:
                        if re.match(r"^[A-Z\s]{5,}$", line.strip()):  # Heuristic for headings
                            heading = line.strip()
                            break
                    doc.metadata.update({
                        "page_number": page_num,
                        "heading": heading,
                        "source": os.path.basename(file_path)
                    })
                    documents.append(doc)
            elif file_path.endswith(".docx"):
                loader = Docx2txtLoader(file_path)
                raw_docs = loader.load()
                for doc in raw_docs:
                    # Extract section numbers (heuristic: look for "Section X" patterns)
                    content = doc.page_content
                    section_match = re.search(r"Section\s+(\d+\.\d+|\d+)", content)
                    section = section_match.group(0) if section_match else None
                    doc.metadata.update({
                        "section": section,
                        "source": os.path.basename(file_path)
                    })
                    documents.append(doc)
            elif file_path.endswith(".txt"):
                print(f"Loading text file: {file_path}")
                loader = TextLoader(file_path, encoding="utf-8")
                raw_docs = loader.load()
                for doc in raw_docs:
                    content = doc.page_content
                    # Extract section numbers or clauses (same as for .docx)
                    section_match = re.search(r"Section\s+(\d+\.\d+|\d+)", content)
                    section = section_match.group(0) if section_match else None
                    doc.metadata.update({
                        "section": section,
                        "source": os.path.basename(file_path)
                    })
                    documents.append(doc)
                print(f"Successfully loaded {len(raw_docs)} documents from {file_path}")
            else:
                print(f"Error: Unsupported file type for {file_path}. Supported types: .pdf, .docx, .txt")
        except Exception as e:
            print(f"Failed to load {file_path}: {str(e)}")
            raise Exception(f"Error loading {file_path}: {str(e)}")
    return documents

def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    # Preserve metadata in chunks
    for chunk in chunks:
        chunk.metadata = chunk.metadata or {}
    return chunks