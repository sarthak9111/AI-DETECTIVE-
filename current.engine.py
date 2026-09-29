import os
import io
import base64
import json
import time
import hashlib
import re

import requests
import numpy as np
import cv2

from PIL import Image, ExifTags

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv


# ============================================================
# AI DETECTIVE
# ============================================================

load_dotenv()

app = FastAPI(
    title="AI DETECTIVE",
    version="1.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# OPENROUTER
# ============================================================

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free"
)

SITE_URL = os.getenv(
    "SITE_URL",
    "http://localhost:8000"
)

SITE_NAME = os.getenv(
    "SITE_NAME",
    "AI DETECTIVE"
)


# ============================================================
# 61 API KEY SLOTS
#
# Actual secrets come from .env
# ============================================================

OPENROUTER_KEYS = [

    "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",
    os.getenv("OPENROUTER_KEY_02", ""),
    os.getenv("OPENROUTER_KEY_03", ""),
    os.getenv("OPENROUTER_KEY_04", ""),
    os.getenv("OPENROUTER_KEY_05", ""),
    os.getenv("OPENROUTER_KEY_06", ""),
    os.getenv("OPENROUTER_KEY_07", ""),
    os.getenv("OPENROUTER_KEY_08", ""),
    os.getenv("OPENROUTER_KEY_09", ""),
    os.getenv("OPENROUTER_KEY_10", ""),

    os.getenv("OPENROUTER_KEY_11", ""),
    os.getenv("OPENROUTER_KEY_12", ""),
    os.getenv("OPENROUTER_KEY_13", ""),
    os.getenv("OPENROUTER_KEY_14", ""),
    os.getenv("OPENROUTER_KEY_15", ""),
    os.getenv("OPENROUTER_KEY_16", ""),
    os.getenv("OPENROUTER_KEY_17", ""),
    os.getenv("OPENROUTER_KEY_18", ""),
    os.getenv("OPENROUTER_KEY_19", ""),
    os.getenv("OPENROUTER_KEY_20", ""),

    os.getenv("OPENROUTER_KEY_21", ""),
    os.getenv("OPENROUTER_KEY_22", ""),
    os.getenv("OPENROUTER_KEY_23", ""),
    os.getenv("OPENROUTER_KEY_24", ""),
    os.getenv("OPENROUTER_KEY_25", ""),
    os.getenv("OPENROUTER_KEY_26", ""),
    os.getenv("OPENROUTER_KEY_27", ""),
    os.getenv("OPENROUTER_KEY_28", ""),
    os.getenv("OPENROUTER_KEY_29", ""),
    os.getenv("OPENROUTER_KEY_30", ""),

    os.getenv("OPENROUTER_KEY_31", ""),
    os.getenv("OPENROUTER_KEY_32", ""),
    os.getenv("OPENROUTER_KEY_33", ""),
    os.getenv("OPENROUTER_KEY_34", ""),
    os.getenv("OPENROUTER_KEY_35", ""),
    os.getenv("OPENROUTER_KEY_36", ""),
    os.getenv("OPENROUTER_KEY_37", ""),
    os.getenv("OPENROUTER_KEY_38", ""),
    os.getenv("OPENROUTER_KEY_39", ""),
    os.getenv("OPENROUTER_KEY_40", ""),

    os.getenv("OPENROUTER_KEY_41", ""),
    os.getenv("OPENROUTER_KEY_42", ""),
    os.getenv("OPENROUTER_KEY_43", ""),
    os.getenv("OPENROUTER_KEY_44", ""),
    os.getenv("OPENROUTER_KEY_45", ""),
    os.getenv("OPENROUTER_KEY_46", ""),
    os.getenv("OPENROUTER_KEY_47", ""),
    os.getenv("OPENROUTER_KEY_48", ""),
    os.getenv("OPENROUTER_KEY_49", ""),
    os.getenv("OPENROUTER_KEY_50", ""),

    os.getenv("OPENROUTER_KEY_51", ""),
    os.getenv("OPENROUTER_KEY_52", ""),
    os.getenv("OPENROUTER_KEY_53", ""),
    os.getenv("OPENROUTER_KEY_54", ""),
    os.getenv("OPENROUTER_KEY_55", ""),
    os.getenv("OPENROUTER_KEY_56", ""),
    os.getenv("OPENROUTER_KEY_57", ""),
    os.getenv("OPENROUTER_KEY_58", ""),
    os.getenv("OPENROUTER_KEY_59", ""),
    os.getenv("OPENROUTER_KEY_60", ""),
    os.getenv("OPENROUTER_KEY_61", ""),
]


