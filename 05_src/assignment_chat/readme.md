# **ASSIGNMENT 2**

This assignemt create a conversational chatbot that act as a travel agent. THe user can ask hotel information, attraction, and temperature on a specific destination (city).

The assignment deliver on the specifications of '.02_activities/assignment_2.md'


the agent interact with the following tools:

Service 1: Sematic query
The source data is hotel reviews in a few European cities (Paris, Amsterdam, Barcelona, Milan)
https://www.kaggle.com/datasets/jiashenliu/515k-hotel-reviews-data-in-europe.
For the purpose of the demonstration, I reduced the dataset so that the compress file is ~20 MB. I removed hotel references in Austria and UK.
I saved the embeddings with lookup information in persistent chroma db file located in: './05_src/assignment_chat/my_chroma_db

When the chat starts, during the service call for the hotel information, if it does not find the chroma db, it will create one with a subset of the dataset.

Service 2: API call to Weatherstack
When the user ask a question on the temperature, an API call is made to Weatherstack: https://app.apilayer.com/api-details/weatherstack

Service 3: web search
When the users asks for attractions in the destination city, an web search is perform with Tavily: https://docs.tavily.com/documentation/api-reference/endpoint/search


The results are reformated to respond using the voice and tone of Omer Simpson.
Guardrail are created to prevent the chat from answering specific topics.