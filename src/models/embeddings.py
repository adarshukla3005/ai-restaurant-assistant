import streamlit as st
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
import chromadb
import uuid

# Define the embedding model name
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

@st.cache_resource
def load_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL_NAME)

def get_embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    ) 

# Download required NLTK resources
@st.cache_resource
def download_nltk_resources():
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
    except Exception as e:
        st.warning(f"Error downloading NLTK resources: {e}")

# Text preprocessing function
def preprocess_text(text, remove_stopwords=True, stemming=False, lemmatization=True):
    """
    Preprocess text by cleaning, normalizing, and optionally removing stopwords and applying stemming/lemmatization
    
    Args:
        text (str): Input text to preprocess
        remove_stopwords (bool): Whether to remove stopwords
        stemming (bool): Whether to apply stemming
        lemmatization (bool): Whether to apply lemmatization
        
    Returns:
        str: Preprocessed text
    """
    # Download NLTK resources if needed
    download_nltk_resources()
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and digits
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    # tokens = [token for token in word_tokenize(text) if len(token) >= 5]
    
    # Remove stopwords if requested
    if remove_stopwords:
        stop_words = set(stopwords.words('english'))
        tokens = [token for token in tokens if token not in stop_words]
    
    # Apply stemming if requested
    if stemming:
        stemmer = PorterStemmer()
        tokens = [stemmer.stem(token) for token in tokens]
    
    # Apply lemmatization if requested
    if lemmatization:
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Join tokens back into text
    return ' '.join(tokens)

# Initialize ChromaDB client and collection
@st.cache_resource
def get_vector_store(collection_name="documents"):
    """
    Initialize or get ChromaDB client and collection
    
    Args:
        collection_name (str): Name of the collection to use
        
    Returns:
        collection: ChromaDB collection
    """
    client = chromadb.Client()
    embedding_function = get_embedding_function()
    
    try:
        collection = client.get_collection(name=collection_name)
    except:
        collection = client.create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )
    
    return collection

def index_documents(documents, metadatas=None, collection_name="documents", preprocess=True):
    """
    Index documents in the vector store
    
    Args:
        documents (list): List of document texts
        metadatas (list, optional): List of metadata dictionaries for each document
        collection_name (str): Name of the collection to use
        preprocess (bool): Whether to preprocess the documents
        
    Returns:
        list: List of document IDs
    """
    collection = get_vector_store(collection_name)
    
    # Preprocess documents if requested
    if preprocess:
        documents = [preprocess_text(doc) for doc in documents]
    
    # Generate IDs if not provided
    ids = [str(uuid.uuid4()) for _ in range(len(documents))]
    
    # Add documents to the collection
    collection.add(
        documents=documents,
        metadatas=metadatas if metadatas else [{}] * len(documents),
        ids=ids
    )
    
    return ids

def search_documents(query, collection_name="documents", preprocess=True, n_results=5):
    """
    Search for documents similar to the query
    
    Args:
        query (str): Search query
        collection_name (str): Name of the collection to search
        preprocess (bool): Whether to preprocess the query
        n_results (int): Number of results to return
        
    Returns:
        dict: Search results including documents, metadatas, and scores
    """
    collection = get_vector_store(collection_name)
    
    # Preprocess query if requested
    if preprocess:
        query = preprocess_text(query)
    
    # Search for similar documents
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    return results 