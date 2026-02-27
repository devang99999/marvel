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

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and MongoDB URI

# Start the Flask backend
python phase_4.py
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
- **Backend**: `http://localhost:5000`
- **Frontend**: `http://localhost:5173`

## ⚙️ Environment Configuration

In the `marvel` directory, copy the example env file and fill in your values:

```bash
cd marvel
cp .env.example .env
# Edit .env with your API keys and MongoDB URI
```

All supported variables (see [.env.example](.env.example) for a full list):

```env
# AI & Search APIs
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_KEY=your_serpapi_key_here

# Database (key is "mongo" in code)
mongo=mongodb://localhost:27017/marvel_crawler

# Chat system prompt: fully dynamic (avoids generic "you're a chatbot" style)
CHATBOT_CREATOR_NAME=Devang Gandhi
CHATBOT_CREATOR_TITLE=AI engineer
CHATBOT_PROJECT_NAME=Marvel Chatbot
# Optional: override sections instead of using defaults
# CHATBOT_IDENTITY=You are {{PROJECT_NAME}}, created by {{CREATOR_NAME}}. Expert in Marvel.
# CHATBOT_TASK=Answer using context when relevant; otherwise your knowledge. No implementation jargon.
# CHATBOT_TONE=Concise, friendly, minimal markdown.
# CHATBOT_EXTRA_RULES=You are still learning and improving every day.
# Full custom prompt (overrides everything): use \n for newlines. Placeholders: {{CREATOR_NAME}}, {{CREATOR_TITLE}}, {{PROJECT_NAME}}
# CHATBOT_SYSTEM_PROMPT=You are {{PROJECT_NAME}}.\nCreated by {{CREATOR_NAME}}, {{CREATOR_TITLE}}.\n\nAnswer Marvel questions clearly. If asked who made you, say {{CREATOR_NAME}}, {{CREATOR_TITLE}}.\n\nTone: concise, friendly.

# Optional: Deployment
RENDER_EXTERNAL_URL=https://marvel-b1wd.onrender.com/
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

1. **Registration/Login**: Users create accounts or sign in
2. **JWT Token**: Server issues secure JWT tokens
3. **Token Storage**: Tokens stored securely in localStorage
4. **Protected Routes**: Chat interface requires valid authentication
5. **Session Persistence**: Chat history tied to user accounts

## 🧪 Testing

Run the test suite to ensure everything works correctly:

```bash

# Frontend testing
cd marvel
npm run dev
```

## 📊 API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/logout` - User logout

### Chat
- `POST /api/chat` - Send message and get AI response
- `GET /api/chat/history` - Retrieve chat history
- `GET /api/chat/sessions` - List all chat sessions

### Search
- `GET /api/search` - Search Marvel database
- `POST /api/scrape` - Trigger manual content scraping

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
```bash
# Build frontend
cd marvel && npm run build

# Deploy to Render/AWS/Heroku
# Configure render.yaml or your preferred platform
```

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