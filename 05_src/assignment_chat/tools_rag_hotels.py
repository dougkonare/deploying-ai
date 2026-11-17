
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain.tools import tool
from dotenv import load_dotenv
from langchain_openai import embeddings
from IPython.display import display, Markdown
from tqdm import tqdm
import json
from pydantic import BaseModel, Field

import chromadb
from langchain_community.document_loaders import CSVLoader
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from utils.clients import get_client
from pathlib import Path

sys.path.append('05_src/')



# _logs = get_logger(__name__)
load_dotenv(".env")
load_dotenv(".secrets")

client = get_client(use_gateway=True)
chroma_client = chromadb.Client()

MODEL = os.getenv('MODEL')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')
DOC_DIR = "05_src/assignment_chat/"
COLLECTION_NAME = "hotel_reviews"
CHROMA_URL = os.getenv("CHROMA_URL")

print(os.getenv("OPENAI_API_KEY"))


def load_full_source():

    DATA_FILE = Path(__file__).resolve().parent / "Hotel_Reviews.csv"
    df = pd.read_csv(DATA_FILE)

    df['city'] = df['Hotel_Address'].str.split().str[-2]
    df['country'] = df['Hotel_Address'].str.split().str[-1]
    df = df[df['country'] != 'Kingdom']
    df = df[df['country'] != 'Austria'] 
    df = df.drop(columns=['lat', 'lng', 'city', 'country'])
    # print(df['country'].unique())
    df.to_csv(Path(__file__).resolve().parent / 'hotels_reviews_partial.csv.gz', index=False, compression='gzip')
    
    # print(df.describe(include='all'))

# load_full_source()

def load_partial_source():
    # df = pd.read_csv("../../05_src/assignment_chat/Hotel_Reviews_selected_countries.csv.gz", compression="gzip")
    DATA_FILE = Path(__file__).resolve().parent / "hotels_reviews_partial.csv.gz"
    df = pd.read_csv(DATA_FILE, compression="gzip")
  
    # df.describe(include='all')

    hotel_source = df.sample(n=500)
    # hotel_source = df
    hotel_source['city'] = hotel_source['Hotel_Address'].str.split().str[-2]
    hotel_source['country'] = hotel_source['Hotel_Address'].str.split().str[-1]
    hotel_source['days_since_review'] = (pd.to_datetime('today') - pd.to_datetime(hotel_source['Review_Date'])).dt.days
    hotel_source['combined_review'] = hotel_source['Positive_Review'].str.cat(hotel_source['Negative_Review'], sep=' ', na_rep='')
    # hotel_source = hotel_source.drop(columns=['lat', 'lng'])
    
    # print(hotel_source.describe(include='all'))

    hotel_reviews_list = hotel_source['combined_review'].tolist()
    
    return hotel_source, hotel_reviews_list

# load_partial_source()

def setup_collection(chroma_url:str,
                     collection_name: str):
    # chroma_client = chromadb.HttpClient(host=chroma_url)
    # chroma_client = chromadb.PersistentClient(path="./my_chroma_db")

    DATA_FILE = Path(__file__).resolve().parent / "my_chroma_db"
    chroma_client = chromadb.PersistentClient(path=DATA_FILE)

    
    collections = chroma_client.list_collections()
    if collection_name in [col.name for col in collections]:
        chroma_client.delete_collection(name=collection_name)

    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function = OpenAIEmbeddingFunction(
                api_key="any value",
                api_base="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
                api_type="openai",
                model_name=EMBEDDING_MODEL,
                default_headers={
                    "x-api-key": os.getenv("API_GATEWAY_KEY")
                }
            )
    )
    return collection

def return_collection(chroma_url:str, collection_name:str):

    DATA_FILE = Path(__file__).resolve().parent / "my_chroma_db"
    chroma_client = chromadb.PersistentClient(path=DATA_FILE)
    # chroma_client = chromadb.PersistentClient(path="./my_chroma_db")
    collections = chroma_client.list_collections()

    if collection_name in [col.name for col in collections]:
        collection = chroma_client.get_collection(name=collection_name)
        return collection
    else:
        print(COLLECTION_NAME)
        hotel_source, hotel_review_list = load_partial_source()
        embeddings = create_and_load_embedding(hotel_review_list)
        ids = [f"id{i}" for i in range(len(hotel_review_list))]
        collection = load_embeddings_to_db(embedding_inputs = embeddings,
                                metadata_inputs = hotel_source.to_dict(orient="records"),
                                documents_inputs = hotel_review_list,
                                id_inputs = ids,
                                collection_name_input = COLLECTION_NAME,
                                chroma_url=CHROMA_URL)
        if collection:
            return collection
        else:
            raise ValueError(f"Collection '{collection_name}' does not exist.")

def load_embeddings_to_db(embedding_inputs:list[dict],
                          metadata_inputs:list[dict],
                          documents_inputs:list[str],
                          id_inputs:list[str],
                          collection_name_input:str,
                          chroma_url:str,
                          ):
    collection = setup_collection(chroma_url=chroma_url, collection_name=collection_name_input)

    collection.add(embeddings = embedding_inputs,
                metadatas = metadata_inputs,
                documents = documents_inputs, 
                ids = id_inputs)
    return collection

