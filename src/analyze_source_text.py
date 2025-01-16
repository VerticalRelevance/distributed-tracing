import os
from dotenv import load_dotenv, find_dotenv
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI

_ = load_dotenv(find_dotenv())  # read local .env file

# Step 1: Load the Python script file
file_path = "/Users/scaswell/VerticalRelevance/Projects/SRE/AWS_DataMeshFoundations/src/ops/post_setup.py"
with open(file_path, "r") as file:
    file_content = file.readlines()

print("file content:")
print("".join(file_content))

# Step 4: Perform a search query
# query = "Find all functions that use an if statement."
# query = "What are the code snippets in your context?"
query = f"""
In the source code below delimited by triple backticks, find all functions containing an 'if' statement. Include the line number of the function in response.
```
{"".join(file_content)}
```
"""

print(query)

# Step 5: Use an LLM to summarize the search results
llm_model = "gpt-4o-mini"
llm = ChatOpenAI(model=llm_model)
qa_chain = load_qa_chain(llm, chain_type="stuff")
answer = qa_chain.run(input_documents=[], question=query)

# Print the answer
print("Answer:", answer)
