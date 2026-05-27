import os
import glob #for file handling for reading
import logging
from dotenv import load_dotenv

#document loaders and splitters
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger("indexer")

def index_docs():
    '''
    Reads the PDFs, chunks them, upload them to Azure AI Search
    '''

    #defines paths, we look for all pdfs in the "documents" folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(current_dir, "../../backend/data")

    #check the environment variables for Azure Search
    logger.info("="*60)
    logger.info("Environment Configuration Check: ")
    logger.info(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    logger.info(f"AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')}")
    logger.info(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT: {os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {os.getenv('AZURE_SEARCH_INDEX_NAME')}")
    logger.info("="*60)

    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX_NAME"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please check your .env file and ensure all necessary variables are set before running the script.")
        return
    
    #initialize the embedding model
    try:
        logger.info("Initializing Azure OpenAI Embeddings...")
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01-preview"),
        )
        logger.info("Azure OpenAI Embeddings initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Azure OpenAI Embeddings: {str(e)}")
        logger.error("Please check your Azure OpenAI deployment and endpoint.")
        return
    
     #initialize the Azure Search vector store
    try:
        logger.info("Initializing Azure Search Vector Store...")
        vector_store = AzureSearch(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            embedding_function=embeddings.embed_query,
        )
        logger.info(f"Azure Search Vector Store initialized successfully : {os.getenv('AZURE_SEARCH_INDEX_NAME')}")
    except Exception as e:
        logger.error(f"Error initializing Azure Search Vector Store: {str(e)}")
        logger.error("Please check your Azure Search configuration.")
        return
    
    # Find all PDF files in the data folder
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {data_folder}. Please add documents to index.")
    
    logger.info(f"Found {len(pdf_files)} PDF files to process: {[os.path.basename(f) for f in pdf_files]}")
    
    all_splits = []

    for pdf_path in pdf_files:
        try:
            logger.info(f"Processing document: {os.path.basename(pdf_path)}...")
            loader = PyPDFLoader(pdf_path)
            raw_docs = loader.load()

            # chunking strategy
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(raw_docs)

            for split in splits:
                split.metadata["source"] = os.path.basename(pdf_path)

            all_splits.extend(splits)
            logger.info(f"Document processed and split into {len(splits)} chunks.")
        except Exception as e:
            logger.error(f"Error processing document {os.path.basename(pdf_path)}: {str(e)}") 

    if all_splits:
        logger.info(f"Uploading {len(all_splits)} chunks to Azure Search '{os.getenv('AZURE_SEARCH_INDEX_NAME')}'.")
        try:
            vector_store.add_documents(documents=all_splits)
            logger.info("="*60)
            logger.info("Document indexing completed successfully.")
            logger.info(f"Indexed {len(all_splits)} chunks from {len(pdf_files)}")
            logger.info("="*60)
        except Exception as e:
            logger.error(f"Error uploading chunks to Azure Search: {str(e)}")
            logger.error("Please check your Azure Search configuration and try again.")
    else:
        logger.warning("No documents were processed.")
    
if __name__ == "__main__":
    index_docs()