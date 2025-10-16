import json
import aiofiles
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Set
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OpenAILLM
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from app_storage import AppStorage

class GraphRAGSystem:
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_username: str,
        neo4j_password: str,
        openai_api_key: str,
        grok_api_key: Optional[str] = None,
        grok_model: str = "grok-4-fast",
        embedding_model: str = "text-embedding-3-small"
    ):
        # Mask password for logging (show first 2 and last 2 characters)
        masked_password = neo4j_password[:2] + "*" * (len(neo4j_password) - 4) + neo4j_password[-2:] if len(neo4j_password) > 4 else "***"
        print(f"Neo4j credentials - Username: {neo4j_username}, Password: {masked_password}")
        print(f"Connecting to Neo4j at {neo4j_uri}")
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_username, neo4j_password)
        )
        
        self.driver.verify_connectivity()
        
        print(f"Initializing OpenAI embeddings: {embedding_model}")
        self.embedder = OpenAIEmbeddings(
            api_key=openai_api_key,
            model=embedding_model,
            base_url="https://api.openai.com/v1"
        )
        
        self.llm = OpenAILLM(
            api_key=grok_api_key,
            base_url="https://api.x.ai/v1",
            model_name=grok_model,
            model_params={"temperature": 0.6}
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
        
        self.storage = AppStorage()
        self.tracking_file = "knowledge_base_tracking.json"
        self.processed_files: Dict[str, Dict] = self._load_tracking()
    
    def _load_tracking(self) -> Dict[str, Dict]:
        try:
            data = self.storage.readdata(self.tracking_file)
            if data:
                return json.loads(data)
            return {}
        except Exception as e:
            print(f"Error loading tracking file: {e}")
            return {}
    
    def _save_tracking(self):
        try:
            data = json.dumps(self.processed_files, indent=2)
            self.storage.writedata(self.tracking_file, data)
        except Exception as e:
            print(f"Error saving tracking file: {e}")
    
    def _get_file_metadata(self, file_path: Path) -> Dict:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return {
            "path": str(file_path),
            "checksum": sha256_hash.hexdigest()
        }
    
    def _file_needs_processing(self, file_path: Path) -> bool:
        file_key = str(file_path)
        if file_key not in self.processed_files:
            return True

        current_meta = self._get_file_metadata(file_path)
        stored_meta = self.processed_files[file_key]

        return current_meta["checksum"] != stored_meta.get("checksum")
    
    def _mark_file_processed(self, file_path: Path):
        self.processed_files[str(file_path)] = self._get_file_metadata(file_path)
    
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
    
    async def build_knowledge_graph(self, directory: str = "knowledge_base", force_rebuild: bool = False):
        print("Checking for new or modified files...")
        knowledge_path = Path(directory)
        
        if not knowledge_path.exists():
            print(f"Knowledge base directory '{directory}' not found.")
            return
        
        all_files = list(knowledge_path.glob("**/*.pdf")) + list(knowledge_path.glob("**/*.md"))
        
        current_file_paths = {str(f) for f in all_files}
        tracked_file_paths = set(self.processed_files.keys())
        
        deleted_files = tracked_file_paths - current_file_paths
        if deleted_files:
            print(f"Removing {len(deleted_files)} deleted file(s) from knowledge graph...")
            for deleted_path in deleted_files:
                with self.driver.session() as session:
                    session.run(
                        "MATCH (c:Chunk {source: $source}) DETACH DELETE c",
                        source=deleted_path
                    )
                del self.processed_files[deleted_path]
                print(f"Removed: {Path(deleted_path).name}")
            self._save_tracking()
        
        if not all_files:
            print("No files found in knowledge base.")
            return
        
        files_to_process = []
        unchanged_files = []
        
        for file in all_files:
            if force_rebuild or self._file_needs_processing(file):
                files_to_process.append(file)
            else:
                unchanged_files.append(file)
        
        if unchanged_files:
            print(f"Skipping {len(unchanged_files)} unchanged file(s)")
        
        if not files_to_process:
            print("All files already processed. Knowledge graph is up to date!")
            if not self.retriever:
                print("Initializing retriever...")
                self.retriever = VectorRetriever(
                    driver=self.driver,
                    index_name=self.vector_index_name,
                    embedder=self.embedder
                )
                self.rag = GraphRAG(
                    retriever=self.retriever,
                    llm=self.llm
                )
            return
        
        print(f"Processing {len(files_to_process)} new/modified file(s)...")
        
        documents = []
        for file in files_to_process:
            if file.suffix == '.pdf':
                try:
                    reader = PdfReader(file)
                    text_content = []
                    for page in reader.pages:
                        text = page.extract_text()
                        if text and text.strip():
                            text_content.append(text)
                    if text_content:
                        doc = Document(
                            page_content="\n\n".join(text_content),
                            metadata={"source": str(file), "filename": file.name, "type": "pdf", "pages": len(reader.pages)}
                        )
                        documents.append(doc)
                        print(f"Loaded: {file.name} ({len(reader.pages)} pages)")
                except Exception as e:
                    print(f"Error loading {file}: {e}")
            
            elif file.suffix == '.md':
                try:
                    async with aiofiles.open(file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        doc = Document(
                            page_content=content,
                            metadata={"source": str(file), "filename": file.name, "type": "markdown"}
                        )
                        documents.append(doc)
                        print(f"Loaded: {file.name}")
                except Exception as e:
                    print(f"Error loading {file}: {e}")
        
        if not documents:
            print("No valid documents to process.")
            return
        
        print(f"Splitting {len(documents)} document(s) into chunks...")
        splits = self.text_splitter.split_documents(documents)
        print(f"Created {len(splits)} chunks")
        
        print("Removing old chunks for modified files...")
        with self.driver.session() as session:
            for file in files_to_process:
                session.run(
                    "MATCH (c:Chunk {source: $source}) DETACH DELETE c",
                    source=str(file)
                )
        
        print("Creating new chunk nodes with embeddings...")
        chunk_count = 0
        batch_size = 10
        for i in range(0, len(splits), batch_size):
            batch = splits[i:i+batch_size]
            
            with self.driver.session() as session:
                for idx, chunk in enumerate(batch, start=i):
                    try:
                        embedding = self.embedder.embed_query(chunk.page_content)
                        
                        session.run(
                            """
                            CREATE (c:Chunk {
                                text: $text,
                                source: $source,
                                filename: $filename,
                                embedding: $embedding,
                                chunk_index: $chunk_index
                            })
                            """,
                            text=chunk.page_content,
                            source=chunk.metadata.get("source", "unknown"),
                            filename=chunk.metadata.get("filename", "unknown"),
                            embedding=embedding,
                            chunk_index=idx
                        )
                        chunk_count += 1
                        if chunk_count % 100 == 0:
                            print(f"Processed {chunk_count}/{len(splits)} chunks...")
                    except Exception as e:
                        print(f"Error processing chunk: {e}")
                        continue
        
        print(f"Created {chunk_count} chunk nodes in Neo4j")
        
        print("Updating sequential relationships...")
        with self.driver.session() as session:
            for file in files_to_process:
                session.run(
                    """
                    MATCH (c1:Chunk {source: $source})
                    MATCH (c2:Chunk {source: $source})
                    WHERE c2.chunk_index = c1.chunk_index + 1
                    MERGE (c1)-[:NEXT_CHUNK]->(c2)
                    """,
                    source=str(file)
                )
        
        print("Ensuring vector index exists...")
        self._create_vector_index()
        
        print("Marking files as processed...")
        for file in files_to_process:
            self._mark_file_processed(file)
        self._save_tracking()
        
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
                
                session.run(
                    """
                    CREATE INDEX chunk_sequence_index IF NOT EXISTS
                    FOR (c:Chunk)
                    ON (c.source, c.chunk_index)
                    """
                )
                print("Composite index on (source, chunk_index) created")
            except Exception as e:
                print(f"Error creating indexes: {e}")
    
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
