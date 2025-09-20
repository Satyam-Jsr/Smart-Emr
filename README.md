# 🏥 EMR - Electronic Medical Records System

A modern, AI-powered Electronic Medical Records system built with React, FastAPI, and advanced AI capabilities for medical document processing and intelligent Q&A.

## ✨ Features

### 📋 Core Functionality
- **Patient Management**: Create, view, edit, and delete patient records
- **Medical Notes**: Add, edit, and manage patient notes with timestamps
- **Document Upload**: Upload medical documents with OCR processing
- **Timeline View**: Chronological visualization of patient medical history
- **Vital Signs Tracking**: Monitor and visualize patient trends

### 🤖 AI-Powered Features
- **Intelligent Q&A**: Ask natural language questions about patient records
- **Medical Document OCR**: Automatic text extraction from uploaded documents
- **AI Summarization**: Generate concise summaries of patient history
- **RAG (Retrieval Augmented Generation)**: Context-aware responses using patient data

### 🔧 Technical Features
- **Multiple AI Providers**: OpenRouter, Gemini, Ollama, GPT4All support
- **Response Optimization**: Timeout handling and response size management
- **Error Handling**: Comprehensive error management with fallback systems
- **Real-time Updates**: Live data synchronization across components

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+**
- **Node.js 18+**
- **npm or yarn**

### 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd emr
   ```

2. **Backend Setup**
   ```bash
   cd backend
   
   # Create virtual environment (recommended)
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure AI Services** (Create `.env` file in backend folder)
   ```env
   # OpenRouter (Primary AI Service)
   OPENROUTER_API_KEY=your_openrouter_api_key
   OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct
   
   # Gemini (Fallback)
   GEMINI_API_KEY=your_gemini_api_key
   
   # Optional: Ollama, GPT4All, etc.
   ```

4. **Initialize Database**
   ```bash
   python seed_db.py
   ```

5. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

### 🏃‍♂️ Running the Application

1. **Start Backend Server**
   ```bash
   cd backend
   python app.py
   ```
   Backend runs on: `http://localhost:8002`

2. **Start Frontend Server**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend runs on: `http://localhost:5173`

3. **Access Application**
   Open `http://localhost:5173` in your browser

## 📁 Project Structure

```
emr/
├── backend/                    # FastAPI backend
│   ├── app/                   # Main application
│   │   ├── api/               # API routes
│   │   ├── database.py        # Database configuration
│   │   ├── models.py          # SQLAlchemy models
│   │   └── schemas.py         # Pydantic schemas
│   ├── app.py                 # Main application file
│   ├── requirements.txt       # Python dependencies
│   ├── seed_db.py            # Database seeding
│   ├── *_wrapper.py          # AI service integrations
│   └── rag_prototype.py      # RAG implementation
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── api/              # API client
│   │   ├── components/       # React components
│   │   ├── context/          # React context providers
│   │   ├── pages/            # Page components
│   │   └── main.tsx          # Application entry point
│   ├── package.json          # Node.js dependencies
│   └── vite.config.ts        # Vite configuration
└── docker-compose.yml        # Docker setup (optional)
```

## 🔌 API Endpoints

### Patient Management
- `GET /patients/` - List all patients
- `POST /patients` - Create new patient
- `GET /patients/{id}` - Get patient details
- `DELETE /patients/{id}` - Delete patient

### Medical Notes
- `GET /patients/{id}/notes` - Get patient notes
- `POST /patients/{id}/notes` - Add new note
- `PUT /patients/notes/{note_id}` - Update note
- `DELETE /notes/{note_id}` - Delete note

### AI Services
- `POST /patients/{id}/qa` - Ask questions about patient
- `POST /patients/{id}/summarize` - Generate patient summary
- `POST /patients/{id}/upload-document` - Upload and process documents

## 🤖 AI Configuration

### Supported AI Providers

1. **OpenRouter** (Recommended)
   ```env
   OPENROUTER_API_KEY=your_key
   OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct
   ```

2. **Google Gemini**
   ```env
   GEMINI_API_KEY=your_key
   ```

3. **Ollama** (Local)
   ```bash
   # Install Ollama and run:
   ollama serve
   ```

4. **GPT4All** (Local)
   - Automatically downloads models on first use

### Performance Optimization
- **Response Timeout**: 20 seconds for OpenRouter
- **Response Size Limit**: 2000 characters (configurable)
- **Fallback Chain**: OpenRouter → Gemini → Local extraction

## 💡 Usage Examples

### Adding a Patient
1. Click "Add Patient" in the left sidebar
2. Fill in patient information
3. Save to create the patient record

### Uploading Documents
1. Select a patient
2. Go to "Medical Documents" tab
3. Upload PDF/image files
4. OCR text is automatically extracted and added as notes

### Using AI Q&A
1. Select a patient with medical history
2. Click "Ask Question" button
3. Type questions like:
   - "What are the recent lab results?"
   - "What medications is the patient taking?"
   - "Any allergies or adverse reactions?"

### Generating Summaries
1. Select a patient
2. Click "Generate Summary"
3. View AI-generated patient overview with key points

## 🛠️ Development

### Adding New AI Providers
1. Create a new wrapper file (e.g., `new_ai_wrapper.py`)
2. Implement the required interface:
   ```python
   def generate_json_summary(retrieved_data, question=None):
       # Your implementation
       return {
           "one_line": "Summary",
           "bullets": ["Point 1", "Point 2"],
           "sources": []
       }
   ```
3. Add to the fallback chain in `app.py`

### Frontend Component Structure
- **PatientPage**: Main patient view with fixed header
- **Timeline**: Medical history timeline with scrolling
- **QAOverlay**: AI question interface
- **DocumentUpload**: File upload with OCR processing

### Database Schema
- **Patient**: Basic patient information
- **Note**: Medical notes with timestamps
- **MedicalDocument**: Uploaded documents with metadata
- **SummaryCache**: Cached AI summaries for performance

## 🚨 Troubleshooting

### Common Issues

1. **Q&A Timeouts**
   - Check AI service configuration
   - Reduce response complexity
   - Verify network connectivity

2. **Document Upload Fails**
   - Check file permissions in uploads/ directory
   - Verify supported file formats (PDF, JPG, PNG)
   - Check file size limits

3. **Backend Won't Start**
   - Verify Python version (3.12+)
   - Install missing dependencies: `pip install -r requirements.txt`
   - Check port 8002 availability

4. **Frontend Build Errors**
   - Update Node.js to version 18+
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Check TypeScript errors

### Performance Tips
- Use local AI models (Ollama/GPT4All) for privacy
- Enable response caching for better performance
- Limit document size for faster OCR processing
- Monitor API rate limits for cloud services

## 🔒 Security Considerations

- **API Keys**: Store in environment variables, never commit to code
- **Patient Data**: Ensure HIPAA compliance in production
- **File Uploads**: Validate file types and scan for malware
- **Database**: Use proper authentication and encryption

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FastAPI**: Modern Python web framework
- **React**: Frontend library with excellent ecosystem
- **OpenRouter**: AI model access platform
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Fast build tool for modern web apps

---

## 📞 Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation

**Happy coding! 🚀**