def get_context_data(query: str, collection: chromadb.api.models.Collection, top_n: int,
                     where_document: dict = None, where: dict = None):
    kwargs = dict(query_texts=[query], n_results=top_n)
    if where_document:
        kwargs['where_document'] = where_document
    if where:
        kwargs['where'] = where
    results = collection.query(**kwargs)
    context_data = []
    for idx in range(len(results['ids'][0])):
        details = dict(results['metadatas'][0][idx])
        details['text'] = results['documents'][0][idx]
        context_data.append(details)
    return context_data

def generate_prompt(query: str, context_data: list):
    top_n = len(context_data)
    prompt = f'Given a query, provide a detailed response using the context from relevant Hotel reviews in Europe. The context will contain references to {top_n} hotel reviews.\n\n'
    prompt += 'The score is numeric and its scale is from 0 to 10, with 10 being the highest rating. Any hotel with a score greater than 8.0 is considered a must-visit; hotel with a score greater than 6.5 is good.\n\n'
    prompt += f'<query>{query}</query>\n\n'
    prompt += '<context>\n'
    for k, context in enumerate(context_data):
        prompt += f'<hotel {k}>\n'
        prompt += f"- Hotel Name: {context.get('Hotel_Name', 'N/A')}\n"
        prompt += f"- City: {context.get('city', 'N/A')}\n"
        prompt += f"- Country: {context.get('country', 'N/A')}\n"
        prompt += f"- Score: {context.get('Average_Score', 'N/A')}\n"
        prompt += f"- Total number of reviews: {context.get('Total_Number_of_Reviews', 'N/A')}\n"
        prompt += f"- Total number of positive reviews: {context.get('Review_Total_Positive_Word_Counts', 'N/A')}\n"
        prompt += f"- Total number of negative reviews: {context.get('Review_Total_Negative_Word_Counts', 'N/A')}\n"
        prompt += f'</hotel {k}>\n\n'
    prompt += '</context>\n\n'
    prompt += '\nBased on the context and nothing else, provide a detailed response to the query. In your response disregard the negative feedbacks.'
    return prompt

def generate_response(query: str, collection: chromadb.api.models.Collection, top_n: int = 3,
                      where_document: dict = None, where: dict = None):
    context_data = get_context_data(query, collection, top_n,
                                    where_document=where_document, where=where)
    prompt = generate_prompt(query, context_data)
    response = client.responses.create(
        model=MODEL,
        instructions='You are a joyfull travel agent that provides information based on TripAdvisor reviews.',
        input=[{'role': 'user', 'content': prompt}],
        max_output_tokens=500,
        temperature=1.0
    )
    return response.output_text

def generate_pydantic_response(query: str, collection: chromadb.api.models.Collection, top_n: int = 3,
                               where_document: dict = None, where: dict = None):
    context_data = get_context_data(query, collection, top_n)
    recommendations = []
    if not context_data:
        return recommendations
    for item in context_data:

        rec = HotelReviewData(
            name=item.get('Hotel_Name', 'N/A'),
            location=f"{item.get('city', '')}, {item.get('country', '')}",
            review=item.get('combined_review', 'N/A'),
            score=item.get('Reviewer_Score', 'N/A'))
        recommendations.append(rec)
    return recommendations

def create_and_load_embedding(hotel_reviews_list:list[str]):
    response_with_embeddings = client.embeddings.create(
    input = hotel_reviews_list,
    model = "text-embedding-3-small"
    )
    embeddings = [item.embedding for item in response_with_embeddings.data]

    return embeddings

class HotelReviewData(BaseModel):
    """Structured hotel review data response."""
    name: str = Field(..., description="The name of the hotel.")
    location: str = Field(..., description="The location of the hotel. The location is a city and country. For example, 'Paris, France'.")
    review: str = Field(..., description="A portion of the hotel review that is relevant to the user query.")
    score: float = Field(None, description="The rating of the hotel. The score is numeric and its scale is from 0 to 10, with 10 being the highest rating. Any hotel with a score greater than 8.0 is considered a must-visit; hotel with a score greater than 6.5 is good.")

@tool
def query_hotels(query: str, top_n: int = 3) -> list[HotelReviewData]:
    """This tool searches for hotels based on user query and returns relevant information."""
    
    collection = return_collection(chroma_url=CHROMA_URL, collection_name=COLLECTION_NAME)
    
    hotel_recommendations = generate_pydantic_response(
        query, collection, top_n,
        # where_document = {'$contains': 'internet'},
        # where={'$and': [{'score': {'$gt': 5.0}}, {'days_since_review': {'$gte': 9000}}]},
    )
    return hotel_recommendations


# returned_collection = return_collection(chroma_url=CHROMA_URL, collection_name=COLLECTION_NAME)
# rag_response = query_hotels.invoke({"query": "What are the lowest rated hotels to visit in Europe?", "top_n": 3})
# print(rag_response)






