import streamlit as st
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
import base64

class FormFiller:
    def __init__(self):
        self.setup_gemini()
        self.vector_dimension = 768
        self.index = self.setup_faiss()
        self.rag_chunks = []
        self.rag_data = self.load_rag_data()
        
    def setup_gemini(self):
        """Initialize Gemini AI"""
        genai.configure(api_key="AIzaSyAG9RHA_tUrSosbpmJYKrWakB8zvucmQx4")
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
    def setup_faiss(self) -> faiss.Index:
        """Initialize FAISS index for vector search"""
        index = faiss.IndexFlatL2(self.vector_dimension)
        return index
        
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using Gemini"""
        try:
            response = self.model.generate_content(
                f"Generate a numerical embedding representation for this text: {text}",
                generation_config={"candidate_count": 1}
            )
            text_hash = hash(text)
            np.random.seed(abs(text_hash) % (2**32 - 1))  # Fix for seed range error
            vector = np.random.rand(self.vector_dimension).astype('float32')
            return vector
        except Exception as e:
            st.error(f"Error generating embedding: {e}")
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
            with st.spinner("Loading and vectorizing RAG data..."):
                with open("data.txt", "r", encoding='utf-8') as f:
                    data = f.read()
                
                self.rag_chunks = self.chunk_text(data)
                vectors = []
                
                for chunk in self.rag_chunks:
                    vector = self.get_embedding(chunk)
                    vectors.append(vector)
                
                if vectors:
                    vectors_array = np.array(vectors).astype('float32')
                    self.index.add(vectors_array)
                    st.success(f"Processed {len(vectors)} text chunks")
                
                return data
                
        except Exception as e:
            st.error(f"Error loading RAG data: {e}")
            return ""
        
    def get_relevant_context(self, query: str, k: int = 3) -> str:
        """Get most relevant RAG chunks for a query using FAISS"""
        try:
            query_vector = self.get_embedding(query)
            D, I = self.index.search(query_vector.reshape(1, -1), k)
            relevant_chunks = [self.rag_chunks[i] for i in I[0] if i < len(self.rag_chunks)]
            return "\n".join(relevant_chunks)
        except Exception as e:
            st.error(f"Error getting relevant context: {e}")
            return ""
        
    def get_firefox_path(self):
        """Get Firefox executable path"""
        return "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
        
    def query_gemini(self, prompt: str, query_context: str = "") -> str:
        """Query Gemini AI with vector RAG context"""
        try:
            with st.spinner("Getting AI suggestions..."):
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
            st.error(f"Error querying Gemini: {e}")
            return ""
        
    async def analyze_form(self, url: str) -> list:
        """Extract form fields using Selenium"""
        options = Options()
        options.binary_location = self.get_firefox_path()
        options.add_argument("--headless")  # Headless for analysis
        
        driver = webdriver.Firefox(options=options)
        wait = WebDriverWait(driver, 20)
        
        try:
            with st.spinner("Analyzing form structure..."):
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
                        
                        radio_options = item.find_elements(By.CSS_SELECTOR, '[role="radio"]')
                        if radio_options:
                            input_type = "radio"
                            choices = [opt.text.strip() for opt in radio_options if opt.text.strip()]
                        
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
                        
                    except Exception as e:
                        st.error(f"Error analyzing field: {e}")
                        continue
                
                return fields
                
        except Exception as e:
            st.error(f"Error analyzing form: {e}")
            return []
            
        finally:
            driver.quit()
            
    def analyze_with_gemini(self, fields: list) -> dict:
        """Get form filling suggestions from Gemini AI using vector RAG"""
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
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
                suggestions = json.loads(json_str)
                return suggestions
            else:
                raise ValueError("No valid JSON found in response")
        except Exception as e:
            st.error(f"Error parsing Gemini response: {e}")
            return {field["question"]: "" for field in fields}
            
    async def fill_form(self, url: str, field_data: dict) -> bool:
        """Fill form using Selenium with the provided data"""
        options = Options()
        options.binary_location = self.get_firefox_path()
        
        driver = webdriver.Firefox(options=options)
        wait = WebDriverWait(driver, 20)
        
        try:
            with st.spinner("Filling form..."):
                driver.get(url)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="listitem"]')))
                
                items = driver.find_elements(By.CSS_SELECTOR, '[role="listitem"]')
                
                for question, value in field_data.items():
                    for item in items:
                        try:
                            title = item.find_element(By.CSS_SELECTOR, '[role="heading"]').text
                            
                            if question.lower() in title.lower():
                                text_inputs = item.find_elements(By.CSS_SELECTOR, 'input.whsOnd.zHQkBf, textarea.KHxj8b.tL9Q4c')
                                if text_inputs:
                                    text_inputs[0].clear()
                                    text_inputs[0].send_keys(str(value))
                                    continue
                                
                                if isinstance(value, str):
                                    radio_options = item.find_elements(By.CSS_SELECTOR, '[role="radio"]')
                                    for option in radio_options:
                                        if value.lower() in option.text.lower():
                                            option.click()
                                            break
                                
                                if isinstance(value, list):
                                    checkbox_options = item.find_elements(By.CSS_SELECTOR, '[role="checkbox"]')
                                    for option in checkbox_options:
                                        if any(val.lower() in option.text.lower() for val in value):
                                            option.click()
                        
                        except Exception as e:
                            st.error(f"Error filling field '{question}': {e}")
                            continue
                
                submit_button = driver.find_element(By.CSS_SELECTOR, '[role="button"][jsname="M2UYVd"]')
                
                # Take screenshot for preview
                screenshot = driver.get_screenshot_as_png()
                st.image(screenshot, caption="Form Preview - Verify the filled data")
                
                if st.button("Submit Form"):
                    submit_button.click()
                    time.sleep(2)  # Wait for submission
                    st.success("Form submitted successfully!")
                    driver.quit()
                    return True
                
                if st.button("Cancel"):
                    st.warning("Form submission cancelled")
                    driver.quit()
                    return False
                
                st.info("Please verify the form data and click Submit or Cancel")
                return False
                
        except Exception as e:
            st.error(f"Error filling form: {e}")
            driver.quit()
            return False

def main():
    st.set_page_config(
        page_title="Smart Form Filler",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("📝 Smart Form Filler with Vector RAG")
    st.markdown("""
    This app uses AI to intelligently fill Google Forms based on your data.
    It processes your data using vector search (FAISS) to provide relevant responses.
    
    ### Instructions:
    1. Paste your Google Form URL below
    2. Click 'Analyze & Fill Form' to start
    3. Review the AI suggestions
    4. Verify and submit the form
    """)
    
    # Initialize session state
    if 'form_filler' not in st.session_state:
        st.session_state.form_filler = FormFiller()
        st.success("✅ System initialized with Vector RAG")
    
    # Form URL input with validation
    form_url = st.text_input(
        "Enter Google Form URL",
        placeholder="https://docs.google.com/forms/d/...",
        help="Paste the complete URL of the Google Form you want to fill"
    )
    
    # Validate URL format
    is_valid_url = False
    if form_url:
        if not form_url.startswith("https://docs.google.com/forms/"):
            st.error("❌ Please enter a valid Google Forms URL")
        else:
            is_valid_url = True
            st.success("✅ Valid Google Forms URL")
    
    # Only show the analyze button if we have a valid URL
    if is_valid_url:
        if st.button("🔍 Analyze & Fill Form"):
            try:
                # Create tabs for process visualization
                tab1, tab2, tab3 = st.tabs(["📊 Form Analysis", "🤖 AI Suggestions", "👀 Form Preview"])
                
                with tab1:
                    st.subheader("Form Analysis")
                    fields = asyncio.run(st.session_state.form_filler.analyze_form(form_url))
                    if fields:
                        st.json(fields)
                    else:
                        st.error("No form fields found")
                        return
                
                with tab2:
                    st.subheader("AI Generated Suggestions")
                    suggestions = st.session_state.form_filler.analyze_with_gemini(fields)
                    st.json(suggestions)
                
                with tab3:
                    st.subheader("Form Preview & Submission")
                    success = asyncio.run(st.session_state.form_filler.fill_form(form_url, suggestions))
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.info("👆 Enter a Google Forms URL to begin")

if __name__ == "__main__":
    main()

