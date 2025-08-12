

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn

# Security configuration
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# FastAPI app
app = FastAPI(
    title="IWNAT API",
    description="Backend API for IWNAT Software Company",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:54067"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    role: str = "user"

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "user"

class Service(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    features: List[str]

class Product(BaseModel):
    id: int
    name: str
    description: str
    features: List[str]
    image_url: Optional[str] = None

class ContactMessage(BaseModel):
    name: str
    email: str
    company: str
    message: str

# Mock database
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@iwnat.com",
        "hashed_password": pwd_context.hash("admin123"),
        "disabled": False,
        "role": "admin"
    },
    "user": {
        "username": "user",
        "full_name": "Regular User",
        "email": "user@example.com",
        "hashed_password": pwd_context.hash("user123"),
        "disabled": False,
        "role": "user"
    }
}

# Mock data
services = [
    Service(
        id=1,
        name="Mobile Development",
        description="Native and cross-platform mobile applications",
        icon="fas fa-mobile-alt",
        features=["iOS Development", "Android Development", "React Native", "Flutter Apps"]
    ),
    Service(
        id=2,
        name="Web Development",
        description="Scalable web applications built with modern technologies",
        icon="fas fa-globe",
        features=["Full-Stack Development", "E-commerce Solutions", "Progressive Web Apps", "API Development"]
    ),
    Service(
        id=3,
        name="Cloud Solutions",
        description="Enterprise-grade cloud infrastructure and migration services",
        icon="fas fa-cloud",
        features=["AWS/Azure/GCP", "DevOps & CI/CD", "Microservices", "Serverless Architecture"]
    ),
    Service(
        id=4,
        name="AI & Machine Learning",
        description="Intelligent solutions powered by artificial intelligence",
        icon="fas fa-robot",
        features=["Predictive Analytics", "Computer Vision", "NLP Solutions", "Custom AI Models"]
    )
]

products = [
    Product(
        id=1,
        name="AnalyticsPro",
        description="Advanced business intelligence platform with real-time analytics",
        features=["Real-time Dashboard", "AI Predictions", "Custom Reports"]
    ),
    Product(
        id=2,
        name="SecureVault",
        description="Enterprise-grade security solution with advanced threat detection",
        features=["Zero Trust", "Threat Intelligence", "Compliance Ready"]
    ),
    Product(
        id=3,
        name="TeamSync",
        description="Collaboration platform designed for modern distributed teams",
        features=["Video Conferencing", "Project Management", "File Sharing"]
    )
]

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Routes
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/api/services", response_model=List[Service])
async def get_services():
    return services

@app.get("/api/services/{service_id}", response_model=Service)
async def get_service(service_id: int):
    service = next((s for s in services if s.id == service_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@app.get("/api/products", response_model=List[Product])
async def get_products():
    return products

@app.get("/api/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    product = next((p for p in products if p.id == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/api/contact")
async def create_contact_message(message: ContactMessage):
    # In a real app, this would save to a database
    return {"message": "Message received successfully", "data": message}

@app.get("/api/admin/users", response_model=List[User])
async def get_all_users(current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return [User(**user) for user in fake_users_db.values()]

@app.post("/api/admin/users", response_model=User)
async def create_user(user: UserCreate, current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "role": user.role
    }
    
    return User(**fake_users_db[user.username])

@app.get("/")
async def root():
    return {"message": "Welcome to IWNAT API", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