ACTIVE_KEYS = [
    key.strip()
    for key in OPENROUTER_KEYS
    if key and key.strip()
]


key_index = 0


# ============================================================
# KEY SELECTION
# ============================================================

def get_next_key():

    global key_index

    if not ACTIVE_KEYS:
        return None

    key = ACTIVE_KEYS[
        key_index % len(ACTIVE_KEYS)
    ]

    key_index += 1

    return key


# ============================================================
# IMAGE VALIDATION
# ============================================================

ALLOWED_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
    "BMP",
    "TIFF"
}


def load_image(data):

    try:

        image = Image.open(
            io.BytesIO(data)
        )

        image.load()

        if image.format not in ALLOWED_FORMATS:

            raise ValueError(
                f"Unsupported format: {image.format}"
            )

        return image.convert("RGB")

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=f"Invalid image: {exc}"
        )


# ============================================================
# HASH
# ============================================================

def calculate_sha256(data):

    return hashlib.sha256(
        data
    ).hexdigest()


# ============================================================
# DIMENSIONS
# ============================================================

def dimension_analysis(image):

    width, height = image.size

    pixels = width * height

    aspect_ratio = (
        width / height
        if height
        else 0
    )

    return {

        "width": width,

        "height": height,

        "pixels": pixels,

        "aspect_ratio":
            round(
                aspect_ratio,
                5
            )
    }


# ============================================================
# EXIF
# ============================================================

def extract_exif(image):

    result = {}

    try:

        exif = image.getexif()

        for tag_id, value in exif.items():

            tag = ExifTags.TAGS.get(
                tag_id,
                str(tag_id)
            )

            result[tag] = str(value)

    except Exception:

        pass

    return result


# ============================================================
# PIXEL STATISTICS
# ============================================================

def pixel_statistics(image):

    arr = np.asarray(
        image
    ).astype(
        np.float32
    )

    mean_rgb = arr.mean(
        axis=(0, 1)
    )

    std_rgb = arr.std(
        axis=(0, 1)
    )

    flat = arr.reshape(
        -1,
        3
    )

    if len(flat) > 1:

        correlation = np.corrcoef(
            flat[:, 0],
            flat[:, 1]
        )[0, 1]

    else:

        correlation = 0

    return {

        "mean_r":
            round(
                float(mean_rgb[0]),
                4
            ),

        "mean_g":
            round(
                float(mean_rgb[1]),
                4
            ),

        "mean_b":
            round(
                float(mean_rgb[2]),
                4
            ),

        "std_r":
            round(
                float(std_rgb[0]),
                4
            ),

        "std_g":
            round(
                float(std_rgb[1]),
                4
            ),

        "std_b":
            round(
                float(std_rgb[2]),
                4
            ),

        "rg_correlation":
            round(
                float(correlation),
                5
            )
    }


# ============================================================
# ENTROPY
# ============================================================

def image_entropy(image):

    gray = np.asarray(
        image.convert("L")
    )

    histogram = np.bincount(
        gray.flatten(),
        minlength=256
    ).astype(
        np.float64
    )

    probability = (
        histogram /
        histogram.sum()
    )

    probability = probability[
        probability > 0
    ]

    entropy = -np.sum(
        probability *
        np.log2(probability)
    )

    return round(
        float(entropy),
        6
    )


# ============================================================
# NOISE RESIDUAL
# ============================================================

