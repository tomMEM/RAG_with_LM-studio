import json
import os
import nltk
from collections import deque
from typing import List, Dict, Tuple, Union, Optional

def save_settings(settings: dict, filename: str = 'settings.json') -> None:
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
    except (IOError, json.JSONEncodeError) as e:  # more specific exception
        print(f"Error saving settings: {e}")

def load_settings(filename: str = 'settings.json') -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], dict]:
    """
    Load the settings from a JSON file and return them as unpacked values.

    Args:
    - filename (str): The name of the JSON file from which settings will be loaded.

    Returns:
    - tuple: The values of working_directory, pdf_collection_path, pdf_path, base_name, database_name, and remaining settings.
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
                        
            # Identify additional settings
            remaining_settings = {key: value for key, value in settings.items() if key not in [
                'working_directory', 'pdf_collection_path', 'pdf_path', 'base_name', 'database_name']}
            print("\npath and name settings from above were loaded")  # Check for any additional settings and warn the user
            if remaining_settings:
                print("\n  There are additional settings that could be added:")
                for key, value in remaining_settings.items():
                    print(f"  {key}: {value}")
            return working_directory, pdf_collection_path, pdf_path, base_name, database_name, remaining_settings
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading settings: {e}")
            return None, None, None, None, None, {}
    else:
        print(f"Settings file {filename} does not exist.")
        return None, None, None, None, None, {}

def manage_conversation_history(history: List[Dict[str, str]], max_tokens: int = 1500) -> List[Dict[str, str]]:
    """
    Manage conversation history by truncating or summarizing

    Args:
        history (list): Conversation history
        max_tokens (int): Maximum token limit for history

    Returns:
        list: Managed conversation history
    """
    def count_tokens(text: str) -> int:
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

def manage_conversation_history_not_tested(history: List[Dict[str, str]], max_tokens: int = 1500) -> List[Dict[str, str]]:
    """
    Manage conversation history by truncating or summarizing

    Args:
        history (list): Conversation history
        max_tokens (int): Maximum token limit for history

    Returns:
        list: Managed conversation history
    """
    def count_tokens(text: str) -> int:
        """Use tiktoken for more accurate token estimation"""
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")  # Assuming you are working with gpt-4
            return len(encoding.encode(text))
        except KeyError:
            # Fallback to a basic tokenizer
            print("Warning: tiktoken model not found. Using basic tokenizer. Token count might be off")
            return len(text.split()) 
    
    total_tokens = 0
    trimmed_history = deque()
    
    # Iterate backwards to keep most recent interactions
    for message in reversed(history):
        message_tokens = count_tokens(message['content'])
        if total_tokens + message_tokens > max_tokens:
            break
        trimmed_history.appendleft(message)  # insert at the beginning of the deque
        total_tokens += message_tokens
    
    return list(trimmed_history)  # return list 

def summarize_history(history: List[Dict[str, str]]) -> Union[str, List[Dict[str, str]]]:
    """
    Optionally summarize conversation history if it becomes too long
    
    Args:
        history (list): Conversation history
    
    Returns:
        str: Summarized context or original history
    """
    if not history:
        return ""
    
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
                model=model_name,  # Use a more capable model for summarization
                messages=[
                    {"role": "system", "content": "You are a context summarization assistant."},
                    {"role": "user", "content": summary_prompt.format(
                        history='\n'.join([msg['content'] for msg in history])
                    )}
                ]
            )
            
            return summary_response.choices[0].message.content
        except openai.APIError as e:
            print(f"Summarization error: {e}")
    
    return history  # Return original history if summarization fails

def decorator(fn):
    last_call = [0]
    def debounced(*args, **kwargs):
        current_time = time.time()
        if current_time - last_call[0] > wait:
            last_call[0] = current_time
            return fn(*args, **kwargs)
        return debounced
    return decorator

def check_and_download_punkt() -> None:
    """Checks if Punkt Sentence Tokenizer is downloaded; downloads if not."""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Downloading Punkt Sentence Tokenizer...")
        nltk.download('punkt')
    except Exception as e:
        print(f"An error occurred while checking or downloading Punkt: {e}")

def word_count(messages: Union[str, List[Dict[str, str]]]) -> int:
    """Counts words in a string or a list of dictionaries (messages)."""
    check_and_download_punkt()
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
