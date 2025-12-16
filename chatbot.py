"""
JIIT Advanced AI Chatbot
=========================

An intelligent chatbot system for JIIT (Jaypee Institute of Information Technology) that provides
accurate, context-aware responses to queries about the institution.

Architecture:
-------------
1. **Web Scraping**: Crawls JIIT website to build a comprehensive knowledge base
2. **Hybrid Search**: Combines FAISS (semantic) and BM25 (keyword) search for optimal retrieval
3. **LLM Integration**: Uses Groq/OpenAI for generating natural language responses
4. **Caching**: Implements intelligent caching to minimize redundant web requests

Key Components:
---------------
- Document: Data model for storing scraped content
- Config: Central configuration for all system parameters
- EnhancedWebScraper: Intelligent web crawler with PDF support
- VectorStore: FAISS-based semantic search engine
- KeywordSearch: BM25-based keyword search engine
- HybridSearch: Combines both search methods using reciprocal rank fusion
- ResponseGenerator: LLM-powered response generation
- JIITAdvancedChatbot: Main orchestrator class

Features:
---------
- Real-time web scraping with caching
- Semantic + keyword hybrid search
- Source citation in responses
- PDF document processing
- Fallback mode when LLM is unavailable
- Persistent index storage

Author: Kartik, Manav, Sujal
Supervisor: Dr. Tribhuvan Kumar Tewary
"""

# ============================================================================
# IMPORTS & CONFIGURATION
# ============================================================================

import os
import sys
import json
import pickle
import hashlib
import re
import io
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

import faiss
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

from rank_bm25 import BM25Okapi

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


