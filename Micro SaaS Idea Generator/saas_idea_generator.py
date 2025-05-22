import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SaasIdeaGenerator:
    """A Micro SaaS Idea Generator that uses Google's Gemini Pro API.
    
    This agent generates AI-powered business ideas for micro SaaS applications
    based on various inputs like target industry, user pain points,
    and technical capabilities.
    """
    
    def __init__(self):
        # Configure the Gemini API
        self.api_key = "AIzaSyCSsKqcpqyepPqJoA7Kqq21WHPZWQRi51A"
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in the .env file.")
        
        try:
            genai.configure(api_key=self.api_key)
            # Set up the model
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Gemini model: {str(e)}")
            
        # Define available options for users
        self.industries = [
            "Healthcare", "Education", "Finance", "E-commerce", 
            "Real Estate", "Legal", "Food & Beverage", "Travel", 
            "Entertainment", "Fitness", "Marketing", "HR & Recruitment",
            "Logistics", "Manufacturing", "Freelancing", "Non-profit"
        ]
        self.tech_stacks = [
            "Web App (React/Node.js)", "Mobile App (React Native)", 
            "Chrome Extension", "WordPress Plugin", "Slack App",
            "Desktop Application", "API Service", "AI-powered Tool",
            "Shopify App", "Automation Tool", "Data Analytics Dashboard"
        ]
    
    def generate_prompt(self, industry=None, pain_point=None, tech_stack=None):
        """Generate a prompt for the LLM based on the inputs."""
        industry_text = f"in the {industry} industry" if industry else "in any promising industry"
        tech_text = f"using {tech_stack}" if tech_stack else "using any suitable technology stack"
        pain_text = f"that solves the problem of '{pain_point}'" if pain_point else "that solves a valuable problem"
        
        prompt = f"""
        Generate a detailed micro-SaaS business idea {industry_text} {tech_text} {pain_text}.

        Your response should be in JSON format with the following structure:
        {{
            "name": "A catchy product name that's memorable and describes the function",
            "description": "A clear description of what the product does and the value it provides",
            "industry": "The specific industry this serves",
            "tech_stack": "The technology stack that would be ideal for building this differentiate with front end, back end and database",
            "key_features": ["Feature 1", "Feature 2", "Feature 3"],
            "target_customers": "Description of the ideal customer",
            "development_time": "Estimated time to develop an MVP",
            "monetization": "Best pricing model and price point"
        }}

        Be creative and practical. Focus on an idea that:
        1. Could be built by a small team or solo developer
        2. Solves a real problem in the target industry
        3. Has clear monetization potential
        4. Is specific enough to be actionable
        5. Would be technically feasible with the specified technology
        
        Return ONLY the JSON with no additional text.
        """
        return prompt

    def generate_idea(self, industry=None, pain_point=None, tech_stack=None):
        """Generate a micro SaaS idea based on provided parameters using Gemini Pro.
        
        Args:
            industry (str, optional): Target industry for the SaaS idea
            pain_point (str, optional): Specific problem to solve
            tech_stack (str, optional): Preferred technology stack
            
        Returns:
            dict: A dictionary containing the generated SaaS idea details
            
        Raises:
            ValueError: If API key is invalid or expired
            ConnectionError: If there's an issue connecting to the API
            RuntimeError: For other API-related issues
        """
        # Generate the prompt for the LLM
        prompt = self.generate_prompt(industry, pain_point, tech_stack)
        
        try:
            # Send request to the model
            response = self.model.generate_content(prompt)
            
            # Try to parse the JSON response
            try:
                # Extract the text from the response
                text = response.text.strip()
                
                # Sometimes the AI includes ```json and ``` around the response, so we remove those
                if text.startswith('```json'):
                    text = text[7:]
                if text.endswith('```'):
                    text = text[:-3]
                
                # Parse the JSON
                return json.loads(text.strip())
            
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Failed to parse JSON response from Gemini: {str(e)}")
        
        except Exception as e:
            error_message = str(e).lower()
            
            if "api key" in error_message and ("invalid" in error_message or "expired" in error_message):
                raise ValueError("Your Gemini API key appears to be invalid or expired. Please get a new key from https://aistudio.google.com/app/apikey")
            elif "quota" in error_message or "limit" in error_message:
                raise ValueError("You've reached your API quota limit. Please try again later or get a different API key.")
            elif "connect" in error_message or "timeout" in error_message:
                raise ConnectionError(f"Failed to connect to Gemini API: {str(e)}")
            else:
                raise RuntimeError(f"Error generating idea with Gemini: {str(e)}") 