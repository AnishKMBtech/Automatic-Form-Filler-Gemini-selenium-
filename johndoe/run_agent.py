import asyncio
from form_filler import FormFiller
import sys

async def main():
    try:
        # Initialize the form filler
        filler = FormFiller()
        
        # Sample data to fill in the form
        sample_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "123-456-7890",
            "age": "25-34",
            "interests": ["Technology", "Science"],
            "message": "This is a test message"
        }
        
        # Form URL (replace with your actual form URL)
        form_url = "https://docs.google.com/forms/d/e/1FAIpQLScOTrkMCIDzdn4NA7pAt4YimkXQPqqjbMqBXgIIETg5oJyK0w/viewform"
        print("Starting form analysis...")
        print("Form URL:", form_url)
        
        print("\nAnalyzing form fields...")
        try:
            fields = await filler.analyze_form(form_url)
            print(f"\nAnalysis complete. Found {len(fields) if fields else 0} fields")
        except Exception as e:
            print(f"Error during form analysis: {str(e)}", file=sys.stderr)
            return
        
        if not fields:
            print("No fields found to process")
            return
            
        print("\nMatching data to fields...")
        try:
            matches = filler.match_data(fields, sample_data)
            print(f"Found {len(matches) if matches else 0} field matches")
        except Exception as e:
            print(f"Error during data matching: {str(e)}", file=sys.stderr)
            return
        
        if not matches:
            print("No matches found to fill")
            return
            
        print("\nFilling form...")
        try:
            await filler.fill_form(form_url, matches)
            print("Form filling complete!")
        except Exception as e:
            print(f"Error during form filling: {str(e)}", file=sys.stderr)

    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
