# Green Cloud Guardian - FinOps Cost Leak Detection

A machine learning-powered platform for detecting cloud cost anomalies and optimizing cloud infrastructure sustainability. This project combines advanced anomaly detection with a full-stack web application to help organizations identify and eliminate cloud cost leaks.

## 🌱 Project Overview

**Green Cloud Guardian** analyzes cloud resource utilization data to:
- Detect cost anomalies using Isolation Forest algorithm
- Identify sustainability optimization opportunities
- Provide actionable insights for FinOps teams
- Visualize cost trends and anomalies in real-time

## 📦 Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **ML/Data**: scikit-learn, pandas, numpy
- **Serialization**: joblib
- **Authentication**: python-jose, passlib
- **API Server**: uvicorn

### Frontend
- **Framework**: React
- **Build Tool**: Vite
- **Package Manager**: npm

### DevOps
- **Containerization**: Docker
- **Runtime**: Python 3.x

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker (optional, for containerization)

### Backend Setup

1. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Unix/macOS
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the main pipeline:
```bash
python main.py --data-dir data --output-file outputs/final_output.csv
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend/green-cloud-guardian
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

## 📋 Project Structure

```
.
├── api.py                          # FastAPI application endpoints
├── data_loader.py                  # Data loading and preprocessing
├── evaluate.py                     # Model evaluation metrics
├── feature_engineering.py          # Feature extraction and decision logic
├── main.py                         # Main pipeline orchestration
├── model.py                        # Model training and artifact management
├── real.csv                        # Sample dataset
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
├── tests/                          # Unit tests
│   ├── test_evaluate.py
│   ├── test_feature_engineering.py
│   └── test_model.py
└── frontend/
    └── green-cloud-guardian/       # React frontend application
        └── package.json
```

## 🔧 Configuration

The main pipeline accepts the following arguments:

| Argument | Default | Description |
|----------|---------|-------------|
| `--data-dir` | `data` | Path to input data directory |
| `--output-file` | `outputs/final_output.csv` | Path to output CSV file |
| `--nrows` | `None` | Optional row limit for testing |
| `--merge-tolerance` | `5` | Timestamp gap tolerance (seconds) |
| `--random-state` | `42` | Random seed for reproducibility |
| `--model-file` | `model.pkl` | Saved model artifact path |
| `--scaler-file` | `scaler.pkl` | Saved scaler artifact path |
| `--contamination` | `0.1` | Anomaly ratio for Isolation Forest |
| `--test-size` | `0.3` | Holdout ratio for evaluation |

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Run specific tests:
```bash
pytest tests/test_model.py
pytest tests/test_evaluate.py
pytest tests/test_feature_engineering.py
```

## 🐳 Docker Deployment

Build the Docker image:
```bash
docker build -t green-cloud-guardian .
```

Run the container:
```bash
docker run -p 8000:8000 green-cloud-guardian
```

## 📊 Pipeline Workflow

1. **Data Loading** (`data_loader.py`): Loads and merges cloud resource data
2. **Feature Engineering** (`feature_engineering.py`): Extracts features and applies decision logic
3. **Model Training** (`model.py`): Trains Isolation Forest model for anomaly detection
4. **Evaluation** (`evaluate.py`): Computes performance metrics and formats results
5. **API Serving** (`api.py`): Exposes endpoints for predictions and analytics
6. **Visualization** (`frontend/`): Interactive dashboard for insights

## 🔒 Security Features

- JWT-based authentication (python-jose)
- Password hashing (bcrypt)
- Input validation and sanitization
- Secure API endpoints

## 🤝 Contributing

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit changes (`git commit -m 'Add amazing feature'`)
3. Push to branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

## 📝 License

This project is licensed under the ISC License.

## 📧 Support

For issues, questions, or contributions, please contact the development team or open an issue in the repository.

---

**Made with ♻️ for sustainable cloud infrastructure**