# ============================================================================
# PAGE CONFIG — Sidebar always expanded (hardcoded)
# ============================================================================
st.set_page_config(
    page_title="JIIT AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Document:
    """
    Data model for storing scraped web documents.
    
    Attributes:
        id (str): Unique MD5 hash identifier for the document
        url (str): Source URL of the document
        title (str): Document title extracted from page
        content (str): Main text content of the document
        doc_type (str): Classification (e.g., 'admission', 'placement', 'pdf', 'general')
        metadata (Dict): Additional information about the document
        embedding (Optional[np.ndarray]): Vector embedding for semantic search
        last_updated (Optional[datetime]): Timestamp of last update
    """
    id: str
    url: str
    title: str
    content: str
    doc_type: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert document to dictionary format for JSON serialization.
        
        Returns:
            Dict: Document data without embedding (for storage efficiency)
        """
        d = asdict(self)
        d.pop('embedding', None)  # Remove embedding to reduce file size
        d['last_updated'] = self.last_updated.isoformat() if self.last_updated else None
        return d


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """
    Central configuration class for the chatbot system.
    
    Contains all system parameters including:
    - Directory paths for data storage
    - Web scraping settings (URLs, timeouts, limits)
    - Embedding model configuration
    - Search parameters (top-k values)
    - LLM API settings and model selection
    
    The class automatically selects the best available LLM provider
    (Groq > OpenAI > Fallback mode) based on API key availability.
    """
    # Directory structure for data persistence
    BASE_DIR = Path("jiit_data")
    CACHE_DIR = BASE_DIR / "cache"  # Cached web pages
    FAISS_DIR = BASE_DIR / "faiss_index"  # Vector search index
    BM25_DIR = BASE_DIR / "bm25_index"  # Keyword search index
    DOCS_DIR = BASE_DIR / "documents"  # Processed documents

    # JIIT website configuration
    BASE_URL = "https://www.jiit.ac.in"
    SITEMAP_URL = "https://www.jiit.ac.in/sitemap.xml"

    # Web scraping parameters
    MAX_PAGES = 1000  # Maximum pages to scrape
    CACHE_VALIDITY_HOURS = 24  # Cache expiration time
    REQUEST_TIMEOUT = 15  # HTTP request timeout in seconds
    REQUEST_DELAY = 0.1  # Delay between requests to avoid overloading server

    # Embedding model configuration
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384  # Dimension of embedding vectors

    # Search parameters
    FAISS_TOP_K = 15  # Top results from semantic search
    BM25_TOP_K = 15  # Top results from keyword search
    FINAL_TOP_K = 8  # Final results after fusion

    # API keys from environment variables
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Determine which LLM provider to use
    USE_GROQ = GROQ_API_KEY is not None and GROQ_AVAILABLE

    if USE_GROQ:
        LLM_MODEL = "llama-3.3-70b-versatile"
        LLM_PROVIDER = "Groq"
    elif OPENAI_API_KEY and OPENAI_AVAILABLE:
        LLM_MODEL = "gpt-4o-mini"
        LLM_PROVIDER = "OpenAI"
    else:
        LLM_MODEL = None
        LLM_PROVIDER = "None (Fallback Mode)"

    # LLM generation parameters
    LLM_TEMPERATURE = 0.2  # Lower temperature for more focused responses
    LLM_MAX_TOKENS = 1200  # Maximum response length

    @classmethod
    def setup_directories(cls) -> None:
        """
        Create all required directories if they don't exist.
        
        This ensures the application can store cached data, indexes,
        and processed documents without errors.
        """
        for dir_path in [cls.CACHE_DIR, cls.FAISS_DIR, cls.BM25_DIR, cls.DOCS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


# ============================================================================
# WEB SCRAPER
# ============================================================================

class EnhancedWebScraper:
    """
    Intelligent web scraper for JIIT website with caching and PDF support.
    
    Features:
    - Automatic sitemap parsing
    - Intelligent caching to minimize redundant requests
    - PDF document processing
    - Content classification
    - Progress tracking via callbacks
    
    Attributes:
        config (Config): Configuration object with scraping parameters
        session (requests.Session): Persistent HTTP session for efficiency
    """
    def __init__(self, config: Config):
        """
        Initialize the web scraper with configuration.
        
        Args:
            config (Config): Configuration object containing scraping parameters
        """
        self.config = config
        self.session = requests.Session()
        # Set user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_website(self, force_refresh: bool = False, progress_callback: Optional[Any] = None) -> List[Document]:
        """
        Main scraping method that crawls the JIIT website.
        
        Args:
            force_refresh (bool): If True, ignore cache and re-scrape all pages
            progress_callback (Optional): Function to call with progress updates
        
        Returns:
            List[Document]: List of successfully scraped documents
        
        Process:
            1. Get all URLs from sitemap and critical pages
            2. Scrape each URL (using cache when available)
            3. Process and classify content
            4. Return list of Document objects
        """
        try:
            # Get list of URLs to scrape
            urls = self._get_all_urls()
            if progress_callback:
                progress_callback(f"Found {len(urls)} URLs to process")
            
            documents: List[Document] = []
            total = min(len(urls), self.config.MAX_PAGES)
            
            # Scrape each URL
            for i, url in enumerate(urls[:self.config.MAX_PAGES], 1):
                try:
                    # Update progress every 10 pages
                    if progress_callback and i % 10 == 0:
                        progress_callback(f"Processing {i}/{total} pages...")
                    
                    doc = self._scrape_page(url, force_refresh)
                    if doc:
                        documents.append(doc)
                except Exception:
                    # Skip failed pages and continue
                    continue
            
            if progress_callback:
                progress_callback(f"✅ Successfully scraped {len(documents)} documents")
            return documents
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Error during scraping: {str(e)}")
            return []

    def _get_all_urls(self) -> List[str]:
        """
        Collects all URLs to scrape from sitemap and critical pages.
        
        Returns:
            List[str]: Unique list of URLs to scrape
        
        Sources:
            - Critical pages (admissions, placements, etc.)
            - Sitemap XML (up to 5 sub-sitemaps, 50 URLs each)
        """
        urls: set = set()
        # Add critical pages first (always included)
        urls.update(self._get_critical_urls())
        
        try:
            # Parse main sitemap
            response = self.session.get(self.config.SITEMAP_URL, timeout=15)
            root = ET.fromstring(response.content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Check if sitemap contains sub-sitemaps
            sitemaps = root.findall('.//ns:sitemap/ns:loc', namespace)
            if sitemaps:
                # Parse up to 5 sub-sitemaps
                for sitemap in sitemaps[:5]:
                    if sitemap.text:
                        sub_urls = self._parse_sitemap(sitemap.text)
                        urls.update(sub_urls[:50])  # Limit to 50 URLs per sitemap
            else:
                # No sub-sitemaps, parse main sitemap directly
                urls.update(self._parse_sitemap(self.config.SITEMAP_URL))
        except Exception:
            # If sitemap parsing fails, continue with critical URLs only
            pass
        
        return list(urls)

    def _parse_sitemap(self, sitemap_url: str) -> List[str]:
        urls: List[str] = []
        try:
            response = self.session.get(sitemap_url, timeout=15)
            root = ET.fromstring(response.content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            for url_elem in root.findall('.//ns:loc', namespace):
                if url_elem.text:
                    urls.append(url_elem.text)
        except Exception:
            pass
        return urls

    def _get_critical_urls(self) -> List[str]:
        """
        Returns list of critical JIIT pages that should always be scraped.
        
        These pages contain essential information about:
        - Admissions and programs
        - Placements and careers
        - Campus facilities
        - Academic departments
        
        Returns:
            List[str]: Full URLs of critical pages
        """
        paths = [
            "/", "/admission", "/admissions", "/btech", "/mtech", "/mba",
            "/placements", "/fee-structure", "/hostel", "/facilities",
            "/faculty", "/departments", "/research", "/about",
            "/departments/cse", "/departments/ece", "/departments/it",
            "/departments/mechanical", "/departments/civil", "/departments/biotechnology",
            "/campus-life", "/student-activities", "/infrastructure",
        ]
        return [urljoin(self.config.BASE_URL, p) for p in paths]

    def _scrape_page(self, url: str, force_refresh: bool = False) -> Optional[Document]:
        doc_id = hashlib.md5(url.encode()).hexdigest()
        cache_path = self.config.CACHE_DIR / f"{doc_id}.json"
        if not force_refresh and cache_path.exists():
            cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
            if datetime.now() - cache_time < timedelta(hours=self.config.CACHE_VALIDITY_HOURS):
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return Document(
                            id=data['id'], url=data['url'], title=data['title'],
                            content=data['content'], doc_type=data['doc_type'],
                            metadata=data['metadata'],
                            last_updated=datetime.fromisoformat(data['last_updated']) if data['last_updated'] else None
                        )
                except Exception:
                    pass
        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            if response.status_code != 200:
                return None
            if 'application/pdf' in response.headers.get('Content-Type', ''):
                return self._process_pdf(url, response.content)
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            title = soup.find('title')
            title_text = title.get_text().strip() if title else url.split('/')[-1]
            content = self._extract_content(soup)
            if not content or len(content) < 100:
                return None
            doc_type = self._classify_page(url, title_text, content)
            metadata: Dict[str, Any] = {'url': url, 'doc_type': doc_type}
            doc = Document(
                id=doc_id, url=url, title=title_text, content=content,
                doc_type=doc_type, metadata=metadata, last_updated=datetime.now()
            )
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(doc.to_dict(), f, indent=2)
            return doc
        except Exception:
            return None

    def _process_pdf(self, url: str, content: bytes) -> Optional[Document]:
        if not PDF_AVAILABLE:
            return None
        try:
            pdf_file = io.BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_file)
            text_parts: List[str] = []
            for page in reader.pages[:30]:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            if not text_parts:
                return None
            full_text = '\n\n'.join(text_parts)
            doc_id = hashlib.md5(url.encode()).hexdigest()
            title = url.split('/')[-1]
            return Document(
                id=doc_id, url=url, title=f"📄 {title}", content=full_text[:30000],
                doc_type='pdf', metadata={'page_count': len(reader.pages)},
                last_updated=datetime.now()
            )
        except Exception:
            return None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        main = soup.find('main') or soup.find('article') or soup.find(class_='content')
        if not main:
            main = soup.find('body')
        if not main:
            return ""
        text_parts: List[str] = []
        for element in main.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'td']):
            text = element.get_text(strip=True)
            if text and len(text) > 10:
                text_parts.append(text)
        content = '\n\n'.join(text_parts)
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n+', '\n\n', content)
        return content.strip()

    def _classify_page(self, url: str, title: str, content: str) -> str:
        url_lower = url.lower()
        title_lower = title.lower()
        classifiers = {
            'admission': ['admission', 'eligibility', 'apply', 'entrance'],
            'placement': ['placement', 'recruit', 'career', 'job'],
            'fee': ['fee', 'tuition', 'payment', 'cost'],
            'hostel': ['hostel', 'accommodation', 'residence'],
            'department': ['department', 'cse', 'ece', 'mechanical', 'civil'],
            'faculty': ['faculty', 'profile', 'dr.', 'professor'],
        }
        for doc_type, keywords in classifiers.items():
            if any(kw in url_lower or kw in title_lower for kw in keywords):
                return doc_type
        return 'general'


# ============================================================================
# VECTOR STORE
# ============================================================================

class VectorStore:
    def __init__(self, config: Config):
        self.config = config
        self.embedding_model: Optional[SentenceTransformer] = None
        self.index: Optional[Any] = None
        self.doc_ids: List[str] = []

    def _init_model(self) -> None:
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers required")
        if self.embedding_model is None:
            self.embedding_model = SentenceTransformer(self.config.EMBEDDING_MODEL)

    def build_index(self, documents: List[Document], progress_callback: Optional[Any] = None) -> None:
        self._init_model()
        if progress_callback:
            progress_callback("Generating embeddings...")
        texts = [f"{doc.title}\n\n{doc.content[:1500]}" for doc in documents]
        if self.embedding_model is None:
            return
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False, batch_size=32)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        self.doc_ids = [doc.id for doc in documents]
        self._save_index()
        if progress_callback:
            progress_callback(f"✅ Built FAISS index with {len(documents)} documents")

    def search(self, query: str, top_k: int = 15) -> List[Tuple[str, float]]:
        if self.index is None:
            self._load_index()
        if self.index is None:
            return []
        self._init_model()
        if self.embedding_model is None:
            return []
        query_embedding = self.embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        scores, indices = self.index.search(query_embedding, top_k)
        results: List[Tuple[str, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if 0 <= idx < len(self.doc_ids):
                results.append((self.doc_ids[idx], float(score)))
        return results

    def _save_index(self) -> None:
        if self.index is not None:
            faiss.write_index(self.index, str(self.config.FAISS_DIR / "index.faiss"))
            with open(self.config.FAISS_DIR / "doc_ids.pkl", 'wb') as f:
                pickle.dump(self.doc_ids, f)

    def _load_index(self) -> None:
        index_path = self.config.FAISS_DIR / "index.faiss"
        if index_path.exists():
            try:
                self.index = faiss.read_index(str(index_path))
                with open(self.config.FAISS_DIR / "doc_ids.pkl", 'rb') as f:
                    self.doc_ids = pickle.load(f)
            except Exception:
                self.index = None


# ============================================================================
# KEYWORD SEARCH
# ============================================================================

class KeywordSearch:
    def __init__(self, config: Config):
        self.config = config
        self.bm25: Optional[BM25Okapi] = None
        self.doc_ids: List[str] = []

    def build_index(self, documents: List[Document], progress_callback: Optional[Any] = None) -> None:
        corpus: List[List[str]] = []
        self.doc_ids = []
        for doc in documents:
            text = f"{doc.title} {doc.content}"
            tokens = self._tokenize(text)
            corpus.append(tokens)
            self.doc_ids.append(doc.id)
        self.bm25 = BM25Okapi(corpus)
        self._save_index()
        if progress_callback:
            progress_callback(f"✅ Built BM25 index with {len(documents)} documents")

    def search(self, query: str, top_k: int = 15) -> List[Tuple[str, float]]:
        if self.bm25 is None:
            self._load_index()
        if self.bm25 is None:
            return []
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:top_k]
        results: List[Tuple[str, float]] = []
        for idx in top_indices:
            if idx < len(self.doc_ids) and scores[idx] > 0:
                results.append((self.doc_ids[idx], float(scores[idx])))
        return results

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return [t for t in tokens if len(t) > 2]

    def _save_index(self) -> None:
        with open(self.config.BM25_DIR / "bm25_index.pkl", 'wb') as f:
            pickle.dump({'bm25': self.bm25, 'doc_ids': self.doc_ids}, f)

    def _load_index(self) -> None:
        path = self.config.BM25_DIR / "bm25_index.pkl"
        if path.exists():
            try:
                with open(path, 'rb') as f:
                    data = pickle.load(f)
                    self.bm25 = data['bm25']
                    self.doc_ids = data['doc_ids']
            except Exception:
                self.bm25 = None


# ============================================================================
# HYBRID SEARCH
# ============================================================================

class HybridSearch:
    def __init__(self, config: Config, vector_store: VectorStore,
                 keyword_search: KeywordSearch, documents: List[Document]):
        self.config = config
        self.vector_store = vector_store
        self.keyword_search = keyword_search
        self.documents = {doc.id: doc for doc in documents}

    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        if top_k is None:
            top_k = self.config.FINAL_TOP_K
        faiss_results = self.vector_store.search(query, self.config.FAISS_TOP_K)
        bm25_results = self.keyword_search.search(query, self.config.BM25_TOP_K)
        combined_scores = self._reciprocal_rank_fusion(faiss_results, bm25_results)
        top_doc_ids = sorted(combined_scores.keys(),
                             key=lambda x: combined_scores[x],
                             reverse=True)[:top_k]
        results: List[Dict[str, Any]] = []
        for doc_id in top_doc_ids:
            doc = self.documents.get(doc_id)
            if doc:
                results.append({
                    'document': doc, 'score': combined_scores[doc_id],
                    'url': doc.url, 'title': doc.title,
                    'excerpt': self._get_excerpt(doc, query)
                })
        return results

    def _reciprocal_rank_fusion(self, faiss_results: List[Tuple[str, float]],
                                 bm25_results: List[Tuple[str, float]], k: int = 60) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for rank, (doc_id, _) in enumerate(faiss_results, 1):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
        for rank, (doc_id, _) in enumerate(bm25_results, 1):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
        return scores

    def _get_excerpt(self, doc: Document, query: str, length: int = 400) -> str:
        content = doc.content.lower()
        query_terms = query.lower().split()
        best_pos = 0
        max_matches = 0
        for i in range(0, max(1, len(content) - length), 100):
            chunk = content[i:i+length]
            matches = sum(1 for term in query_terms if term in chunk)
            if matches > max_matches:
                max_matches = matches
                best_pos = i
        excerpt = doc.content[best_pos:best_pos+length]
        if best_pos > 0:
            excerpt = "..." + excerpt
        if best_pos + length < len(doc.content):
            excerpt = excerpt + "..."
        return excerpt.strip()


# ============================================================================
# RESPONSE GENERATOR
# ============================================================================

class ResponseGenerator:
    def __init__(self, config: Config):
        self.config = config
        self.client: Optional[Any] = None
        self.using_groq = False
        if GROQ_AVAILABLE and config.GROQ_API_KEY:
            try:
                self.client = Groq(api_key=config.GROQ_API_KEY)
                self.using_groq = True
            except Exception:
                pass
        if not self.client and OPENAI_AVAILABLE and config.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=config.OPENAI_API_KEY)
                self.using_groq = False
            except Exception:
                pass

    def generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        if not self.client:
            return self._generate_fallback_response(query, search_results)
        context = self._prepare_context(search_results)
        system_prompt = """You are an intelligent AI assistant for JIIT (Jaypee Institute of Information Technology).
Answer questions accurately using ONLY the provided context. Be helpful, detailed, and professional.
Always cite sources using [Source: URL] after relevant information.
Format responses with clear sections and bullet points for readability."""
        user_prompt = f"""Question: {query}

Context from JIIT official sources:
{context}

Provide a comprehensive answer with source citations."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.LLM_TEMPERATURE,
                max_tokens=self.config.LLM_MAX_TOKENS
            )
            answer = response.choices[0].message.content
            sources = self._format_sources(search_results)
            return f"{answer}\n\n{sources}"
        except Exception:
            return self._generate_fallback_response(query, search_results)

    def _prepare_context(self, search_results: List[Dict[str, Any]]) -> str:
        parts: List[str] = []
        for i, result in enumerate(search_results[:5], 1):
            doc = result['document']
            parts.append(f"""--- SOURCE {i} ---
Title: {doc.title}
Type: {doc.doc_type}
URL: {doc.url}
Content: {result['excerpt']}
""")
        return '\n'.join(parts)

    def _format_sources(self, search_results: List[Dict[str, Any]]) -> str:
        parts = ["---", "### 📚 **Official Sources:**", ""]
        for i, result in enumerate(search_results[:5], 1):
            doc = result['document']
            emoji = "📄" if doc.doc_type == 'pdf' else "🌐"
            parts.append(f"{i}. {emoji} **{doc.title}**")
            parts.append(f"   🔗 [{doc.url}]({doc.url})")
            parts.append("")
        return '\n'.join(parts)

    def _generate_fallback_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        if not search_results:
            return f"""### ℹ️ No Information Found
I couldn't find specific information about "{query}" in the JIIT database."""
        parts = [f"# 📚 {query}\n", "Based on official JIIT sources:\n"]
        for i, result in enumerate(search_results[:3], 1):
            doc = result['document']
            excerpt = result['excerpt']
            if len(excerpt) > 300:
                excerpt = excerpt[:300] + "..."
            parts.append(f"### {i}. {doc.title}")
            parts.append(f"\n{excerpt}\n")
            parts.append(f"📎 **Source**: [{doc.url}]({doc.url})\n")
            parts.append("---\n")
        parts.append(self._format_sources(search_results))
        return '\n'.join(parts)


