# Automatic Form Filler using Gemini & Selenium

This project is an **Automatic Form Filler** that leverages the power of Google's Gemini large language model and Selenium WebDriver. With this tool, you can automate the process of filling out web forms using AI-generated responses, making tasks like testing, data entry, and web automation seamless and efficient.

## Features

- 📝 **AI-Powered Input Generation:** Uses Gemini to generate intelligent responses for form fields.
- 🌐 **Web Automation:** Automates any browser-based form using Selenium WebDriver.
- ⚡ **Customizable:** Easily adapt to various forms by updating configuration or prompts.
- 🔒 **Secure:** Handles sensitive data with care.
- 📄 **Extensible:** Add support for more websites and form types.

## How It Works

1. **Gemini Integration:** The tool sends form context or questions to Gemini, which generates suitable answers.
2. **Selenium Automation:** Selenium WebDriver interacts with the web form, filling in the fields with Gemini's responses.
3. **Submission:** Once all fields are populated, the form can be submitted automatically.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AnishKMBtech/Automatic-Form-Filler-Gemini-selenium-.git
   cd Automatic-Form-Filler-Gemini-selenium-
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   - Make sure you have [Python](https://www.python.org/) and [pip](https://pip.pypa.io/) installed.
   - If using Chrome, make sure to have the [ChromeDriver](https://sites.google.com/chromium.org/driver/) installed and in your PATH.

3. **Configure Gemini API:**
   - Obtain an API key for Google's Gemini LLM.
   - Set it as an environment variable or in the configuration file as needed.

## Usage

```bash
python form_filler.py --url "https://example.com/form"
```

- Update `form_filler.py` or the config to match the form fields and prompts.
- You may specify additional parameters, such as form selectors or user profile data.

## Example

Automate filling a sample registration form:

```bash
python form_filler.py --url "https://sample-website.com/register"
```

The script will:
- Load the registration page
- Use Gemini to generate realistic user data
- Fill and optionally submit the form

## Configuration

- **form_filler.py:** Main script for automation.
- **config.json:** (If present) Customize form fields, selectors, and Gemini prompts.
- **requirements.txt:** Python dependencies.

## Dependencies

- [Selenium](https://selenium.dev/)
- [Gemini API Client](#) (*Add link to the Gemini Python client*)
- [Any other libraries you use...]

## Limitations & Notes

- Only works on forms accessible via a direct URL.
- Some complex or JavaScript-heavy forms may require additional handling.
- Ensure compliance with web terms of service and privacy policies when automating.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

[MIT](LICENSE)

## Author

- [AnishKMBtech](https://github.com/AnishKMBtech)

---

*This project is not affiliated with Google or Selenium. Use responsibly.*
