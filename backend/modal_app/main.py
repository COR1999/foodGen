# modal_app/main.py - Complete single file version
import modal
import os
import json
import re
import boto3
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ==================== DATA MODELS ====================


class RecipeRequest(BaseModel):
    ingredients: list[str]
    cuisine: str | None = None
    cook_time: str | None = None


class StructuredRecipe(BaseModel):
    title: str
    description: str
    ingredients: list[str]
    instructions: list[str]
    cook_time: str
    cuisine: str


class RecipeResponse(BaseModel):
    recipe: StructuredRecipe
    source: str
    match_score: Optional[float] = None

# ==================== CONFIGURATION ====================


class Config:
    MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
    CACHE_PATH = "/model-cache"
    MIN_MATCH_SCORE = 0.6
    COOK_TIME_WEIGHT = 0.9

# ==================== S3 MANAGER ====================


class S3Manager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
        self.bucket_name = os.environ.get("S3_BUCKET_NAME")

    def upload_to_s3(self, content: str, folder: str = "responses") -> str:
        """Upload content to S3 and return the object key"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            object_key = f"model_responses/{folder}/{timestamp}.json"

            self.s3_client.put_object(
                Body=content.encode('utf-8'),
                Bucket=self.bucket_name,
                Key=object_key,
                ContentType='application/json'
            )

            print(f"✅ Uploaded to s3://{self.bucket_name}/{object_key}")
            return object_key
        except Exception as e:
            print(f"⚠️ S3 upload failed: {e}")
            return ""

    def get_all_recipes(self) -> List[Dict]:
        """Get all recipes from S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="model_responses/generated_recipes/"
            )

            recipes = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    try:
                        file_obj = self.s3_client.get_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        recipe_data = json.loads(
                            file_obj['Body'].read().decode('utf-8'))
                        recipes.append(recipe_data)
                    except Exception as e:
                        print(f"Error loading recipe {obj['Key']}: {e}")
                        continue

            return recipes
        except Exception as e:
            print(f"Error fetching recipes from S3: {e}")
            return []

    def get_recipe(self, filename: str) -> Dict:
        """Get a specific recipe from S3"""
        try:
            object_key = f"model_responses/generated_recipes/{filename}"
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except Exception as e:
            print(f"Error fetching recipe: {e}")
            return {}

    def list_recipe_files(self) -> List[Dict]:
        """List all recipe files metadata"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="model_responses/generated_recipes/"
            )

            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'filename': obj['Key'].split('/')[-1]
                    })

            return files
        except Exception as e:
            print(f"Error listing recipes: {e}")
            return []

# ==================== RECIPE MATCHER ====================


class RecipeMatcher:
    """Handles recipe matching logic"""

    @staticmethod
    def calculate_ingredient_match(user_ingredients: List[str], recipe_ingredients: List[str]) -> float:
        """
        Calculate how well the recipe matches the user's ingredients
        Returns a score between 0 and 1
        """
        user_ing_normalized = [ing.lower().strip() for ing in user_ingredients]

        match_count = 0
        for user_ing in user_ing_normalized:
            for recipe_ing in recipe_ingredients:
                recipe_ing_lower = recipe_ing.lower()
                if user_ing in recipe_ing_lower or any(word in recipe_ing_lower for word in user_ing.split()):
                    match_count += 1
                    break

        return match_count / len(user_ing_normalized) if user_ing_normalized else 0

    @staticmethod
    def matches_criteria(recipe_data: Dict, request: RecipeRequest, min_match_score: float = None) -> Tuple[bool, float]:
        """
        Check if a recipe matches the user's criteria
        Returns (matches: bool, score: float)
        """
        if min_match_score is None:
            min_match_score = Config.MIN_MATCH_SCORE

        recipe_ingredients = recipe_data.get('ingredients', [])
        match_score = RecipeMatcher.calculate_ingredient_match(
            request.ingredients, recipe_ingredients)

        if match_score < min_match_score:
            return False, match_score

        # Check cuisine if specified
        if request.cuisine:
            recipe_cuisine = recipe_data.get('cuisine', '').lower()
            if request.cuisine.lower() not in recipe_cuisine:
                return False, match_score

        # Check cook time if specified (optional)
        if request.cook_time:
            recipe_cook_time = recipe_data.get('cook_time', '').lower()
            if request.cook_time.lower() not in recipe_cook_time:
                match_score *= Config.COOK_TIME_WEIGHT

        return True, match_score

    @staticmethod
    def find_best_match(recipes: List[Dict], request: RecipeRequest) -> Optional[Tuple[StructuredRecipe, float]]:
        """
        Find the best matching recipe from a list of recipes
        Returns (recipe, match_score) if found, None otherwise
        """
        best_match = None
        best_score = 0.0

        for recipe_data in recipes:
            try:
                matches, score = RecipeMatcher.matches_criteria(
                    recipe_data, request)

                if matches and score > best_score:
                    best_score = score
                    recipe_clean = {
                        'title': recipe_data.get('title'),
                        'description': recipe_data.get('description'),
                        'ingredients': recipe_data.get('ingredients'),
                        'instructions': recipe_data.get('instructions'),
                        'cook_time': recipe_data.get('cook_time'),
                        'cuisine': recipe_data.get('cuisine')
                    }
                    best_match = StructuredRecipe(**recipe_clean)
                    print(
                        f"✅ Found matching recipe: {best_match.title} (score: {best_score:.2f})")

            except Exception as e:
                print(f"Error processing recipe: {e}")
                continue

        if best_match:
            print(f"🎯 Best match found with score: {best_score:.2f}")
            return best_match, best_score

        return None

# ==================== RECIPE MODEL ====================


class RecipeModel:
    """Main AI recipe generation model"""

    def __init__(self, cache_path: str):
        # Import torch/transformers here to avoid loading until needed
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        print(f"Loading model from cache path: {cache_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            Config.MODEL_NAME,
            cache_dir=cache_path
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            Config.MODEL_NAME,
            device_map="auto",
            quantization_config=quantization_config,
            cache_dir=cache_path
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # Initialize managers
        self.s3_manager = S3Manager()

        print("✅ Model loaded successfully.")

    def _clean_json_response(self, response_text: str) -> str:
        """Clean common JSON formatting issues from LLM responses"""
        response_text = re.sub(
            r'^```json\s*', '', response_text, flags=re.MULTILINE)
        response_text = re.sub(
            r'^```\s*$', '', response_text, flags=re.MULTILINE)
        response_text = response_text.strip()
        response_text = re.sub(r'\.\s*(\}|\])', r'\1', response_text)
        response_text = re.sub(r',\s*(\}|\])', r'\1', response_text)

        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            response_text = match.group(0)

        return response_text

    def search_s3_recipes(self, request: RecipeRequest) -> Optional[Tuple[StructuredRecipe, float]]:
        """
        Search S3 for existing recipes that match the request
        Returns (recipe, match_score) if found, None otherwise
        """
        print(f"🔍 Searching S3 for recipes matching: {request.ingredients}")

        recipes = self.s3_manager.get_all_recipes()
        if not recipes:
            print("No recipes found in S3")
            return None

        print(
            f"Found {len(recipes)} recipes in S3, searching for best match...")
        return RecipeMatcher.find_best_match(recipes, request)

    def generate_new_recipe(self, request: RecipeRequest) -> StructuredRecipe:
        """Generate a new recipe using the AI model"""
        prompt_parts = [f"Ingredients: {', '.join(request.ingredients)}."]
        if request.cuisine:
            prompt_parts.append(f"Cuisine: {request.cuisine}.")
        if request.cook_time:
            prompt_parts.append(f"Desired Cook Time: {request.cook_time}.")
        user_prompt = " ".join(prompt_parts)

        system_prompt = """You are a culinary assistant that creates delicious recipes. Based on the user's request, generate a single recipe.
        You must respond ONLY with a valid JSON object. Do not include any other text, markdown formatting (like ```json), or explanations.

        CRITICAL: The JSON must be perfectly valid. Do NOT add periods, commas, or any punctuation after the last field value before the closing brace.

        The JSON object MUST have the following exact structure:

        {
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
        }

        Ensure 'ingredients' and 'instructions' are lists of strings, NOT lists of objects.
        All fields are required. The last field should be followed immediately by a closing brace with NO trailing punctuation."""

        chat = [{"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}]

        formatted_prompt = self.tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(
            formatted_prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=1024,
            pad_token_id=self.tokenizer.eos_token_id,
            do_sample=True,
            temperature=0.7,
            top_p=0.95
        )

        response_text = self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[-1]:],
            skip_special_tokens=True
        )
        cleaned_response = self._clean_json_response(response_text)

        print(f"Original response length: {len(response_text)}")
        print(f"Cleaned response length: {len(cleaned_response)}")

        # Upload raw responses to S3 for debugging
        self.s3_manager.upload_to_s3(response_text, folder="original")
        self.s3_manager.upload_to_s3(cleaned_response, folder="cleaned")

        try:
            data = json.loads(cleaned_response)
            recipe_data = data.get("recipe", data)

            structured_recipe = StructuredRecipe(**recipe_data)

            # Save the successfully parsed recipe to S3
            recipe_with_metadata = {
                **recipe_data,
                "generated_at": datetime.now().isoformat(),
                "request": {
                    "ingredients": request.ingredients,
                    "cuisine": request.cuisine,
                    "cook_time": request.cook_time
                }
            }
            self.s3_manager.upload_to_s3(
                json.dumps(recipe_with_metadata, indent=2),
                folder="generated_recipes"
            )

            return structured_recipe

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"❌ Error parsing JSON from model response: {e}")

            error_data = {
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat(),
                "original": response_text,
                "cleaned": cleaned_response,
                "request": {
                    "ingredients": request.ingredients,
                    "cuisine": request.cuisine,
                    "cook_time": request.cook_time
                }
            }
            self.s3_manager.upload_to_s3(
                json.dumps(error_data, indent=2),
                folder="errors"
            )

            raise ValueError(
                f"Failed to parse AI output into StructuredRecipe. Error: {e}")

    def get_or_generate_recipe(self, request: RecipeRequest) -> RecipeResponse:
        """
        First search S3 for matching recipes, if not found or match is too low, generate a new one
        """
        search_result = self.search_s3_recipes(request)

        if search_result:
            recipe, match_score = search_result
            
            # Check if match score is good enough (51% or higher)
            if match_score >= 0.51:
                print(f"✨ Returning existing recipe from S3: {recipe.title} (match: {match_score*100:.1f}%)")
                return RecipeResponse(
                    recipe=recipe,
                    source="s3",
                    match_score=match_score
                )
            else:
                print(f"⚠️ Match score too low ({match_score*100:.1f}%), generating new recipe instead")

        print("🤖 Generating new recipe with AI")
        recipe = self.generate_new_recipe(request)
        return RecipeResponse(
            recipe=recipe,
            source="generated",
            match_score=None
        )


# ==================== MODAL SETUP ====================
app = modal.App("recipe-generator-final-test")
model_cache_volume = modal.Volume.from_name(
    "recipe-cache-final-test",
    create_if_missing=True
)
CACHE_PATH = "/model-cache"

# Define the image
image = (
    modal.Image.debian_slim()
    .pip_install(
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "accelerate>=0.20.0",
        "bitsandbytes>=0.41.0",
        "fastapi>=0.100.0",
        "pydantic>=2.0.0",
        "boto3>=1.28.0",
        "sentencepiece>=0.1.99",
        "protobuf>=3.20.0"
    )
)


@app.function(
    image=image,
    gpu="A10G",
    volumes={CACHE_PATH: model_cache_volume},
    secrets=[modal.Secret.from_name("food-gen-secret")],
    scaledown_window=300,
    timeout=600
)
@modal.asgi_app()
def fastapi_app():
    web_app = FastAPI(
        title="Recipe Generator API",
        description="AI-powered recipe generator with S3 caching",
        version="1.0.0"
    )

    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize model once per container
    recipe_model = RecipeModel(cache_path=CACHE_PATH)

    @web_app.post("/", tags=["Recipes"])
    def generate_recipe(request: RecipeRequest):
        """
        🔍 Search for existing recipe in S3, or generate new one if not found
        """
        result = recipe_model.get_or_generate_recipe(request)
        
        # Add debug logging
        print("=" * 50)
        print("📤 SENDING RESPONSE TO FRONTEND:")
        print(f"Recipe title: {result.recipe.title}")
        print(f"Ingredients count: {len(result.recipe.ingredients)}")
        print(f"Instructions count: {len(result.recipe.instructions)}")
        print(f"Source: {result.source}")
        print("=" * 50)
        
        # Return the recipe model directly, not from model_dump
        return {
            "recipe": {
                "title": result.recipe.title,
                "description": result.recipe.description,
                "ingredients": result.recipe.ingredients,
                "instructions": result.recipe.instructions,
                "cook_time": result.recipe.cook_time,
                "cuisine": result.recipe.cuisine,
            },
            "source": result.source,
            "match_score": result.match_score
        }
    
    @web_app.post("/generate-new", tags=["Recipes"])
    def force_generate_recipe(request: RecipeRequest):
        """
        🤖 Force generation of a new recipe (skip S3 search)

        Use this when you want a completely new recipe regardless of what's cached.
        """
        print("🚀 Forcing new recipe generation (skipping S3 search)")
        recipe = recipe_model.generate_new_recipe(request)
        return {
            "recipe": recipe.model_dump(),
            "source": "generated",
            "match_score": None
        }

    @web_app.post("/search", tags=["Search"])
    def search_recipes(request: RecipeRequest):
        """
        🔎 Search S3 for matching recipes without generating a new one

        Returns the best matching recipe from S3 or a message if none found.
        """
        search_result = recipe_model.search_s3_recipes(request)
        if search_result:
            recipe, match_score = search_result
            return {
                "found": True,
                "recipe": recipe.model_dump(),
                "match_score": match_score,
                "match_percentage": f"{match_score * 100:.1f}%"
            }
        return {
            "found": False,
            "message": "No matching recipes found in S3. Try /generate-new to create one!"
        }

    @web_app.get("/recipes", tags=["Browse"])
    def list_recipes():
        """
        📋 List all generated recipes from S3

        Returns metadata for all cached recipes.
        """
        files = recipe_model.s3_manager.list_recipe_files()
        return {
            "recipes": files,
            "count": len(files),
            "message": f"Found {len(files)} recipe(s) in cache"
        }

    @web_app.get("/recipe/{filename}", tags=["Browse"])
    def get_recipe(filename: str):
        """
        📖 Get a specific recipe from S3 by filename

        Example: /recipe/20240115_123456_789012.json
        """
        recipe = recipe_model.s3_manager.get_recipe(filename)
        if recipe:
            return recipe
        return {
            "error": "Recipe not found",
            "message": f"No recipe found with filename: {filename}"
        }

    @web_app.get("/health", tags=["System"])
    def health_check():
        """
        ✅ Health check endpoint

        Returns system status and S3 connection info.
        """
        try:
            recipes_count = len(recipe_model.s3_manager.list_recipe_files())
        except Exception as e:
            print(f"Error getting recipe count: {e}")
            recipes_count = 0

        return {
            "status": "healthy",
            "model": "loaded",
            "s3_connected": recipe_model.s3_manager.bucket_name is not None,
            "bucket_name": recipe_model.s3_manager.bucket_name,
            "cached_recipes": recipes_count,
            "cache_path": CACHE_PATH
        }

    @web_app.get("/stats", tags=["System"])
    def get_stats():
        """
        📊 Get statistics about cached recipes

        Returns counts by cuisine, ingredient usage, etc.
        """
        try:
            recipes = recipe_model.s3_manager.get_all_recipes()

            cuisines = {}
            total_recipes = len(recipes)

            for recipe in recipes:
                cuisine = recipe.get('cuisine', 'Unknown')
                cuisines[cuisine] = cuisines.get(cuisine, 0) + 1

            most_popular = None
            if cuisines:
                most_popular = max(cuisines.items(), key=lambda x: x[1])[0]

            return {
                "total_recipes": total_recipes,
                "cuisines": cuisines,
                "most_popular_cuisine": most_popular
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                "error": str(e),
                "total_recipes": 0,
                "cuisines": {}
            }

    @web_app.get("/", tags=["System"])
    def root():
        """
        👋 Welcome endpoint
        """
        return {
            "message": "Welcome to Recipe Generator API",
            "version": "1.0.0",
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "stats": "/stats",
                "generate": "POST /",
                "force_new": "POST /generate-new",
                "search": "POST /search",
                "list": "GET /recipes"
            }
        }

    return web_app
