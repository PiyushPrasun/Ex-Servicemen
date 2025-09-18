# 🎖️ NeoResuMaker - Ex-Servicemen Resume Builder

A powerful AI-enhanced resume builder specifically designed for military veterans transitioning to civilian careers. This application leverages advanced OCR technology and AI to extract information from military documents and generate professional civilian resumes.

## ✨ Features

### 🔍 Advanced Document Processing

- **OCR Support**: Extract text from image-based PDFs and scanned documents
- **Multi-format Support**: Handle PDF, PNG, JPG, JPEG files
- **Automatic Detection**: Smart detection of text-based vs image-based documents
- **Military Document Optimization**: Specialized patterns for military service records

### 🤖 AI-Powered Enhancement

- **Military Rank Detection**: Automatically identifies and maps military ranks (Colonel, Captain, Major, etc.)
- **Civilian Translation**: Converts military jargon to civilian-friendly terminology
- **Professional Content Generation**: AI-generated summaries, experience descriptions, and skills
- **ATS Optimization**: Resume content optimized for Applicant Tracking Systems

### 📋 Comprehensive Data Extraction

- **Personal Information**: Name, contact details, address, military rank
- **Professional Experience**: Service history with rank-specific translations
- **Education & Certifications**: Academic background and military training
- **Skills & Competencies**: Technical and leadership skills with rank-based enhancements
- **Achievements & Awards**: Military honors translated for civilian understanding

### 🎨 Professional Resume Design

- **Modern Layout**: Clean, professional design with white header and structured sections
- **Photo Integration**: Optional profile photo placement
- **Responsive Design**: Optimized for both digital viewing and printing
- **Multiple Export Formats**: PDF and HTML download options

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR (for image text extraction)
- Git

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd military_resume
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Install Tesseract OCR**

**Windows:**

- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Add Tesseract to your system PATH

**macOS:**

```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

4. **Download spaCy language model**

```bash
python -m spacy download en_core_web_sm
```

5. **Set up environment variables (optional)**
   Create a `.env` file in the project root:

```
MISTRAL_API_KEY=your_mistral_api_key_here
```

### Running the Application

```bash
streamlit run resume.py --server.port 8502
```

Open your browser and navigate to `http://localhost:8502`

## 📖 Usage Guide

### 1. Document Upload

- Navigate to the "📄 Document Upload" tab
- Upload your military service document (PDF or image)
- Choose between basic extraction or AI-enhanced extraction
- Wait for the processing to complete

### 2. Data Review & Editing

- Switch to the "✏ Manual Entry" tab
- Review and edit the extracted information
- Add or modify personal details, experience, skills, etc.
- The system automatically detects military ranks and suggests appropriate civilian equivalents

### 3. Resume Generation

- Click "🚀 Generate AI-Enhanced Resume"
- Preview your professional resume
- Download as PDF or HTML format

### 4. Data Preview

- Use the "📊 Data Preview" tab to see all extracted information
- Export extracted data as JSON for future use

## 🛠️ Technical Architecture

### Core Components

#### Enhanced Resume Extractor

- **Text Processing**: Advanced regex patterns for various document formats
- **Military Rank Detection**: Specialized algorithm for rank identification
- **Context-Aware Extraction**: Uses document structure analysis for better accuracy
- **Multi-strategy Approach**: Combines pattern matching, NLP, and context analysis

#### AI Enhancement Engine

- **Mistral AI Integration**: Professional content generation
- **Military-to-Civilian Translation**: Specialized prompts for career transition
- **Content Optimization**: ATS-friendly formatting and keyword optimization

#### OCR Processing Pipeline

- **Automatic Detection**: Determines if OCR is needed
- **Image Enhancement**: Preprocessing for better text recognition
- **Error Correction**: Post-processing to fix common OCR errors

### Data Flow

1. **Document Upload** → **Format Detection** → **Text/OCR Extraction**
2. **Text Analysis** → **Pattern Matching** → **Data Extraction**
3. **Military Rank Detection** → **AI Enhancement** → **Content Generation**
4. **Resume Assembly** → **HTML/PDF Generation** → **Download**

## 🔧 Configuration

### Environment Variables

- `MISTRAL_API_KEY`: Your Mistral AI API key for enhanced content generation
- `TESSERACT_CMD`: Custom path to Tesseract executable (if not in PATH)

### Customization Options

- **Military Ranks**: Extend the rank detection in `extract_military_rank()` function
- **Resume Templates**: Modify the HTML template in `get_resume_html()` function
- **AI Prompts**: Customize AI enhancement prompts for different career paths

## 🎯 Military Rank Support

The application recognizes and properly handles various military ranks:

### Army Ranks

- **Officers**: Brigadier, Colonel, Lieutenant Colonel, Major, Captain, Lieutenant, Second Lieutenant
- **Enlisted**: Subedar Major, Subedar, Naib Subedar, Havildar, Naik, Lance Naik, Sepoy

### Navy Ranks

- **Officers**: Commodore, Rear Admiral, Vice Admiral, Admiral

### Air Force Ranks

- **Officers**: Wing Commander, Squadron Leader, Flight Lieutenant

## 📁 Project Structure

```
military_resume/
├── resume.py                 # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                # Project documentation
└── resume/                  # Sample military documents (optional)
```

## 🚨 Troubleshooting

### Common Issues

**OCR Not Working**

- Ensure Tesseract is properly installed and in PATH
- Check if pytesseract and Pillow are correctly installed
- Verify document image quality (minimum 300 DPI recommended)

**Missing Military Rank Detection**

- Check if the document contains clear rank information
- Verify the rank is in the supported list
- Manual entry is always available as fallback

**AI Enhancement Errors**

- Verify Mistral API key is set correctly
- Check internet connectivity
- Fallback to manual content editing if needed

**PDF Processing Issues**

- Ensure PyMuPDF is properly installed
- Try converting PDF to image format first
- Check if PDF is password-protected or corrupted

### Performance Optimization

- Use text-based PDFs when possible (faster than OCR)
- Ensure good document scan quality for OCR
- Close other applications to free up memory for large documents

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Military Community**: For inspiring this project
- **Mistral AI**: For providing excellent AI capabilities
- **Streamlit Team**: For the amazing web framework
- **Tesseract OCR**: For optical character recognition
- **Open Source Contributors**: For the various libraries used

## 📞 Support

For support, questions, or feature requests:

- Open an issue on GitHub
- Contact the development team
- Check the troubleshooting section above

---

**Made with ❤️ for military veterans transitioning to civilian careers**
