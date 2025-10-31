"""Basic usage example for TokenWise."""

import requests
import json


def main():
    """Run basic optimization example."""

    # API endpoint
    base_url = "http://localhost:8000"

    # Example context (simulate a codebase)
    context = [
        {
            "id": "auth_module",
            "text": """
            # Authentication Module
            
            def authenticate_user(username, password):
                '''Authenticate user with username and password.'''
                user = get_user_from_db(username)
                if user and verify_password(password, user.password_hash):
                    return generate_jwt_token(user)
                return None
            
            def verify_token(token):
                '''Verify JWT token validity.'''
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                    return payload
                except jwt.InvalidTokenError:
                    return None
            
            def generate_jwt_token(user):
                '''Generate JWT token for user.'''
                payload = {
                    'user_id': user.id,
                    'username': user.username,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }
                return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            """,
            "type": "code",
        },
        {
            "id": "database_module",
            "text": """
            # Database Module
            
            def get_user_from_db(username):
                '''Fetch user from database by username.'''
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                conn.close()
                return user
            
            def save_user_to_db(user):
                '''Save user to database.'''
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (user.username, user.email, user.password_hash)
                )
                conn.commit()
                conn.close()
            """,
            "type": "code",
        },
        {
            "id": "api_routes",
            "text": """
            # API Routes
            
            @app.post("/login")
            def login(credentials: LoginCredentials):
                '''User login endpoint.'''
                token = authenticate_user(credentials.username, credentials.password)
                if token:
                    return {"access_token": token, "token_type": "bearer"}
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            @app.get("/profile")
            def get_profile(token: str = Depends(oauth2_scheme)):
                '''Get user profile endpoint.'''
                payload = verify_token(token)
                if not payload:
                    raise HTTPException(status_code=401, detail="Invalid token")
                user = get_user_from_db(payload['username'])
                return {"username": user.username, "email": user.email}
            """,
            "type": "code",
        },
        {
            "id": "readme",
            "text": """
            # Project Documentation
            
            This is a web application with user authentication. It uses JWT tokens
            for authentication and stores user data in a SQLite database.
            
            ## Features
            - User registration
            - User login with JWT tokens
            - Protected API endpoints
            - Password hashing with bcrypt
            
            ## Setup
            1. Install dependencies: pip install -r requirements.txt
            2. Initialize database: python init_db.py
            3. Run server: uvicorn main:app --reload
            """,
            "type": "docs",
        },
    ]

    # User query
    query = "How does the JWT authentication work in this application?"

    # Optimization request
    request_data = {
        "query": query,
        "context": context,
        "targetTokens": 2000,
        "options": {
            "strategy": "diversity",
            "includeMetadata": True,
            "preserveOrder": False,
            "minRelevanceScore": 0.3,
            "diversityLambda": 0.5,
        },
    }

    print("=" * 80)
    print("TokenWise Context Optimization Example")
    print("=" * 80)
    print(f"\nQuery: {query}")
    print(f"\nOriginal Context: {len(context)} items")

    # Send request
    try:
        response = requests.post(f"{base_url}/optimize", json=request_data, timeout=30)

        if response.status_code == 200:
            result = response.json()

            print("\n" + "=" * 80)
            print("Optimization Results")
            print("=" * 80)

            stats = result["stats"]
            print(f"\n📊 Statistics:")
            print(f"  • Original Tokens: {stats['original_tokens']}")
            print(f"  • Optimized Tokens: {stats['optimized_tokens']}")
            print(f"  • Reduction: {stats['reduction_percent']}%")
            print(f"  • Estimated Savings: ${stats['estimated_savings_usd']}")
            print(f"  • Processing Time: {stats['processing_time_ms']}ms")
            print(f"  • Chunks Analyzed: {stats['chunks_analyzed']}")
            print(f"  • Chunks Selected: {stats['chunks_selected']}")

            print(f"\n🎯 Selected Context Chunks:")
            for i, chunk in enumerate(result["optimized_context"], 1):
                print(f"\n  {i}. Source: {chunk['source']}")
                print(f"     Relevance: {chunk['relevance_score']:.3f}")
                print(f"     Reason: {chunk['reason']}")
                print(f"     Preview: {chunk['text'][:100]}...")

            print("\n" + "=" * 80)

        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.json())

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to TokenWise API")
        print("   Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
