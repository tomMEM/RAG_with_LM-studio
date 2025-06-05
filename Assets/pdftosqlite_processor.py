# pdftosqlite_processor.py
import os
import sqlite3
import pandas as pd # Keep for potential future use, though not strictly in this refactor
from grobid_client.grobid_client import GrobidClient
import grobid_tei_xml
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# --- Proxy Setup (same as main script, ensure consistency) ---
# It's good practice to have this configured centrally if possible,
# but for a module, it might be called when imported.
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,127.0.0.1:8070' # Added Grobid port
import urllib3
import requests
urllib3.disable_warnings()
if hasattr(urllib3.util.connection, 'is_connection_dropped'):
    urllib3.util.connection.is_connection_dropped = lambda conn: False
if hasattr(requests.Session(), 'trust_env'):
    requests.Session().trust_env = False

class GrobidAuthor: # From your script
    def __init__(self, full_name):
        self.full_name = full_name

class GrobidBiblio: # From your script
    def __init__(self, index, authors, title, date, volume, pages, issue, journal, doi):
        self.index = index
        self.authors = authors
        self.title = title
        self.date = date
        self.volume = volume
        self.pages = pages
        self.issue = issue
        self.journal = journal
        self.doi = doi

def extract_bibliographic_details(biblios: List[GrobidBiblio], print_choice=False) -> str: # From your script
    # ... (Your existing extract_bibliographic_details function) ...
    for biblio in biblios:
        if print_choice: # This print_choice is not used in current logic path, but kept
            print("Index", biblio.index, "| Title:", biblio.title)
            print("Authors:")
            for author in biblio.authors:
                print("-", author.full_name)
            print("Date:", biblio.date)
            print("Volume:", biblio.volume)
            print("Pages:", biblio.pages)
            print("Journal:", biblio.journal)
            print("Doi:", biblio.doi)
            print()
    
    ref_list = '*'.join([
        f" * Index: {biblio.index} | Title: {biblio.title} | Authors: {', '.join([author.full_name for author in biblio.authors])} | Date: {biblio.date} | Volume: {biblio.volume} | Pages: {biblio.pages} | Journal: {biblio.journal} | Doi: {biblio.doi}\|"
        for biblio in biblios
    ])
    return ref_list

