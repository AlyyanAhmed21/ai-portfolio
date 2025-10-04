import ollama
from langchain_community.vectorstores import FAISS
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

class RAGService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="llama3")
        self.personal_vector_store = None
        self.projects_vector_store = None
        print("RAGService initialized with multi-expert knowledge bases.")

    def _create_vector_store(self, documents: list[Document]):
        """Helper function to create a vector store from documents."""
        if not documents:
            return None
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        print(f"    -> Split {len(documents)} documents into {len(chunks)} chunks.")
        vector_store = FAISS.from_documents(documents=chunks, embedding=self.embeddings)
        return vector_store

    def build_knowledge_bases(self, personal_docs: list[Document], project_docs: list[Document]):
        """Builds the separate vector stores for personal and project info."""
        print("  -> Building 'Personal Info' knowledge base...")
        self.personal_vector_store = self._create_vector_store(personal_docs)
        print("  -> Building 'Project Info' knowledge base...")
        self.projects_vector_store = self._create_vector_store(project_docs)
        print("Knowledge bases built successfully.")

    def route_query(self, query: str) -> str:
        """Uses the LLM to classify the user's query."""
        prompt = f"""
        You are a query routing expert. Your task is to classify the user's question into one of two categories based on its content:

        1.  **personal_info**: For questions about Alyyan's skills, education, experience, contact details, or personal background.
        2.  **project_info**: For questions about specific technical projects, repositories, code, or architecture.

        User Question: "{query}"
        
        Category:
        """
        try:
            response = ollama.chat(
                model='llama3',
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0} # We want deterministic classification
            )
            # Clean up the response to get only the category name
            category = response['message']['content'].strip().lower()
            if "personal_info" in category:
                return "personal_info"
            elif "project_info" in category:
                return "project_info"
            return "personal_info" # Default to personal info if classification is unclear
        except Exception:
            return "personal_info" # Default on error

    def get_retriever(self, category: str):
        """Returns the appropriate retriever based on the classified category."""
        if category == "personal_info" and self.personal_vector_store:
            print(" -> Routing to 'Personal Info' knowledge base.")
            return self.personal_vector_store.as_retriever()
        elif category == "project_info" and self.projects_vector_store:
            print(" -> Routing to 'Project Info' knowledge base.")
            return self.projects_vector_store.as_retriever()
        
        # Fallback to the personal store if the requested one doesn't exist
        return self.personal_vector_store.as_retriever() if self.personal_vector_store else None

rag_service_instance = RAGService()