# ============================================================================
# DOCUMENT MANAGER
# ============================================================================

class DocumentManager:
    def __init__(self, config: Config):
        self.config = config
        self.documents: Dict[str, Document] = {}
        self._load_documents()

    def save_documents(self, documents: List[Document]) -> None:
        self.documents = {doc.id: doc for doc in documents}
        docs_data = [doc.to_dict() for doc in documents]
        with open(self.config.DOCS_DIR / "documents.json", 'w', encoding='utf-8') as f:
            json.dump(docs_data, f, indent=2)

    def _load_documents(self) -> None:
        path = self.config.DOCS_DIR / "documents.json"
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    docs_data = json.load(f)
                documents = []
                for data in docs_data:
                    doc = Document(
                        id=data['id'], url=data['url'], title=data['title'],
                        content=data['content'], doc_type=data['doc_type'],
                        metadata=data['metadata'],
                        last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else None
                    )
                    documents.append(doc)
                self.documents = {doc.id: doc for doc in documents}
            except Exception:
                self.documents = {}

    def get_all_documents(self) -> List[Document]:
        return list(self.documents.values())


# ============================================================================
# MAIN CHATBOT SYSTEM
# ============================================================================

class JIITAdvancedChatbot:
    def __init__(self):
        self.config = Config()
        self.config.setup_directories()
        self.scraper = EnhancedWebScraper(self.config)
        self.doc_manager = DocumentManager(self.config)
        self.vector_store = VectorStore(self.config)
        self.keyword_search = KeywordSearch(self.config)
        self.hybrid_search: Optional[HybridSearch] = None
        self.response_generator = ResponseGenerator(self.config)
        self.initialized = False
        self.initialization_error: Optional[str] = None

    def initialize(self, force_rebuild: bool = False, status_callback: Optional[Any] = None) -> bool:
        try:
            documents = self.doc_manager.get_all_documents()
            if force_rebuild or not documents:
                if status_callback:
                    status_callback("📥 Building database from scratch...")
                success = self.update_database(force_refresh=True, status_callback=status_callback)
                if not success:
                    self.initialization_error = "Failed to scrape website"
                    return False
                documents = self.doc_manager.get_all_documents()
            if not documents:
                self.initialization_error = "No documents available"
                return False
            if status_callback:
                status_callback("🔧 Initializing search systems...")
            self.vector_store._load_index()
            self.keyword_search._load_index()
            if self.vector_store.index is None:
                if status_callback:
                    status_callback("Building FAISS index...")
                self.vector_store.build_index(documents, status_callback)
            if self.keyword_search.bm25 is None:
                if status_callback:
                    status_callback("Building BM25 index...")
                self.keyword_search.build_index(documents, status_callback)
            self.hybrid_search = HybridSearch(
                self.config, self.vector_store, self.keyword_search, documents
            )
            self.initialized = True
            if status_callback:
                status_callback(f"✅ System ready with {len(documents)} documents!")
            return True
        except Exception as e:
            self.initialization_error = str(e)
            if status_callback:
                status_callback(f"❌ Initialization error: {str(e)}")
            return False

    def update_database(self, force_refresh: bool = False, status_callback: Optional[Any] = None) -> bool:
        try:
            documents = self.scraper.scrape_website(force_refresh, status_callback)
            if not documents:
                if status_callback:
                    status_callback("⚠️ No documents scraped")
                return False
            self.doc_manager.save_documents(documents)
            if status_callback:
                status_callback("Building FAISS index...")
            self.vector_store.build_index(documents, progress_callback=status_callback)
            if status_callback:
                status_callback("Building BM25 index...")
            self.keyword_search.build_index(documents, progress_callback=status_callback)
            self.hybrid_search = HybridSearch(
                self.config, self.vector_store, self.keyword_search, documents
            )
            return True
        except Exception as e:
            if status_callback:
                status_callback(f"❌ Update error: {str(e)}")
            return False

    def query(self, question: str) -> str:
        if not self.initialized:
            if self.initialization_error:
                return f"❌ System not initialized: {self.initialization_error}"
            return "❌ System not initialized. Please wait for initialization to complete."
        if not question or not question.strip():
            return "Please ask a question about JIIT."
        try:
            if self.hybrid_search is None:
                return "❌ Search system not available"
            search_results = self.hybrid_search.search(question)
            if not search_results:
                return f"### ℹ️ No Information Found\n\nI couldn't find information about '{question}'."
            response = self.response_generator.generate_response(question, search_results)
            return response
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def display_typing_effect(text: str, placeholder, speed: int = 25) -> None:
    """Display text with typing effect"""
    displayed_text = ""
    words = re.findall(r'\S+|\s+', text)
    for word in words:
        displayed_text += word
        placeholder.markdown(displayed_text + "▌")
        if word.isspace():
            delay = 0.01
        else:
            delay = speed / 1000
        time.sleep(delay)
    placeholder.markdown(text)


