from dotenv import load_dotenv
import json
import time
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

REPO_ID = "google/gemma-2-2b-it"

def build_chain(repo_id=REPO_ID):
    llm = HuggingFaceEndpoint(repo_id=repo_id, task="text-generation")
    model = ChatHuggingFace(llm=llm)
    parser = JsonOutputParser()

    schema_description = '''
Top-level JSON object with these keys:
date, branding_priorities, cleaning_slots, stabling_geometry,
fitness_certificates, job_card_status, mileage
'''

    prompt_template = PromptTemplate(
        template=(
            "Convert the following messy train operational text into valid JSON.\n"
            "Follow this schema strictly:\n{schema}\n\n"
            "Raw text:\n{raw_text}\n\n"
            "Output ONLY JSON."
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
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing key: {key}")

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

        except Exception as e:
            print(f"Attempt {attempt+1} failed:", e)
            if attempt == max_retries:
                raise
            time.sleep(1)


raw_text = """
train KMRC-012 daily clean at 11 pm, team A, scheduled.
branding election awareness priority 1 from 1 nov to 30 nov.
KMRC-018 fitness signalling valid 27 nov, telecom 1 dec, needs check.
"""

output = convert_text_to_json(raw_text)
print(json.dumps(output, indent=2))

