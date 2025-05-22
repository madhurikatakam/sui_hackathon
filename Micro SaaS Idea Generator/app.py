import gradio as gr
from saas_idea_generator import SaasIdeaGenerator
import random
# Initialize error flag for checking API key validity
api_initialized = False

try:
    # Initialize our generator
    idea_generator = SaasIdeaGenerator()
    api_initialized = True
except ValueError as e:
    # API key related errors
    error_message = str(e)
    print(f"API Key Error: {error_message}")
except ConnectionError as e:
    # Connection related errors
    error_message = str(e)
    print(f"Connection Error: {error_message}")
except Exception as e:
    # General errors
    error_message = f"Unexpected error: {str(e)}"
    print(error_message)

def generate_idea(industry, pain_point, tech_stack):
    """Generate a SaaS idea based on user inputs"""
    
    if not api_initialized:
        return """
        ## ⚠️ API Key Error
        
        Unable to initialize the Gemini API. Please check your API key in the .env file.
        
        The most common issues are:
        1. Missing API key - Make sure you've created a .env file with GEMINI_API_KEY=your_key
        2. Invalid or expired API key - Get a new key from https://aistudio.google.com/app/apikey
        3. API quota limit reached - Wait a while or create a new key
        """
    
    # Format inputs for the generator
    industry_input = random.choice(idea_generator.industries) if industry == "Random" else industry
    tech_stack_input = random.choice(idea_generator.tech_stacks) if tech_stack == "Random" else tech_stack
    pain_point_input = None if not pain_point.strip() else pain_point
    

        # Generate the idea using the API
    idea = idea_generator.generate_idea(
        industry=industry_input,
        pain_point=pain_point_input, 
        tech_stack=tech_stack_input
    )
    
        # Format the output for display
    output = f"""
## {idea['name']}

**Description:** {idea['description']}

**Industry:** {idea['industry']}

**Tech Stack:** {idea['tech_stack']}

### Key Features:
{'\n'.join(['- ' + feature for feature in idea['key_features']])}

**Target Customers:** {idea['target_customers']}

**Estimated Development Time:** {idea['development_time']}

**Monetization Strategy:** {idea['monetization']}
"""
    return output
    

# Create the Gradio interface
with gr.Blocks(title="Micro SaaS Idea Generator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 Micro SaaS Idea Generator")
    gr.Markdown("Generate your next profitable micro-SaaS business idea in seconds!")
    
    if not api_initialized:
        gr.Markdown("### ⚠️ API Key Not Configured")
        gr.Markdown(
            """
            Please follow these steps to configure your API key:
            
            1. Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
            2. Create a file named `.env` in the project root
            3. Add your key to the file: `GEMINI_API_KEY=your_actual_key_here`
            4. Restart the application
            """
        )
    
    with gr.Row():
        with gr.Column():
            # Input components
            industries =  ["Random"] + (idea_generator.industries if api_initialized else [])
            tech_stacks = ["Random"] + (idea_generator.tech_stacks if api_initialized else [])
            
            industry_dropdown = gr.Dropdown(
                choices=industries,
                value="Random", 
                label="Target Industry"
            )
            
            tech_stack_dropdown = gr.Dropdown(
                choices=tech_stacks, 
                value="Random", 
                label="Tech Stack"
            )
            
            pain_point_input = gr.Textbox(
                placeholder="e.g., managing employee time-off requests", 
                label="Pain Point (Optional)"
            )
            
            generate_button = gr.Button(
                "Generate Idea 💡", 
                variant="primary",
                interactive=api_initialized
            )
        
        with gr.Column():
            # Output component
            output_box = gr.Markdown(label="Generated Idea")
    
    # Set up the click event
    generate_button.click(
        generate_idea,
        inputs=[industry_dropdown, pain_point_input, tech_stack_dropdown],
        outputs=output_box
    )
    
    gr.Markdown("### How to Use")
    gr.Markdown(
        """
        1. Select a target industry or leave as "Random"
        2. Select a tech stack or leave as "Random"
        3. Optionally, specify a pain point you want to solve
        4. Click "Generate Idea" to get your micro-SaaS business idea
        """
    )
    

if __name__ == "__main__":
    demo.launch() 