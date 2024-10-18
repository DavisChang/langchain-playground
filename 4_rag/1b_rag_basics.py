import os

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings.ollama import OllamaEmbeddings

# Define the persistent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
persistent_directory = os.path.join(current_dir, "db", "chroma_db")

# Define the embedding model

## OpenAIEmbeddings
# embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

## OllamaEmbeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")


# Load the existing vector store with the embedding function
db = Chroma(persist_directory=persistent_directory, embedding_function=embeddings)

# Define the user's question
query = "Who is Odysseus' wife?"

# Retrieve relevant documents based on the query
# retriever = db.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={"k": 3, "score_threshold": 0.2},  # top 3
# )
# relevant_docs = retriever.invoke(query)

# Display the relevant results with metadata
# print("\n--- Relevant Documents ---")
# for i, doc in enumerate(relevant_docs, 1):
#     print(f"Document {i}:\n{doc.page_content}\n")
#     if doc.metadata:
#         print(f"Source: {doc.metadata.get('source', 'Unknown')}\n")

## OllamaEmbeddings
relevant_docs = db.similarity_search_with_score(query, k=3)
context_text = "\n\n---\n\n".join(
    [
        f"{index+1}. page_content: {doc.page_content} \n\nScore: {_score} \nSource: {doc.metadata['source']}"
        for index, (doc, _score), in enumerate(relevant_docs)
    ]
)
print("\n--- Relevant context_text ---")
print(context_text)
