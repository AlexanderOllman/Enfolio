from langchain_openai import OpenAI, ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os
import json
import requests
from urllib.parse import urljoin
import time
from werkzeug.utils import secure_filename

class ImageGenerator:
    def __init__(self, api_key=None):
        # Use provided API key or get from environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        print(f"API Key loaded (first 8 chars): {self.api_key[:8] if self.api_key else 'None'}")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

    def generate_image_prompt(self, title, description, type_content="project"):
        """Generate an optimal prompt for DALL-E image generation based on title and description"""
        
        # Configure the prompt template based on content type
        if type_content == "project":
            prompt_text = """
            You are an expert AI image prompt engineer. Generate a detailed image prompt for DALL-E to create
            a visually appealing featured image for a technology project with the following details:
            
            Title: {title}
            Description: {description}
            
            The image should represent the project professionally without text overlays.
            Make the prompt detailed (lighting, style, mood, perspective) but concise (max 200 characters).
            Generate only the prompt text that should be sent to DALL-E, nothing else.
            """
        elif type_content == "blog":
            prompt_text = """
            You are an expert AI image prompt engineer. Generate a detailed image prompt for DALL-E to create
            a visually appealing featured image for a blog post with the following details:
            
            Title: {title}
            Description: {description}
            
            The image should be eye-catching and relevant to the blog post topic without text overlays.
            Make the prompt detailed (lighting, style, mood, perspective) but concise (max 200 characters).
            Generate only the prompt text that should be sent to DALL-E, nothing else.
            """
        
        # Create the prompt template and chain
        prompt = PromptTemplate(
            input_variables=["title", "description"],
            template=prompt_text
        )
        
        try:
            # Initialize the language model
            print("Initializing ChatOpenAI with model: gpt-4o")
            llm = ChatOpenAI(
                model="gpt-4o",
                openai_api_key=self.api_key,
                temperature=0.7
            )
            
            # Create and run the chain
            print("Creating LLMChain and generating prompt")
            chain = LLMChain(llm=llm, prompt=prompt)
            result = chain.run(title=title, description=description)
            
            print(f"Generated prompt: {result[:50]}...")
            # Clean up the result
            return result.strip()
        except Exception as e:
            print(f"Error in generate_image_prompt: {str(e)}")
            raise

    def generate_image(self, prompt, size="1024x1024", quality="standard", upload_folder="app/static/uploads"):
        """Generate an image using OpenAI's DALL-E model"""
        
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality
        }
        
        print(f"Sending request to DALL-E API with prompt length: {len(prompt)}")
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            print(f"DALL-E API Response Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error response body: {response.text}")
                raise Exception(f"Error generating image: {response.text}")
            
            # Extract the image URL
            result = response.json()
            image_url = result["data"][0]["url"]
            print(f"Image URL received: {image_url[:30]}...")
            
            # Download the image
            image_response = requests.get(image_url)
            if image_response.status_code != 200:
                raise Exception("Failed to download generated image")
            
            # Save the image
            timestamp = int(time.time())
            filename = f"generated_{timestamp}.png"
            
            # Ensure upload directory exists
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            file_path = os.path.join(upload_folder, filename)
            
            with open(file_path, "wb") as f:
                f.write(image_response.content)
            
            print(f"Image saved to {file_path}")
            return filename
        except Exception as e:
            print(f"Error in generate_image: {str(e)}")
            raise

    def generate_content_image(self, title, description, type_content="project", upload_folder="app/static/uploads"):
        """Complete process to generate an image for content based on title and description"""
        
        # Validate inputs
        if not title or not description:
            raise ValueError("Title and description are required")
        
        # Generate the prompt
        print(f"Generating prompt for {type_content}: {title}")
        prompt = self.generate_image_prompt(title, description, type_content)
        
        # Generate and save the image
        print("Generating image from prompt")
        filename = self.generate_image(prompt, upload_folder=upload_folder)
        
        return filename 