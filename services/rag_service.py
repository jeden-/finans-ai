import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
from models.transaction import Transaction
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        """Initialize the RAG service with ChromaDB."""
        try:
            # Initialize ChromaDB with persistence
            self.chroma_client = chromadb.PersistentClient(path=".chromadb")
            
            # Create or get the collection for transactions
            self.collection = self.chroma_client.get_or_create_collection(
                name="transactions",
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
            
            # Initial update of embeddings
            self.update_transaction_embeddings()
        except Exception as e:
            logger.error(f"Error initializing RAG service: {str(e)}")
            raise

    def prepare_chat_context(self, query: str, k: int = 5) -> str:
        """Get relevant transaction context for a given query."""
        try:
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            if not results or not results['documents']:
                return "No relevant transaction history found."
            
            # Format the results into a readable context
            context_parts = []
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                date = datetime.fromtimestamp(metadata['timestamp']).strftime('%Y-%m-%d')
                amount = f"{metadata['amount']:.2f} PLN"
                context_parts.append(f"{i+1}. [{date}] {doc} ({amount})")
            
            return "Relevant transactions:\n" + "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error preparing chat context: {str(e)}")
            return "Error retrieving transaction context."

    def update_transaction_embeddings(self) -> bool:
        """Update the transaction embeddings in ChromaDB."""
        try:
            # Get all transactions
            transaction_model = Transaction()
            transactions = transaction_model.get_all_transactions()
            
            if not transactions:
                logger.info("No transactions found to update embeddings.")
                return True
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(transactions)
            
            # Prepare documents and metadata
            documents = []
            ids = []
            metadatas = []
            
            for _, row in df.iterrows():
                # Create a descriptive text for each transaction
                doc = f"{row['description']} ({row['type']}, {row['category']})"
                
                # Prepare metadata
                metadata = {
                    "type": row['type'],
                    "category": row['category'],
                    "amount": float(row['amount']),
                    "timestamp": int(pd.to_datetime(row['created_at']).timestamp())
                }
                
                documents.append(doc)
                ids.append(str(row['id']))
                metadatas.append(metadata)
            
            # Clear existing embeddings and add new ones
            self.collection.delete()
            self.collection = self.chroma_client.get_or_create_collection(
                name="transactions",
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
            
            # Add documents in batches
            if documents:
                self.collection.add(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )
            
            logger.info(f"Successfully updated embeddings for {len(documents)} transactions")
            return True
            
        except Exception as e:
            logger.error(f"Error updating transaction embeddings: {str(e)}")
            return False
