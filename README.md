# DocQuery-Chat

A secure, chatbot-style document query application built with Streamlit, Weaviate, Gemini embeddings, and the Gemini model.

## 🌟 Overview

**DocQuery-Chat** allows you to upload documents (PDF, DOCX, TXT) and query them using natural language. It leverages:

- 🖥️ **Streamlit** for the user interface  
- 🧠 **Weaviate (free tier)** as the vector database to store document embeddings  
- 🔍 **Gemini embeddings** to convert text into vector representations  
- 💬 **Gemini model** for generating responses to user queries
- 📊 **LangSmith** for tracing and user feedback evaluation

The app includes features like:
- 🔐 User authentication
- 📁 File validation
- ⏳ Session timeout
- 💬 A conversational chat interface
- 📜 Detailed logging for debugging (app.log)

---

## ✅ Prerequisites

- Python 3.8 or higher  
- Git  
- A [Weaviate Cloud account (free tier)](https://console.weaviate.cloud/)  
- A [Google API key](https://makersuite.google.com/app/apikey) for Gemini embeddings and model
- A LangSmith API key for tracing

---

## ⚙️ Setup

### 1. Clone the Repository
```bash
git clone https://github.com/hxaxnxa/DocQuery-Chat.git
cd DocQuery-Chat
````

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root and add the following:

```
GOOGLE_API_KEY=your_key
WEAVIATE_URL=your_url
WEAVIATE_API_KEY=your_key
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT_NAME=DocQuery-Chat-Eval
```

* `GOOGLE_API_KEY`: Your Gemini API key from Google AI Studio
* `WEAVIATE_URL`: Your Weaviate cluster URL (e.g., [https://your-cluster.weaviate.cloud](https://your-cluster.weaviate.cloud))
* `WEAVIATE_API_KEY`: Your Weaviate API key from the Weaviate Cloud dashboard
* `LANGCHAIN_API_KEY`: Your LangSmith API key for tracing
* `LANGCHAIN_PROJECT_NAME`: Your LangSmith project name (set to DocQuery-Chat-Eval as used in the app)
* `LANGCHAIN_TRACING_V2`: Set to true for tracing

### 5. Create User Credentials

Run the following script:

```bash
python create_users.py
```

This creates a default user:
`Username: admin`
`Password: securepass123`

### 6. Verify Weaviate Setup

Ensure your Weaviate cluster is running and accessible. The app connects to the Document class in Weaviate to store embeddings.

---

## 🚀 Run the Application

```bash
streamlit run app.py
```

Open your browser and go to:
📍 [http://localhost:8501](http://localhost:8501)

---

## 🧑‍💻 Usage

### 🔐 Log In

* Use default credentials: `admin / securepass123`
* For security, edit `users.json` to add your own credentials after first login

### 📁 Upload Documents

* Upload up to 50 documents (PDF, DOCX, TXT)
* Max total size: **200 MB**

### ⚙️ Process Documents

* Click **Process Documents** to load and embed into Weaviate

### 💬 Ask Questions

* Use natural language in the chat (e.g., "What is the latest version of Python?", "Summarize the document").
* Queries are rewritten for clarity (e.g., "What is the latest version of Python?" → "Current version of Python") using the Gemini model.
* Answers are generated using the Gemini model and displayed in the chat interface.
* Provide feedback on responses using the "👍 Yes" or "👎 No" options, which is logged to LangSmith for evaluation.

### ⏲️ Session Management

* Session timeout: 30 minutes of inactivity
* Use **Clear Session** or **Logout** to reset

---

## 📝 Notes

* **Weaviate Free Tier**: Has limits on storage and query throughput. Consider upgrading for production.
* **Gemini API**: Ensure your API key allows access to both **embeddings** and **chat model**.
* **Security**: Includes basic authentication and validation. For production, implement:

  * HTTPS
  * Malware scanning
  * Database-backed user system
* **Performance**: For large documents, reduce the `chunk size` in `rag_pipeline/file_loader.py` or batch process documents.
* **Logging**: Detailed logs are saved to app.log for debugging.

---

## 🛠️ Troubleshooting

**Weaviate Connection Issues**

* Check `WEAVIATE_URL` and `WEAVIATE_API_KEY` in your `.env` file

**Gemini API Errors**

* Validate your `GOOGLE_API_KEY` and permissions in [Google AI Studio](https://makersuite.google.com/)

**File Upload Problems**

* Use only PDF, DOCX, or TXT formats
* Max size: 200 MB
* Clear `temp_uploads/` if needed:

```powershell
Remove-Item -Recurse -Force temp_uploads
```

---

## 🤝 Contributing

Have ideas or improvements?
Feel free to open [issues](https://github.com/hxaxnxa/DocQuery-Chat/issues) or submit a pull request!

---

## 📄 License

This project is licensed under the [MIT License](License).
