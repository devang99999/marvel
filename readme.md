# 🦸‍♂️ Marvel AI Chatbot

> *"With great power comes great responsibility... to build incredible AI experiences."*

A cutting-edge, real-time Marvel-themed chatbot powered by Groq's LLaMA models, featuring intelligent web scraping, MongoDB data storage, and a sleek React frontend. Built for Marvel fans who demand both style and substance.

## ✨ Features

### 🧠 **Intelligent AI Chat**
- **Groq LLaMA Integration**: Harnesses the power of Groq's advanced LLaMA models for context-aware, intelligent responses
- **Multi-turn Conversations**: Maintains conversation memory for natural, flowing dialogue
- **Marvel-Specialized**: Fine-tuned responses focused on Marvel universe content

### 🔍 **Hybrid Search System**
- **Local MongoDB Search**: Lightning-fast queries from curated Marvel database
- **Real-time Web Scraping**: Automatic fallback to live web scraping using SerpAPI + Playwright
- **Smart Query Generation**: AI-powered search query optimization

### 📚 **Advanced Data Pipeline**
- **Dynamic Content Crawling**: Automatically discovers and indexes Marvel-related content
- **Intelligent Classification**: AI-powered content categorization and curation
- **Clean Data Storage**: Processed and structured content storage in MongoDB

### 💬 **Session Management**
- **Unique Chat Sessions**: Each conversation gets a unique ID for easy reference
- **Persistent History**: All conversations auto-saved and retrievable
- **Cross-device Sync**: Access your chat history from anywhere

### 🧭 **Smart Recommendations**
- **Context-Aware Suggestions**: Recommendations based on current conversation
- **Historical Analysis**: Leverages chat history for personalized suggestions
- **Trending Topics**: Integration with popular Marvel discussions

### 🎨 **Modern User Experience**
- **Responsive Design**: Seamless experience across desktop, tablet, and mobile
- **Dark/Light Mode**: Beautiful themes for any preference
- **JWT Authentication**: Secure user sessions and data protection
- **Real-time Updates**: Instant message delivery and status updates

## 🏗️ Architecture

```
marvel-ai-chatbot/
├── 🔧 Backend Core
│   ├── phase_1.py              # Query generation & web scraping
│   ├── phase_2.py              # Data classification & curation
│   ├── phase_3.py              # Core chat logic & AI integration
│   ├── phase_4.py              # Live fallback & scraping engine
│   ├── server_prime.py         # Flask API server with JWT auth
│   └── requirements.txt        # Python dependencies
│
├── 🎨 Frontend (React)
│   ├── src/
│   │   ├── api/                # Backend API integration
│   │   ├── components/         # Reusable UI components
│   │   │   ├── Chat/           # Chat interface components
│   │   │   ├── Auth/           # Authentication forms
│   │   │   └── UI/             # Common UI elements
│   │   ├── contexts/           # React contexts (Auth, Theme)
│   │   ├── hooks/              # Custom hooks (useChat, useDarkMode)
│   │   ├── pages/              # Route components
│   │   └── utils/              # Helper functions
│   ├── index.html
│   ├── tailwind.config.js      # Tailwind configuration
│   └── vite.config.js          # Vite build configuration
│
├── 🧪 Testing
│   ├── test.py                 # Pipeline testing
│   └── test2.py                # Integration testing
│
└── 🚀 Deployment
    └── render.yaml             # Deployment configuration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB instance
- Groq API key
- SerpAPI key

### 🔧 Backend Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd marvel-ai-chatbot

# Install Python dependencies
pip install -r requirements.txt 

# Configure environment variables (see backend/.env.example)
cd backend && cp .env.example .env
# Edit .env with MONGO_URI, JWT_SECRET_KEY, GROQ_API_KEY, etc.

# Start the Flask backend (development only)
python server_prime.py
# Production: use gunicorn (e.g. gunicorn server_prime:app); never run python server_prime.py in production.
```

### 🎨 Frontend Setup

```bash
# Navigate to frontend directory
cd marvel

# Install dependencies
npm install

# Start development server
npm run dev
```

Your application will be available at:
- **Backend**: `http://localhost:5001` (server_prime.py; use gunicorn in production)
- **Frontend**: `http://localhost:5173`

## ⚙️ Environment Configuration

Create a `.env` file in the `backend` directory (see `backend/.env.example`):

```env
# Database
MONGO_URI=mongodb://localhost:27017/marvel_chatbot

# Auth (required for login/register)
JWT_SECRET_KEY=your_secret_key_at_least_32_chars

# AI
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_KEY=your_serpapi_key_here

# Optional
FRONTEND_URL=https://your-app.netlify.app
# Production: set FLASK_ENV=production or DEBUG=0; never put real secrets in render.yaml (use Render dashboard).
```

## 🛠️ Technology Stack

### **Backend**
| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Core backend language | 3.8+ |
| **Flask** | Web framework | 2.3+ |
| **Groq API** | LLaMA model integration | Latest |
| **MongoDB** | Database & search | 4.4+ |
| **SerpAPI** | Search results | Latest |
| **Playwright** | Web scraping | Latest |

