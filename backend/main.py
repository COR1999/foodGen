# main2.py - The final, working version with stricter AI prompt.

import modal
import os
from pydantic import BaseModel
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- 1. SETUP MODAL APP AND CACHING ---
app = modal.App("recipe-generator-final-test")
model_cache_volume = modal.Volume.from_name(
    "recipe-cache-final-test", create_if_missing=True
)
CACHE_PATH = "/model-cache"

# --- 2. DEFINE THE IMAGE FROM requirements.txt ---
image = (
    modal.Image.debian_slim()
    .pip_install_from_requirements("requirements.txt")
)

# --- 3. DEFINE DATA MODELS ---
class RecipeRequest(BaseModel):
    ingredients: list[str]
    cuisine: str | None = None
    cook_time: str | None = None

class StructuredRecipe(BaseModel):
    title: str
    description: str
    ingredients: list[str] # Expecting a list of strings
    instructions: list[str] # Expecting a list of strings
    cook_time: str
    cuisine: str

# --- 4. A PLAIN PYTHON CLASS TO HOLD THE MODEL ---
class Model:
    def __init__(self):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

        model_name = "mistralai/Mistral-7B-Instruct-v0.2"
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
        print(f"Loading model from cache path: {CACHE_PATH}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, cache_dir=CACHE_PATH
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            quantization_config=quantization_config,
            cache_dir=CACHE_PATH
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        print("Model loaded successfully.")

    def generate(self, request: RecipeRequest) -> StructuredRecipe:
        prompt_parts = [f"Ingredients: {', '.join(request.ingredients)}."]
        if request.cuisine: prompt_parts.append(f"Cuisine: {request.cuisine}.")
        if request.cook_time: prompt_parts.append(f"Desired Cook Time: {request.cook_time}.")
        user_prompt = " ".join(prompt_parts)

        # -------------------------------------------------------------------
        # ## CRITICAL FIX: Make the system prompt EXTREMELY explicit about the JSON format
        # -------------------------------------------------------------------
        system_prompt = f"""
        You are a culinary assistant that creates delicious recipes. Based on the user's request, generate a single recipe.
        You must respond ONLY with a valid JSON object. Do not include any other text, markdown formatting (like ```json), or explanations.

        The JSON object MUST have the following exact structure and field types:

        ```json
        {{
          "title": "string",
          "description": "string",
          "ingredients": [
            "string - e.g., 4 Salmon fillets",
            "string - e.g., 1 head Broccoli, chopped"
          ],
          "instructions": [
            "string - e.g., Preheat oven to 400°F (200°C).",
            "string - e.g., Place salmon on a baking sheet."
          ],
          "cook_time": "string - e.g., Approx. 25 minutes",
          "cuisine": "string - e.g., Asian"
        }}
        ```
        Ensure 'ingredients' and 'instructions' are lists of strings, NOT lists of objects.
        All fields are required. Provide valid values for cook_time and cuisine.
        """
        # -------------------------------------------------------------------
        
        chat = [{"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}]
        
        formatted_prompt = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs, max_new_tokens=1024, pad_token_id=self.tokenizer.eos_token_id,
            do_sample=True, temperature=0.7, top_p=0.95
        )
        
        response_text = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)

        try:
            data = json.loads(response_text)
            # ## Keep the flexible parsing for 'recipe' key in case AI still adds it
            recipe_data = data.get("recipe", data) 
            return StructuredRecipe(**recipe_data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing JSON from model response: {e}")
            print(f"Model raw response: {response_text}")
            # If parsing fails, try to return a default or re-raise with more context
            raise ValueError(f"Failed to parse AI output into StructuredRecipe. Raw AI response: {response_text}. Error: {e}")


# --- 5. THE WEB SERVER FUNCTION ---
@app.function(
    image=image,
    gpu="A10G",
    volumes={CACHE_PATH: model_cache_volume},
    scaledown_window=300
)
@modal.asgi_app()
def fastapi_app():
    web_app = FastAPI()
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    model = Model() # Load the model once per container startup

    @web_app.post("/")
    def generate_recipe(request: RecipeRequest) -> StructuredRecipe:
        return model.generate(request)

    return web_app