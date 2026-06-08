# modal_app/main.py - Complete single file version
import modal
import os
import json
import re
import boto3
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env (project root)
load_dotenv()

# ==================== DATA MODELS ====================


class RecipeRequest(BaseModel):
    ingredients: List[str]
    cuisine: Optional[str] = None
    cook_time: Optional[str] = None
    cooking_style: Optional[str] = None
    dietary_restrictions: List[str] = []
    skill_level: Optional[str] = None
    meal_type: Optional[str] = None
    spice_level: Optional[str] = None
    user_id: str  # NEW: Required user ID


class StructuredRecipe(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    cook_time: str
    cuisine: str
    cooking_style: Optional[str] = None
    servings: int = 4  # ADDED - your code uses this
    chef_notes: Optional[str] = None  
    user_id: Optional[str] = None  # NEW: Track user ID who generated the recipe
    
    class Config:
        # Allow extra fields without error
        extra = "ignore"

class RecipeResponse(BaseModel):
    recipe: StructuredRecipe
    source: str  # "s3" or "generated"
    match_score: Optional[float] = None
    
    class Config:
        # Example for JSON serialization
        json_schema_extra = {
            "example": {
                "recipe": {
                    "title": "Classic Spaghetti Carbonara",
                    "description": "Authentic Italian pasta with eggs, cheese, and pancetta",
                    "ingredients": ["12 oz Spaghetti", "4 oz Pancetta", "3 Eggs"],
                    "instructions": ["Boil pasta", "Cook pancetta", "Mix with eggs"],
                    "cook_time": "25 minutes",
                    "cuisine": "Italian",
                    "cooking_style": "Traditional",
                    "servings": 4,
                    "chef_notes": "Use freshly grated Parmigiano-Reggiano"
                },
                "source": "generated",
                "match_score": None
            }
        }

# ==================== CONFIGURATION ====================


class Config:
    MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
    CACHE_PATH = "/model-cache"
    MIN_MATCH_SCORE = 0.8
    COOK_TIME_WEIGHT = 0.9
    
     # Define the JSON schema as a Python dict for validation
    RECIPE_SCHEMA = {
        "type": "object",
        "required": ["title", "description", "ingredients", "instructions", "cook_time", "cuisine", "cooking_style", "servings", "chef_notes"],
        "properties": {
            "chef_notes": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "ingredients": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1
            },
            "instructions": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1
            },
            "cook_time": {"type": "string"},
            "cuisine": {"type": "string"},
            "cooking_style": {"type": "string"},
            "servings": {"type": "integer"}
        }
    }
    CHEF_SYSTEM_PROMPT = """You are a professional chef AI. You MUST output valid JSON only.

CRITICAL: Your ENTIRE response must be ONLY this JSON structure. No text before or after.

{
  "chef_notes": "one sentence insight",
  "title": "Recipe Name",
  "description": "brief description",
  "ingredients": [
    "30 ml Olive Oil",
    "500 g Chicken Breast (diced)",
    "3 cloves Garlic (minced)"
  ],
  "instructions": [
    "Heat oil in pan over medium heat",
    "Add garlic and cook 1 minute until fragrant",
    "Add chicken and cook 8 minutes until golden"
  ],
  "cook_time": "25 minutes",
  "cuisine": "Italian",
  "cooking_style": "Pan-seared",
  "servings": 4
}

Rules:
- Copy the structure exactly
- Use double quotes only
- No markdown, no code blocks
- Field names: chef_notes, title, description, ingredients, instructions, cook_time, cuisine, cooking_style, servings
- Metric units: ml, g, kg, L, °C
- At least 5-8 instruction steps"""
    
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

    # ============================================================
    # LEGACY METHODS (Keep for backward compatibility)
    # ============================================================

    def upload_to_s3(self, content: str, folder: str = "responses") -> str:
        """Upload content to S3 and return the object key (LEGACY)"""
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
        """Get all recipes from S3 (LEGACY - no user filtering)"""
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
        """Get a specific recipe from S3 (LEGACY)"""
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
        """List all recipe files metadata (LEGACY)"""
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

    # ============================================================
    # NEW USER-BASED METHODS
    # ============================================================

    def upload_user_recipe(self, recipe_data: Dict, user_id: str) -> str:
        """
        Upload a recipe to a user-specific folder
        
        Structure: users/{user_id}/recipes/{timestamp}.json
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            object_key = f"users/{user_id}/recipes/{timestamp}.json"

            # Add user_id to the recipe data
            recipe_data['user_id'] = user_id
            recipe_data['created_at'] = datetime.now().isoformat()

            self.s3_client.put_object(
                Body=json.dumps(recipe_data, indent=2).encode('utf-8'),
                Bucket=self.bucket_name,
                Key=object_key,
                ContentType='application/json'
            )

            print(f"✅ Uploaded user recipe to s3://{self.bucket_name}/{object_key}")
            return object_key
        except Exception as e:
            print(f"⚠️ S3 upload failed: {e}")
            return ""

    def get_user_recipes(self, user_id: str) -> List[Dict]:
        """
        Get all recipes for a specific user
        """
        try:
            prefix = f"users/{user_id}/recipes/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            recipes = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    try:
                        # Skip if it's just the folder
                        if obj['Key'] == prefix:
                            continue
                            
                        file_obj = self.s3_client.get_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        recipe_data = json.loads(
                            file_obj['Body'].read().decode('utf-8')
                        )

                        # Add metadata
                        filename = obj['Key'].split('/')[-1]
                        recipe_data['id'] = filename.replace('.json', '')
                        recipe_data['filename'] = filename
                        recipe_data['last_modified'] = obj['LastModified'].isoformat()

                        recipes.append(recipe_data)
                    except Exception as e:
                        print(f"Error loading recipe {obj['Key']}: {e}")
                        continue

            # Sort by last_modified (newest first)
            recipes.sort(
                key=lambda x: x.get('last_modified', ''),
                reverse=True
            )

            print(f"📂 Found {len(recipes)} recipes for user {user_id}")
            return recipes
        except Exception as e:
            print(f"Error fetching user recipes: {e}")
            return []

    def get_user_recipe(self, user_id: str, filename: str) -> Optional[Dict]:
        """
        Get a specific recipe for a user
        """
        try:
            if not filename.endswith('.json'):
                filename = f"{filename}.json"

            object_key = f"users/{user_id}/recipes/{filename}"

            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            recipe_data = json.loads(response['Body'].read().decode('utf-8'))

            # Add metadata
            recipe_data['id'] = filename.replace('.json', '')
            recipe_data['filename'] = filename

            return recipe_data
        except self.s3_client.exceptions.NoSuchKey:
            print(f"Recipe not found: {filename}")
            return None
        except Exception as e:
            print(f"Error fetching recipe: {e}")
            return None

    def delete_user_recipe(self, user_id: str, filename: str) -> Tuple[bool, str]:
        """
        Delete a recipe only if it belongs to the user
        
        Returns: (success: bool, message: str)
        """
        try:
            if not filename.endswith('.json'):
                filename = f"{filename}.json"

            object_key = f"users/{user_id}/recipes/{filename}"

            # Check if file exists first
            try:
                self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=object_key
                )
            except self.s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    return False, "Recipe not found or you don't have permission to delete it"
                raise e

            # Delete the file
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            print(f"🗑️ Deleted recipe: {object_key}")
            return True, "Recipe deleted successfully"
        except Exception as e:
            print(f"❌ Error deleting recipe: {e}")
            return False, str(e)

    def get_user_recipe_count(self, user_id: str) -> int:
        """
        Get the number of recipes a user has
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"users/{user_id}/recipes/"
            )

            if 'Contents' in response:
                # Subtract 1 if the folder itself is counted
                return len([
                    obj for obj in response['Contents']
                    if obj['Key'].endswith('.json')
                ])
            return 0
        except Exception as e:
            print(f"Error counting recipes: {e}")
            return 0

    def search_user_recipes(self, user_id: str, query: str) -> List[Dict]:
        """
        Search a user's recipes by title, cuisine, or ingredients
        """
        recipes = self.get_user_recipes(user_id)
        query = query.lower()

        results = []
        for recipe in recipes:
            # Search in title
            if query in recipe.get('title', '').lower():
                results.append(recipe)
                continue

            # Search in cuisine
            if query in recipe.get('cuisine', '').lower():
                results.append(recipe)
                continue

            # Search in description
            if query in recipe.get('description', '').lower():
                results.append(recipe)
                continue

            # Search in ingredients
            ingredients = recipe.get('ingredients', [])
            for ingredient in ingredients:
                if query in ingredient.lower():
                    results.append(recipe)
                    break

        return results


