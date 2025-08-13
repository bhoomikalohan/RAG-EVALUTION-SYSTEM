import google.generativeai as genai  
#from google.genai import types
from qdrant_client import QdrantClient, models
import json
import wave
from typing import List
import uuid
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GENAI_KEY")
client = genai.GenerativeModel("gemini-1.5-flash")


class HybridSearcher:
    DENSE_MODEL = "BAAI/bge-base-en-v1.5"
    SPARSE_MODEL = "prithivida/Splade_PP_en_v1"
    options = {"cache_dir": "./models"}
    bp_prompt = """
    - format - KEYWORD ['Website' 'Document' 'Video' 'Multiple']
    - district - TEXT
    - year - DATETIME
    - continent - TEXT ['Asia' 'Africa' 'Multiple' 'South America' 'Australia' 'Europe' 'North America' nan]
    - brief_description - TEXT
    - state - TEXT ['UTTARAKHAND', 'PAN-INDIA', 'UTTAR PRADESH', 'BIHAR', 'PUDUCHERRY', 'ARUNACHAL PRADESH', 'ASSAM', 'THE DADRA AND NAGAR HAVELI AND DAMAN AND DIU', 'GUJARAT', 'SIKKIM', 'HIMACHAL PRADESH', 'JHARKHAND', 'TRIPURA', 'JAMMU & KASHMIR', 'MIZORAM', 'HARYANA', 'PUNJAB', 'GOA', 'ODISHA', 'LAKSHADWEEP', 'KARNATAKA', 'NAGALAND', 'MULTIPLE STATES', 'KERALA', 'MANIPUR', 'ANDHRA PRADESH', 'MAHARASHTRA', 'TELANGANA', 'DELHI', 'MEGHALAYA', 'LADAKH', 'RAJASTHAN', 'LEH', 'CHANDIGARH', 'CHHATTISGARH', 'TAMIL NADU', 'MADHYA PRADESH', 'WEST BENGAL', 'ANDAMAN AND NICOBAR ISLANDS']
    - name_of_best_practice - TEXT
    - village_city - TEXT
    - nation - KEYWORD ['India' 'International']
    - country - TEXT
    - sector - KEYWORD
    - panchayat - TEXT
    - topic - TEXT
    - source - TEXT
    - doc_id - UUID
    """

    pol_prompt = """
    - parent_organisation_type - TEXT ['Department' 'Ministry']
    - state_name - TEXT ['ANDAMAN AND NICOBAR ISLANDS', 'ANDHRA PRADESH', 'TELANGANA',
       'ARUNACHAL PRADESH', 'ASSAM', 'BIHAR', 'CHHATTISGARH', 'DELHI',
       'GOA', 'GUJARAT', 'HARYANA', 'HIMACHAL PRADESH',
       'JAMMU AND KASHMIR', 'JHARKHAND', 'KARNATAKA', 'KERALA', 'LADAKH',
       'MADHYA PRADESH', 'MAHARASHTRA', 'MANIPUR', 'MEGHALAYA', 'MIZORAM',
       nan, 'NAGALAND', 'ODISHA', 'PUDUCHERRY', 'PUNJAB', 'RAJASTHAN',
       'SIKKIM', 'TAMIL NADU',
       'THE DADRA AND NAGAR HAVELI AND DAMAN AND DIU', 'TRIPURA',
       'UTTAR PRADESH', 'UTTARAKHAND', 'WEST BENGAL']
    - sdg_goal - TEXT ['GOAL 15: Life on Land' 'GOAL 14: Life Below Water' 'GOAL 2: Zero Hunger' 'GOAL 1: No Poverty' 'GOAL 9: Industry, Innovation and Infrastructure' 'GOAL 8: Decent Work and Economic Growth' 'GOAL 12: Responsible Consumption and Production' 'GOAL 7: Affordable and Clean Energy' 'GOAL 4: Quality Education' 'GOAL 6: Clean Water and Sanitation' 'GOAL 17: Partnerships to achieve the Goal' 'GOAL 13: Climate Action' 'GOAL 11: Sustainable Cities and Communities' 'GOAL 3: Good Health and Well-being' 'GOAL 10: Reduced Inequality' 'GOAL 5: Gender Equality']
    - description - TEXT
    - organisation_name - TEXT
    - organisation_type - TEXT ['Department' 'Organization' 'Ministry']
    - year_mm_yyyy - DATETIME
    - institution_type - TEXT ['State government department' 'Think-tanks' 'Govt research institute' 'Multilaterals' 'Central Government Ministry' 'Autonomous Bodies' 'Central government ministry' 'Academic']
    - geo_level - TEXT ['State' 'National' 'Global'] 
    - content_type - TEXT  ['Act' 'Scheme' 'Guidelines and Action Plans' 'Act (Amendment)' 'Implementation Agency' 'Research Report' 'Programme' 'Rules/Regulations' 'Bill' 'Toolkits/Modules' 'Policy' 'Rules/regulations']
    - language - TEXT ['English' 'Telugu' 'English, Hindi' 'Gujarati' 'Hindi' 'Kannada' 'Marathi' 'English, Marathi' 'Bengali']    
    - source - TEXT
    - beneficiary_type - TEXT
    - doc_id - UUID
    - sector - TEXT
    - district_name - TEXT
    - file_format - KEYWORD ['PDF' 'HTML']
    - content_name - TEXT
    - parent_organisation_name - TEXT
    """

    bp_columns = [
    "id",
    "name_of_best_practice",
    "brief_description",
    "source",
    "Link",
    "format",
    "sector",
    "topic",
    "nation",
    "country",
    "continent",
    "state", 
    "district",
    "panchayat",
    "village_city",
    "year",
    "individual_case",
    "doc_id"
]
    pol_columns = [
    "id",
    "Content Name ",
    "content_type",
    "geo_level",
    "institution_type",
    "state_name",
    "district_name",
    "organisation_name",
    "organisation_type",
    "parent_organisation_name",
    "parent_organisation_type",
    "sector",
    "sdg_goal",
    "beneficiary_type",
    "source",
    "year_mm_yyyy",
    "description",
    "hyperlink",
    "file_format",
    "language",
    "doc_id"
]


    def __init__(self):
        self.qdrant_client = QdrantClient()
        self.client = genai
        self.active_chat = None
        self.chat_history = {}  # Store chat instances by ID

        search_function = {
            "name": "search_documents",
            "description": "Searches for documents in database based on the user's intent and the collection to search in. Call this function if the user wants to search for practices, policies, acts etc or wants specific statistics. Also use this if user wants to filter before getting content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "formatted_query": {
                        "type": "string",
                        "description": "String inferred from the user's query based on available context. If in another language, translate to english. Keep it short and simple so it can be used for vector search.",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["search", "qna"],
                        "description": "Whether to search for entire documents or query information inside those documents. If the user wants to search for specifc practices or policy documents, use 'search'. If the user's query is asking about facts and data, use 'qna'.",
                    },
                    "n": {
                        "type": "integer",
                        "description": "Number of documents the user wants. Default is 5.",
                    },
                },
                "required": ["formatted_query", "mode"]  # Fixed the required fields formatting
            },
        }

        qna_function = {
            "name": "search_content",
            "description": "Searches for document content if doc_ids are already available in context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "description": "Extracted intent from the user's query (e.g., 'Search for best practices of format website.'). If in another language, translate to english first.",
                    },
                    "doc_ids": {
                        "type": "array",
                        "items": {"type": "string"},  # Added items property for array
                        "description": "List of doc_ids of the documents to be searched in."
                    },
                    "n": {
                        "type": "integer",
                        "description": "Number of documents the user wants. Default is 5. Increase it if the context does not completely answer the query.",
                    },
                },
                "required": ["intent", "doc_ids"]
            },
        }

        system_instruction = "You are an assistant that helps users interact with NITI Aayog's NITI For States platform. You will be provided the relevant information in the context. Answer only in the language of the original query. Limit your answers to the context. If the context is not sufficient, say so. Do not answer from outside the context. If listing practices and policies, briefly describe them as well. Provide sources and links for any text you use. Link the source beneath the referenced text with the label 'Source'."
        tools = types.Tool(function_declarations=[search_function, qna_function])
        self.config = types.GenerateContentConfig(system_instruction=system_instruction,tools=[tools])
        self.active_chat = self.create_new_chat()

    def create_new_chat(self) -> str:
        """Creates a new chat and returns its ID"""
        chat_id = str(uuid.uuid4())
        self.chat_history[chat_id] = self.client.chats.create(model="gemini-2.0-flash", config=self.config)
        self.active_chat = chat_id
        return chat_id

    def switch_chat(self, chat_id: str) -> bool:
        """Switch to an existing chat session"""
        if chat_id in self.chat_history:
            self.active_chat = chat_id
            return True
        return False

    def get_active_chat(self):
        """Get the current active chat instance"""
        if self.active_chat and self.active_chat in self.chat_history:
            return self.chat_history[self.active_chat]
        return None

    def new_chat(self) -> str:
        """Create a new chat session and make it active"""
        return self.create_new_chat()

    def create_filter(self, query, field_prompt):
        example = """
        Examples:
        Query: "Find acts related to environmental protection before 2010"
        Response:
        {
          "vector_string": "environmental protection",
          "filter": {
            "must": [
              {
                "key": "Category",
                "match": {
                  "text": "acts"
                }
              },
              {
                "key": "Year",
                "range": {
                  "lte": 2009
                }
              }
            ]
          }
        }

        Query: "Show me best practices about citizen engagement"
        Response:
        {
          "vector_string": "citizen engagement",
          "filter": {}
        }

        Query: "Policies present in the database related to education reform"
        Response:
        {
          "vector_string": "education reform",
          "filter": {
            "must_not": [
              {
                "key": "doc_id",
                "match": {
                  "value": ""
                }
              }
            ],
            "must": [
              {
                "key": "Category",
                "match": {
                  "text": "policies"
                }
              }
            ]
          }
        }
        """

        doc_id_filter = """
        {
            "must_not": [
              {
                "key": "doc_id",
                "match": {
                  "value": ""
                }
              }
            ],
        """

        prompt = f"""Analyze the following user query and create a 'vector_string' for semantic vector similarity search and a Qdrant filter object based on the provided filterable fields. Keep the vector string short and simple.

        Use the following filter to filter for documents present in the database:

        {doc_id_filter}
            
        <query>"{query}"</query>

        <fields>{field_prompt}</fields>

        <examples>{example}</examples

        """

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            },
        )

        try:
            parsed_response = json.loads(response.text)
            vector_string = parsed_response.get("vector_string", query)  # Default to full query if not extracted
            filter_obj = parsed_response.get("filter", {})
            print(f"vector string: {vector_string}")
            print(f"filter: {filter_obj}")
            return {
                "vector_string": vector_string,
                "filter": filter_obj,
            }
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            print(f"Raw response: {response.text}")
            return {
                "vector_string": query,
                "filter": {},
            }
    
    
    def search_metadata(self, text: str, collection_name: str, filter: dict = None, n: int = 5):           
        if filter is not None:
            filter = models.Filter(**filter)
        search_result = self.qdrant_client.query_points(
            collection_name=collection_name,
            query=models.FusionQuery(
                fusion=models.Fusion.RRF  # we are using reciprocal rank fusion here
            ),
            prefetch=[
                models.Prefetch(
                    query=models.Document(text=text, model=self.DENSE_MODEL, options=self.options),
                    using="dense"
                ),
                models.Prefetch(
                    query=models.Document(text=text, model=self.SPARSE_MODEL, options=self.options),
                    using="sparse"
                ),
            ],
            query_filter=filter,  # If you don't want any filters for now
            limit=n,  # 5 the closest results
        ).points
        # `search_result` contains models.QueryResponse structure
        # We can access list of scored points with the corresponding similarity scores,
        # vectors (if `with_vectors` was set to `True`), and payload via `points` attribute.

        # Select and return metadata
        metadata = []
        allowed_columns = self.bp_columns if collection_name == "best_practices" else self.pol_columns

        if collection_name == "data":
            metadata = [point.payload for point in search_result]
        else:
            for point in search_result:
                filtered_payload = {k: v for k, v in point.payload.items() if k in allowed_columns}
                if "doc_id" not in filtered_payload.keys():
                    filtered_payload["doc_id"] = "Document not available in local database."
                metadata.append(filtered_payload)
            
        return metadata
    
    
    def search_docs(self, intent: str, doc_ids: list = None, n: int = 10):
        print(intent, doc_ids)
        if doc_ids is not None:
            filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchAny(any=doc_ids)
                    )
                ]
            )
        else:
            filter = None

        search_result = self.qdrant_client.query_points(
            collection_name="docs",
            query=models.FusionQuery(
                fusion=models.Fusion.RRF  # we are using reciprocal rank fusion here
            ),
            prefetch=[
                models.Prefetch(
                    query=models.Document(text=intent, model=self.DENSE_MODEL, options=self.options),
                    using="dense"
                ),
                models.Prefetch(
                    query=models.Document(text=intent, model=self.SPARSE_MODEL, options=self.options),
                    using="sparse"
                ),
            ],
            query_filter=filter,
            limit=n,
        ).points

        metadata = [point.payload for point in search_result]
        return metadata
 
    def validator(self, docs: list, intent: str, doc_ids: list, n: int = 5):
        text = [doc['text'] for doc in docs]
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Validate the following documents for the query: " + intent + "\n" + str(text),
            config={
                "response_mime_type": "application/json",
                },
        )
        return response.text
    
    def docs_to_context(self, docs, data):
        context = "<documents>\n"
        for doc in docs:
            context += "<doc>"
            for k, v in doc.items():
                context += f"{k}: {v}" + "\n"
            context += "</doc>\n"
        for doc in data:
            context += "<doc>"
            for k, v in doc.items():
                context += f"{v}"
            context += "</doc>\n"
        context += "</documents>\n"
        return context

    def search(self, formatted_query: str, collections: List[str], mode: str, n: int = 5):
        """
        Search across any combination of collections.
        """
        docs = []
        data = []
        output_map = {}
        for collection_name in collections:
            if collection_name != "data":
                prompt = self.bp_prompt if collection_name == "best_practices" else self.pol_prompt
                output = self.create_filter(formatted_query, prompt)
                output_map[collection_name] = output
                docs += self.search_metadata(output['vector_string'], collection_name, output['filter'], n)
            else:
                print("[DEBUG] data collection")
                prompt = ""
                output = self.create_filter(formatted_query, prompt)
                output_map[collection_name] = output
                data += self.search_metadata(output['vector_string'], collection_name, None, 5)

        print(f"[DEBUG] {docs}\n{data}")

        if mode == "qna":
            doc_ids = [doc["doc_id"] for doc in docs]
            # Use the vector_string from the first collection for QnA context
            metadata = self.search_docs(output_map[collections[0]]['vector_string'], doc_ids, 50)
            context = self.docs_to_context(metadata, data)
        else:
            print(f"[DEBUG] docs: {docs}")
            context = self.docs_to_context(docs, data)
        return context

    def send_audio(self, audio_bytes: bytes):
        response = self.client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[
            'Respond with only the transcription of the audio file.',
            types.Part.from_bytes(
            data=audio_bytes,
            mime_type='audio/webm',
            )
        ]
        )

        return response.text

    async def process_query(self, query: str, collections: List[str]):
        print(f"[DEBUG] Processing query: {query}, Collections: {collections}")
        try:
            active_chat = self.get_active_chat()
            if not active_chat:
                print("[DEBUG] No active chat, creating new one")
                self.create_new_chat()
                active_chat = self.get_active_chat()

            # Send initial message to get function calls
            response = active_chat.send_message(query)
            print(f"[DEBUG] Initial response: {response}")

            print(response.function_calls)
            if response.function_calls is not None:
                response_parts = []
                for call in response.function_calls:
                    print(f"[DEBUG] Function call detected: {call.name}")
                    if call.name == 'search_documents':
                        print(f"[DEBUG] Call Args: {call.args}")
                        context = self.search(
                            call.args["formatted_query"],
                            collections,
                            call.args["mode"],
                            call.args.get("n", 5)
                        )
                        response_parts.append(
                            types.Part.from_function_response(name=call.name, response={"result": context}))
                    elif call.name == "search_content":
                        context = self.search_docs(**call.args)
                        response_parts.append(
                            types.Part.from_function_response(name=call.name, response={"result": context}))

                print(context)
                # Get streaming response with context
                for chunk in active_chat.send_message_stream(response_parts):
                    print(f"[DEBUG] Streaming chunk: {chunk.text}", end='')
                    yield chunk
            else:
                # For direct responses without function calls
                print(f"[DEBUG] Direct response: {response.text}", end='')
                yield response

        except Exception as e:
            print(f"[ERROR] Error in process_query: {str(e)}")
            yield {"text": f"An error occurred: {str(e)}"}
        
    
    def tts(self, message, file_name):
        def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(rate)
                wf.writeframes(pcm)

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=message,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Charon',
                        )
                    )
                ),
            )
        )

        data = response.candidates[0].content.parts[0].inline_data.data
        wave_file(file_name, data) # Saves the file to current directory
        return file_name