### **Frontend**
| Technology | Purpose | Version |
|------------|---------|---------|
| **React** | UI framework | 18+ |
| **Vite** | Build tool | 4+ |
| **Tailwind CSS** | Styling | 3+ |
| **React Router** | Navigation | 6+ |
| **Axios** | HTTP client | Latest |

## 🔐 Authentication Flow

1. **Registration/Login**: Users create accounts or sign in; server validates email format and password length (min 8 characters).
2. **JWT Token**: Server issues signed JWT tokens (set `JWT_SECRET_KEY` in env).
3. **Token Storage**: Tokens stored in localStorage; send as `Authorization: Bearer <token>` for protected routes.
4. **Protected Routes**: `/chat-response`, `/chats/<user_id>`, `/history/<chat_id>` require a valid JWT; server verifies ownership.
5. **Session Persistence**: Chat history tied to user accounts; production API is `server_prime.py` (phase_*.py are scripts/legacy).

## 🧪 Testing

Run the test suite to ensure everything works correctly:

```bash
# Frontend
cd frontend && npm run dev
```

Security checks (optional): `pip install pip-audit && pip-audit` in backend; `npm audit` in frontend.

## 📊 API Endpoints (server_prime.py)

### Authentication
- `POST /register` - User registration (returns JWT and user)
- `POST /login` - User login (returns JWT and user)

### Chat (protected: send `Authorization: Bearer <JWT>`)
- `POST /chat` - Send message, get AI response (no auth; RAG-only)
- `POST /chat-response` - Send messages + optional chatId; returns answer and chat_id (auth required)
- `GET /chats/<user_id>` - List chat sessions for user (auth required; user_id must match token)
- `GET /history/<chat_id>` - Get messages for a chat (auth required; chat must belong to user)
- `GET /chat/<chat_id>/<user_id>` - Alias for history (auth required)
- `POST /recommendations` - Get follow-up suggestions from messages

## 🌟 Key Features Deep Dive

### **AI-Powered Conversations**
The chatbot uses Groq's LLaMA models to provide intelligent, contextual responses about the Marvel universe. Each conversation maintains context and can reference previous messages for natural dialogue flow.

### **Hybrid Search Strategy**
- **Primary**: Fast local search through curated MongoDB database
- **Fallback**: Real-time web scraping when local data is insufficient
- **Smart Routing**: AI determines the best search strategy for each query

### **Dynamic Content Pipeline**
1. **Query Generation**: AI creates optimal search queries
2. **Web Crawling**: Discovers relevant Marvel content across the web
3. **Content Processing**: Cleans and structures scraped data
4. **Database Storage**: Stores processed content in MongoDB
5. **Classification**: Categorizes content for improved searchability

## 🚀 Deployment

### **Development**
```bash
# Backend
python server_prime.py

# Frontend
cd marvel && npm run dev
```

### **Production**
- **Backend**: Run with `gunicorn server_prime:app` (e.g. in Render); set `FLASK_ENV=production` or `DEBUG=0`. Do not run `python server_prime.py` in production (debug mode off when env is set).
- **Secrets**: Set `MONGO_URI`, `JWT_SECRET_KEY`, `GROQ_API_KEY` in the Render dashboard (or your platform); do not put secrets in `render.yaml`.
- **Frontend**: Build with `cd frontend && npm run build` and deploy the `dist` folder.
- **Keep Render awake**: A GitHub Actions workflow (`.github/workflows/ping-render.yml`) pings the backend every 14 minutes so the free tier doesn’t sleep. Default URL is `https://marvel-b1wd.onrender.com/`; override with repo variable `RENDER_BACKEND_URL` in Settings → Actions → Variables.

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript/React
- Write tests for new features
- Update documentation as needed

## 📋 Roadmap

### **Phase 1: Core Features** ✅
- [x] AI chat integration
- [x] Basic web scraping
- [x] MongoDB storage
- [x] User authentication
- [x] React frontend

### **Phase 2: Enhanced Experience** 🚧
- [ ] Advanced recommendation engine
- [ ] Voice chat capabilities
- [ ] Marvel character personas
- [ ] Social sharing features

### **Phase 3: Scale & Polish** 📋
- [ ] Performance optimization
- [ ] Advanced analytics
- [ ] Mobile app (React Native)
- [ ] Admin dashboard

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Acknowledgments

- **Marvel Entertainment** for creating the incredible universe that inspired this project
- **Groq** for providing powerful LLaMA model access
- **MongoDB** for robust data storage solutions
- **The Open Source Community** for the amazing tools and libraries
<!-- 
## 📞 Support

Having issues? We're here to help!

- 🐛 **Bug Reports**: [Open an issue](../../issues)
- 💡 **Feature Requests**: [Start a discussion](../../discussions)
- 📧 **Direct Contact**: [your-email@example.com] -->

---

<div align="center">

**⚡ Built with passion for the Marvel Universe ⚡**

<!-- *Made with ❤️ by developers who believe in heroes* -->

[⬆️ Back to Top](#-marvel-ai-chatbot)

</div>