def parse_structured_text_file(text_file_path: str) -> List[Dict[str, Any]]: # From your script, adapted
    records = []
    try:
        with open(text_file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            # Assuming records are separated by double newlines and each field is on a new line.
            # This parsing is specific to the format in your example.
            raw_records = text.split("\n\n") 
            for record_text in raw_records:
                if not record_text.strip():
                    continue
                record = {}
                lines = record_text.split('\n')
                for line in lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        # Normalize keys for consistency with Grobid output where possible
                        key_map = {
                            "Record Number": "Record_Number",
                            "Author": "Authors", # Grobid uses Authors (plural)
                            # Add other mappings if needed
                        }
                        db_key = key_map.get(key.strip(), key.strip())
                        record[db_key] = value.strip()
                
                # Ensure essential keys for the DB schema exist, even if empty
                for key_to_ensure in ["Title", "Authors", "DOI", "Abstract", "Date", "Journal", "Record_Number", "Citations", "Body", "Refs"]:
                    if key_to_ensure not in record:
                        record[key_to_ensure] = ""
                if record.get("Abstract"): # If abstract is present, put it in Body too if Body is empty
                    if not record.get("Body"):
                        record["Body"] = record["Abstract"]

                if record.get("Title"): # Only add if there's a title
                    records.append(record)
    except Exception as e:
        print(f"Error parsing structured text file {text_file_path}: {e}")
    return records

def process_documents_to_sqlite(
    input_path_str: str,           # Path to PDF directory or a single TXT file
    output_db_dir_str: str,        # Directory where the SQLite DB will be saved
    db_name_stem: str,             # e.g., "my_collection" -> "my_collection.db"
    processing_mode: str,          # "grobid", "text", "both"
    overwrite_db: bool,
    grobid_config_path: str = "config.json", # Path to grobid config
    progress_callback: Optional[callable] = None # For Gradio progress
) -> Tuple[str, Optional[str]]:
    
    input_path = Path(input_path_str)
    output_db_dir = Path(output_db_dir_str)
    output_db_dir.mkdir(parents=True, exist_ok=True)
    database_name = output_db_dir / f"{db_name_stem}.db"
    
    status_messages = []
    id_key = 1

    if database_name.exists():
        if overwrite_db:
            status_messages.append(f"Overwriting existing database: {database_name}")
            try:
                os.remove(database_name)
            except Exception as e:
                return f"Error removing existing database {database_name}: {e}", None
        else: # Append mode or determine starting ID
            status_messages.append(f"Appending to existing database: {database_name}")
            try:
                conn_check = sqlite3.connect(database_name)
                cursor_check = conn_check.cursor()
                # Check if the table exists and get table name
                cursor_check.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'document_table%';") # Allow for suffixed names
                table_result = cursor_check.fetchone()
                if table_result:
                    table_name_existing = table_result[0]
                    cursor_check.execute(f"SELECT MAX(ID) FROM {table_name_existing}")
                    max_id = cursor_check.fetchone()[0]
                    id_key = (max_id + 1) if max_id is not None else 1
                conn_check.close()
            except Exception as e:
                status_messages.append(f"Could not read max ID from existing DB, starting ID at 1. Error: {e}")
                id_key = 1
    
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    # Ensure table exists
    # Use a consistent table name, or derive it if necessary (e.g., from db_name_stem)
    table_name = "document_table" # Simplified from your script
    try:
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                        (ID INTEGER PRIMARY KEY,
                        Title TEXT,
                        Authors TEXT,
                        DOI TEXT,
                        Citations TEXT, -- Changed to TEXT as Grobid might return string like "0"
                        Abstract TEXT,
                        Body TEXT,
                        Date TEXT,
                        Record_Number TEXT, -- Changed to TEXT
                        Refs TEXT,
                        Journal TEXT,
                        Source_File TEXT)''')
        status_messages.append(f"Ensured table '{table_name}' exists in {database_name}.")
    except Exception as e:
        conn.close()
        return f"Error creating/ensuring table: {e}", None

    files_to_process = []
    if input_path.is_dir():
        if processing_mode in ["grobid", "both"]:
            for filename in os.listdir(input_path):
                if filename.lower().endswith(".pdf"):
                    files_to_process.append({"type": "pdf", "path": input_path / filename, "name": filename})
        if processing_mode in ["text", "both"]: # Allow TXT files from a directory too
             for filename in os.listdir(input_path):
                if filename.lower().endswith(".txt"):
                    files_to_process.append({"type": "txt", "path": input_path / filename, "name": filename})

    elif input_path.is_file():
        if input_path.name.lower().endswith(".pdf") and processing_mode in ["grobid", "both"]:
            files_to_process.append({"type": "pdf", "path": input_path, "name": input_path.name})
        elif input_path.name.lower().endswith(".txt") and processing_mode in ["text", "both"]:
            files_to_process.append({"type": "txt", "path": input_path, "name": input_path.name})
        else:
            conn.close()
            return f"Unsupported file type or processing mode for single file: {input_path.name}", None
    else:
        conn.close()
        return f"Input path does not exist or is not a file/directory: {input_path_str}", None

    if not files_to_process:
        conn.close()
        return "No compatible files found to process with the selected mode.", None

    # Initialize Grobid client if needed
    grobid_client = None
    if any(f['type'] == 'pdf' for f in files_to_process): # Only init if PDFs are to be processed by Grobid
        try:
            # Try to use NO_PROXY from environment if set, else default
            no_proxy_env = os.environ.get('NO_PROXY', 'localhost,127.0.0.1,127.0.0.1:8070')
            
            # GrobidClient might not directly use os.environ['NO_PROXY'].
            # It uses requests internally. The global requests session setting might help.
            # However, explicit proxy config in config.json or GrobidClient params is more reliable if needed.
            
            grobid_client = GrobidClient(config_path=grobid_config_path, check_server=True) # check_server pings on init
            status_messages.append(f"GROBID client initialized (config: {grobid_config_path}).")
        except Exception as e:
            status_messages.append(f"GROBID client initialization failed: {e}. PDF processing will be skipped.")
            grobid_client = None # Ensure it's None if failed

    total_files = len(files_to_process)
    for i, file_info in enumerate(files_to_process):
        file_path = file_info["path"]
        file_name = file_info["name"]
        file_type = file_info["type"]

        if progress_callback:
            progress_callback(i / total_files, f"Processing {file_name} ({i+1}/{total_files})")
        
        status_messages.append(f"Processing {file_name}...")

        if file_type == "pdf" and grobid_client:
            try:
                # Note: process_pdf is a mock name for process_fulltext_document or similar
                _service = "processFulltextDocument" 
                # For TEI Coordinates and sentence segmentation, ensure your Grobid version/config supports it.
                # The default client might not expose all these as direct args to a generic `process_pdf`
                # It's usually client.process_fulltext_document(pdf_file, ...)
                # For simplicity, using the direct call as in your script.
                resp, status_code, text_content = grobid_client.process_pdf(
                    _service, str(file_path), # process_pdf is an alias in some client versions
                    generateIDs=True, consolidate_header=True, consolidate_citations=True,
                    include_raw_citations=True, include_raw_affiliations=True,
                    tei_coordinates=True, segment_sentences=True # Check if your client version supports these directly
                )

                if status_code != 200 or not text_content or text_content.strip() == '':
                    raise ValueError(f"GROBID processing failed for {file_name} (status {status_code}) or no text extracted.")

                doc = grobid_tei_xml.parse_document_xml(text_content)
                
                title = doc.header.title if hasattr(doc.header, 'title') and doc.header.title else "No Title"
                authors = '; '.join([a.full_name for a in doc.header.authors]) if hasattr(doc.header, 'authors') and doc.header.authors else "No Authors"
                doi = str(doc.header.doi) if hasattr(doc.header, 'doi') and doc.header.doi else "No DOI"
                
                # Citations: count of biblStruct elements in the TEI body's listBibl
                # This might differ from `len(doc.citations)` which could be for internal citation markers.
                # For now, using len(doc.citations) as per your script for consistency.
                citations = str(len(doc.citations)) if hasattr(doc, 'citations') else "0"
                
                abstract = doc.abstract if hasattr(doc, 'abstract') and doc.abstract else "No Abstract"
                body = doc.body if hasattr(doc, 'body') and doc.body else "No Body"
                date_obj = doc.header.date if hasattr(doc.header, 'date') else None
                date_str = str(date_obj) if date_obj else "No Date" # Improve date parsing if needed
                journal = doc.header.journal if hasattr(doc.header, 'journal') and doc.header.journal else "No Journal"

                ref_list = ""
                if hasattr(doc, 'citations') and doc.citations: # Assuming doc.citations is a list of biblio objects
                    # The `grobid_tei_xml.parse_citation_list_xml` was used on the raw TEI `text_content`.
                    # If `doc.citations` already contains structured GrobidBiblio-like objects, adapt.
                    # If not, and you need to parse from raw TEI again:
                    try:
                        grobid_biblios = grobid_tei_xml.parse_citation_list_xml(text_content) # Re-parsing for biblio from full text
                        ref_list = extract_bibliographic_details(grobid_biblios)
                    except Exception as cite_error:
                        status_messages.append(f"Citation parsing error for {file_name}: {cite_error}")
                        ref_list = "Error parsing references"
                else:
                    ref_list = "No references found by parser"

                cursor.execute(f'''
                    INSERT INTO {table_name} (ID, Title, Authors, DOI, Citations, Abstract, Body, Date, Refs, Journal, Source_File)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (id_key, title, authors, doi, citations, abstract, body, date_str, ref_list, journal, file_name))
                conn.commit()
                id_key += 1
                status_messages.append(f"Successfully processed and stored PDF: {file_name}")

            except Exception as e:
                status_messages.append(f"Error processing PDF {file_name} with GROBID: {e}")
                continue

        elif file_type == "txt":
            try:
                records = parse_structured_text_file(str(file_path))
                if not records:
                    status_messages.append(f"No records found or parsed from TXT: {file_name}")
                    continue
                
                for record in records:
                    # Ensure all fields expected by the DB are present, defaulting to None or empty string
                    cursor.execute(f'''
                        INSERT INTO {table_name} (ID, Title, Authors, DOI, Citations, Abstract, Body, Date, Record_Number, Refs, Journal, Source_File)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        id_key,
                        record.get('Title'), record.get('Authors'), record.get('DOI'),
                        record.get('Citations'), record.get('Abstract'), record.get('Body'),
                        record.get('Date'), record.get('Record_Number'), record.get('Refs'),
                        record.get('Journal'), file_name
                    ))
                    conn.commit()
                    id_key += 1
                status_messages.append(f"Successfully processed and stored TXT: {file_name} ({len(records)} records)")
            except Exception as e:
                status_messages.append(f"Error processing TXT {file_name}: {e}")
                continue
    
    if progress_callback:
        progress_callback(1.0, "Processing complete.")

    final_count = 0
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        final_count = cursor.fetchone()[0]
        status_messages.append(f"Total records in '{table_name}': {final_count}")
    except Exception as e:
        status_messages.append(f"Error getting final count from DB: {e}")
        
    conn.close()
    
    # Check if any records were actually added in this run
    # This id_key logic assumes new records were added. If appending, this might not be accurate
    # if id_key == 1 and final_count == 0 (and not overwrite_db): # No new records added to a new DB
    #    return "\n".join(status_messages) + "\nNo new records were added.", None
        
    return "\n".join(status_messages), str(database_name)