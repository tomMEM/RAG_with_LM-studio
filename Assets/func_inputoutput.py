import json
import os
def save_settings(settings, filename='settings.json'):
    """
    Save the settings dictionary to a JSON file.
    Args:
    - settings (dict): A dictionary containing the settings to be saved.
    - filename (str): The name of the JSON file where settings will be saved.
    """
    try:
        with open(filename, 'w') as json_file:
            json.dump(settings, json_file, indent=4)
        print(f"Settings saved to {filename}.")
    except Exception as e:
        print(f"Error saving settings: {e}")
        
def load_settings(filename='settings.json'):
    """
    Load the settings from a JSON file and return them as unpacked values.
    Args:
    - filename (str): The name of the JSON file from which settings will be loaded.
    Returns:
    - tuple: The values of pdf_collection_path, database_directory, database_name, and remaining settings.
    """
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as json_file:
                settings = json.load(json_file)
            print(f"Settings loaded from {filename}.")
            # Extract primary settings
            working_directory = settings.get('working_directory')
            pdf_collection_path = settings.get('pdf_collection_path')
            pdf_path = settings.get('pdf_path')
            base_name = settings.get('base_name')
            database_name = settings.get('database_name')
            value1 = settings.get('additional')
                        
            # Identify additional settings
            remaining_settings = {key: value for key, value in settings.items() if key not in ['working_directory', 'pdf_collection_path', 'pdf_path', 'base_name', 'database_name']}
            print("\npath and name settings from above were loaded")# Check for any additional settings and warn the user
            if remaining_settings:
                print("\n  There are additional settings that could be added:")
                for key, value in remaining_settings.items():
                    print(f"  {key}: {value}")
            return working_directory, pdf_collection_path, pdf_path, base_name, database_name, remaining_settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return None, None, None, None, None, {}
    else:
        print(f"Settings file {filename} does not exist.")
        return None, None, None, None, None, {}
    
    

import re
class DocumentRetriever:
    def __init__(self, vectordb):
        """
        Initializes the DocumentRetriever with a vector database.
        
        Parameters:
            vectordb: The vector database used for similarity search.
        """
        self.vectordb = vectordb
    def retrieve_documents(self, query, is_first_run, k=10, method='combined'):
        """
        Retrieves similar documents based on a query using different methods.

        Parameters:
            query (str): The search query.
            is_first_run (bool): Flag indicating if this is the first run.
            k (int): The number of similar documents to retrieve. Default is 4.
            method (str): The method to use for generating the query ('keywords', 'llm', or 'combined').

        Returns:
            tuple: A tuple containing formatted string with retrieved documents and the used query.
        """
        retrieved_text = ""
        refined_query = ""

        if not is_first_run:
            # Extract keywords or generate refined query
            if method == 'keywords':
                refined_query = self.extract_keywords(query)
            elif method == 'llm':
                refined_query = self.generate_useful_query(query)
            elif method == 'combined':
                keywords = self.extract_keywords(query)
                refined_query = self.generate_useful_query(keywords)

            # Check if the refined query is meaningful
            if self.is_query_meaningful(refined_query):
                # Use refined query for similarity search
                similar_docs = self.vectordb.similarity_search(refined_query, k=k)

                # Format documents
                for i, doc in enumerate(similar_docs):
                    retrieved_text += (
                        f"**Document {doc.metadata['doc_id']}, "
                        f"Chunk {doc.metadata.get('chunk_id', 'N/A')}**:\n{doc.page_content}\n\n"
                    )
            else:
                # No meaningful query found, return empty results
                retrieved_text = ""
                refined_query = ""

        return retrieved_text, refined_query

    def is_query_meaningful(self, query):
        """
        Determines if the query is meaningful enough for retrieval.

        Parameters:
            query (str): The input query.

        Returns:
            bool: True if the query is meaningful, False otherwise.
        """
        # Remove common non-meaningful phrases
        if not query or query.lower() in ['no content found.', 'no keywords found']:
            return False

        # Check query length
        if len(query.strip()) < 3:
            return False

        # Optional: Add more sophisticated meaning detection
        # For example, check against a list of stop words or minimum information content
        meaningless_phrases = [
            'no content found',
            'no keywords',
            'not specified',
            'empty query'
        ]

        # Convert to lowercase for case-insensitive comparison
        query_lower = query.lower()

        # Check if query matches any meaningless phrases
        if any(phrase in query_lower for phrase in meaningless_phrases):
            return False

        return True

    def extract_keywords(self, query):
        """
        Extracts keywords from the query based on curly braces.

        Parameters:
            query (str): The input query.

        Returns:
            str: A string of extracted keywords or empty string.
        """
        # Find keywords within curly braces
        keywords = re.findall(r'\{(.*?)\}', query)

        # Return joined keywords or empty string if no keywords found
        return ' '.join(keywords) if keywords else ''
    
    def generate_useful_query(self, query):
        """
        Generates a useful query using an LLM based on the given input.
        
        Parameters:
            query (str): The input query.
        
        Returns:
            str: A refined query generated by the LLM.
        """
        try:
            instruction = "Extract named entities and specific technical terms from the following query that are most relevant for search. Provide ONLY the entities/terms, separated by commas. Focus on proper nouns, specific technologies, or key concepts."         
           
            prompt_template = """
                                {instruction}
                                Original Query: "{query}"
                                Refined Query: 
                                """
            prompt = prompt_template.format(
                query=query,
                instruction=instruction
            )
            
            # Call the LLM with the generated prompt
            completion = client.chat.completions.create(
                model="LLMA/Meta-Llama-3-8B",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting precise semantic phrase groups from complex queries"},
                    {"role": "user", "content": prompt}
                ],              
                temperature=0.8,
                stream=True,
            )
            
            # Collect the response from the LLM
            full_response = ''.join(
                chunk.choices[0].delta.content 
                for chunk in completion 
                if chunk.choices[0].delta.content
            )
            
            return full_response.strip()
        
        except Exception as e:
            print(f"Error in query generation: {e}")
            return query  # Fallback to original query

    def should_use_original(self, query):
        """
        Determines if the original query should be used for similarity retrieval.
        
        Parameters:
            query (str): The input query.
        
        Returns:
            bool: True if original query should be used, False otherwise.
        """
        # Add more sophisticated logic if needed
        return len(query.strip()) > 3  # Use original query if longer than 3 characters
    
    
