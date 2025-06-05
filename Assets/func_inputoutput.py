import json
import os
from pathlib import Path
def save_settings_old(settings, filename='settings.json'):
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
        
def load_settings_old(filename='settings.json', return_dict_directly=False):
    """
    Load settings from a JSON file.
    Args:
    - filename (str): The name of the JSON file.
    - return_dict_directly (bool): If True, returns the raw settings dictionary.
                                   If False (default), returns the specific unpacked tuple.
    """
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as json_file:
                settings = json.load(json_file)
            print(f"Settings loaded from {filename}.")

            if return_dict_directly:
                return settings # Gradio app would prefer this
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
            if return_dict_directly:
                return {}
            return None, None, None, None, None, {}
    else:
        print(f"Settings file {filename} does not exist.")
        if return_dict_directly:
            return {}
        return None, None, None, None, None, {}
    


def load_settings(filename="settings.json") -> dict:
    """
    Loads settings from a JSON file and always returns a dictionary.
    If the file doesn't exist, is empty, or contains invalid JSON,
    an empty dictionary is returned.

    Args:
        filename (str): The name of the JSON file.

    Returns:
        dict: The loaded settings as a dictionary, or an empty dictionary on failure.
    """
    settings_path = Path(filename) # Using pathlib.Path for robustness
    if settings_path.exists() and settings_path.is_file():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                print(f"Settings successfully loaded from {filename}.")
                return data
            else:
                print(f"Warning: Content of '{filename}' is not a valid dictionary. Returning empty settings.")
                return {}
        except json.JSONDecodeError:
            print(f"Warning: '{filename}' contains invalid JSON. Returning empty settings.")
            return {}
        except Exception as e:
            print(f"Error loading settings from '{filename}': {e}. Returning empty settings.")
            return {}
    else:
        print(f"Settings file '{filename}' not found or is not a file. Returning empty settings.")
        return {}

def save_settings(settings_data: dict, filename="settings.json") -> str:
    """
    Saves the given settings data (dictionary) to a JSON file.

    Args:
        settings_data (dict): The dictionary of settings to save.
        filename (str): The name of the JSON file to save to.

    Returns:
        str: A status message.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=4)
        return f"Settings successfully saved to {filename}"
    except Exception as e:
        return f"Error saving settings to {filename}: {e}"

    
    
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
def check_and_download_punkt():
    """Checks if Punkt Sentence Tokenizer is downloaded; downloads if not."""
    try:
        punkt_path = nltk.data.find('tokenizers/punkt')
        if not punkt_path:
            print("Downloading Punkt Sentence Tokenizer...")
            nltk.download('punkt')
    except LookupError:
        print("Downloading Punkt Sentence Tokenizer...")
        nltk.download('punkt')
    except Exception as e:
        print(f"An error occurred while checking or downloading Punkt: {e}")

def word_count(messages):
    """Counts words in a string or a list of dictionaries (messages)."""
    check_and_download_punkt() # Added Punkt download check here.
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