# ============================================================================
# STREAMLIT UI - CLEANED (NO TOGGLE BUTTON)
# ============================================================================

def show() -> None:
    """Main Streamlit UI with sidebar always visible"""

    # Initialize session state
    if 'initialization_complete' not in st.session_state:
        st.session_state.initialization_complete = False
    if 'advanced_chatbot' not in st.session_state:
        st.session_state.advanced_chatbot = JIITAdvancedChatbot()
    if 'advanced_messages' not in st.session_state:
        st.session_state.advanced_messages = [{
            "role": "assistant",
            "content": "### 👋 Welcome to JIIT Advanced AI Assistant!\n\n**I can help you with:**\n- 📝 Admissions & Eligibility\n- 💰 Fee Structure\n- 💼 Placement Statistics\n- 🏠 Hostel & Campus Life"
        }]

    # CHATGPT-LIKE THEME CSS (cleaned, removed toggle CSS)
    st.markdown("""
    <style>
    /* Main App Background */
    }

    /* Main Content Area Margin */
    .main .block-container {
        padding-top: 2rem;
        padding-left: 5rem;
        max-width: 100%;
    }

    /* Chat Messages */
    .stChatMessage {
        background-color: transparent;
        border: none;
    }

    [data-testid="stChatMessageAvatarUser"] {
        background-color: #5436DA;
    }

    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: #19C37D;
    }

    /* Chat Input */
    .stChatInput input {
        background-color: #40414F;
        color: white;
        border: 1px solid #565869;
        border-radius: 12px;
        padding: 12px 16px;
    }

    .stChatInput input:focus {
        border-color: #8e8ea0;
        box-shadow: 0 0 0 1px #8e8ea0;
    }

    /* Sidebar Buttons */
    .stButton > button[kind="primary"] {
        background-color: transparent;
        border: 1px solid #565869;
        color: #ECECF1;
        width: 100%;
        text-align: left;
        border-radius: 8px;
        padding: 12px 16px;
        font-weight: 500;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #2A2B32;
        border-color: #8e8ea0;
    }

    .stButton > button[kind="tertiary"] {
        background: transparent;
        border: none;
        color: #ECECF1;
        text-align: left;
        padding: 10px 12px;
        width: 100%;
    }

    .stButton > button[kind="tertiary"]:hover {
        background-color: #2A2B32;
        border-radius: 6px;
    }

    /* Quick Action Buttons */
    .stButton > button[kind="secondary"] {
        background: #40414F;
        color: #ECECF1;
        border: 1px solid #565869;
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
    }

    .stButton > button[kind="secondary"]:hover {
        background: #4d4d4f;
    }
    </style>
    """, unsafe_allow_html=True)

    # SIDEBAR CONTENT (permanent)
    with st.sidebar:
        if st.button("➕ New chat", key="new_chat_btn", type="primary"):
            st.session_state.advanced_messages = [{
                "role": "assistant",
                "content": "Chat cleared. How can I help you today?"
            }]
            st.rerun()

        st.markdown("---")

        st.caption("📅 Today")
        st.markdown("📄 Admission Requirements")
        st.markdown("💰 B.Tech Fee Structure")
        st.markdown("📊 Placement Statistics")

        st.markdown("<br>" * 2, unsafe_allow_html=True)

        st.caption("🛠️ Tools")

        col1, col2 = st.columns([1, 9])
        with col1:
            st.markdown("🔄")
        with col2:
            if st.button("Update Database", key="update_db_btn", type="tertiary",
                         disabled=not st.session_state.initialization_complete):
                with st.spinner("Updating database..."):
                    success = st.session_state.advanced_chatbot.update_database(force_refresh=True)
                    if success:
                        st.success("✅ Database updated!")
                        st.session_state.advanced_chatbot.initialize(force_rebuild=False)
                    else:
                        st.error("❌ Update failed")
                st.rerun()

        col1, col2 = st.columns([1, 9])
        with col1:
            st.markdown("⚡")
        with col2:
            if st.button("Force Rebuild", key="rebuild_db_btn", type="tertiary"):
                st.session_state.initialization_complete = False
                with st.spinner("Rebuilding database..."):
                    st.session_state.advanced_chatbot.initialize(force_rebuild=True)
                    st.session_state.initialization_complete = True
                st.success("✅ Rebuild complete!")
                st.rerun()

        col1, col2 = st.columns([1, 9])
        with col1:
            st.markdown("🗑️")
        with col2:
            if st.button("Clear Chat", key="clear_chat_btn", type="tertiary"):
                st.session_state.advanced_messages = [{
                    "role": "assistant",
                    "content": "Chat cleared. How can I help you?"
                }]
                st.rerun()

        st.markdown("---")
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown("👤")
        with col2:
            st.markdown("**Your Profile**")

    # MAIN CONTENT
    st.markdown("<h2 style='text-align: center;'>🎓 JIIT AI Assistant</h2>",
                unsafe_allow_html=True)

    # Initialize System
    if not st.session_state.initialization_complete:
        with st.spinner("🚀 Initializing AI system... (2-3 minutes)"):
            success = st.session_state.advanced_chatbot.initialize()
            if success:
                st.session_state.initialization_complete = True
                st.rerun()
            else:
                st.error(f"❌ Initialization failed: {st.session_state.advanced_chatbot.initialization_error}")
                st.info("💡 Click 'Force Rebuild' in the sidebar.")
                st.stop()

    # Display Chat History
    for message in st.session_state.advanced_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Quick Action Buttons
    if len(st.session_state.advanced_messages) == 1:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        if col1.button("📝 Admission", key="quick_admission", type="secondary", use_container_width=True):
            st.session_state.advanced_messages.append({
                "role": "user",
                "content": "What is the admission process for B.Tech?"
            })
            st.rerun()

        if col2.button("💰 Fees", key="quick_fees", type="secondary", use_container_width=True):
            st.session_state.advanced_messages.append({
                "role": "user",
                "content": "What is the fee structure for B.Tech?"
            })
            st.rerun()

        if col3.button("📊 Placements", key="quick_placements", type="secondary", use_container_width=True):
            st.session_state.advanced_messages.append({
                "role": "user",
                "content": "Tell me about placement statistics"
            })
            st.rerun()

        if col4.button("🏫 Campus", key="quick_campus", type="secondary", use_container_width=True):
            st.session_state.advanced_messages.append({
                "role": "user",
                "content": "Tell me about campus life and facilities"
            })
            st.rerun()

    # Chat Input
    if prompt := st.chat_input("Ask anything about JIIT..."):
        st.session_state.advanced_messages.append({"role": "user", "content": prompt})
        st.rerun()

    # Generate Response
    if (st.session_state.advanced_messages and
            st.session_state.advanced_messages[-1]["role"] == "user"):

        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                response = st.session_state.advanced_chatbot.query(
                    st.session_state.advanced_messages[-1]["content"]
                )
                placeholder = st.empty()
                display_typing_effect(response, placeholder, speed=20)

        st.session_state.advanced_messages.append({
            "role": "assistant",
            "content": response
        })


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main() -> None:
    """Main entry point - sidebar state already initialized at top"""
    show()


if __name__ == "__main__":
    main()