def manage_conversation_history(history, max_tokens=1500):
    """
    Manage conversation history by truncating or summarizing
    
    Args:
        history (list): Conversation history
        max_tokens (int): Maximum token limit for history
    
    Returns:
        list: Managed conversation history
    """
    def count_tokens(text):
        """Simple token estimation"""
        return len(text.split())  # Basic token counting
    
    total_tokens = 0
    trimmed_history = []
    
    # Iterate backwards to keep most recent interactions
    for message in reversed(history):
        message_tokens = count_tokens(message['content'])
        if total_tokens + message_tokens > max_tokens:
            break
        trimmed_history.insert(0, message)
        total_tokens += message_tokens
    
    return trimmed_history

def summarize_history(history):
    """
    Optionally summarize conversation history if it becomes too long
    
    Args:
        history (list): Conversation history
    
    Returns:
        str: Summarized context or original history
    """
    if len(history) > 10:  # Example threshold for summarization
        try:
            summary_prompt = """
            Summarize the key points and context from the following conversation history,
            focusing on the most relevant information for future context:
            
            {history}
            
            Provide a concise summary that captures the essential context.
            """
            
            # Use LLM to generate summary
            summary_response = client.chat.completions.create(
                model="gpt-4",  # Use a more capable model for summarization
                messages=[
                    {"role": "system", "content": "You are a context summarization assistant."},
                    {"role": "user", "content": summary_prompt.format(
                        history='\n'.join([msg['content'] for msg in history])
                    )}
                ]
            )
            
            return summary_response.choices[0].message.content
        except Exception as e:
            print(f"Summarization error: {e}")
    
    return history  # Return original history if summarization fails

def debounce(wait):
    """Decorator to debounce function calls"""
    def decorator(fn):
        last_call = [0]
        def debounced(*args, **kwargs):
            current_time = time.time()
            if current_time - last_call[0] > wait:
                last_call[0] = current_time
                return fn(*args, **kwargs)
        return debounced
    return decorator



import nltk
nltk.download('punkt')  # Download necessary data if you haven't already

def word_count(messages):
    total_tokens = 0  # To keep track of the total token count
    
    # Handle single long text input or list of messages
    if isinstance(messages, str):
        # If the input is a single string, tokenize directly
        try:
            tokens = nltk.word_tokenize(messages)
            total_tokens += len(tokens)  # Update the total token count
        except Exception as e:
            print(f"Error during tokenization of input text: {e}")
    elif isinstance(messages, list):
        for msg in messages:
            # Ensure msg is a dictionary
            if not isinstance(msg, dict):
                print(f"Warning: Invalid message format, expected a dictionary, got {type(msg).__name__}. Skipping.")
                continue  # Skip invalid messages
            
            # Get the content while ensuring it's a string
            content = msg.get('content', '')
            if not isinstance(content, str):
                print(f"Warning: Invalid content format in msg, expected a string, got {type(content).__name__}. Converting to empty string.")
                content = ''  # Default to empty string if content is not a string
            
            # Tokenize the content and handle any exceptions
            try:
                tokens = nltk.word_tokenize(content)
                total_tokens += len(tokens)  # Update the total token count
            except Exception as e:
                print(f"Error during tokenization of message: {e}. Content: {content}")
    else:
        print("Warning: Input should be either a string or a list of dictionaries.")
    
    return total_tokens  # Return the total token count