def noise_analysis(image):

    gray = np.asarray(
        image.convert("L")
    ).astype(
        np.float32
    )

    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    residual = (
        gray -
        blurred
    )

    return {

        "noise_std":
            round(
                float(
                    np.std(residual)
                ),
                6
            ),

        "noise_mean":
            round(
                float(
                    np.mean(residual)
                ),
                6
            )
    }


# ============================================================
# NOISE AUTOCORRELATION
# ============================================================

def noise_autocorrelation(image):

    gray = np.asarray(
        image.convert("L")
    ).astype(
        np.float32
    )

    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    residual = (
        gray -
        blurred
    )

    if residual.shape[1] < 2:

        return 0.0

    a = residual[:, :-1].flatten()
    b = residual[:, 1:].flatten()

    if (
        np.std(a) == 0
        or
        np.std(b) == 0
    ):

        return 0.0

    correlation = np.corrcoef(
        a,
        b
    )[0, 1]

    return round(
        float(correlation),
        6
    )


# ============================================================
# EDGE ANALYSIS
# ============================================================

def edge_analysis(image):

    gray = np.asarray(
        image.convert("L")
    )

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    ratio = (
        np.count_nonzero(edges)
        /
        edges.size
    )

    return {

        "edge_ratio":
            round(
                float(ratio),
                7
            )
    }


# ============================================================
# LAPLACIAN
# ============================================================

def laplacian_analysis(image):

    gray = np.asarray(
        image.convert("L")
    )

    laplacian = cv2.Laplacian(
        gray,
        cv2.CV_64F
    )

    variance = float(
        laplacian.var()
    )

    return {

        "laplacian_variance":
            round(
                variance,
                6
            )
    }


# ============================================================
# FFT
# ============================================================

def fft_analysis(image):

    gray = np.asarray(
        image.convert("L")
    ).astype(
        np.float32
    )

    gray = cv2.resize(
        gray,
        (512, 512)
    )

    fft = np.fft.fft2(
        gray
    )

    shifted = np.fft.fftshift(
        fft
    )

    magnitude = np.abs(
        shifted
    )

    magnitude = np.log1p(
        magnitude
    )

    h, w = magnitude.shape

    cy = h // 2
    cx = w // 2

    y, x = np.ogrid[
        :h,
        :w
    ]

    distance = np.sqrt(
        (x - cx) ** 2
        +
        (y - cy) ** 2
    )

    radius = min(
        cx,
        cy
    )

    low_mask = (
        distance <
        radius * 0.10
    )

    high_mask = (
        distance >
        radius * 0.60
    )

    low_energy = float(
        magnitude[
            low_mask
        ].mean()
    )

    high_energy = float(
        magnitude[
            high_mask
        ].mean()
    )

    ratio = (
        high_energy /
        max(
            low_energy,
            1e-8
        )
    )

    return {

        "fft_low_energy":
            round(
                low_energy,
                6
            ),

        "fft_high_energy":
            round(
                high_energy,
                6
            ),

        "fft_high_low_ratio":
            round(
                ratio,
                6
            )
    }


# ============================================================
# JPEG
# ============================================================

def jpeg_analysis(data):

    result = {

        "format":
            None,

        "quantization_tables":
            False
    }

    try:

        image = Image.open(
            io.BytesIO(data)
        )

        result["format"] = image.format

        if image.format == "JPEG":

            result[
                "quantization_tables"
            ] = bool(
                getattr(
                    image,
                    "quantization",
                    None
                )
            )

    except Exception:

        pass

    return result


# ============================================================
# LOCAL FORENSICS
# ============================================================

def run_local_forensics(
    image,
    original_data
):

    return {

        "dimensions":
            dimension_analysis(
                image
            ),

        "pixels":
            pixel_statistics(
                image
            ),

        "entropy":
            image_entropy(
                image
            ),

        "noise":
            noise_analysis(
                image
            ),

        "noise_autocorrelation":
            noise_autocorrelation(
                image
            ),

        "edges":
            edge_analysis(
                image
            ),

        "laplacian":
            laplacian_analysis(
                image
            ),

        "fft":
            fft_analysis(
                image
            ),

        "jpeg":
            jpeg_analysis(
                original_data
            ),

        "exif":
            extract_exif(
                image
            )
    }


