import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

class RAGSystem:
    def __init__(self, openai_api_key: str, embedding_model: str = "text-embedding-3-small"):
        print(f"Initializing OpenAI embeddings: {embedding_model}")
        self.embeddings = OpenAIEmbeddings(
            api_key=openai_api_key,
            model=embedding_model,
            base_url="https://api.openai.com/v1"
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        self.vectorstore = None
        self.knowledge_dir = Path("knowledge_base")
        self.knowledge_dir.mkdir(exist_ok=True)
        self.persist_directory = "./chroma_db"
    
    def load_markdown_files(self, directory: str = "knowledge_base") -> List[Document]:
        documents = []
        knowledge_path = Path(directory)
        
        if not knowledge_path.exists():
            print(f"Knowledge base directory '{directory}' not found. Creating it...")
            knowledge_path.mkdir(exist_ok=True)
            return documents
        
        markdown_files = list(knowledge_path.glob("**/*.md"))
        
        if not markdown_files:
            print(f"No markdown files found in '{directory}'")
            return documents
        
        for md_file in markdown_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    doc = Document(
                        page_content=content,
                        metadata={"source": str(md_file), "filename": md_file.name}
                    )
                    documents.append(doc)
                    print(f"Loaded: {md_file.name}")
            except Exception as e:
                print(f"Error loading {md_file}: {e}")
        
        return documents
    
    def index_documents(self, directory: str = "knowledge_base"):
        print("Loading markdown files...")
        documents = self.load_markdown_files(directory)
        
        if not documents:
            print("No documents to index.")
            return
        
        print(f"Splitting {len(documents)} documents into chunks...")
        splits = self.text_splitter.split_documents(documents)
        print(f"Created {len(splits)} chunks")
        
        print("Initializing vector database...")
        try:
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                print(f"Cleared old database")
        except Exception as e:
            print(f"Note: Could not clear old database: {e}")
        
        print("Creating embeddings and storing in vector database...")
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            collection_name="markdown_docs",
            persist_directory=self.persist_directory
        )
        
        print(f"Indexing complete! {len(splits)} chunks indexed.")
    
    def search(self, query: str, k: int = 4) -> List[Dict]:
        if not self.vectorstore:
            return []
        
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "filename": doc.metadata.get("filename", "Unknown"),
                "score": score
            })
        
        return formatted_results
    
    def get_context_for_query(self, query: str, k: int = 4) -> str:
        results = self.search(query, k=k)
        
        if not results:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}: {result['filename']}]\n{result['content']}\n")
        
        return "\n".join(context_parts)
