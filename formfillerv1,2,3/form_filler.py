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

class FormFiller:
    def __init__(self):
        self.setup_gemini()
        self.rag_data = self.load_rag_data()
        print("\nInitialized FormFiller with RAG data")
        
    def setup_gemini(self):
        """Initialize Gemini AI"""
        genai.configure(api_key="AIzaSyAG9RHA_tUrSosbpmJYKrWakB8zvucmQx4")
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        print("\nGemini AI initialized")
        
    def load_rag_data(self):
        """Load and process RAG data at startup"""
        try:
            print("\nLoading RAG data from data.txt...")
            with open("data.txt", "r", encoding='utf-8') as f:
                data = f.read()
                
            # Process the data with Gemini to create initial context
            print("Processing RAG data with Gemini...")
            response = self.model.generate_content("""
            Process and understand the following data. This will be used as context for form filling:
            
            {}
            
            Analyze the key information, entities, and relationships in this data.
            """.format(data))
            
            print("RAG data processed successfully")
            return data
            
        except Exception as e:
            print(f"Warning: Error loading RAG data: {e}")
            return ""
        
    def get_firefox_path(self):
        """Get Firefox executable path"""
        return "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
        
    def query_gemini(self, prompt: str) -> str:
        """Query Gemini AI with RAG context"""
        try:
            # Always include RAG data in the context
            full_prompt = f"""
            Reference Knowledge Base:
            {self.rag_data}

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
        options.add_argument("--headless")
        
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
            
            return fields
            
        except Exception as e:
            print(f"Error analyzing form: {str(e)}")
            return []
        
        finally:
            driver.quit()
            
    def analyze_with_gemini(self, fields: list) -> dict:
        """Get form filling suggestions from Gemini AI using RAG data"""
        print("\nAnalyzing form fields with Gemini AI...")
        
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
        
        response = self.query_gemini(prompt)
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
                suggestions = json.loads(json_str)
                print("\nGenerated suggestions based on RAG data:")
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
        options.add_argument("--headless")
        
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
            
            # Find and click submit button
            submit_button = driver.find_element(By.CSS_SELECTOR, '[role="button"][jsname="M2UYVd"]')
            submit_button.click()
            print("\nForm submitted successfully!")
            
            return True
            
        except Exception as e:
            print(f"Error filling form: {str(e)}")
            return False
        
        finally:
            driver.quit()

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
        
        # Get suggestions using RAG data
        suggestions = filler.analyze_with_gemini(fields)
        
        if input("\nProceed with form submission? (y/n): ").lower() == 'y':
            success = await filler.fill_form(form_url, suggestions)
            if success:
                print("Form submission completed!")
            else:
                print("Form submission failed!")
        else:
            print("Form submission cancelled.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
