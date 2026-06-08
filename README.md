# 🍳 ChefAI - AI Recipe Generator

ChefAI is a full-stack AI-powered recipe generation platform that transforms available ingredients into complete recipes using a Large Language Model (LLM).

The application combines:

* Next.js 16 frontend
* Clerk Authentication
* FastAPI backend
* Modal serverless GPU hosting
* Mistral 7B Instruct LLM
* AWS S3 recipe storage and caching

Users can enter ingredients, cooking preferences, dietary restrictions, and cuisine styles to generate personalized recipes in seconds.

---

## ✨ Features

### 🤖 AI Recipe Generation

Generate complete recipes from:

* Available ingredients
* Preferred cuisine
* Cooking style
* Dietary restrictions
* Skill level
* Meal type
* Spice level
* Desired cooking time

Powered by:

```text
mistralai/Mistral-7B-Instruct-v0.2
```

---

### 📚 Smart Recipe Caching

Instead of generating every recipe from scratch:

1. Previous recipes are stored in AWS S3
2. Requests are matched against existing recipes
3. Similar recipes are returned when available
4. New recipes are generated only when needed

Benefits:

* Faster response times
* Lower AI inference costs
* Reduced duplicate recipe generation

---

### 🔐 Authentication

Authentication is powered by Clerk.

Users can:

* Sign up
* Sign in
* Generate recipes
* Save recipes linked to their account

---

### ☁️ Modal AI Hosting

The backend is deployed using Modal.

Modal provides:

* Serverless GPU execution
* Automatic scaling
* Fast API deployment
* Efficient model hosting

---

## 🏗 Architecture

```text
┌─────────────────────┐
│     Next.js App     │
│ React + TailwindCSS │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      FastAPI        │
│   Modal Hosted API  │
└──────────┬──────────┘
           │
   ┌───────┴────────┐
   ▼                ▼

Mistral 7B       AWS S3
Recipe Model     Recipe Cache

   ▼                ▲
   └──── Generated Recipes ────┘
```

---

## 🛠 Tech Stack

### Frontend

* Next.js 16
* React 19
* TypeScript
* Tailwind CSS
* Clerk Authentication
* Lucide React

### Backend

* FastAPI
* Pydantic
* Transformers
* PyTorch
* Accelerate
* BitsAndBytes
* SentencePiece

### Infrastructure

* Modal
* AWS S3

---

## 📂 Project Structure

```text
foodGen/

├── recipe-frontend/
│   ├── app/
│   │   ├── components/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── package.json
│   └── next.config.ts
│
├── backend/
│   ├── modal_app/
│   │   ├── main.py
│   │   └── __init__.py
│   │
│   ├── requirements.txt
│   └── README.md
│
└── README.md
```

---

## 🚀 How It Works

1. User enters ingredients and preferences.
2. Frontend sends request to the FastAPI backend.
3. Backend checks AWS S3 for similar recipes.
4. If a match exists, the cached recipe is returned.
5. Otherwise, Mistral 7B generates a new recipe.
6. Generated recipe is stored in S3 for future use.
7. Recipe is returned to the user.

---

## 📥 Example Request

```json
{
  "ingredients": [
    "chicken",
    "garlic",
    "rice"
  ],
  "cuisine": "Asian",
  "cook_time": "30 minutes",
  "cooking_style": "Stir Fry",
  "dietary_restrictions": [],
  "skill_level": "Beginner",
  "meal_type": "Dinner",
  "spice_level": "Medium",
  "user_id": "user_123"
}
```

---

## 📤 Example Response

```json
{
  "title": "Garlic Chicken Rice Bowl",
  "description": "A flavorful stir-fried chicken and rice dish.",
  "ingredients": [],
  "instructions": [],
  "cook_time": "30 minutes",
  "cuisine": "Asian",
  "cooking_style": "Stir Fry",
  "servings": 4,
  "chef_notes": "Best served fresh."
}
```

---

## ⚙️ Environment Variables

### Frontend

Create a `.env.local` file:

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
```

### Backend

```env
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
S3_BUCKET_NAME=
```

### Modal

```env
MODAL_TOKEN_ID=
MODAL_TOKEN_SECRET=
```

---

## 💻 Running the Frontend

Install dependencies:

```bash
cd recipe-frontend
npm install
```

Run development server:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

---

## 🔧 Running the Backend

Create virtual environment:

```bash
python -m venv .venv
```

Activate environment:

### Windows

```bash
.venv\Scripts\activate
```

### Mac/Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
uvicorn modal_app.main:app --reload
```

---

## ☁️ Deploying to Modal

Authenticate:

```bash
modal token new
```

Deploy application:

```bash
modal deploy modal_app/main.py
```

Modal will automatically provision infrastructure and expose the FastAPI endpoint.

---

## 🔮 Future Improvements

* AI-generated recipe images
* Nutrition analysis
* Grocery list generation
* Meal planning calendar
* User recipe collections
* Recipe rating system
* Social recipe sharing
* Vector database similarity search
* Multi-model AI support

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

---

## 📄 License

This project is intended for educational and personal use.

---

## 👨‍💻 Author

Created by **COR1999**

Built with **Next.js**, **FastAPI**, **Modal**, **AWS S3**, and **Mistral 7B**.
