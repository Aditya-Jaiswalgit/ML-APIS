from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
import time
import os
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Train Data Converter API",
    description="Convert messy train operational text to structured JSON",
    version="1.0.0"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_ID = "google/gemma-2-2b-it"


def build_chain(repo_id=REPO_ID):
    llm = HuggingFaceEndpoint(repo_id=repo_id, task="text-generation")
    model = ChatHuggingFace(llm=llm)
    parser = JsonOutputParser()

    schema_description = '''
Top-level JSON object with these keys (ALL REQUIRED):
- date: The date mentioned or current date
- branding_priorities: Branding or awareness priorities and campaigns
- cleaning_slots: Scheduled cleaning times and teams
- stabling_geometry: Train identifiers and stabling information
- fitness_certificates: Fitness and certificate validity information
- job_card_status: Status of job cards and maintenance work
- mileage: Mileage information if available

IMPORTANT: Every field above MUST be included in the output JSON, even if the value is "Not specified" or "Not mentioned".
'''

    prompt_template = PromptTemplate(
        template=(
            "Convert the following messy train operational text into valid JSON.\n"
            "Follow this schema strictly:\n{schema}\n\n"
            "Raw text:\n{raw_text}\n\n"
            "Output ONLY valid JSON with ALL required keys. If a value is missing, use 'Not specified'."
        ),
        input_variables=["raw_text"],
        partial_variables={"schema": schema_description}
    )

    return model, parser, prompt_template


def validate_json(json_str: str):
    try:
        data = json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Invalid JSON output: {e}")

    required_keys = [
        "date", "branding_priorities", "cleaning_slots",
        "stabling_geometry", "fitness_certificates",
        "job_card_status", "mileage"
    ]
    
    # Add missing keys with default "Not specified" value
    for key in required_keys:
        if key not in data:
            data[key] = "Not specified"

    return data


def convert_text_to_json(raw_text: str, repo_id=REPO_ID, max_retries=2):
    model, parser, template = build_chain(repo_id)
    format_instructions = JsonOutputParser().get_format_instructions()

    prompt = template.format(raw_text=raw_text) + "\n\n" + format_instructions

    for attempt in range(max_retries + 1):
        try:
            chain = template | model
            result = chain.invoke({"raw_text": raw_text})

            if hasattr(result, "content"):
                text_out = result.content
            else:
                text_out = str(result)

            try:
                data = parser.parse(text_out)
            except:
                data = json.loads(text_out)

            validated = validate_json(json.dumps(data))

            return validated

        except ValueError as val_err:
            print(f"Attempt {attempt+1} failed: {val_err}")
            # For ValueError (missing keys), we can still validate and add defaults
            try:
                chain = template | model
                result = chain.invoke({"raw_text": raw_text})
                if hasattr(result, "content"):
                    text_out = result.content
                else:
                    text_out = str(result)
                
                # Try to extract JSON even if incomplete
                try:
                    data = parser.parse(text_out)
                except:
                    data = json.loads(text_out)
                
                validated = validate_json(json.dumps(data))
                return validated
            except:
                if attempt == max_retries:
                    raise
                time.sleep(1)
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries:
                raise
            time.sleep(1)


@app.get("/")
async def root():
    """Root endpoint - API welcome message"""
    return {
        "message": "Train Data Converter API",
        "description": "Upload a text file to convert train operational data to JSON",
        "endpoint": "/convert"
    }


@app.post("/convert")
async def convert_file(file: UploadFile = File(...)):
    """
    Convert uploaded text file to JSON format.
    
    Args:
        file: Text file containing train operational data
        
    Returns:
        JSON response with converted data
    """
    try:
        # Check file type
        if not file.filename.endswith('.txt'):
            raise HTTPException(
                status_code=400,
                detail="Only .txt files are supported"
            )

        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')

        if not text_content.strip():
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )

        # Convert text to JSON
        result = convert_text_to_json(text_content)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "filename": file.filename
            }
        )

    except HTTPException as http_exc:
        raise http_exc
    except ValueError as val_err:
        raise HTTPException(
            status_code=400,
            detail=f"Conversion error: {str(val_err)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@app.post("/convert-text")
async def convert_text(request: dict):
    """
    Convert text directly (without file upload).
    
    Args:
        request: JSON body with 'text' field containing the raw text
        
    Returns:
        JSON response with converted data
    """
    try:
        if "text" not in request:
            raise HTTPException(
                status_code=400,
                detail="Missing 'text' field in request body"
            )

        raw_text = request["text"]

        if not raw_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text cannot be empty"
            )

        # Convert text to JSON
        result = convert_text_to_json(raw_text)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result
            }
        )

    except HTTPException as http_exc:
        raise http_exc
    except ValueError as val_err:
        raise HTTPException(
            status_code=400,
            detail=f"Conversion error: {str(val_err)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
