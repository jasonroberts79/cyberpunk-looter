import json
import aiofiles
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional, Set, Callable, Any
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, SessionExpired, TransientError
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OpenAILLM
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from src.config import AppConfig
from src.interfaces import Storage

class GraphRAGSystem:
    NO_DATA_MESSAGE = "No relevant information found in the knowledge base."

    def __init__(
        self,
        storage: Storage,
        config: AppConfig,
    ):
        # Store connection parameters for reconnection
        self.neo4j_uri = config.neo4j_uri
        self.neo4j_username = config.neo4j_username
        self.neo4j_password = config.neo4j_password
        self.max_retry_attempts = config.graphrag.max_retries
        self.retry_delay = config.graphrag.retry_delay_seconds

        print(f"Connecting to Neo4j at {self.neo4j_uri}")
        self.driver_initialized = False
        self._connect_to_neo4j()        
                
        print(f"Initializing OpenAI embeddings: {config.graphrag.embeddings_model}")
        self.embedder = OpenAIEmbeddings(
            api_key=config.embeddings_key,
            model=config.graphrag.embeddings_model,
            base_url=config.embeddings_url,
        )
        
        self.llm = OpenAILLM(
            api_key=config.anthropic_api_key,
            base_url=config.llm_url,
            model_name=config.llm_model,
            model_params={"temperature": config.llm.temperature},
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.graphrag.chunk_size,
            chunk_overlap=config.graphrag.chunk_overlap,
            length_function=len,
        )

        self.knowledge_dir = Path(config.graphrag.kb_path)
        self.knowledge_dir.mkdir(exist_ok=True)

        self.vector_index_name = config.graphrag.vector_index_name
        self.retriever = None
        self.rag = None

        self.storage = storage
        self.tracking_file = config.graphrag.file_tracking_file
        self.processed_files: Dict[str, Dict] = self._load_tracking()

    def _load_tracking(self) -> Dict[str, Dict]:
        try:
            data = self.storage.read_data(self.tracking_file)
            if data:
                return json.loads(data)
            return {}
        except Exception as e:
            print(f"Error loading tracking file: {e}")
            return {}

    def _save_tracking(self):
        try:
            data = json.dumps(self.processed_files, indent=2)
            self.storage.write_data(self.tracking_file, data)
        except Exception as e:
            print(f"Error saving tracking file: {e}")

    def _connect_to_neo4j(self):
        """Connect to Neo4j and verify connectivity."""
        try:
            if self.driver_initialized and self.driver:
                self.driver.close()

            self.driver = GraphDatabase.driver(
                self.neo4j_uri, auth=(self.neo4j_username, self.neo4j_password)
            )
            self.driver_initialized = True
            self.driver.verify_connectivity()
            print("Successfully connected to Neo4j")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            raise

    def _ensure_connection(self):
        """Ensure the Neo4j connection is alive, reconnect if necessary."""
        try:
            self.driver.verify_connectivity()
        except (ServiceUnavailable, SessionExpired, TransientError, Exception) as e:
            print(f"Connection lost: {e}. Attempting to reconnect...")
            self._connect_to_neo4j()

    def _execute_with_retry(
        self, operation: Callable[[], Any], operation_name: str = "operation"
    ) -> Any:
        """Execute a database operation with automatic retry on connection failures."""
        last_exception = None

        for attempt in range(self.max_retry_attempts):
            try:
                self._ensure_connection()
                return operation()
            except (ServiceUnavailable, SessionExpired, TransientError) as e:
                last_exception = e
                if attempt < self.max_retry_attempts - 1:
                    wait_time = self.retry_delay * (2**attempt)  # Exponential backoff
                    print(
                        f"{operation_name} failed (attempt {attempt + 1}/{self.max_retry_attempts}): {e}"
                    )
                    print(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    try:
                        self._connect_to_neo4j()
                    except Exception as reconnect_error:
                        print(f"Reconnection failed: {reconnect_error}")
                else:
                    print(f"{operation_name} failed after {self.max_retry_attempts} attempts")

        raise (last_exception if last_exception else Exception(f"{operation_name} failed"))

    def _get_file_metadata(self, file_path: Path) -> Dict:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return {"path": str(file_path), "checksum": sha256_hash.hexdigest()}

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
                            "pages": len(reader.pages),
                        },
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
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": str(md_file),
                            "filename": md_file.name,
                            "type": "markdown",
                        },
                    )
                    documents.append(doc)
                    print(f"Loaded: {md_file.name}")
            except Exception as e:
                print(f"Error loading {md_file}: {e}")

        return documents

    def _remove_deleted_files(self, current_file_paths: Set[str]):
        """Remove chunks from Neo4j for files that no longer exist."""
        tracked_file_paths = set(self.processed_files.keys())
        deleted_files = tracked_file_paths - current_file_paths

        if not deleted_files:
            return

        print(f"Removing {len(deleted_files)} deleted file(s) from knowledge graph...")
        for deleted_path in deleted_files:

            def delete_chunks(source=deleted_path):
                with self.driver.session() as session:
                    session.run(
                        "MATCH (c:Chunk {source: $source}) DETACH DELETE c",
                        source=source,
                    )

            self._execute_with_retry(delete_chunks, f"Delete chunks for {Path(deleted_path).name}")
            del self.processed_files[deleted_path]
            print(f"Removed: {Path(deleted_path).name}")

        self._save_tracking()

    def _categorize_files(
        self, all_files: List[Path], force_rebuild: bool
    ) -> tuple[List[Path], List[Path]]:
        """Categorize files into those needing processing and those unchanged."""
        files_to_process = []
        unchanged_files = []

        for file in all_files:
            if force_rebuild or self._file_needs_processing(file):
                files_to_process.append(file)
            else:
                unchanged_files.append(file)

        if unchanged_files:
            print(f"Skipping {len(unchanged_files)} unchanged file(s)")

        return files_to_process, unchanged_files

    async def _load_documents_from_files(self, files_to_process: List[Path]) -> List[Document]:
        """Load documents from PDF and Markdown files."""
        documents = []

        for file in files_to_process:
            if file.suffix == ".pdf":
                doc = self._load_pdf_document(file)
                if doc:
                    documents.append(doc)
            elif file.suffix == ".md":
                doc = await self._load_markdown_document(file)
                if doc:
                    documents.append(doc)

        return documents

    def _load_pdf_document(self, file: Path) -> Optional[Document]:
        """Load a single PDF document."""
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
                    metadata={
                        "source": str(file),
                        "filename": file.name,
                        "type": "pdf",
                        "pages": len(reader.pages),
                    },
                )
                print(f"Loaded: {file.name} ({len(reader.pages)} pages)")
                return doc
        except Exception as e:
            print(f"Error loading {file}: {e}")
        return None

    async def _load_markdown_document(self, file: Path) -> Optional[Document]:
        """Load a single Markdown document."""
        try:
            async with aiofiles.open(file, "r", encoding="utf-8") as f:
                content = await f.read()
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": str(file),
                        "filename": file.name,
                        "type": "markdown",
                    },
                )
                print(f"Loaded: {file.name}")
                return doc
        except Exception as e:
            print(f"Error loading {file}: {e}")
        return None

    def _remove_old_chunks(self, files_to_process: List[Path]):
        """Remove old chunks from Neo4j for files being reprocessed."""
        print("Removing old chunks for modified files...")
        for file in files_to_process:

            def remove_old_chunks(source=str(file)):
                with self.driver.session() as session:
                    session.run(
                        "MATCH (c:Chunk {source: $source}) DETACH DELETE c",
                        source=source,
                    )

            self._execute_with_retry(remove_old_chunks, f"Remove old chunks for {file.name}")

    def _create_chunk_nodes(self, splits: List[Document]) -> int:
        """Create chunk nodes in Neo4j with embeddings."""
        print("Creating new chunk nodes with embeddings...")
        chunk_count = 0
        batch_size = 10

        for i in range(0, len(splits), batch_size):
            batch = splits[i : i + batch_size]

            for idx, chunk in enumerate(batch, start=i):
                try:
                    embedding = self.embedder.embed_query(chunk.page_content)

                    def create_chunk_node(
                        chunk_param=chunk, embedding_param=embedding, idx_param=idx
                    ):
                        with self.driver.session() as session:
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
                                text=chunk_param.page_content,
                                source=chunk_param.metadata.get("source", "unknown"),
                                filename=chunk_param.metadata.get("filename", "unknown"),
                                embedding=embedding_param,
                                chunk_index=idx_param,
                            )

                    self._execute_with_retry(create_chunk_node, f"Create chunk {idx}")
                    chunk_count += 1
                    if chunk_count % 100 == 0:
                        print(f"Processed {chunk_count}/{len(splits)} chunks...")
                except Exception as e:
                    print(f"Error processing chunk: {e}")
                    continue

        print(f"Created {chunk_count} chunk nodes in Neo4j")
        return chunk_count

    def _create_sequential_relationships(self, files_to_process: List[Path]):
        """Create sequential relationships between chunks."""
        print("Updating sequential relationships...")
        for file in files_to_process:

            def create_relationships(source=str(file)):
                with self.driver.session() as session:
                    session.run(
                        """
                        MATCH (c1:Chunk {source: $source})
                        MATCH (c2:Chunk {source: $source})
                        WHERE c2.chunk_index = c1.chunk_index + 1
                        MERGE (c1)-[:NEXT_CHUNK]->(c2)
                        """,
                        source=source,
                    )

            self._execute_with_retry(create_relationships, f"Create relationships for {file.name}")

    def _initialize_retriever(self):
        """Initialize the retriever and RAG components."""
        print("Initializing retriever...")
        self.retriever = VectorRetriever(
            driver=self.driver,
            index_name=self.vector_index_name,
            embedder=self.embedder,
        )

        print("Initializing GraphRAG pipeline...")
        self.rag = GraphRAG(retriever=self.retriever, llm=self.llm)

    async def build_knowledge_graph(
        self, directory: str = "knowledge_base", force_rebuild: bool = False
    ):
        """Build or update the knowledge graph from documents in the specified directory."""
        print("Checking for new or modified files...")
        knowledge_path = Path(directory)

        if not knowledge_path.exists():
            print(f"Knowledge base directory '{directory}' not found.")
            return

        # Gather all PDF and Markdown files
        all_files = list(knowledge_path.glob("**/*.pdf")) + list(knowledge_path.glob("**/*.md"))
        current_file_paths = {str(f) for f in all_files}

        # Remove chunks for deleted files
        self._remove_deleted_files(current_file_paths)

        if not all_files:
            print("No files found in knowledge base.")
            return

        # Categorize files into those needing processing and those unchanged
        files_to_process, _ = self._categorize_files(all_files, force_rebuild)

        # If no files need processing, ensure retriever is initialized and exit
        if not files_to_process:
            print("All files already processed. Knowledge graph is up to date!")
            if not self.retriever:
                self._initialize_retriever()
            return

        # Load documents from files
        print(f"Processing {len(files_to_process)} new/modified file(s)...")
        documents = await self._load_documents_from_files(files_to_process)

        if not documents:
            print("No valid documents to process.")
            return

        # Split documents into chunks
        print(f"Splitting {len(documents)} document(s) into chunks...")
        splits = self.text_splitter.split_documents(documents)
        print(f"Created {len(splits)} chunks")

        # Remove old chunks and create new ones
        self._remove_old_chunks(files_to_process)
        self._create_chunk_nodes(splits)

        # Create sequential relationships between chunks
        self._create_sequential_relationships(files_to_process)

        # Ensure vector index exists
        print("Ensuring vector index exists...")
        self._create_vector_index()

        # Mark files as processed
        print("Marking files as processed...")
        for file in files_to_process:
            self._mark_file_processed(file)
        self._save_tracking()

        # Initialize retriever and RAG pipeline
        self._initialize_retriever()

        print("GraphRAG system ready!")

    def _create_vector_index(self):
        def create_indexes():
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
                    raise

        self._execute_with_retry(create_indexes, "Create vector indexes")

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
            return self.NO_DATA_MESSAGE

        try:
            query_vector = self.embedder.embed_query(query)

            def query_context():
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
                        query_vector=query_vector,
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
                        return self.NO_DATA_MESSAGE

            return self._execute_with_retry(query_context, "Query context")
        except Exception as e:
            print(f"Context retrieval error: {e}")
            return self.NO_DATA_MESSAGE

    def close(self):
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed")
