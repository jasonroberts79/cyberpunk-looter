import os
from pathlib import Path
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OpenAILLM
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

class GraphRAGSystem:
    def __init__(
        self, 
        neo4j_uri: str,
        neo4j_username: str,
        neo4j_password: str,
        openai_api_key: str,
        grok_api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        print(f"Connecting to Neo4j at {neo4j_uri}")
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_username, neo4j_password)
        )
        
        print(f"Initializing OpenAI embeddings: {embedding_model}")
        self.embedder = OpenAIEmbeddings(
            api_key=openai_api_key,
            model=embedding_model,
            base_url="https://api.openai.com/v1"
        )
        
        if grok_api_key:
            self.llm = OpenAILLM(
                api_key=grok_api_key,
                base_url="https://api.x.ai/v1",
                model_name="grok-beta",
                model_params={"temperature": 0.7}
            )
        else:
            self.llm = OpenAILLM(
                api_key=openai_api_key,
                model_name="gpt-4",
                model_params={"temperature": 0.7}
            )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        self.knowledge_dir = Path("knowledge_base")
        self.knowledge_dir.mkdir(exist_ok=True)
        
        self.vector_index_name = "document_embeddings"
        self.retriever = None
        self.rag = None
    
    def load_pdf_files(self, directory: str = "knowledge_base") -> List[Document]:
        documents = []
        knowledge_path = Path(directory)
        
        if not knowledge_path.exists():
            return documents
        
        pdf_files = list(knowledge_path.glob("**/*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in '{directory}'")
            return documents
        
        for pdf_file in pdf_files:
            try:
                reader = PdfReader(pdf_file)
                text_content = []
                
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text and text.strip():
                        text_content.append(text)
                
                if text_content:
                    full_text = "\n\n".join(text_content)
                    doc = Document(
                        page_content=full_text,
                        metadata={
                            "source": str(pdf_file), 
                            "filename": pdf_file.name,
                            "type": "pdf",
                            "pages": len(reader.pages)
                        }
                    )
                    documents.append(doc)
                    print(f"Loaded: {pdf_file.name} ({len(reader.pages)} pages)")
                else:
                    print(f"Warning: {pdf_file.name} contains no extractable text")
            except Exception as e:
                print(f"Error loading {pdf_file}: {e}")
        
        return documents
    
    def load_markdown_files(self, directory: str = "knowledge_base") -> List[Document]:
        documents = []
        knowledge_path = Path(directory)
        
        if not knowledge_path.exists():
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
                        metadata={"source": str(md_file), "filename": md_file.name, "type": "markdown"}
                    )
                    documents.append(doc)
                    print(f"Loaded: {md_file.name}")
            except Exception as e:
                print(f"Error loading {md_file}: {e}")
        
        return documents
    
    async def build_knowledge_graph(self, directory: str = "knowledge_base"):
        print("Loading documents for knowledge graph...")
        documents = []
        
        print("Loading markdown files...")
        md_docs = self.load_markdown_files(directory)
        documents.extend(md_docs)
        
        print("Loading PDF files...")
        pdf_docs = self.load_pdf_files(directory)
        documents.extend(pdf_docs)
        
        if not documents:
            print("No documents to process.")
            return
        
        print(f"Splitting {len(documents)} documents into chunks...")
        splits = self.text_splitter.split_documents(documents)
        print(f"Created {len(splits)} chunks")
        
        print("Clearing existing graph data...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        print("Creating chunk nodes with embeddings...")
        chunk_count = 0
        batch_size = 10
        for i in range(0, len(splits), batch_size):
            batch = splits[i:i+batch_size]
            
            with self.driver.session() as session:
                for chunk in batch:
                    try:
                        embedding = self.embedder.embed_query(chunk.page_content)
                        
                        session.run(
                            """
                            CREATE (c:Chunk {
                                text: $text,
                                source: $source,
                                filename: $filename,
                                embedding: $embedding
                            })
                            """,
                            text=chunk.page_content,
                            source=chunk.metadata.get("source", "unknown"),
                            filename=chunk.metadata.get("filename", "unknown"),
                            embedding=embedding
                        )
                        chunk_count += 1
                        if chunk_count % 100 == 0:
                            print(f"Processed {chunk_count}/{len(splits)} chunks...")
                    except Exception as e:
                        print(f"Error processing chunk: {e}")
                        continue
        
        print(f"Created {chunk_count} chunk nodes in Neo4j")
        
        print("Creating sequential relationships between chunks...")
        with self.driver.session() as session:
            session.run(
                """
                MATCH (c1:Chunk), (c2:Chunk)
                WHERE id(c1) + 1 = id(c2) AND c1.filename = c2.filename
                CREATE (c1)-[:NEXT_CHUNK]->(c2)
                """
            )
        
        print("Creating vector index...")
        self._create_vector_index()
        
        print("Initializing retriever...")
        self.retriever = VectorRetriever(
            driver=self.driver,
            index_name=self.vector_index_name,
            embedder=self.embedder
        )
        
        print("Initializing GraphRAG pipeline...")
        self.rag = GraphRAG(
            retriever=self.retriever,
            llm=self.llm
        )
        
        print("GraphRAG system ready!")
    
    def _create_vector_index(self):
        with self.driver.session() as session:
            try:
                session.run("DROP INDEX document_embeddings IF EXISTS")
                
                session.run(
                    """
                    CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
                    FOR (c:Chunk)
                    ON c.embedding
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 1536,
                        `vector.similarity_function`: 'cosine'
                    }}
                    """
                )
                print(f"Vector index '{self.vector_index_name}' created")
            except Exception as e:
                print(f"Error creating vector index: {e}")
    
    def search(self, query: str, k: int = 10) -> str:
        if not self.rag:
            return "GraphRAG system not initialized. Please run build_knowledge_graph first."
        
        try:
            result = self.rag.search(query, retriever_config={"top_k": k})
            return result.answer
        except Exception as e:
            print(f"Search error: {e}")
            return f"Error performing search: {str(e)}"
    
    def get_context_for_query(self, query: str, k: int = 10) -> str:
        if not self.retriever:
            return "No relevant information found in the knowledge base."
        
        try:
            query_vector = self.embedder.embed_query(query)
            
            with self.driver.session() as session:
                result = session.run(
                    """
                    CALL db.index.vector.queryNodes($index_name, $k, $query_vector)
                    YIELD node, score
                    OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
                    RETURN node.text AS text, 
                           node.filename AS filename, 
                           next.text AS next_text,
                           score
                    ORDER BY score DESC
                    LIMIT $k
                    """,
                    index_name=self.vector_index_name,
                    k=k,
                    query_vector=query_vector
                )
                
                context_parts = []
                for i, record in enumerate(result, 1):
                    text = record.get("text", "")
                    filename = record.get("filename", "Unknown")
                    next_text = record.get("next_text", "")
                    
                    if text:
                        full_context = text
                        if next_text:
                            full_context += "\n\n" + next_text
                        context_parts.append(f"[Source {i}: {filename}]\n{full_context}\n")
                
                if context_parts:
                    return "\n".join(context_parts)
                else:
                    return "No relevant information found in the knowledge base."
        except Exception as e:
            print(f"Context retrieval error: {e}")
            return "No relevant information found in the knowledge base."
    
    def close(self):
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed")
