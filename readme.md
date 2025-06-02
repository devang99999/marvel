# Marvel AI Chatbot 🦸‍♂️

> A real-time Marvel-themed AI chatbot that mimics the ChatGPT experience with persistent chat sessions, user authentication, and Marvel-specific knowledge powered by Groq's LLaMA model.

## 🌟 Features

- **🦸 Marvel Universe Knowledge** - Specialized AI responses about Marvel characters, storylines, and universe
- **💬 Real-time Chat** - ChatGPT-style conversational interface with multi-turn context
- **🔐 User Authentication** - Secure login/register system with JWT tokens
- **💾 Persistent Chat History** - MongoDB-powered chat sessions that persist across visits
- **📱 Fully Responsive** - Optimized for desktop, tablet, and mobile devices
- **🌙 Theme Support** - Dark/light mode toggle for comfortable viewing
- **📂 Session Management** - Create and switch between multiple chat sessions

## 🚀 Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | [https://your-frontend-url.vercel.app](https://your-frontend-url.vercel.app) |
<!--| **Backend API** | [https://your-backend-url.onrender.com](https://your-backend-url.onrender.com) |-->

## 🏗️ Architecture

**Tech Stack:**
- **Backend:** Flask (Python) + MongoDB + Groq LLaMA API
- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Deployment:** Render (Backend) + Vercel (Frontend)

## 📂 Project Structure

```
marvel-ai-chatbot/
├── backend/                    # Flask API Server
│   ├── server.py              # Main Flask application
│   ├── auth.py                # Authentication routes
│   ├── chat.py                # Chat logic & Groq integration
│   ├── database.py            # MongoDB connection
│   ├── models.py              # Database schemas
│   ├── utils.py               # Helper functions
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page components
│   │   ├── App.tsx            # Main App component
│   │   └── main.tsx           # Entry point
│   ├── public/                # Static assets
│   ├── index.html             # HTML template
│   ├── vite.config.ts         # Vite configuration
│   ├── tailwind.config.js     # Tailwind CSS config
│   └── package.json           # Node dependencies
│
├── render.yaml                # Render deployment config
├── README.md                  # Project documentation
└── .gitignore                 # Git ignore rules
```

## 🛠️ Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB database
- Groq API key

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create `.env` file in the backend folder:
   ```env
   MONGO_URI=your-mongodb-connection-string
   GROQ_API_KEY=your-groq-api-key
   SECRET_KEY=your-flask-secret-key
   ```

4. **Start the Flask server**
   ```bash
   python server.py
   ```

   Server will run on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   
   Create `.env` file in the frontend folder:
   ```env
   VITE_BACKEND_URL=http://localhost:5000
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

   Application will run on `http://localhost:5173`

## 🚀 Deployment

### Backend (Render)

1. Connect your GitHub repository to Render
2. Use the included `render.yaml` configuration
3. Set environment variables in Render dashboard:
   - `MONGO_URI`
   - `GROQ_API_KEY`
   - `SECRET_KEY`

### Frontend (Vercel/Netlify)

1. Connect your GitHub repository
2. Set build command: `npm run build`
3. Set output directory: `dist`
4. Configure environment variable:
   - `VITE_BACKEND_URL=https://your-backend-url.onrender.com`

## 📋 Development Roadmap

### ✅ Completed Phases

- **Phase 1:** Dynamic Query Generation + Data Scraping
  - Groq LLaMA integration for search term generation
  - SerpAPI for URL fetching
  - Playwright + BeautifulSoup for data scraping
  - MongoDB data storage

- **Phase 2:** Authentication System
  - User registration and login endpoints
  - JWT token-based authentication
  - Frontend auth integration

- **Phase 3:** Real-time Chat Interface
  - ChatGPT-style UI implementation
  - Multi-turn conversation context
  - Backend chat API endpoints

- **Phase 4:** Chat History Persistence
  - MongoDB chat session storage
  - Unique session UUID generation
  - Chat resume functionality

- **Phase 5:** Session Management
  - Multiple chat sessions per user
  - Session switching interface
  - Sidebar session listing

### 🚧 In Progress

- **Phase 6:** Contextual Recommendations
  - Smart question suggestions
  - Related character recommendations
  - Context-aware prompts

### 📅 Planned

- **Phase 7:** Production Polish
  - Performance optimizations
  - Enhanced error handling
  - Advanced security features

## 🔧 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `POST /logout` - User logout

### Chat
- `POST /chat` - Send message and get AI response
- `GET /chat/sessions` - Get user's chat sessions
- `GET /chat/sessions/:id` - Get specific chat session
- `DELETE /chat/sessions/:id` - Delete chat session

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Groq** for providing the LLaMA API
- **Marvel** for the incredible universe of characters and stories
- **OpenAI** for ChatGPT interface inspiration

---

<div align="center">

**Made with ❤️ for Marvel fans and AI enthusiasts**

[Report Bug](https://github.com/yourusername/marvel-ai-chatbot/issues) · [Request Feature](https://github.com/yourusername/marvel-ai-chatbot/issues) · [Documentation](https://github.com/yourusername/marvel-ai-chatbot/wiki)

</div>
