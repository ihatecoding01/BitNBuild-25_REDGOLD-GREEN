# Revuze - AI-Powered Amazon Review Analysis Extension 🚀

[![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-red?logo=googlechrome)](chrome://extensions/)
[![AI Powered](https://img.shields.io/badge/AI-Powered-blue?logo=openai)](https://huggingface.co/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green?logo=fastapi)](https://fastapi.tiangolo.com/)

## ✨ Unique Features

**Unlike Amazon's basic AI review stats, Revuze provides:**

- 🎯 **Purchase Confidence Score** - ML-powered algorithm to predict buying confidence (0-100%)
- 🔍 **Authenticity Analysis** - Advanced trust indicators to detect fake reviews  
- ❤️ **Love vs Hate Comparison** - Side-by-side emotional analysis breakdown
- 📊 **Smart Category Insights** - Aspect-based sentiment analysis with visual metrics
- 🎨 **Premium Visual Interface** - Professional gradient UI with animated components

## 🏗️ Architecture

### Frontend (Chrome Extension)
- **Manifest V3** extension with modern APIs
- **Async Job Polling** for real-time analysis updates
- **Chart.js Integration** for beautiful data visualization
- **Responsive Design** with gradient backgrounds and animations

### Backend (FastAPI + HuggingFace)
- **HuggingFace Transformers**: `facebook/bart-large-mnli` for zero-shot classification
- **Sentiment Models**: `cardiffnlp/twitter-roberta-base-sentiment` for emotion analysis
- **Advanced NLP Pipeline**: TF-IDF keyword extraction + aspect-based analysis
- **ML Algorithms**: Authenticity scoring using scikit-learn

## 🚀 Installation

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 2. Extension Installation
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked" and select the `review_extension` folder
4. The Revuze icon will appear in your toolbar

### 3. Usage
1. Visit any Amazon product page with reviews
2. Click the Revuze extension icon
3. Click "Analyze Reviews" to get advanced AI insights
4. View your unique analytics dashboard with:
   - Purchase confidence meter
   - Authenticity trust score  
   - Love vs hate comparison
   - Category breakdown charts

## 🎯 What Makes Us Different

| Feature | Amazon AI | Revuze AI |
|---------|-----------|-----------|
| Purchase Confidence | ❌ | ✅ ML-powered 0-100% score |
| Authenticity Detection | ❌ | ✅ Advanced trust algorithms |
| Emotional Analysis | Basic | ✅ Love vs Hate comparison |
| Visual Interface | Basic | ✅ Premium gradient design |
| Aspect Analysis | Limited | ✅ Detailed category insights |
| Real-time Processing | ❌ | ✅ Async job polling |

## 🔧 Technical Stack

**AI & ML:**
- HuggingFace Transformers (BART, RoBERTa models)
- TF-IDF vectorization for keyword extraction
- Scikit-learn for authenticity scoring
- Custom sentiment analysis pipeline

**Backend:**
- FastAPI with async job processing
- CORS middleware for extension communication
- Advanced NLP integration wrapper
- RESTful API design

**Frontend:**
- Chrome Extension Manifest V3
- Chart.js for data visualization
- Responsive CSS with animations
- Modern JavaScript async/await patterns

## 📊 Analytics Dashboard

### Purchase Confidence Meter
Advanced ML algorithm analyzes review patterns, language sentiment, and product-specific indicators to generate a confidence score for purchase decisions.

### Authenticity Score  
Trust indicators analyze review authenticity using:
- Language pattern analysis
- Reviewer behavior signals
- Sentiment distribution patterns
- Temporal review clustering

### Love vs Hate Analysis
Emotional comparison grid showing:
- Positive vs negative sentiment ratios
- Category-specific love/hate breakdowns
- Visual comparison charts
- Emotional intensity metrics

## 🎨 UI Screenshots

The extension features a beautiful gradient interface with:
- Professional card-based layout
- Animated progress meters
- Color-coded trust indicators
- Interactive comparison charts
- Mobile-responsive design

## 🤖 Advanced NLP Features

- **Zero-shot Classification**: Categorizes reviews without training data
- **Aspect-based Sentiment**: Analyzes sentiment for specific product aspects
- **Keyword Extraction**: TF-IDF-based important term identification
- **Authenticity Detection**: ML-based fake review identification
- **Confidence Scoring**: Purchase decision confidence algorithms

## 🚀 Future Enhancements

- [ ] Multi-language review support
- [ ] Historical trend analysis
- [ ] Competitor comparison insights
- [ ] Export analysis reports
- [ ] Browser-wide analytics dashboard

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for better shopping decisions through AI-powered review analysis**