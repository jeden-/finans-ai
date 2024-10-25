import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
from models.transaction import Transaction
import pandas as pd
import json

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.transaction_model = Transaction()
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.create_collection(
            name="transactions",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )
        self.update_transaction_embeddings()

    def update_transaction_embeddings(self):
        """Update the vector store with all transactions."""
        try:
            transactions = self.transaction_model.get_all_transactions()
            if not transactions:
                return

            # Convert transactions to documents
            docs = []
            metadatas = []
            ids = []

            for tx in transactions:
                # Create a natural language description
                doc = (
                    f"A {tx['type']} transaction of {tx['amount']} PLN in category '{tx['category']}' "
                    f"for '{tx['description']}' on {tx['created_at']}. "
                    f"This is a {tx['cycle']} transaction."
                )
                docs.append(doc)
                metadatas.append({
                    "id": str(tx["id"]),
                    "type": tx["type"],
                    "category": tx["category"],
                    "amount": str(tx["amount"]),
                    "cycle": tx["cycle"]
                })
                ids.append(str(tx["id"]))

            # Add documents to collection
            self.collection.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Updated embeddings for {len(docs)} transactions")

        except Exception as e:
            logger.error(f"Error updating transaction embeddings: {str(e)}")

    def get_relevant_context(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Get relevant transactions for a given query."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            relevant_transactions = []
            for i in range(len(results['ids'][0])):
                relevant_transactions.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })

            return relevant_transactions

        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return []

    def prepare_chat_context(self, query: str) -> str:
        """Prepare context for the chat based on the query and transaction history."""
        relevant_txs = self.get_relevant_context(query)
        
        context = "Based on the transaction history:\n\n"
        for tx in relevant_txs:
            context += f"- {tx['text']}\n"
            
        return context