# ============================================================
# HEURISTIC SIGNAL
#
# SUPPORTING SIGNAL ONLY.
# NOT A TRAINED AI DETECTOR.
# ============================================================

def heuristic_signal(
    forensics
):

    score = 50.0

    reasons = []

    noise_std = (
        forensics[
            "noise"
        ][
            "noise_std"
        ]
    )

    noise_corr = (
        forensics[
            "noise_autocorrelation"
        ]
    )

    edge_ratio = (
        forensics[
            "edges"
        ][
            "edge_ratio"
        ]
    )

    laplacian = (
        forensics[
            "laplacian"
        ][
            "laplacian_variance"
        ]
    )

    fft_ratio = (
        forensics[
            "fft"
        ][
            "fft_high_low_ratio"
        ]
    )

    entropy = (
        forensics[
            "entropy"
        ]
    )


    if noise_std < 2:

        score += 5

        reasons.append(
            "Low high-frequency noise residual."
        )


    if noise_corr > 0.35:

        score += 4

        reasons.append(
            "Relatively correlated noise residual."
        )


    if edge_ratio < 0.015:

        score += 3

        reasons.append(
            "Low edge density."
        )


    if laplacian < 50:

        score += 2

        reasons.append(
            "Low Laplacian variance."
        )


    if fft_ratio < 0.05:

        score += 3

        reasons.append(
            "Weak high-frequency FFT energy."
        )


    if entropy < 5:

        score += 2

        reasons.append(
            "Relatively low image entropy."
        )


    score = max(
        0,
        min(
            100,
            score
        )
    )


    return {

        "score":
            round(
                score,
                2
            ),

        "reasons":
            reasons
    }


# ============================================================
# IMAGE -> DATA URL
# ============================================================

def image_to_data_url(
    image,
    max_side=1600
):

    img = image.copy()

    largest_side = max(
        img.size
    )

    if largest_side > max_side:

        scale = (
            max_side /
            largest_side
        )

        new_size = (

            int(
                img.width *
                scale
            ),

            int(
                img.height *
                scale
            )
        )

        img = img.resize(
            new_size,
            Image.Resampling.LANCZOS
        )


    buffer = io.BytesIO()

    img.save(
        buffer,
        format="JPEG",
        quality=90
    )

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode(
        "utf-8"
    )

    return (
        "data:image/jpeg;base64,"
        +
        encoded
    )


# ============================================================
# OPENROUTER AI
# ============================================================

