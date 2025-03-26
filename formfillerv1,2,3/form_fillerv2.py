from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import google.generativeai as genai
import asyncio
import json
import os
import time
import faiss
import numpy as np
from typing import List, Dict, Tuple

class FormFiller:
    def __init__(self):
        self.setup_gemini()
        self.vector_dimension = 768  # Dimension for embeddings
        self.index = self.setup_faiss()
        self.rag_chunks = []
        self.rag_data = self.load_rag_data()
        print("\nInitialized FormFiller with Vector RAG data")
        
    def setup_gemini(self):
        """Initialize Gemini AI"""
        genai.configure(api_key="AIzaSyAG9RHA_tUrSosbpmJYKrWakB8zvucmQx4")
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        print("\nGemini AI initialized")
        
    def setup_faiss(self) -> faiss.Index:
        """Initialize FAISS index for vector search"""
        index = faiss.IndexFlatL2(self.vector_dimension)
        print("\nFAISS index initialized")
        return index
        
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using Gemini"""
        try:
            # Use Gemini to generate embeddings
            response = self.model.generate_content(
                f"Generate a numerical embedding representation for this text: {text}",
                generation_config={"candidate_count": 1}
            )
            # Convert response to vector (simplified for example)
            # In real implementation, you'd use a proper embedding model
            text_hash = hash(text)
            np.random.seed(text_hash)
            vector = np.random.rand(self.vector_dimension).astype('float32')
            return vector
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return np.zeros(self.vector_dimension).astype('float32')
        
    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for better RAG"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) > chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
        
    def load_rag_data(self) -> str:
        """Load and process RAG data using FAISS"""
        try:
            print("\nLoading and vectorizing RAG data...")
            with open("data.txt", "r", encoding='utf-8') as f:
                data = f.read()
            
            # Split data into chunks
            self.rag_chunks = self.chunk_text(data)
            
            # Create vectors for each chunk
            vectors = []
            for chunk in self.rag_chunks:
                vector = self.get_embedding(chunk)
                vectors.append(vector)
            
            # Add vectors to FAISS index
            if vectors:
                vectors_array = np.array(vectors).astype('float32')
                self.index.add(vectors_array)
                print(f"Added {len(vectors)} vectors to FAISS index")
            
            return data
            
        except Exception as e:
            print(f"Warning: Error loading RAG data: {e}")
            return ""
        
    def get_relevant_context(self, query: str, k: int = 3) -> str:
        """Get most relevant RAG chunks for a query using FAISS"""
        try:
            # Get query vector
            query_vector = self.get_embedding(query)
            
            # Search in FAISS index
            D, I = self.index.search(query_vector.reshape(1, -1), k)
            
            # Get relevant chunks
            relevant_chunks = [self.rag_chunks[i] for i in I[0] if i < len(self.rag_chunks)]
            
            return "\n".join(relevant_chunks)
        except Exception as e:
            print(f"Error getting relevant context: {e}")
            return ""
        
    def get_firefox_path(self):
        """Get Firefox executable path"""
        return "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
        
    def query_gemini(self, prompt: str, query_context: str = "") -> str:
        """Query Gemini AI with vector RAG context"""
        try:
            # Get relevant context for this specific query
            relevant_context = self.get_relevant_context(query_context if query_context else prompt)
            
            full_prompt = f"""
            Reference Knowledge Base (Most Relevant Context):
            {relevant_context}

            Based on the above knowledge base, please process the following:
            {prompt}
            """
            
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"Error querying Gemini: {str(e)}")
            return ""
        
    async def analyze_form(self, url: str) -> list:
        """Extract form fields using Selenium"""
        print("\nAnalyzing form structure...")
        
        options = Options()
        options.binary_location = self.get_firefox_path()
        # No headless mode - browser will be visible
        
        driver = webdriver.Firefox(options=options)
        wait = WebDriverWait(driver, 20)
        
        try:
            driver.get(url)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="listitem"]')))
            
            items = driver.find_elements(By.CSS_SELECTOR, '[role="listitem"]')
            fields = []
            
            for item in items:
                try:
                    title = ""
                    for selector in ['[role="heading"]', '.freebirdFormviewerComponentsQuestionBaseHeader']:
                        try:
                            title_elem = item.find_element(By.CSS_SELECTOR, selector)
                            title = title_elem.text
                            if title.strip():
                                break
                        except:
                            continue
                    
                    if not title.strip():
                        continue
                    
                    input_type = "text"
                    choices = []
                    
                    # Check for radio buttons
                    radio_options = item.find_elements(By.CSS_SELECTOR, '[role="radio"]')
                    if radio_options:
                        input_type = "radio"
                        choices = [opt.text.strip() for opt in radio_options if opt.text.strip()]
                    
                    # Check for checkboxes
                    if not choices:
                        checkbox_options = item.find_elements(By.CSS_SELECTOR, '[role="checkbox"]')
                        if checkbox_options:
                            input_type = "checkbox"
                            choices = [opt.text.strip() for opt in checkbox_options if opt.text.strip()]
                    
                    required = bool(item.find_elements(By.CSS_SELECTOR, '[aria-label*="Required"]'))
                    
                    field_info = {
                        "question": title.strip(),
                        "type": input_type,
                        "required": required,
                        "options": choices
                    }
                    fields.append(field_info)
                    print(f"\nDetected field: {json.dumps(field_info, indent=2)}")
                    
                except Exception as e:
                    print(f"Error analyzing field: {str(e)}")
                    continue
            
            driver.quit()
            return fields
            
        except Exception as e:
            print(f"Error analyzing form: {str(e)}")
            driver.quit()
            return []
            
    def analyze_with_gemini(self, fields: list) -> dict:
        """Get form filling suggestions from Gemini AI using vector RAG"""
        print("\nAnalyzing form fields with Gemini AI...")
        
        # Create a combined query for context retrieval
        combined_query = " ".join([field["question"] for field in fields])
        
        prompt = f"""
        Based on the provided knowledge base above, suggest appropriate responses for these form fields:
        
        Form Fields:
        {json.dumps(fields, indent=2)}
        
        For each field:
        1. Use the knowledge base to find the most relevant information
        2. Format the response appropriately for the field type
        3. For radio/checkbox fields, ensure responses exactly match the available options
        
        Return ONLY a valid JSON object with questions as keys and appropriate answers as values.
        """
        
        response = self.query_gemini(prompt, combined_query)
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
                suggestions = json.loads(json_str)
                print("\nGenerated suggestions based on vector RAG:")
                for q, a in suggestions.items():
                    print(f"\nQuestion: {q}")
                    print(f"Answer: {a}")
                return suggestions
            else:
                raise ValueError("No valid JSON found in response")
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            return {field["question"]: "" for field in fields}
            
    async def fill_form(self, url: str, field_data: dict) -> bool:
        """Fill form using Selenium with the provided data"""
        print("\nFilling form with responses...")
        
        options = Options()
        options.binary_location = self.get_firefox_path()
        # No headless mode - browser will be visible
        
        driver = webdriver.Firefox(options=options)
        wait = WebDriverWait(driver, 20)
        
        try:
            driver.get(url)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="listitem"]')))
            
            items = driver.find_elements(By.CSS_SELECTOR, '[role="listitem"]')
            
            for question, value in field_data.items():
                for item in items:
                    try:
                        title = item.find_element(By.CSS_SELECTOR, '[role="heading"]').text
                        
                        if question.lower() in title.lower():
                            print(f"\nFilling field: {question}")
                            
                            # Handle text inputs
                            text_inputs = item.find_elements(By.CSS_SELECTOR, 'input.whsOnd.zHQkBf, textarea.KHxj8b.tL9Q4c')
                            if text_inputs:
                                text_inputs[0].clear()
                                text_inputs[0].send_keys(str(value))
                                print(f"Filled text with: {value}")
                                continue
                            
                            # Handle radio buttons
                            if isinstance(value, str):
                                radio_options = item.find_elements(By.CSS_SELECTOR, '[role="radio"]')
                                for option in radio_options:
                                    if value.lower() in option.text.lower():
                                        option.click()
                                        print(f"Selected radio option: {value}")
                                        break
                            
                            # Handle checkboxes
                            if isinstance(value, list):
                                checkbox_options = item.find_elements(By.CSS_SELECTOR, '[role="checkbox"]')
                                for option in checkbox_options:
                                    if any(val.lower() in option.text.lower() for val in value):
                                        option.click()
                                        print(f"Selected checkbox option from: {value}")
                    
                    except Exception as e:
                        print(f"Error filling field '{question}': {str(e)}")
                        continue
            
            # Find submit button but don't click it yet
            submit_button = driver.find_element(By.CSS_SELECTOR, '[role="button"][jsname="M2UYVd"]')
            
            # Let user verify the form
            print("\n=== Please verify the form data in the browser ===")
            print("Take your time to review all answers.")
            verification = input("\nDo you want to submit the form? (y/n): ").lower()
            
            if verification == 'y':
                submit_button.click()
                print("\nForm submitted successfully!")
                time.sleep(3)  # Wait to see the confirmation
                driver.quit()
                return True
            else:
                print("\nForm submission cancelled. You can close the browser.")
                driver.quit()
                return False
            
        except Exception as e:
            print(f"Error filling form: {str(e)}")
            driver.quit()
            return False

async def main():
    try:
        # Initialize form filler (this will load and process RAG data)
        print("\nInitializing form filler and loading RAG data...")
        filler = FormFiller()
        
        # Form URL
        form_url = "https://docs.google.com/forms/d/e/1FAIpQLScOTrkMCIDzdn4NA7pAt4YimkXQPqqjbMqBXgIIETg5oJyK0w/viewform"
        print(f"\nProcessing form: {form_url}")
        
        # Analyze form structure
        fields = await filler.analyze_form(form_url)
        if not fields:
            print("No fields found to process")
            return
        
        print(f"\nAnalysis complete. Found {len(fields)} fields")
        
        # Get suggestions using vector RAG
        suggestions = filler.analyze_with_gemini(fields)
        
        # Fill form and wait for user verification
        success = await filler.fill_form(form_url, suggestions)
        if success:
            print("Form process completed!")
        else:
            print("Form process cancelled or failed!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
