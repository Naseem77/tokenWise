"""Advanced usage example with vector store indexing."""

import requests
import json
import time


def main():
    """Run advanced optimization example with indexing."""

    base_url = "http://localhost:8000"

    # Check API health
    print("Checking API health...")
    health_response = requests.get(f"{base_url}/health")
    print(f"Status: {health_response.json()}\n")

    # Example: Large codebase context
    codebase_files = [
        {
            "id": "user_model.py",
            "text": """
            from sqlalchemy import Column, Integer, String, DateTime
            from database import Base
            import bcrypt
            
            class User(Base):
                __tablename__ = 'users'
                
                id = Column(Integer, primary_key=True)
                username = Column(String(50), unique=True, nullable=False)
                email = Column(String(100), unique=True, nullable=False)
                password_hash = Column(String(255), nullable=False)
                created_at = Column(DateTime, default=datetime.utcnow)
                
                def set_password(self, password):
                    self.password_hash = bcrypt.hashpw(
                        password.encode('utf-8'), 
                        bcrypt.gensalt()
                    ).decode('utf-8')
                
                def check_password(self, password):
                    return bcrypt.checkpw(
                        password.encode('utf-8'),
                        self.password_hash.encode('utf-8')
                    )
            """,
            "type": "code",
        },
        {
            "id": "auth_service.py",
            "text": """
            from jose import JWTError, jwt
            from datetime import datetime, timedelta
            from config import settings
            
            class AuthService:
                def create_access_token(self, data: dict):
                    to_encode = data.copy()
                    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                    to_encode.update({"exp": expire})
                    encoded_jwt = jwt.encode(
                        to_encode, 
                        settings.SECRET_KEY, 
                        algorithm=settings.ALGORITHM
                    )
                    return encoded_jwt
                
                def verify_token(self, token: str):
                    try:
                        payload = jwt.decode(
                            token, 
                            settings.SECRET_KEY, 
                            algorithms=[settings.ALGORITHM]
                        )
                        username: str = payload.get("sub")
                        if username is None:
                            return None
                        return username
                    except JWTError:
                        return None
            """,
            "type": "code",
        },
        {
            "id": "api_endpoints.py",
            "text": """
            from fastapi import APIRouter, Depends, HTTPException, status
            from sqlalchemy.orm import Session
            from auth_service import AuthService
            from user_model import User
            from database import get_db
            
            router = APIRouter()
            auth_service = AuthService()
            
            @router.post("/register")
            def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
                existing_user = db.query(User).filter(User.username == username).first()
                if existing_user:
                    raise HTTPException(status_code=400, detail="Username already exists")
                
                user = User(username=username, email=email)
                user.set_password(password)
                db.add(user)
                db.commit()
                return {"message": "User created successfully"}
            
            @router.post("/login")
            def login(username: str, password: str, db: Session = Depends(get_db)):
                user = db.query(User).filter(User.username == username).first()
                if not user or not user.check_password(password):
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                
                access_token = auth_service.create_access_token(data={"sub": user.username})
                return {"access_token": access_token, "token_type": "bearer"}
            """,
            "type": "code",
        },
    ]

    print("=" * 80)
    print("Advanced TokenWise Example: Indexing + Optimization")
    print("=" * 80)

    # Step 1: Index all files (optional, for faster future queries)
    print("\n📚 Step 1: Indexing codebase...")
    for file in codebase_files:
        try:
            response = requests.post(f"{base_url}/index", json=file, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Indexed {file['id']}: {result['chunks_indexed']} chunks")
        except Exception as e:
            print(f"  ✗ Failed to index {file['id']}: {e}")

    # Step 2: Test different optimization strategies
    queries = [
        ("How do I authenticate a user?", "diversity"),
        ("Show me the user model structure", "top-n"),
        ("How are passwords hashed?", "dependency"),
    ]

    for query, strategy in queries:
        print(f"\n{'=' * 80}")
        print(f"🔍 Query: {query}")
        print(f"📐 Strategy: {strategy}")
        print("=" * 80)

        request_data = {
            "query": query,
            "context": codebase_files,
            "targetTokens": 1500,
            "options": {"strategy": strategy, "includeMetadata": True, "minRelevanceScore": 0.2},
        }

        try:
            start = time.time()
            response = requests.post(f"{base_url}/optimize", json=request_data, timeout=30)
            elapsed = (time.time() - start) * 1000

            if response.status_code == 200:
                result = response.json()
                stats = result["stats"]

                print(f"\n✅ Optimization Complete:")
                print(f"  • Reduction: {stats['reduction_percent']}%")
                print(f"  • Tokens: {stats['original_tokens']} → {stats['optimized_tokens']}")
                print(f"  • Savings: ${stats['estimated_savings_usd']}")
                print(
                    f"  • Time: {elapsed:.1f}ms (API) + {stats['processing_time_ms']:.1f}ms (processing)"
                )
                print(f"  • Selected: {stats['chunks_selected']}/{stats['chunks_analyzed']} chunks")

                print(f"\n📋 Top Selected Chunks:")
                for i, chunk in enumerate(result["optimized_context"][:3], 1):
                    print(f"  {i}. {chunk['source']} (score: {chunk['relevance_score']:.3f})")
                    print(f"     → {chunk['reason']}")

        except Exception as e:
            print(f"❌ Error: {e}")

    # Step 3: Get system statistics
    print(f"\n{'=' * 80}")
    print("📊 System Statistics")
    print("=" * 80)

    try:
        stats_response = requests.get(f"{base_url}/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"\nVector Store: {stats['vector_store']['total_chunks']} chunks")
            print(f"Cache TTL: {stats['cache']['ttl']}s")
            print(f"Token Budget: {stats['config']['default_token_budget']}")
            print(f"Embedding Model: {stats['config']['embedding_model']}")
            print(f"\nScoring Weights:")
            for key, value in stats["config"]["scoring_weights"].items():
                print(f"  • {key.capitalize()}: {value}")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
