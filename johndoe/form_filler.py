from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import asyncio
import json
import requests
import os

class FormFiller:
    def __init__(self):
        self.ollama_endpoint = "http://localhost:11434/api/generate"
        
    def get_firefox_path(self):
        """Get Firefox executable path"""
        return "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
        
    async def analyze_form(self, url):
        """Extract form fields using Selenium with Firefox"""
        print("\nStarting form analysis...")
        
        # Set up Firefox options
        options = Options()
        options.binary_location = self.get_firefox_path()
        options.add_argument("--start-maximized")
        
        # Create Firefox driver
        driver = webdriver.Firefox(options=options)
        wait = WebDriverWait(driver, 20)
        
        try:
            print(f"\nNavigating to form: {url}")
            driver.get(url)
            
            # Wait for form elements to load
            print("Waiting for form to load...")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="listitem"]')))
            
            # Find all form items
            items = driver.find_elements(By.CSS_SELECTOR, '[role="listitem"]')
            print(f"Found {len(items)} form items")
            
            fields = []
            for item in items:
                try:
                    # Get question text
                    title = ""
                    title_selectors = [
                        '[role="heading"]',
                        '.freebirdFormviewerComponentsQuestionBaseHeader',
                        '.freebirdFormviewerViewItemsItemItemTitle'
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = item.find_element(By.CSS_SELECTOR, selector)
                            title = title_elem.text
                            if title and title.strip():
                                break
                        except:
                            continue
                            
                    if not title or not title.strip():
                        continue
                        
                    # Determine input type and get choices
                    input_type = "text"  # default
                    choices = []
                    
                    # Check for radio buttons
                    try:
                        radio_options = item.find_elements(By.CSS_SELECTOR, '[role="radio"]')
                        if radio_options:
                            input_type = "radio"
                            for opt in radio_options:
                                opt_text = opt.text
                                if opt_text and opt_text.strip():
                                    choices.append(opt_text.strip())
                    except:
                        pass
                        
                    # Check for checkboxes if no radio buttons
                    if not choices:
                        try:
                            checkbox_options = item.find_elements(By.CSS_SELECTOR, '[role="checkbox"]')
                            if checkbox_options:
                                input_type = "checkbox"
                                for opt in checkbox_options:
                                    opt_text = opt.text
                                    if opt_text and opt_text.strip():
                                        choices.append(opt_text.strip())
                        except:
                            pass
                            
                    # Check for text input if no choices
                    if not choices:
                        try:
                            text_inputs = item.find_elements(By.CSS_SELECTOR, 'input[type="text"], textarea, [role="textbox"]')
                            if text_inputs:
                                input_type = "text"
                        except:
                            pass
                            
                    # Check if required
                    required = False
                    required_selectors = [
                        '[aria-label*="Required"]',
                        '.freebirdFormviewerComponentsQuestionBaseRequiredAsterisk'
                    ]
                    
                    for selector in required_selectors:
                        try:
                            required_elem = item.find_element(By.CSS_SELECTOR, selector)
                            if required_elem:
                                required = True
                                break
                        except:
                            continue
                            
                    field_info = {
                        "question": title.strip(),
                        "type": input_type,
                        "required": required,
                        "options": choices
                    }
                    fields.append(field_info)
                    print(f"\nDetected field: {json.dumps(field_info, indent=2)}")
                    
                except Exception as e:
                    print(f"Error analyzing item: {str(e)}")
                    continue
                    
            if not fields:
                print("\nNo fields were successfully analyzed!")
            else:
                print(f"\nSuccessfully analyzed {len(fields)} fields")
                
            return fields
            
        except Exception as e:
            print(f"Error during form analysis: {str(e)}")
            return []
            
        finally:
            driver.quit()
            
    async def fill_form(self, url, field_data):
        """Fill form using Selenium with Firefox"""
        if not field_data:
            print("No field data to fill!")
            return
            
        # Set up Firefox options
        options = Options()
        options.binary_location = self.get_firefox_path()
        options.add_argument("--start-maximized")
        
        # Create Firefox driver
        driver = webdriver.Firefox(options=options)
        wait = WebDriverWait(driver, 20)
        
        try:
            print(f"\nNavigating to form: {url}")
            driver.get(url)
            
            # Wait for form elements to load
            print("Waiting for form to load...")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="listitem"]')))
            
            # Find all form items
            items = driver.find_elements(By.CSS_SELECTOR, '[role="listitem"]')
            
            print("\nFilling form fields...")
            for question, value in field_data.items():
                try:
                    # Find matching question
                    for item in items:
                        try:
                            title = item.find_element(By.CSS_SELECTOR, '[role="heading"]').text
                            
                            if question.lower() in title.lower():
                                print(f"\nFilling field: {question}")
                                
                                # Handle text inputs
                                try:
                                    text_inputs = item.find_elements(By.CSS_SELECTOR, 'input.whsOnd.zHQkBf, textarea.KHxj8b.tL9Q4c')
                                    if text_inputs:
                                        text_inputs[0].clear()  # Clear any existing text
                                        text_inputs[0].send_keys(str(value))
                                        print(f"Filled text with: {value}")
                                        continue
                                except Exception as e:
                                    print(f"Error filling text input: {str(e)}")
                                    pass
                                    
                                # Handle radio buttons
                                try:
                                    radio_options = item.find_elements(By.CSS_SELECTOR, '[role="radio"]')
                                    for option in radio_options:
                                        if str(value).lower() in option.text.lower():
                                            option.click()
                                            print(f"Selected radio: {option.text}")
                                            break
                                except:
                                    pass
                                    
                                # Handle checkboxes
                                try:
                                    checkbox_options = item.find_elements(By.CSS_SELECTOR, '[role="checkbox"]')
                                    if checkbox_options:
                                        values = [value] if not isinstance(value, list) else value
                                        for option in checkbox_options:
                                            for val in values:
                                                if str(val).lower() in option.text.lower():
                                                    option.click()
                                                    print(f"Checked: {option.text}")
                                except:
                                    pass
                                    
                        except Exception as e:
                            print(f"Error with item: {str(e)}")
                            continue
                            
                except Exception as e:
                    print(f"Error filling {question}: {str(e)}")
                    continue
                    
            # Find and click submit button
            print("\nLooking for submit button...")
            submit_selectors = [
                'div[role="button"][jsname="M2UYVd"]',
                '.freebirdFormviewerViewNavigationSubmitButton',
                'div[jscontroller="soHxf"][jsname="M2UYVd"]'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if "submit" in button.text.lower():
                            submit_button = button
                            break
                except:
                    continue
                    
            if submit_button:
                print("Clicking submit button...")
                submit_button.click()
                print("Form submitted!")
                # Wait to see confirmation
                await asyncio.sleep(2)
            else:
                print("No submit button found!")
                
        except Exception as e:
            print(f"Error during form interaction: {str(e)}")
            
        finally:
            driver.quit()

    def match_data(self, fields, data_dict):
        """Match data with form fields using Ollama"""
        if not fields:
            print("No fields to match!")
            return {}
            
        prompt = f"""Given these Google Form fields:
{json.dumps(fields, indent=2)}

And this user data:
{json.dumps(data_dict, indent=2)}

Create a mapping between questions and appropriate answers. Consider:
1. Question text and expected data type
2. Available options for multiple choice questions
3. Required fields

Return ONLY a JSON object mapping questions to their answers. Example:
{{"What is your name?": "John Doe"}}"""
        
        payload = {
            "model": "gemma3:1b",
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(self.ollama_endpoint, json=payload)
        if response.status_code == 200:
            result = response.json()
            try:
                response_text = result['response']
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = response_text[start:end]
                    matches = json.loads(json_str)
                    print("\nMatched fields:")
                    print(json.dumps(matches, indent=2))
                    return matches
                else:
                    return {}
            except json.JSONDecodeError:
                print("Warning: Could not parse Ollama response as JSON")
                return {}
        else:
            raise Exception(f"Error from Ollama API: {response.text}")

# Example usage
if __name__ == "__main__":
    # Sample data that would be scraped
    sample_data = {
        "What is your name?": "John Doe",
        "What is your email?": "john@example.com",
        "What is your phone number?": "123-456-7890"
    }
    
    filler = FormFiller()
    
    # Analyze form from URL
    form_url = "https://docs.google.com/forms/d/e/your-form-id/viewform"
    asyncio.run(filler.analyze_form(form_url))
    
    # Match data with fields
    fields = asyncio.run(filler.analyze_form(form_url))
    matches = filler.match_data(fields, sample_data)
    print("Field Matches:", matches)
    
    # Fill the form
    asyncio.run(filler.fill_form(form_url, matches))