# ==================== RECIPE MATCHER ====================


class RecipeMatcher:
    """Handles recipe matching logic"""

    @staticmethod
    def calculate_ingredient_match(user_ingredients: List[str], recipe_ingredients: List[str]) -> float:
        user_ing_normalized = [ing.lower().strip() for ing in user_ingredients]
        recipe_ing_combined = " ".join(recipe_ingredients).lower()

        match_count = 0
        for user_ing in user_ing_normalized:
            # \b ensures "ice" matches "ice" but not "rice" or "spiced"
            # escape the user input to handle characters like parens ()
            pattern = r'\b' + re.escape(user_ing) + r'\b'
            if re.search(pattern, recipe_ing_combined):
                match_count += 1

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

        # Check cooking style if specified (NEW)
        if request.cooking_style:
            recipe_instructions = " ".join(
                recipe_data.get('instructions', [])).lower()
            cooking_style_lower = request.cooking_style.lower()

            # Map cooking styles to expected instruction keywords
            style_keywords = {
                "fried": ["fry", "frying", "fried", "pan-fry", "deep-fry"],
                "baked": ["bake", "baking", "baked", "oven"],
                "grilled": ["grill", "grilling", "grilled", "barbecue", "bbq"],
                "steamed": ["steam", "steaming", "steamed"],
                "roasted": ["roast", "roasting", "roasted"],
                "sauteed": ["sauté", "sautéed", "sauteed", "pan"],
                "boiled": ["boil", "boiling", "boiled"],
                "slow cooked": ["slow cook", "crockpot", "slow cooker", "braise"]
            }

            keywords = style_keywords.get(
                cooking_style_lower, [cooking_style_lower])

            # If none of the keywords appear in instructions, penalize heavily
            if not any(kw in recipe_instructions for kw in keywords):
                match_score *= 0.3  # Heavy penalty for mismatched cooking style
                if match_score < min_match_score:
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
        self.s3_manager = S3Manager()
        print("✅ Model loaded successfully.")

    def _clean_and_parse_json(self, response_text: str) -> Dict[str, Any]:
        """
        Super simple parser - just extract and validate.
        """
        print(f"\n{'='*70}")
        print("PARSING LLM RESPONSE")
        print(f"{'='*70}")
        
        text = response_text.strip()
        
        # Remove markdown if present
        if '```' in text:
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
            text = text.strip()
        
        # Extract JSON
        start = text.find('{')
        end = text.rfind('}')
        
        if start == -1 or end == -1:
            print("❌ No JSON found")
            return self._get_default_recipe()
        
        json_str = text[start:end + 1]
        
        # Try to parse
        try:
            data = json.loads(json_str)
            print("✅ JSON parsed successfully")
            
            # Quick validation
            required = ["title", "ingredients", "instructions"]
            if all(k in data and data[k] for k in required):
                if len(data["ingredients"]) >= 2 and len(data["instructions"]) >= 3:
                    print(f"✅ Valid recipe: {len(data['ingredients'])} ingredients, {len(data['instructions'])} steps")
                    return self._normalize_fields(data)
            
            print("⚠️  Incomplete recipe data")
            return self._get_default_recipe()
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse failed: {str(e)[:100]}")
            print(f"Sample: {json_str[:300]}")
            return self._get_default_recipe()

    def _normalize_fields(self, data: Dict) -> Dict:
        """Minimal normalization"""
        # Ensure all required fields exist
        defaults = {
            "chef_notes": "",
            "title": "Generated Recipe",
            "description": "A delicious dish",
            "ingredients": [],
            "instructions": [],
            "cook_time": "30 minutes",
            "cuisine": "Fusion",
            "cooking_style": "Traditional",
            "servings": 4
        }
        
        for key, default in defaults.items():
            if key not in data:
                data[key] = default
        
        # Clean strings
        for key in ["title", "description", "chef_notes", "cuisine", "cooking_style", "cook_time"]:
            if isinstance(data[key], str):
                data[key] = data[key].strip().strip('"\'').strip()
        
        return data

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

    def _build_chef_prompt(self, request: RecipeRequest) -> str:
        """Build minimal, clear prompt"""
        
        persona = ChefPersonaBuilder.build_persona(request.cuisine)
        
        # Build ingredient list
        ing_list = '\n'.join(f'- {ing}' for ing in request.ingredients) if request.ingredients else "Use appropriate ingredients"
        
        prompt = f"""You are {persona['name']}.

    Create a {request.cuisine or 'delicious'} recipe using these ingredients:
    {ing_list}

    {f'Meal type: {request.meal_type}' if request.meal_type else ''}
    {f'Cooking style: {request.cooking_style}' if request.cooking_style else ''}
    {f'Spice level: {request.spice_level}' if request.spice_level else ''}

    Output ONLY valid JSON. No other text.

    {{
    "chef_notes": "your insight here",
    "title": "Recipe Name",
    "description": "description here",
    "ingredients": ["30 ml item1", "500 g item2"],
    "instructions": ["step 1", "step 2", "step 3"],
    "cook_time": "XX minutes",
    "cuisine": "{request.cuisine or 'Fusion'}",
    "cooking_style": "{request.cooking_style or 'Traditional'}",
    "servings": 4
    }}"""
        
        return prompt
        
    def generate_new_recipe(self, request: RecipeRequest) -> StructuredRecipe:
        """Simplified generation with retries"""
        
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n{'='*70}")
            print(f"ATTEMPT {attempt}/{max_attempts}")
            print(f"{'='*70}")
            
            try:
                # Build prompt
                prompt = self._build_chef_prompt(request)
                
                # Format for model
                chat = [
                    {"role": "system", "content": Config.CHEF_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
                
                formatted = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
                inputs = self.tokenizer(formatted, return_tensors="pt").to(self.model.device)
                
                # Generate
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=1200,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                
                response = self.tokenizer.decode(
                    outputs[0][inputs.input_ids.shape[-1]:],
                    skip_special_tokens=True
                )
                
                print(f"Response length: {len(response)} chars")
                
                # Parse
                data = self._clean_and_parse_json(response)
                
                # Check if it's the default error recipe
                if data["title"] == "Recipe Generation Failed":
                    if attempt < max_attempts:
                        print(f"⚠️  Retrying...")
                        continue
                
                # Build recipe object
                recipe = StructuredRecipe(**data)
                
                # Cache to S3
                try:
                    self.s3_manager.upload_to_s3(
                        json.dumps(recipe.model_dump(), indent=2),
                        folder="generated_recipes"
                    )
                except:
                    pass
                
                print(f"✅ SUCCESS: {recipe.title}")
                return recipe
                
            except Exception as e:
                print(f"❌ Attempt {attempt} failed: {str(e)[:100]}")
                if attempt >= max_attempts:
                    return StructuredRecipe(**self._get_default_recipe())
        
        return StructuredRecipe(**self._get_default_recipe())
        
    def _validate_recipe_comprehensive(self, data: dict, request: RecipeRequest) -> dict:
        """Comprehensive validation of generated recipe against requirements"""
        
        issues = []
        is_valid = True
        
        # 1. Check required fields
        required_fields = ["title", "description", "ingredients", "instructions", "cook_time", "cuisine"]
        for field in required_fields:
            if field not in data or not data[field]:
                issues.append(f"Missing or empty field: {field}")
                is_valid = False
        
        # 2. Validate meal type appropriateness
        if request.meal_type and not self._validate_meal_type_appropriateness(data, request):
            issues.append(f"Recipe not appropriate for {request.meal_type}")
            is_valid = False
        
        # 3. Validate cooking method
        if request.cooking_style and not self._validate_cooking_method(data, request):
            issues.append(f"Recipe doesn't use {request.cooking_style} method properly")
            is_valid = False
        
        # 4. Check ingredient usage
        if request.ingredients:
            missing_ingredients = self._check_ingredient_usage(data, request)
            if missing_ingredients:
                issues.append(f"Customer ingredients not used: {', '.join(missing_ingredients)}")
                is_valid = False
        
        # 5. Validate portions
        portion_issues = self._validate_portions(data)
        if portion_issues:
            issues.extend(portion_issues)
            # Don't invalidate for portion issues, just note them
        
        return {
            'is_valid': is_valid,
            'issues': issues
        }
        
    def _normalize_recipe_fields(self, data: dict, request: RecipeRequest) -> dict:
        """Normalize fields that LLM might return in unexpected formats"""
        
        # Fix cooking_style if it's a list
        if "cooking_style" in data:
            if isinstance(data["cooking_style"], list):
                # Take the first item if it's a list
                if data["cooking_style"]:
                    data["cooking_style"] = data["cooking_style"][0]
                    print(f"   Fixed cooking_style from list to: {data['cooking_style']}")
                else:
                    data["cooking_style"] = request.cooking_style or "varied"
            elif not isinstance(data["cooking_style"], str):
                data["cooking_style"] = str(data["cooking_style"])
        
        # Fix cuisine if it's a list
        if "cuisine" in data:
            if isinstance(data["cuisine"], list):
                if data["cuisine"]:
                    data["cuisine"] = data["cuisine"][0]
                    print(f"   Fixed cuisine from list to: {data['cuisine']}")
                else:
                    data["cuisine"] = request.cuisine or "Fusion"
            elif not isinstance(data["cuisine"], str):
                data["cuisine"] = str(data["cuisine"])
        
        # Fix title if it's not a string
        if "title" in data and not isinstance(data["title"], str):
            data["title"] = str(data["title"])
        
        # Fix description if it's not a string
        if "description" in data and not isinstance(data["description"], str):
            data["description"] = str(data["description"])
        
        # Fix cook_time if it's not a string
        if "cook_time" in data and not isinstance(data["cook_time"], str):
            data["cook_time"] = str(data["cook_time"])
        
        # Ensure instructions is a list of strings
        if "instructions" in data:
            if not isinstance(data["instructions"], list):
                data["instructions"] = [str(data["instructions"])]
            else:
                data["instructions"] = [str(item) for item in data["instructions"]]
        
        # Ensure ingredients is a list of strings (already handled by _normalize_ingredients but double-check)
        if "ingredients" in data:
            if not isinstance(data["ingredients"], list):
                data["ingredients"] = [str(data["ingredients"])]
        
        return data

    def _validate_meal_type_appropriateness(self,   data: dict, request: RecipeRequest) -> bool:
        """Check if generated recipe matches requested meal type"""
        
        if not request.meal_type:
            return True
        
        title_lower = data.get("title", "").lower()
        meal_type = request.meal_type.lower()
        
        # Keywords that indicate meal types
        meal_indicators = {
            "breakfast": ["breakfast", "morning", "scrambled", "pancake", "waffle", "omelette", 
                        "frittata", "hash", "eggs", "oatmeal", "porridge"],
            "lunch": ["sandwich", "wrap", "salad", "soup", "bowl", "panini"],
            "dinner": ["roast", "braised", "steak", "grilled", "curry", "stew"],
            "snack": ["dip", "chips", "bites", "appetizer", "finger"],
            "dessert": ["cake", "cookie", "pie", "sweet", "chocolate", "ice cream", "pudding"]
        }
        
        # Check if title contains appropriate keywords
        if meal_type in meal_indicators:
            keywords = meal_indicators[meal_type]
            if any(keyword in title_lower for keyword in keywords):
                return True
        
        # Check instructions for meal-specific preparation
        instructions_text = " ".join(data.get("instructions", [])).lower()
        if meal_type == "breakfast" and "eggs" in instructions_text:
            return True
        
        return False  # Be lenient - only fail if clearly wrong

    def _validate_cooking_method(self, data: dict, request: RecipeRequest) -> bool:
        """Validate that recipe uses requested cooking method"""
        
        if not request.cooking_style:
            return True
        
        title_lower = data.get("title", "").lower()
        instructions_text = " ".join(data.get("instructions", [])).lower()
        cooking_style = request.cooking_style.lower()
        
        # Method indicators
        method_keywords = {
            "fried": ["fry", "fried", "crispy", "golden brown", "oil temperature"],
            "baked": ["bake", "oven", "preheat", "degrees F"],
            "grilled": ["grill", "char", "marks", "barbecue"],
            "steamed": ["steam", "steamer", "covered"],
            "roasted": ["roast", "oven", "caramelized"],
            "sauteed": ["sauté", "pan", "stir frequently"],
            "boiled": ["boil", "simmer", "rolling boil"],
            "braised": ["braise", "sear", "liquid", "covered"],
            "stir fried": ["stir-fry", "wok", "high heat", "toss"]
        }
        
        if cooking_style in method_keywords:
            keywords = method_keywords[cooking_style]
            # Check both title and instructions
            if any(kw in title_lower or kw in instructions_text for kw in keywords):
                return True
        
        return False
    
    
    def _check_ingredient_usage(self, data: dict, request: RecipeRequest) -> list:
        """Check if all customer ingredients are used"""
        
        recipe_ingredients = " ".join(data.get("ingredients", [])).lower()
        instructions = " ".join(data.get("instructions", [])).lower()
        
        missing = []
        for ingredient in request.ingredients:
            ing_lower = ingredient.lower()
            # Check if ingredient appears in either ingredients list or instructions
            if ing_lower not in recipe_ingredients and ing_lower not in instructions:
                # Check for common variations
                if not self._ingredient_has_variation(ing_lower, recipe_ingredients + " " + instructions):
                    missing.append(ingredient)
        
        return missing
    
    def _validate_portions(self, data: dict) -> list:
        """Validate portion sizes are reasonable"""
        
        issues = []
        ingredients = data.get("ingredients", [])
        
        # Check for excessive quantities
        for ing in ingredients:
            ing_lower = ing.lower()
            
            # Check for container problems
            if "bottle" in ing_lower or "carton" in ing_lower or "package" in ing_lower:
                issues.append(f"Container quantity found: {ing}")
            
            # Check for metric units
            if re.search(r'\d+\s*(ml|g|kg|l)\b', ing_lower):
                issues.append(f"Metric unit found: {ing}")
            
            # Check for excessive oil (more than 1 cup for non-deep-frying)
            if "oil" in ing_lower:
                oil_match = re.search(r'(\d+)\s*cup', ing_lower)
                if oil_match and int(oil_match.group(1)) > 4:
                    issues.append(f"Excessive oil quantity: {ing}")
            
            # Check for excessive alcohol
            if any(alcohol in ing_lower for alcohol in ["wine", "beer", "vodka", "rum", "whiskey"]):
                if "bottle" in ing_lower or re.search(r'[2-9]\s*cup', ing_lower):
                    issues.append(f"Excessive alcohol: {ing}")
        
        # Check servings
        servings = data.get("servings", 4)
        if servings < 1 or servings > 12:
            issues.append(f"Unusual serving size: {servings}")
        
        return issues

    def _auto_fix_validation_issues(self, data: dict, validation_results: dict, request: RecipeRequest) -> dict:
        """Attempt to automatically fix validation issues"""
        
        fixed_data = data.copy()
        
        for issue in validation_results['issues']:
            # Fix missing fields
            if "Missing or empty field:" in issue:
                field = issue.split(": ")[1]
                if field == "title":
                    fixed_data["title"] = f"{request.cuisine or 'Delicious'} {request.cooking_style or 'Recipe'}"
                elif field == "description":
                    fixed_data["description"] = "A delicious homemade dish"
                elif field == "cook_time":
                    fixed_data["cook_time"] = "30 minutes"
                elif field == "cuisine":
                    fixed_data["cuisine"] = request.cuisine or "Fusion"
            
            # Fix meal type issues
            if "not appropriate for" in issue and request.meal_type:
                if request.meal_type.lower() == "breakfast":
                    # Add "Breakfast" to title if missing
                    if "title" in fixed_data and "breakfast" not in fixed_data["title"].lower():
                        fixed_data["title"] = f"Breakfast {fixed_data['title']}"
            
            # Fix cooking method issues
            if "doesn't use" in issue and request.cooking_style:
                # Update cooking_style field
                fixed_data["cooking_style"] = request.cooking_style
                # Add cooking method to title if missing
                if "title" in fixed_data:
                    style_words = {
                        "fried": "Fried", "baked": "Baked", "grilled": "Grilled",
                        "steamed": "Steamed", "roasted": "Roasted", "sauteed": "Sautéed"
                    }
                    if request.cooking_style in style_words:
                        style_word = style_words[request.cooking_style]
                        if style_word.lower() not in fixed_data["title"].lower():
                            fixed_data["title"] = f"{style_word} {fixed_data['title']}"
        
        return fixed_data

    def _ingredient_has_variation(self, ingredient: str, text: str) -> bool:
        """Check if ingredient has a common variation in text"""
        
        variations = {
            "chicken": ["chicken breast", "chicken thighs", "chicken pieces", "chicken wings", "chicken drumsticks"],
            "beef": ["ground beef", "beef chunks", "steak", "beef strips", "beef roast", "beef stew meat"],
            "pork": ["pork chops", "ground pork", "pork tenderloin", "bacon", "ham"],
            "onion": ["onions", "shallot", "shallots", "scallions", "green onions"],
            "tomato": ["tomatoes", "tomato sauce", "diced tomatoes", "cherry tomatoes", "tomato paste"],
            "cheese": ["cheddar", "mozzarella", "parmesan", "cheese blend", "feta", "goat cheese"],
            "pasta": ["spaghetti", "penne", "linguine", "fettuccine", "rigatoni", "macaroni"],
            "rice": ["white rice", "brown rice", "jasmine rice", "basmati rice", "wild rice"]
        }
        
        for base, vars in variations.items():
            if base in ingredient:
                if any(v in text for v in vars):
                    return True
        
        return False

    def _apply_light_quantity_fixes(self, data: Dict) -> Dict:
        """Fix only the most obvious quantity mistakes"""
        
        if "ingredients" not in data or not isinstance(data["ingredients"], list):
            return data
        
        fixed_ingredients = []
        
        for line in data.get("ingredients", []):
            # Ensure line is a string
            if not isinstance(line, str):
                fixed_ingredients.append(str(line))
                continue
                
            original = line
            lower = line.lower()
            
            # Fix: "1 bottle" → "1/2 cup" (for wine/vinegar)
            if "bottle" in lower:
                if any(liquid in lower for liquid in ["wine", "vinegar", "sauce"]):
                    line = re.sub(r'\d+\s*bottle[s]?\s+', '1/2 cup ', line, flags=re.IGNORECASE)
                else:
                    line = re.sub(r'\d+\s*bottle[s]?\s+', '2 cups ', line, flags=re.IGNORECASE)
            
            # Fix: container quantities
            if "carton" in lower:
                line = re.sub(r'\d+\s*carton[s]?\s+', '2 cups ', line, flags=re.IGNORECASE)
            if "package" in lower:
                line = re.sub(r'\d+\s*package[s]?\s+', '1 lb ', line, flags=re.IGNORECASE)
            if "bag" in lower:
                line = re.sub(r'\d+\s*bag[s]?\s+', '12 oz ', line, flags=re.IGNORECASE)
            if "box" in lower:
                line = re.sub(r'\d+\s*box(?:es)?\s+', '1 lb ', line, flags=re.IGNORECASE)
            
            # Fix: metric conversions
            # ml to cups/tbsp (more precise)
            line = re.sub(r'(\d+)\s*ml\b', 
                        lambda m: (
                            f"{round(int(m.group(1))/240, 2)} cup" if int(m.group(1)) >= 240
                            else f"{round(int(m.group(1))/15, 1)} tbsp" if int(m.group(1)) >= 15
                            else f"{round(int(m.group(1))/5, 1)} tsp"
                        ), 
                        line, flags=re.IGNORECASE)
            
            # grams to pounds/ounces (more precise)
            line = re.sub(r'(\d+)\s*g\b', 
                        lambda m: (
                            f"{round(int(m.group(1))*0.00220462, 2)} lb" if int(m.group(1)) >= 450
                            else f"{round(int(m.group(1))*0.035274, 1)} oz"
                        ), 
                        line, flags=re.IGNORECASE)
            
            # kg to pounds
            line = re.sub(r'(\d+(?:\.\d+)?)\s*kg\b', 
                        lambda m: f"{round(float(m.group(1))*2.20462, 2)} lb", 
                        line, flags=re.IGNORECASE)
            
            # liters to cups
            line = re.sub(r'(\d+(?:\.\d+)?)\s*l\b', 
                        lambda m: f"{round(float(m.group(1))*4.227, 1)} cups", 
                        line, flags=re.IGNORECASE)
            
            # Celsius to Fahrenheit (for temperatures in ingredients/instructions)
            line = re.sub(r'(\d+)\s*°?\s*C\b', 
                        lambda m: f"{round(int(m.group(1))*9/5 + 32)} °F", 
                        line, flags=re.IGNORECASE)
            
            # Fix excessive quantities for 4 servings
            # Too much oil (more than 1 cup for non-deep-frying)
            if "oil" in lower and "deep" not in lower:
                oil_match = re.search(r'([2-9]|\d{2,})\s*cup', line)
                if oil_match:
                    line = re.sub(r'([2-9]|\d{2,})\s*cup', '1/4 cup', line)
            
            # Too much salt (more than 2 tbsp is excessive)
            if "salt" in lower and not "salted" in lower:
                salt_match = re.search(r'([3-9]|\d{2,})\s*tbsp', line)
                if salt_match:
                    line = re.sub(r'([3-9]|\d{2,})\s*tbsp', '2 tsp', line)
            
            # Too much alcohol (cap at 1 cup for cooking)
            if any(alcohol in lower for alcohol in ["wine", "beer", "sake", "sherry", "cognac"]):
                alcohol_match = re.search(r'([2-9]|\d{2,})\s*cup', line)
                if alcohol_match:
                    line = re.sub(r'([2-9]|\d{2,})\s*cup', '1/2 cup', line)
            
            # Log changes for debugging
            if line != original:
                print(f"   Fixed quantity: '{original}' → '{line}'")
            
            fixed_ingredients.append(line)
        
        data["ingredients"] = fixed_ingredients
        
        # Also fix instructions if they contain metric units or containers
        if "instructions" in data and isinstance(data["instructions"], list):
            fixed_instructions = []
            for instruction in data["instructions"]:
                if not isinstance(instruction, str):
                    fixed_instructions.append(str(instruction))
                    continue
                
                original_inst = instruction
                
                # Fix temperatures in instructions
                instruction = re.sub(r'(\d+)\s*°?\s*C\b', 
                                    lambda m: f"{round(int(m.group(1))*9/5 + 32)}°F", 
                                    instruction, flags=re.IGNORECASE)
                
                # Fix metric volumes in instructions
                instruction = re.sub(r'(\d+)\s*ml\b', 
                                lambda m: f"{round(int(m.group(1))/240, 2)} cup" if int(m.group(1)) >= 240
                                else f"{round(int(m.group(1))/15, 1)} tbsp",
                                instruction, flags=re.IGNORECASE)
                
                # Fix container references
                instruction = re.sub(r'entire bottle', 'the wine', instruction, flags=re.IGNORECASE)
                instruction = re.sub(r'whole carton', 'the liquid', instruction, flags=re.IGNORECASE)
                
                if instruction != original_inst:
                    print(f"   Fixed instruction: Modified metric/container references")
                
                fixed_instructions.append(instruction)
            
            data["instructions"] = fixed_instructions
        
        return data
   
    
    def _normalize_ingredients(self, data: Dict) -> Dict:
        """
        Convert nested arrays or malformed ingredients into a clean list of strings.
        This is more robust than the previous version.
        """
        if "ingredients" not in data or not isinstance(data["ingredients"], list):
            return data

        normalized = []
        for item in data.get("ingredients", []):
            try:
                # Case 1: Already a proper string
                if isinstance(item, str) and item.strip():
                    normalized.append(item.strip())
                
                # Case 2: Nested list like ["1 lb", "Beef", "(cut into strips)"]
                elif isinstance(item, list):
                    parts = [str(p).strip() for p in item if p is not None and str(p).strip()]
                    if parts:
                        normalized.append(" ".join(parts))
                
                # Case 3: Other data types (numbers, dicts)
                elif item is not None:
                    normalized.append(str(item))
            except Exception as e:
                print(f"⚠️  Could not normalize ingredient item '{item}': {e}")
                continue # Skip malformed items

        data["ingredients"] = normalized
        return data

    def _ensure_ingredient_instruction_consistency(self, data: dict) -> dict:
        """
        Soft check to ensure all ingredients are used in instructions and vice versa.
        Logs warnings for potential inconsistencies.
        """
        if not data.get("ingredients") or not data.get("instructions"):
            return data

        # Extract normalized ingredient names
        ingredient_names = []
        for ing in data["ingredients"]:
            # Simple extraction: take the first non-numeric, non-unit word as the core ingredient
            parts = re.split(r'[\s,()]', ing)
            for part in parts:
                if part and not re.match(r'^\d', part) and part.lower() not in ['tsp', 'tbsp', 'cup', 'oz', 'lb']:
                    ingredient_names.append(part.lower())
                    break
        
        instructions_text = " ".join(data.get("instructions", [])).lower()
        
        # Check if listed ingredients are mentioned in instructions
        unused_ingredients = [
            ing_name for ing_name in ingredient_names 
            if ing_name not in instructions_text and not self._ingredient_has_variation(ing_name, instructions_text)
        ]

        if unused_ingredients:
            print(f"⚠️  Consistency Warning: Ingredients may not be used in instructions: {', '.join(unused_ingredients)}")

        return data
        
    def _validate_and_fix_servings(self, data: dict) -> dict:
        """Ensure the 'servings' field is a valid integer, defaulting to 4."""
        try:
            servings = int(data.get("servings", 4))
            if not (1 <= servings <= 16):
                servings = 4 # Reset unreasonable values
            data["servings"] = servings
        except (ValueError, TypeError):
            data["servings"] = 4
        return data

    # ===================================================================
    # Main Public Method
    # ===================================================================

    def get_or_generate_recipe(self, request: RecipeRequest) -> RecipeResponse:
        """
        First, search S3 for a matching recipe. If the match score is too low
        or no match is found, generate a new one with robust validation.
        """
        search_result = self.search_s3_recipes(request)

        if search_result:
            recipe, match_score = search_result
            if match_score >= 0.51:
                print(f"✨ Returning existing recipe from S3: {recipe.title} (match: {match_score*100:.1f}%)")
                return RecipeResponse(
                    recipe=recipe,
                    source="s3",
                    match_score=match_score
                )
            else:
                print(f"⚠️  Match score too low ({match_score*100:.1f}%), generating new recipe.")

        print("🤖 Generating new recipe with AI...")
        try:
            # The generate_new_recipe method now contains all the new logic
            recipe = self.generate_new_recipe(request)
            return RecipeResponse(
                recipe=recipe,
                source="generated",
                match_score=None
            )
        except Exception as e:
            print(f"❌ Critical error during recipe generation: {e}")
            # Depending on your application's needs, you might return a default
            # error response or re-raise the exception.
            raise e

class ChefPersonaBuilder:
    """Builds appropriate chef persona based on request"""

    CUISINE_EXPERTS: Dict[str, Dict[str, Any]] = {
        "italian": {
            "name": "Chef Marco Antonelli",
            "background": "20 years in Tuscany, trained under Michelin-starred chefs in traditional Italian cooking",
            "philosophy": "Fresh ingredients, simple preparations, let flavors shine",
            "staples": ["olive oil", "garlic", "tomatoes", "parmesan", "basil", "oregano", "pasta", "balsamic vinegar", "white wine", "mozzarella"],
            "typical_fats": "Extra Virgin Olive Oil",
            "avoid": ["soy sauce", "fish sauce", "miso", "gochujang", "sesame oil", "curry powder"],
            "signature_techniques": ["slow-simmering sauces", "fresh pasta", "risotto stirring"]
        },
        "chinese": {
            "name": "Chef Wei Chen",
            "background": "Szechuan and Cantonese master from Chengdu with 25 years experience",
            "philosophy": "Balance of flavors, wok hei is essential",
            "staples": ["soy sauce", "rice vinegar", "ginger", "garlic", "scallions", "sesame oil", "shaoxing wine", "oyster sauce", "white pepper", "cornstarch"],
            "typical_fats": "Peanut Oil or Vegetable Oil",
            "avoid": ["butter", "cream", "cheese", "olive oil", "parmesan", "balsamic vinegar"],
            "signature_techniques": ["high-heat wok cooking", "velveting", "stir-frying"]
        },
        "mexican": {
            "name": "Chef Rosa Martinez",
            "background": "Oaxaca family recipes passed down 3 generations, expert in mole and traditional techniques",
            "philosophy": "Build layers of flavor with chiles and spices",
            "staples": ["cumin", "chili powder", "cilantro", "lime", "garlic", "tomatoes", "onions", "jalapeños", "coriander", "mexican oregano", "corn tortillas"],
            "typical_fats": "Vegetable Oil, Lard, or Avocado Oil",
            "avoid": ["soy sauce", "mirin", "fish sauce", "curry powder", "sesame oil"],
            "signature_techniques": ["toasting spices", "charring peppers", "slow-braising"]
        },
        "indian": {
            "name": "Chef Anjali Sharma",
            "background": "Kerala spice expert with North and South Indian mastery, trained in Mumbai",
            "philosophy": "Spices are medicine, balance is key",
            "staples": ["cumin", "coriander", "turmeric", "garam masala", "ginger", "garlic", "ghee", "cardamom", "curry leaves", "yogurt", "basmati rice"],
            "typical_fats": "Ghee or Vegetable Oil",
            "avoid": ["soy sauce", "mirin", "fish sauce", "olive oil", "parmesan"],
            "signature_techniques": ["tempering spices", "tandoor cooking", "dum cooking"]
        },
        "japanese": {
            "name": "Chef Takashi Yamamoto",
            "background": "Kyoto-trained kaiseki specialist with 15 years perfecting umami balance",
            "philosophy": "Respect ingredients, highlight natural flavors",
            "staples": ["soy sauce", "mirin", "sake", "dashi", "ginger", "rice vinegar", "sesame oil", "miso", "nori", "wasabi", "bonito flakes"],
            "typical_fats": "Sesame Oil or Neutral Vegetable Oil",
            "avoid": ["heavy cream", "butter", "cheese", "olive oil", "wine", "tomato sauce"],
            "signature_techniques": ["precise knife cuts", "tempura battering", "sushi rice preparation"]
        },
        "thai": {
            "name": "Chef Somchai Prasert",
            "background": "Bangkok street food master, expert in balancing sweet-sour-salty-spicy",
            "philosophy": "Every dish needs all four flavors in harmony",
            "staples": ["fish sauce", "lime juice", "palm sugar", "thai basil", "lemongrass", "galangal", "thai chilies", "cilantro", "coconut milk", "tamarind"],
            "typical_fats": "Vegetable Oil or Coconut Oil",
            "avoid": ["soy sauce", "butter", "heavy cream", "cheese", "olive oil"],
            "signature_techniques": ["mortar and pestle grinding", "high-heat stir-frying", "coconut milk tempering"]
        },
        "french": {
            "name": "Chef Antoine Dubois",
            "background": "Le Cordon Bleu Paris graduate, classically trained in haute cuisine",
            "philosophy": "Technique is everything, butter makes it better",
            "staples": ["butter", "cream", "white wine", "shallots", "thyme", "tarragon", "dijon mustard", "garlic", "bay leaf", "cognac"],
            "typical_fats": "Butter or Olive Oil",
            "avoid": ["fish sauce", "soy sauce", "mirin", "gochujang", "sesame oil"],
            "signature_techniques": ["classical sauces", "proper emulsification", "braising"]
        },
        "mediterranean": {
            "name": "Chef Dimitris Papadopoulos",
            "background": "Coastal Mediterranean specialist from Greek islands and Southern Italy",
            "philosophy": "Sun, sea, and simplicity",
            "staples": ["olive oil", "lemon", "garlic", "oregano", "basil", "tomatoes", "olives", "feta cheese", "capers", "parsley"],
            "typical_fats": "Extra Virgin Olive Oil",
            "avoid": ["soy sauce", "fish sauce", "heavy cream", "butter", "sesame oil"],
            "signature_techniques": ["grilling over coals", "preserving in oil", "slow-roasting"]
        },
        "american": {
            "name": "Chef Jake Thompson",
            "background": "Modern American cuisine with Southern BBQ and comfort food expertise",
            "philosophy": "Bold flavors, generous portions, comfort first",
            "staples": ["butter", "garlic powder", "onion powder", "paprika", "black pepper", "worcestershire sauce", "mustard", "brown sugar", "hot sauce", "bacon"],
            "typical_fats": "Butter, Vegetable Oil, or Bacon Fat",
            "avoid": ["fish sauce", "mirin", "gochujang"],
            "signature_techniques": ["low and slow BBQ", "cast-iron cooking", "deep-frying"]
        },
        "korean": {
            "name": "Chef Min-ju Park",
            "background": "Seoul-trained in royal court cuisine and modern Korean fusion",
            "philosophy": "Fermentation creates depth, balance sweet and spicy",
            "staples": ["gochujang", "gochugaru", "soy sauce", "sesame oil", "garlic", "ginger", "scallions", "doenjang", "rice vinegar", "perilla leaves"],
            "typical_fats": "Sesame Oil or Vegetable Oil",
            "avoid": ["butter", "cream", "cheese", "olive oil", "fish sauce"],
            "signature_techniques": ["fermentation", "banchan preparation", "Korean BBQ grilling"]
        },
        "spanish": {
            "name": "Chef Carmen Rodriguez",
            "background": "Barcelona-trained in traditional tapas and paella mastery",
            "philosophy": "Share food, share life",
            "staples": ["olive oil", "garlic", "smoked paprika", "saffron", "tomatoes", "parsley", "almonds", "sherry vinegar", "chorizo", "manchego"],
            "typical_fats": "Spanish Olive Oil",
            "avoid": ["soy sauce", "fish sauce", "butter", "sesame oil", "curry powder"],
            "signature_techniques": ["paella socarrat", "tapas plating", "jamón carving"]
        },
        "middle eastern": {
            "name": "Chef Khalil Hassan",
            "background": "Lebanese-Syrian cuisine expert with Persian influences",
            "philosophy": "Hospitality through abundance",
            "staples": ["olive oil", "tahini", "sumac", "za'atar", "pomegranate molasses", "yogurt", "mint", "parsley", "cumin", "cinnamon"],
            "typical_fats": "Olive Oil or Ghee",
            "avoid": ["soy sauce", "fish sauce", "miso", "gochujang"],
            "signature_techniques": ["spice blending", "mezze preparation", "flatbread baking"]
        }
    }

    # Common cuisine aliases mapping
    CUISINE_ALIASES = {
        "asian": "chinese",
        "tex-mex": "mexican", 
        "tex mex": "mexican",
        "southwestern": "mexican",
        "cajun": "american",
        "southern": "american",
        "bbq": "american",
        "barbecue": "american",
        "levantine": "mediterranean",
        "middle eastern": "mediterranean",
        "arabic": "mediterranean",
        "greek": "greek",
        "hellenic": "greek"
    }
    
    
    @staticmethod
    def build_persona(cuisine: Optional[str]) -> Dict[str, Any]:
        """
        Return the matching chef persona or a generalist if none specified.
        
        Args:
            cuisine: The requested cuisine type (optional)
            
        Returns:
            Dict containing chef persona with name, background, staples, etc.
        """
        # Default generalist chef
        if not cuisine:
            return {
                "name": "Chef Alexandre Martin",
                "background": "Culinary Institute graduate with 20 years global fusion experience",
                "philosophy": "Every ingredient has potential, technique unlocks it",
                "staples": ["salt", "pepper", "garlic", "onions", "olive oil", "butter", "herbs", "spices", "lemon", "vinegar"],
                "typical_fats": "Olive Oil or Butter",
                "avoid": [],
                "signature_techniques": ["adapting to available ingredients", "fusion creativity"]
            }

        # Normalize cuisine name
        normalized_cuisine = cuisine.lower().strip()
        
        # Check aliases first
        if normalized_cuisine in ChefPersonaBuilder.CUISINE_ALIASES:
            normalized_cuisine = ChefPersonaBuilder.CUISINE_ALIASES[normalized_cuisine]
        
        # Return specific expert if found
        if normalized_cuisine in ChefPersonaBuilder.CUISINE_EXPERTS:
            return ChefPersonaBuilder.CUISINE_EXPERTS[normalized_cuisine]
        
        # Create a generic specialist for unknown cuisines
        return {
            "name": f"Chef Alexandre (specialized in {cuisine.title()})",
            "background": f"{cuisine.title()} cuisine specialist with international training",
            "philosophy": f"Authentic {cuisine.title()} flavors with modern techniques",
            "staples": ["salt", "pepper", "garlic", "onions", "oil", "herbs", "spices", "vinegar", "lemon"],
            "typical_fats": "appropriate cooking fat for the cuisine",
            "avoid": [],
            "signature_techniques": [f"{cuisine.lower()} traditional methods", "regional adaptations"]
        }

    @staticmethod
    def get_all_cuisines() -> List[str]:
        """Return list of all supported cuisines"""
        return list(ChefPersonaBuilder.CUISINE_EXPERTS.keys())

class IngredientAnalyzer:
    """Analyzes user ingredients for cuisine conflicts and provides recommendations"""

    # Common ingredient substitutions by cuisine
    SUBSTITUTIONS = {
        "japanese": {
            "white wine": "sake or mirin",
            "butter": "sesame oil",
            "olive oil": "vegetable oil",
            "heavy cream": "silken tofu or soy milk",
            "cheese": "tofu or omit",
            "milk": "soy milk or dashi"
        },
        "chinese": {
            "butter": "vegetable oil or peanut oil",
            "olive oil": "peanut oil or vegetable oil",
            "wine": "shaoxing wine or dry sherry",
            "parmesan": "omit or use tofu",
            "cream": "coconut milk or cornstarch slurry",
            "cheese": "tofu or omit"
        },
        "mexican": {
            "soy sauce": "worcestershire sauce or lime juice",
            "fish sauce": "worcestershire sauce",
            "sesame oil": "vegetable oil",
            "mirin": "honey and lime juice",
            "gochujang": "chipotle in adobo"
        },
        "italian": {
            "soy sauce": "worcestershire sauce or anchovies",
            "fish sauce": "anchovies or capers",
            "sesame oil": "olive oil",
            "mirin": "white wine with sugar",
            "gochujang": "calabrian chili paste"
        },
        "indian": {
            "soy sauce": "tamarind or worcestershire",
            "olive oil": "ghee or vegetable oil",
            "butter": "ghee",
            "wine": "vinegar or lemon juice",
            "fish sauce": "tamarind or amchur"
        },
        "thai": {
            "soy sauce": "fish sauce or tamari",
            "butter": "coconut oil",
            "olive oil": "vegetable oil",
            "cheese": "tofu or omit",
            "cream": "coconut milk"
        },
        "french": {
            "soy sauce": "worcestershire or beef stock reduction",
            "fish sauce": "anchovies",
            "sesame oil": "walnut oil or olive oil",
            "gochujang": "harissa or tomato paste with cayenne",
            "miso": "concentrated beef or mushroom stock"
        },
        "mediterranean": {
            "soy sauce": "worcestershire or balsamic reduction",
            "butter": "olive oil",
            "cream": "yogurt or olive oil",
            "fish sauce": "anchovies or capers",
            "sesame oil": "olive oil"
        },
        "korean": {
            "olive oil": "sesame oil or vegetable oil",
            "butter": "sesame oil",
            "cream": "soy milk or omit",
            "fish sauce": "soy sauce or salted shrimp",
            "wine": "soju or rice wine"
        }
    }

    # Ingredient categories for conflict detection
    INGREDIENT_CATEGORIES = {
        "asian_condiments": [
            "soy sauce", "miso", "mirin", "sake", "fish sauce", 
            "oyster sauce", "hoisin sauce", "gochujang", "gochugaru",
            "doenjang", "sambal", "sriracha", "sesame oil"
        ],
        "western_dairy": [
            "butter", "cream", "heavy cream", "milk", "cheese",
            "parmesan", "mozzarella", "cheddar", "sour cream",
            "cream cheese", "yogurt", "buttermilk"
        ],
        "mediterranean": [
            "olive oil", "olives", "capers", "sun-dried tomatoes",
            "feta", "balsamic vinegar", "anchovies"
        ],
        "latin_american": [
            "cilantro", "lime", "jalapeño", "chipotle", "adobo",
            "queso fresco", "cotija", "mexican crema", "tomatillo"
        ],
        "indian_spices": [
            "garam masala", "turmeric", "cardamom", "curry powder",
            "curry leaves", "mustard seeds", "ghee", "paneer"
        ],
        "french_classic": [
            "wine", "cognac", "brandy", "dijon mustard", "tarragon",
            "herbes de provence", "gruyere", "brie"
        ]
    }

    @staticmethod
    def detect_conflicts(user_ingredients: List[str], cuisine: Optional[str]) -> Dict:
        """
        Detect if user ingredients conflict with requested cuisine.
        
        Args:
            user_ingredients: List of ingredients provided by user
            cuisine: The requested cuisine type
            
        Returns:
            Dict containing conflict analysis and recommendations
        """
        # No cuisine specified = no conflicts
        if not cuisine:
            return {
                "has_conflict": False,
                "conflicts": [],
                "staples": ["salt", "pepper", "garlic", "onions", "oil", "vinegar", "herbs"],
                "typical_fats": "oil or butter",
                "suggestions": []
            }

        # Get the chef persona for this cuisine
        persona = ChefPersonaBuilder.build_persona(cuisine)
        
        # Get avoid list from persona
        avoid_list = persona.get("avoid", [])
        staples = persona.get("staples", [])
        typical_fats = persona.get("typical_fats", "oil")
        
        conflicts = []
        suggestions = []
        
        # Check each user ingredient for conflicts
        for ingredient in user_ingredients:
            ing_lower = ingredient.lower().strip()
            
            # Check against avoid list
            for avoid_item in avoid_list:
                avoid_lower = avoid_item.lower()
                
                # Check for exact match or substring
                if (avoid_lower in ing_lower or 
                    ing_lower in avoid_lower or
                    IngredientAnalyzer._similar_ingredient(ing_lower, avoid_lower)):
                    
                    # Find substitution if available
                    substitution = IngredientAnalyzer._get_substitution(
                        avoid_item, cuisine
                    )
                    
                    conflicts.append({
                        "ingredient": ingredient,
                        "issue": avoid_item,
                        "suggestion": f"atypical for {cuisine} cuisine",
                        "substitution": substitution
                    })
                    
                    if substitution:
                        suggestions.append(
                            f"Consider replacing {ingredient} with {substitution}"
                        )
                    break

        # Analyze ingredient categories for better recommendations
        category_analysis = IngredientAnalyzer._analyze_categories(
            user_ingredients, cuisine
        )
        
        return {
            "has_conflict": len(conflicts) > 0,
            "conflicts": conflicts,
            "staples": staples,
            "typical_fats": typical_fats,
            "suggestions": suggestions,
            "category_notes": category_analysis
        }
    
    @staticmethod
    def _similar_ingredient(ing1: str, ing2: str) -> bool:
        """
        Check if two ingredients are similar (handles variations).
        
        Args:
            ing1: First ingredient
            ing2: Second ingredient
            
        Returns:
            True if ingredients are similar
        """
        # Common variations to check
        variations = [
            ("soy sauce", "soya sauce", "shoyu"),
            ("sesame oil", "sesame seed oil"),
            ("olive oil", "evoo", "extra virgin olive oil"),
            ("butter", "unsalted butter", "salted butter"),
            ("cream", "heavy cream", "whipping cream", "double cream"),
            ("wine", "white wine", "red wine", "cooking wine")
        ]
        
        for group in variations:
            if ing1 in group and ing2 in group:
                return True
                
        return False
    
    @staticmethod
    def _get_substitution(ingredient: str, cuisine: str) -> Optional[str]:
        """
        Get substitution for an ingredient in a specific cuisine.
        
        Args:
            ingredient: The conflicting ingredient
            cuisine: The target cuisine
            
        Returns:
            Suggested substitution or None
        """
        cuisine_lower = cuisine.lower()
        ingredient_lower = ingredient.lower()
        
        if cuisine_lower in IngredientAnalyzer.SUBSTITUTIONS:
            subs = IngredientAnalyzer.SUBSTITUTIONS[cuisine_lower]
            
            # Check for exact match
            if ingredient_lower in subs:
                return subs[ingredient_lower]
            
            # Check for partial matches
            for key, value in subs.items():
                if key in ingredient_lower or ingredient_lower in key:
                    return value
                    
        return None
    
    @staticmethod
    def _analyze_categories(ingredients: List[str], cuisine: str) -> List[str]:
        """
        Analyze ingredient categories for cuisine compatibility.
        
        Args:
            ingredients: List of user ingredients
            cuisine: Target cuisine
            
        Returns:
            List of category-based notes
        """
        notes = []
        ingredient_lower = [i.lower() for i in ingredients]
        
        # Count ingredients by category
        category_counts = {}
        for category, items in IngredientAnalyzer.INGREDIENT_CATEGORIES.items():
            count = sum(1 for ing in ingredient_lower 
                       if any(item in ing for item in items))
            if count > 0:
                category_counts[category] = count
        
        # Generate notes based on category analysis
        cuisine_lower = cuisine.lower() if cuisine else ""
        
        if "asian" not in cuisine_lower and "chinese" not in cuisine_lower and "japanese" not in cuisine_lower:
            if category_counts.get("asian_condiments", 0) >= 2:
                notes.append("Multiple Asian condiments detected - consider fusion approach")
        
        if "french" in cuisine_lower or "italian" in cuisine_lower:
            if category_counts.get("asian_condiments", 0) > 0:
                notes.append("Mix of European and Asian ingredients - creative fusion opportunity")
        
        if cuisine_lower in ["japanese", "chinese", "thai", "korean"]:
            if category_counts.get("western_dairy", 0) >= 2:
                notes.append("Multiple dairy products uncommon in Asian cuisine - use sparingly")
        
        return notes
    
    @staticmethod
    def enhance_ingredients(base_ingredients: List[str], cuisine: str) -> List[str]:
        """
        Suggest additional ingredients to enhance the dish based on cuisine.
        
        Args:
            base_ingredients: User's provided ingredients
            cuisine: Target cuisine
            
        Returns:
            List of suggested additional ingredients
        """
        persona = ChefPersonaBuilder.build_persona(cuisine)
        staples = persona.get("staples", [])
        
        # Find missing essential staples
        base_lower = [i.lower() for i in base_ingredients]
        suggestions = []
        
        # Essential ingredients by cuisine
        essentials = {
            "italian": ["garlic", "olive oil", "parmesan"],
            "chinese": ["soy sauce", "ginger", "garlic"],
            "japanese": ["soy sauce", "mirin", "rice vinegar"],
            "mexican": ["lime", "cilantro", "onion"],
            "indian": ["ginger", "garlic", "cumin"],
            "thai": ["fish sauce", "lime", "cilantro"],
            "french": ["butter", "shallot", "wine"]
        }
        
        cuisine_lower = cuisine.lower() if cuisine else ""
        if cuisine_lower in essentials:
            for essential in essentials[cuisine_lower]:
                if not any(essential in ing for ing in base_lower):
                    suggestions.append(essential)
        
        return suggestions[:5]  # Return top 5 suggestions


class RecipePromptBuilder:
    """Builds complete, structured prompts for recipe generation"""
    
    @staticmethod
    def build_complete_prompt(
        user_request: str,
        user_ingredients: Optional[List[str]] = None,
        cuisine: Optional[str] = None,
        dietary_restrictions: Optional[List[str]] = None
    ) -> str:
        """
        Builds a complete prompt with persona, constraints, and clear JSON requirements.
        
        Args:
            user_request: The user's recipe request
            user_ingredients: Optional list of available ingredients
            cuisine: Optional cuisine type
            dietary_restrictions: Optional list of restrictions
            
        Returns:
            Complete formatted prompt string
        """
        # Get chef persona
        persona = ChefPersonaBuilder.build_persona(cuisine)
        
        # Analyze ingredients for conflicts if provided
        ingredient_analysis = None
        if user_ingredients and cuisine:
            ingredient_analysis = IngredientAnalyzer.detect_conflicts(
                user_ingredients, cuisine
            )
        
        # Build the prompt sections
        sections = []
        
        # 1. System context (who the chef is)
        sections.append(f"""You are {persona['name']}, {persona['background']}.
Your culinary philosophy: {persona['philosophy']}

""")
        
        # 2. Cuisine-specific constraints
        if cuisine:
            sections.append(f"""CUISINE REQUIREMENTS FOR {cuisine.upper()}:
- Typical cooking fats: {persona['typical_fats']}
- Essential staple ingredients: {', '.join(persona['staples'][:8])}
- Signature techniques: {', '.join(persona['signature_techniques'])}
- AVOID using: {', '.join(persona['avoid']) if persona['avoid'] else 'N/A'}

""")
        
        # 3. Ingredient constraints
        if user_ingredients:
            sections.append(f"""AVAILABLE INGREDIENTS:
{chr(10).join(f'- {ing}' for ing in user_ingredients)}

You MUST incorporate these ingredients into the recipe where appropriate.
""")
            
            # Add conflict warnings
            if ingredient_analysis and ingredient_analysis['has_conflict']:
                sections.append(f"""
⚠️ INGREDIENT NOTES:
{chr(10).join(f'- {conf["ingredient"]}: {conf["suggestion"]}' for conf in ingredient_analysis['conflicts'])}

Suggestions: {chr(10).join(f'- {s}' for s in ingredient_analysis['suggestions'])}
""")
        
        # 4. Dietary restrictions
        if dietary_restrictions:
            sections.append(f"""DIETARY RESTRICTIONS:
{chr(10).join(f'- {restriction}' for restriction in dietary_restrictions)}

Ensure the recipe complies with ALL restrictions.
""")
        
        # 5. The actual request
        sections.append(f"""USER REQUEST:
"{user_request}"

""")
        
        # 6. Clear JSON output instruction
        sections.append("""YOUR RESPONSE:
Return ONLY the JSON object below with NO additional text, markdown, or formatting.

START YOUR RESPONSE WITH: {
END YOUR RESPONSE WITH: }

Required JSON structure:
{
  "chef_notes": "Brief insight about this dish",
  "title": "Recipe Name",
  "description": "Brief description (1-2 sentences)",
  "ingredients": [
    "2 tbsp Ingredient Name",
    "1 lb Another Ingredient (preparation note)"
  ],
  "instructions": [
    "Step 1 description",
    "Step 2 description"
  ],
  "cook_time": "XX minutes",
  "cuisine": "Cuisine Type",
  "cooking_style": "Cooking Method",
  "servings": 4
}

Begin your JSON response now:""")
        
        return ''.join(sections)
    
    @staticmethod
    def build_simple_prompt(user_request: str) -> str:
        """
        Builds a simple prompt for quick recipe generation without constraints.
        
        Args:
            user_request: The user's recipe request
            
        Returns:
            Simple formatted prompt string
        """
        return f"""Create a recipe for: "{user_request}"

Return ONLY valid JSON in this exact format (no markdown, no code blocks):

{{
  "chef_notes": "Your insight about this dish",
  "title": "Recipe Name",
  "description": "Brief description",
  "ingredients": ["ingredient 1", "ingredient 2"],
  "instructions": ["step 1", "step 2"],
  "cook_time": "XX minutes",
  "cuisine": "Cuisine Type",
  "cooking_style": "Cooking Method",
  "servings": 4
}}

Begin JSON:"""

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
        description="AI-powered recipe generator with S3 caching and user accounts",
        version="2.0.0"
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

    # ============================================================
    # LEGACY ENDPOINTS (Keep for backward compatibility)
    # ============================================================

    @web_app.post("/", tags=["Recipes"])
    def generate_recipe(request: RecipeRequest):
        """Generate or fetch a recipe"""
        result = recipe_model.get_or_generate_recipe(request)

        recipe_data = {
            "title": result.recipe.title,
            "description": result.recipe.description,
            "ingredients": result.recipe.ingredients,
            "instructions": result.recipe.instructions,
            "cook_time": result.recipe.cook_time,
            "cuisine": result.recipe.cuisine,
        }

        # If user_id provided, save to user's folder
        if request.user_id:
            recipe_model.s3_manager.upload_user_recipe(recipe_data, request.user_id)
        else:
            # Legacy: save to general folder
            recipe_model.s3_manager.upload_to_s3(
                json.dumps(recipe_data),
                folder="generated_recipes"
            )

        return {
            "recipe": recipe_data,
            "source": result.source,
            "match_score": result.match_score
        }

    @web_app.get("/recipes", tags=["Browse"])
    def list_recipes():
        """List all generated recipes (LEGACY)"""
        files = recipe_model.s3_manager.list_recipe_files()
        return {
            "recipes": files,
            "count": len(files),
        }

    @web_app.get("/recipes/all", tags=["Browse"])
    def list_all_recipes_with_data():
        """List all recipes with full data (LEGACY)"""
        try:
            response = recipe_model.s3_manager.s3_client.list_objects_v2(
                Bucket=recipe_model.s3_manager.bucket_name,
                Prefix="model_responses/generated_recipes/"
            )

            if 'Contents' not in response:
                return {"recipes": [], "count": 0}

            recipes_with_id = []

            for obj in response['Contents']:
                try:
                    key = obj['Key']
                    filename = key.split('/')[-1]

                    if not filename.endswith('.json'):
                        continue

                    file_obj = recipe_model.s3_manager.s3_client.get_object(
                        Bucket=recipe_model.s3_manager.bucket_name,
                        Key=key
                    )
                    recipe_data = json.loads(file_obj['Body'].read().decode('utf-8'))

                    recipe_data['id'] = filename.replace('.json', '')
                    recipe_data['filename'] = filename
                    recipe_data['last_modified'] = obj['LastModified'].isoformat()

                    recipes_with_id.append(recipe_data)
                except Exception as e:
                    print(f"⚠️ Error loading {obj['Key']}: {e}")
                    continue

            recipes_with_id.sort(
                key=lambda x: x.get('last_modified', ''),
                reverse=True
            )

            return {
                "recipes": recipes_with_id,
                "count": len(recipes_with_id)
            }
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"recipes": [], "count": 0, "error": str(e)}

    @web_app.get("/recipe/{filename}", tags=["Browse"])
    def get_recipe(filename: str):
        """Get a specific recipe (LEGACY)"""
        recipe = recipe_model.s3_manager.get_recipe(filename)
        if recipe:
            return recipe
        return {"error": "Recipe not found"}

    @web_app.delete("/recipes/{filename}", tags=["Browse"])
    def delete_recipe(filename: str):
        """Delete a recipe (LEGACY - no user check)"""
        try:
            if not filename.endswith('.json'):
                filename = f"{filename}.json"

            object_key = f"model_responses/generated_recipes/{filename}"

            recipe_model.s3_manager.s3_client.delete_object(
                Bucket=recipe_model.s3_manager.bucket_name,
                Key=object_key
            )

            return {"success": True, "message": "Recipe deleted"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================
    # NEW USER-BASED ENDPOINTS
    # ============================================================

    @web_app.post("/user/generate", tags=["User Recipes"])
    def generate_user_recipe(request: RecipeRequest):
        """
        🍳 Generate a recipe for a specific user
        
        Requires user_id in the request.
        """
        if not request.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        result = recipe_model.get_or_generate_recipe(request)

        recipe_data = {
            "title": result.recipe.title,
            "description": result.recipe.description,
            "ingredients": result.recipe.ingredients,
            "instructions": result.recipe.instructions,
            "cook_time": result.recipe.cook_time,
            "cuisine": result.recipe.cuisine,
        }

        # Save to user's folder
        object_key = recipe_model.s3_manager.upload_user_recipe(
            recipe_data,
            request.user_id
        )

        return {
            "recipe": recipe_data,
            "source": result.source,
            "match_score": result.match_score,
            "saved_to": object_key
        }

    @web_app.get("/user/{user_id}/recipes", tags=["User Recipes"])
    def get_user_recipes(user_id: str):
        """
        📋 Get all recipes for a specific user
        """
        recipes = recipe_model.s3_manager.get_user_recipes(user_id)
        return {
            "recipes": recipes,
            "count": len(recipes),
            "user_id": user_id
        }

    @web_app.get("/user/{user_id}/recipes/{filename}", tags=["User Recipes"])
    def get_user_recipe(user_id: str, filename: str):
        """
        📖 Get a specific recipe for a user
        """
        recipe = recipe_model.s3_manager.get_user_recipe(user_id, filename)
        if recipe:
            return recipe
        raise HTTPException(status_code=404, detail="Recipe not found")

    @web_app.delete("/user/{user_id}/recipes/{filename}", tags=["User Recipes"])
    def delete_user_recipe(user_id: str, filename: str):
        """
        🗑️ Delete a user's recipe
        
        Only deletes if the recipe belongs to the specified user.
        """
        success, message = recipe_model.s3_manager.delete_user_recipe(
            user_id,
            filename
        )

        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)

    @web_app.get("/user/{user_id}/stats", tags=["User Recipes"])
    def get_user_stats(user_id: str):
        """
        📊 Get statistics for a user's recipes
        """
        recipes = recipe_model.s3_manager.get_user_recipes(user_id)

        cuisines = {}
        for recipe in recipes:
            cuisine = recipe.get('cuisine', 'Unknown')
            cuisines[cuisine] = cuisines.get(cuisine, 0) + 1

        most_popular = None
        if cuisines:
            most_popular = max(cuisines.items(), key=lambda x: x[1])[0]

        return {
            "user_id": user_id,
            "total_recipes": len(recipes),
            "cuisines": cuisines,
            "most_popular_cuisine": most_popular
        }

    @web_app.get("/user/{user_id}/search", tags=["User Recipes"])
    def search_user_recipes(user_id: str, q: str):
        """
        🔍 Search a user's recipes
        
        Query parameter 'q' searches title, cuisine, description, and ingredients.
        """
        if not q or len(q) < 2:
            raise HTTPException(
                status_code=400,
                detail="Search query must be at least 2 characters"
            )

        results = recipe_model.s3_manager.search_user_recipes(user_id, q)
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }

    # ============================================================
    # SYSTEM ENDPOINTS
    # ============================================================

    @web_app.get("/health", tags=["System"])
    def health_check():
        """Health check"""
        return {
            "status": "healthy",
            "version": "2.0.0"
        }

    @web_app.get("/", tags=["System"])
    def root():
        """Welcome endpoint"""
        return {
            "message": "Welcome to Recipe Generator API v2.0",
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "generate": "POST /",
                "user_generate": "POST /user/generate",
                "user_recipes": "GET /user/{user_id}/recipes",
                "user_delete": "DELETE /user/{user_id}/recipes/{filename}"
            }
        }

    return web_app