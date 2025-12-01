# Train Data Converter API

A FastAPI-based service that converts messy train operational text into structured JSON format.

## Features

- **File Upload**: Upload .txt files with train operational data
- **Direct Text Input**: Send text directly via API
- **Structured JSON Output**: Converts data to a standardized JSON schema
- **Web Frontend**: Interactive HTML interface for easy testing
- **CORS Support**: Works with frontend applications

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
   Create a `.env` file with your Hugging Face API token:
```
HUGGINGFACEHUB_API_TOKEN=your_token_here
```

Get your token from: https://huggingface.co/settings/tokens

## Running the API

```bash
python app.py
```

The API will start at `http://localhost:8000`

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

## API Endpoints

### 1. File Upload
**POST** `/convert`

Upload a .txt file to convert:
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@your_file.txt"
```

**Response:**
```json
{
  "success": true,
  "filename": "your_file.txt",
  "data": {
    "date": "...",
    "branding_priorities": "...",
    "cleaning_slots": "...",
    "stabling_geometry": "...",
    "fitness_certificates": "...",
    "job_card_status": "...",
    "mileage": "..."
  }
}
```

### 2. Direct Text Input
**POST** `/convert-text`

Send text directly via JSON:
```bash
curl -X POST "http://localhost:8000/convert-text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "train KMRC-012 daily clean at 11 pm, team A, scheduled..."
  }'
```

### 3. Health Check
**GET** `/`

Check if the API is running:
```bash
curl http://localhost:8000/
```

## Using the Web Frontend

1. **Open the HTML file in a browser:**
   - Simply open `frontend.html` in your web browser

2. **Features:**
   - Two tabs: "Upload File" and "Paste Text"
   - Real-time conversion
   - Beautiful JSON output display
   - Copy to clipboard functionality

## JSON Output Schema

The API converts messy text into JSON with these required fields:

```json
{
  "date": "string",
  "branding_priorities": "string",
  "cleaning_slots": "string",
  "stabling_geometry": "string",
  "fitness_certificates": "string",
  "job_card_status": "string",
  "mileage": "string"
}
```

## Error Handling

The API returns appropriate HTTP status codes:
- **200**: Successful conversion
- **400**: Bad request (empty file, wrong format, missing text)
- **500**: Server error

Error responses include a `detail` field explaining the issue.

## File Structure

```
.
├── app.py                 # FastAPI application
├── converter.py           # Original conversion script
├── frontend.html          # Web interface
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── RaliwayData.txt        # Sample data file
└── README.md             # This file
```

## Development

To install additional development dependencies:
```bash
pip install pytest pytest-asyncio httpx
```

To run with auto-reload:
```bash
uvicorn app:app --reload
```

## Troubleshooting

1. **"Module not found" errors**
   - Ensure you've installed all requirements: `pip install -r requirements.txt`

2. **API key errors**
   - Check that your `.env` file exists and contains `HUGGINGFACEHUB_API_TOKEN`

3. **CORS errors in frontend**
   - The API is configured to allow all origins. If issues persist, check browser console for details.

4. **Connection refused (localhost:8000)**
   - Make sure the API is running: `python app.py`
   - Check that port 8000 is not in use

## API Response Examples

### Success Response (File Upload)
```json
{
  "success": true,
  "filename": "RaliwayData.txt",
  "data": {
    "date": "December 1, 2025",
    "branding_priorities": "Election awareness priority 1 from 1 nov to 30 nov",
    "cleaning_slots": "Daily clean at 11 pm, team A",
    "stabling_geometry": "KMRC-012, KMRC-018",
    "fitness_certificates": "Valid 27 nov, telecom 1 dec",
    "job_card_status": "Scheduled, needs check",
    "mileage": "Not specified"
  }
}
```

### Error Response
```json
{
  "detail": "Only .txt files are supported"
}
```

## Technologies Used

- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **LangChain**: LLM orchestration
- **Hugging Face**: Model hosting and API
- **Google Gemma 2**: LLM model for text conversion

## License

This project is part of the SIH Innov8ors initiative.