def ask_openrouter(
    image,
    forensics,
    filename
):

    if not ACTIVE_KEYS:

        return {

            "available":
                False,

            "error":
                "No OpenRouter API keys configured."
        }


    image_url = image_to_data_url(
        image
    )


    forensic_json = json.dumps(
        forensics,
        indent=2,
        default=str
    )


    prompt = f"""

You are the primary visual investigation engine
inside an application called AI DETECTIVE.

Your job is to investigate an image and estimate
whether it may be:

1. A real camera photograph
2. AI-generated
3. Heavily edited/manipulated
4. Inconclusive

Do not claim certainty based only on appearance.

Use the supplied local forensic measurements
as supporting evidence.

IMAGE FILE:
{filename}

LOCAL FORENSIC DATA:

{forensic_json}


Analyze:

- anatomy
- hands
- fingers
- eyes
- teeth
- hair
- reflections
- shadows
- lighting
- perspective
- geometry
- text
- repeated patterns
- object boundaries
- texture
- background consistency
- photographic characteristics
- possible generation artifacts
- possible editing artifacts


Return EXACTLY these sections:

VERDICT:

AI PROBABILITY:

CONFIDENCE:

VISUAL EVIDENCE:

FORENSIC EVIDENCE:

METADATA EVIDENCE:

POSSIBLE GENERATION CLUES:

POSSIBLE CAMERA/REAL-IMAGE CLUES:

CONTRADICTORY EVIDENCE:

LIMITATIONS:

FINAL ASSESSMENT:


Rules:

AI PROBABILITY must be a number from 0 to 100.

Confidence must be:
Low, Medium, or High.

Missing EXIF does not prove AI generation.

Unusual noise does not prove AI generation.

A realistic image does not prove it is a photograph.

An unrealistic-looking image does not automatically prove
AI generation.

If evidence conflicts, explicitly explain the conflict.

Do not invent metadata.

Do not claim to have performed a reverse-image search
unless an actual search result was supplied.
"""


    errors = []

    attempts = min(
        len(ACTIVE_KEYS),
        61
    )


    for _ in range(attempts):

        api_key = get_next_key()

        if not api_key:
            break


        headers = {

            "Authorization":
                f"Bearer {api_key}",

            "Content-Type":
                "application/json",

            "HTTP-Referer":
                SITE_URL,

            "X-Title":
                SITE_NAME
        }


        payload = {

            "model":
                OPENROUTER_MODEL,

            "messages": [

                {

                    "role":
                        "user",

                    "content": [

                        {

                            "type":
                                "text",

                            "text":
                                prompt
                        },

                        {

                            "type":
                                "image_url",

                            "image_url": {

                                "url":
                                    image_url
                            }
                        }
                    ]
                }
            ],

            "temperature":
                0.1,

            "max_tokens":
                2500
        }


        try:

            response = requests.post(

                OPENROUTER_URL,

                headers=headers,

                json=payload,

                timeout=90
            )


            if response.ok:

                data = response.json()

                choices = data.get(
                    "choices",
                    []
                )

                if not choices:

                    errors.append(
                        "OpenRouter returned no choices."
                    )

                    continue


                message = choices[0].get(
                    "message",
                    {}
                )


                content = message.get(
                    "content",
                    ""
                )


                if isinstance(
                    content,
                    list
                ):

                    parts = []

                    for part in content:

                        if isinstance(
                            part,
                            dict
                        ):

                            text = part.get(
                                "text",
                                ""
                            )

                            if text:
                                parts.append(
                                    text
                                )

                    content = "\n".join(
                        parts
                    )


                return {

                    "available":
                        True,

                    "model":
                        data.get(
                            "model",
                            OPENROUTER_MODEL
                        ),

                    "report":
                        content
                }


            errors.append(

                f"HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )


            time.sleep(
                0.5
            )


        except Exception as exc:

            errors.append(
                str(exc)
            )


    return {

        "available":
            False,

        "error":
            "OpenRouter request failed.",

        "details":
            errors
    }


# ============================================================
# EXTRACT AI PROBABILITY
# ============================================================

def extract_probability(
    report
):

    if not report:
        return None


    patterns = [

        r"AI\s*PROBABILITY\s*:\s*(\d+(?:\.\d+)?)",

        r"AI\s*PROBABILITY\s*=\s*(\d+(?:\.\d+)?)",

        r"AI\s*PROBABILITY[^\d]*(\d+(?:\.\d+)?)\s*%"

    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            report,
            re.IGNORECASE
        )

        if match:

            try:

                value = float(
                    match.group(1)
                )

                return max(
                    0,
                    min(
                        100,
                        value
                    )
                )

            except Exception:

                pass


    return None


# ============================================================
# CROP GENERATION
# ============================================================

def generate_crops(
    image,
    crop_size=512
):

    width, height = image.size

    crops = []

    crops.append(
        image.copy()
    )


    if (
        width >= crop_size
        and
        height >= crop_size
    ):

        left = (
            width -
            crop_size
        ) // 2

        top = (
            height -
            crop_size
        ) // 2


        crops.append(

            image.crop(
                (
                    left,
                    top,
                    left + crop_size,
                    top + crop_size
                )
            )
        )


        positions = [

            (0, 0),

            (
                width -
                crop_size,
                0
            ),

            (
                0,
                height -
                crop_size
            ),

            (
                width -
                crop_size,
                height -
                crop_size
            )
        ]


        for left, top in positions:

            crops.append(

                image.crop(
                    (
                        left,
                        top,
                        left + crop_size,
                        top + crop_size
                    )
                )
            )


    return crops


# ============================================================
# MULTI-CROP AI
# ============================================================

def multi_crop_analysis(
    image,
    forensics,
    filename
):

    crops = generate_crops(
        image
    )


    # Keep this controlled.
    # One upload should not generate
    # unlimited provider requests.

    crops = crops[:3]


    results = []

    probabilities = []


    for index, crop in enumerate(
        crops
    ):

        result = ask_openrouter(

            crop,

            forensics,

            f"{filename} - crop {index + 1}"
        )


        results.append(
            result
        )


        if result.get(
            "available"
        ):

            probability = extract_probability(
                result.get(
                    "report",
                    ""
                )
            )


            if probability is not None:

                probabilities.append(
                    probability
                )


    average = None


    if probabilities:

        average = (
            sum(probabilities)
            /
            len(probabilities)
        )


    return {

        "crop_results":
            results,

        "average_ai_probability":

            (
                round(
                    average,
                    2
                )

                if average is not None

                else None
            ),

        "samples":
            len(probabilities)
    }


# ============================================================
# EVIDENCE FUSION
# ============================================================

def combine_evidence(
    heuristic,
    visual_probability
):

    if visual_probability is None:

        return {

            "ai_probability":
                heuristic["score"],

            "visual_probability":
                None,

            "heuristic_signal":
                heuristic["score"],

            "disagreement":
                None,

            "confidence":
                "Low",

            "method":
                "Local forensic heuristic only"
        }


    final = (

        visual_probability * 0.85

        +

        heuristic["score"] * 0.15
    )


    final = max(
        0,
        min(
            100,
            final
        )
    )


    disagreement = abs(

        visual_probability
        -
        heuristic["score"]
    )


    if disagreement > 35:

        confidence = "Low"

    elif disagreement > 20:

        confidence = "Medium"

    else:

        confidence = "Medium"


    return {

        "ai_probability":
            round(
                final,
                2
            ),

        "visual_probability":
            round(
                visual_probability,
                2
            ),

        "heuristic_signal":
            heuristic["score"],

        "disagreement":
            round(
                disagreement,
                2
            ),

        "confidence":
            confidence,

        "method":
            "Vision AI + local forensic evidence"
    }


# ============================================================
# ANALYZE ENDPOINT
# ============================================================

@app.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...)
):

    data = await file.read()


    if not data:

        raise HTTPException(
            status_code=400,
            detail="Empty file."
        )


    if len(data) > 20 * 1024 * 1024:

        raise HTTPException(
            status_code=413,
            detail="Maximum image size is 20 MB."
        )


    image = load_image(
        data
    )


    sha256 = calculate_sha256(
        data
    )


    # LOCAL FORENSICS

    forensics = run_local_forensics(
        image,
        data
    )


    heuristic = heuristic_signal(
        forensics
    )


    # AI INVESTIGATION

    visual = multi_crop_analysis(

        image,

        forensics,

        file.filename
        or
        "uploaded-image"
    )


    # FINAL EVIDENCE

    final = combine_evidence(

        heuristic,

        visual.get(
            "average_ai_probability"
        )
    )


    return {

        "success":
            True,

        "file": {

            "name":
                file.filename,

            "content_type":
                file.content_type,

            "size_bytes":
                len(data),

            "sha256":
                sha256
        },

        "final":
            final,

        "local_forensics":
            forensics,

        "heuristic":
            heuristic,

        "vision_analysis":
            visual
    }


# ============================================================
# STATUS
# ============================================================

@app.get("/")
def root():

    return {

        "name":
            "AI DETECTIVE",

        "status":
            "online",

        "openrouter":
            bool(ACTIVE_KEYS),

        "configured_keys":
            len(ACTIVE_KEYS),

        "model":
            OPENROUTER_MODEL
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "detector:app",

        host="0.0.0.0",

        port=8000,

        reload=True
    )