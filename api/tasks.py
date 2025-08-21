# app/tasks.py
import openai
import os
from datetime import datetime
from django.conf import settings
from utils.supabase import get_supabase_client
from pathlib import Path
from celery import shared_task
from io import BytesIO
from PIL import Image
import base64
import os
import re
import uuid
from .models import VisualPrompt, GeneratedImage
from google import genai
from google.genai import types
from supabase import create_client, Client 
import requests
import json

import subprocess
import tempfile
import requests
import shutil
from io import BytesIO
from datetime import datetime






# Init Gemini
genai_client = genai.Client(api_key="AIzaSyBGfw0hdiJBGvcz3ytZYIH0NNCT1JDe3ZM")
openai.api_key = "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"

@shared_task
def generate_audio_and_srt2(text, voice, name):
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        base_filename = f"{name}_{timestamp}"
        mp3_filename = f"{base_filename}.mp3"
        srt_filename = f"{base_filename}.srt"

        audio_dir = os.path.join(settings.MEDIA_ROOT, "audio")
        srt_dir = os.path.join(settings.MEDIA_ROOT, "srt")
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(srt_dir, exist_ok=True)

        mp3_path = os.path.join(audio_dir, mp3_filename)
        srt_path = os.path.join(srt_dir, srt_filename)

        # Generate TTS
        tts_response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        with open(mp3_path, "wb") as f:
            f.write(tts_response.content)

        # Transcribe
        with open(mp3_path, "rb") as audio_file:
            transcript_response = openai.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="srt"
            )

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcript_response)

        audio_url = settings.MEDIA_URL + f"audio/{mp3_filename}"
        srt_url = settings.MEDIA_URL + f"srt/{srt_filename}"

        return {
            "audio_url": audio_url,
            "srt_url": srt_url
        }

    except Exception as e:
        return {"error": str(e)}
    


@shared_task(bind=True)
def generate_audio_and_srt(self, text, voice, name, webhook_url):
    task_id = self.request.id
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        base_filename = f"{name}_{timestamp}"
        output_dir = os.path.join("media", "tts")
        os.makedirs(output_dir, exist_ok=True)

        mp3_path = os.path.join(output_dir, f"{base_filename}.mp3")
        srt_path = os.path.join(output_dir, f"{base_filename}.srt")
        

        # --- TTS with OpenAI ---
        tts_response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="mp3"
        )

        # Save MP3 locally
        with open(mp3_path, "wb") as f:
            f.write(tts_response.content)

        # --- Transcription with Whisper ---
        
        with open(mp3_path, "rb") as audio_file:
            transcription = openai.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="srt"
            )
    
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcription)

        # --- Upload to Supabase ---
        supabase = get_supabase_client()

        audio_storage_path = f"{base_filename}.mp3"
        srt_storage_path = f"{base_filename}.srt"

        with open(mp3_path, "rb") as f:
            supabase.storage.from_("tts-outputs").upload(audio_storage_path, f, file_options={"content-type": "audio/mpeg"})

        with open(srt_path, "rb") as f:
            supabase.storage.from_("tts-outputs").upload(srt_storage_path, f, file_options={"content-type": "text/plain"})

        # --- Build public URLs ---
        base_url = settings.SUPABASE_URL
        audio_url = f"{base_url}/storage/v1/object/public/tts-outputs/{audio_storage_path}"
        srt_url = f"{base_url}/storage/v1/object/public/tts-outputs/{srt_storage_path}"

        if webhook_url: 
    
            data = {"task_id": task_id,"audio_url": audio_url,"srt_url": srt_url}
            try:
                response = requests.post(webhook_url, json=data)
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
                print("Success! Response data:", response.json())
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")
            except requests.exceptions.RequestException as req_err:
                print(f"Request error occurred: {req_err}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        else:
            print("No URL provided. Skipping POST request.")

        return {
            "task_id": task_id,
            "audio_url": audio_url,
            "srt_url": srt_url
        }

    except Exception as e:
        return {"error": str(e)}


def parse_srt_content(content):
    pattern = re.compile(
        r"(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)\s*(?=\n\d+\s+\d{2}|\Z)",
        re.DOTALL
    )
    entries = []
    for idx, start, end, text in pattern.findall(content):
        clean_text = " ".join(line.strip() for line in text.splitlines())
        entries.append({
            "index": int(idx),
            "start": start,
            "end": end,
            "text": clean_text
        })
    return entries

def build_transcript_string(segments):
    return "\n".join(
        f"[{s['start']} --> {s['end']}] {s['text']}"
        for s in segments
    )

def ask_model_to_segment(transcript_text):
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                   "You are a helpful assistant that turns a short subtitle text into a clear, "
                   "diagrammatic image‑generation prompt. The images should use shapes with lines, "
                     "arrows and flowchart connectors on a grid background, mimicking a no‑code automation builder UI."
                    "Group related subtitle lines into 3–7 visual scenes. "
                    "Each scene should include:\n"
                    "- start timestamp\n"
                    "- end timestamp\n"
                    "- a prompt \n"
                    "Return the result as JSON — no explanation, just the list."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Subtitle: \"{transcript_text}\"\n\n"
                    "Based on the subtitle above, generate a vivid, structured image generation prompt that can be used to create a high-quality, engaging image. "
                    "The image will be featured in a faceless YouTube channel video, so avoid any human faces. "
                    "Focus on metaphor, emotion, setting, and visual storytelling that enhances the viewer's understanding of the subtitle's message. "
                    "Keep it concise and visually descriptive."
                )
            }
        ],
        temperature=0.3,
        max_tokens=1500
    )

    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```json"):
        raw = raw.removeprefix("```json").removesuffix("```").strip()
    elif raw.startswith("```"):
        raw = raw.removeprefix("```").removesuffix("```").strip()

    return json.loads(raw)


@shared_task(bind=True)
def generate_prompts_from_srt_url(self, srt_url, webhook_url):
    task_id = self.request.id
    try:
        response = requests.get(srt_url)
        response.raise_for_status()

        segments = parse_srt_content(response.text)
        transcript_text = build_transcript_string(segments)
        prompts_data = ask_model_to_segment(transcript_text)

        print(prompts_data)

        results = []
        for item in prompts_data:
            prompt_obj = VisualPrompt.objects.create(
                start=item["start"],
                end=item["end"],
                prompt=item["prompt"]
            )
            results.append({
                "task_id": task_id,
                "id": prompt_obj.id,
                "start": prompt_obj.start,
                "end": prompt_obj.end,
                "prompt": prompt_obj.prompt
            })
        
        if webhook_url: 
    
            
            try:
                response = requests.post(webhook_url, json=results)
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
                print("Success! Response data:", response.json())
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")
            except requests.exceptions.RequestException as req_err:
                print(f"Request error occurred: {req_err}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        else:
            print("No URL provided. Skipping POST request.")

       

        return results

    except Exception as e:
        return {"error": str(e)}
    

def sanitize_filename(text):
    return re.sub(r"[^\w\s-]", "", text).strip().replace(" ", "_")

@shared_task(bind=True)
def generate_image_from_prompt(self,prompt_id, webhook_url):
    task_id = self.request.id
    try:
        supabase = get_supabase_client()
        prompt_obj = VisualPrompt.objects.get(id=prompt_id)
        prompt_text = prompt_obj.prompt
        start = prompt_obj.start
        end = prompt_obj.end

        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents="Create a vertical image (portrait orientation, 1080x1920 aspect ratio) using this prompt: " + prompt_text,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
        )

        candidates = response.candidates if response and hasattr(response, 'candidates') else []

        if not candidates or not candidates[0].content or not hasattr(candidates[0].content, "parts"):
            return {"error": "No valid image content returned by the model."}

        for part in candidates[0].content.parts:
            if part.inline_data:
                image_data = part.inline_data.data
                img = Image.open(BytesIO(image_data))

                filename = sanitize_filename(f"{prompt_id}_{start}_{end}.png")

                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)

               
                supabase.storage.from_("images").upload(
                        path=filename,
                        file=buffer.read(),
                        file_options={"content-type": "image/png"}
                        )

                public_url = supabase.storage.from_("images").get_public_url(filename)

                GeneratedImage.objects.create(
                    prompt=prompt_obj,
                    image_url=public_url
                )

                if webhook_url: 
                    data = {"task_id": task_id,"image_url": public_url,"start": start,"end": end}
            
                    try:
                        response = requests.post(webhook_url, json=data)
                        response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
                        print("Success! Response data:", response.json())
                    except requests.exceptions.HTTPError as http_err:
                        print(f"HTTP error occurred: {http_err}")
                    except requests.exceptions.RequestException as req_err:
                        print(f"Request error occurred: {req_err}")
                    except Exception as e:
                       print(f"An unexpected error occurred: {e}")
                else:
                    print("No URL provided. Skipping POST request.")                

                return {"task_id": task_id,"image_url": public_url,"start": start,"end": end}

        return {"error": "No image data found."}
    except Exception as e:
        return {"error": str(e)}
    

 # seconds


def time_to_seconds(t):
    t = t.replace(",", ".")
    x = datetime.strptime(t, "%H:%M:%S.%f")
    return x.hour * 3600 + x.minute * 60 + x.second + x.microsecond / 1e6


@shared_task(bind=True)
def create_video_from_images(self, mp3_url, data_array, webhook_url):
    fade_duration = 1.0
    task_id = self.request.id
    try:
        if isinstance(data_array, str):
            try:
                data_array = json.loads(data_array)
            except Exception as e:
                return {"error": f"Invalid JSON for images array: {str(e)}"}

        supabase = get_supabase_client()

        # Setup working directory
        unique_id = str(uuid.uuid4())
        base_dir = os.path.join("media", "videos", "tmp", unique_id)
        os.makedirs(base_dir, exist_ok=True)
        audio_path = os.path.join(base_dir, "audio.mp3")
        final_video = os.path.join(base_dir, "final_output.mp4")
        temp_folder = os.path.join(base_dir, "segments")
        os.makedirs(temp_folder, exist_ok=True)

        # Step 1: Download audio
        audio_resp = requests.get(mp3_url)
        if not audio_resp.ok:
            return {"error": "Failed to download audio file."}
        with open(audio_path, "wb") as f:
            f.write(audio_resp.content)

        # Step 2: Create video segments
        segment_files = []
        for i, row in enumerate(data_array):
            start = time_to_seconds(row["start"])
            end = time_to_seconds(row["end"])
            duration = end - start + fade_duration
            image_url = row["image_url"]

            if duration <= fade_duration:
                return {"error": f"Segment {i} is too short for fade transition."}

            img_resp = requests.get(image_url, stream=True)
            if not img_resp.ok:
                return {"error": f"Failed to download image {image_url}"}
            image_path = os.path.join(temp_folder, f"image_{i}.png")
            with open(image_path, "wb") as f:
                f.write(img_resp.content)

            segment_path = os.path.join(temp_folder, f"segment_{i}.mp4")
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-t", str(duration),
                "-i", image_path,
                "-vf", "scale=1080:1920",
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                segment_path
            ]
            subprocess.run(cmd, check=True)
            if not os.path.exists(segment_path) or os.path.getsize(segment_path) == 0:
                return {"error": f"Segment {segment_path} failed to render."}
            segment_files.append((segment_path, duration))

        # Step 3: Build xfade filter
        filter_parts = [f"[{i}:v]" for i in range(len(segment_files))]
        filter_chain = ""
        for i in range(len(filter_parts) - 1):
            input1 = f"[v{i}]" if i > 0 else filter_parts[i]
            input2 = filter_parts[i + 1]
            output = f"[v{i + 1}]" if i < len(filter_parts) - 2 else "[vout]"
            offset = sum(d for _, d in segment_files[:i + 1]) - fade_duration * (i + 1)
            filter_chain += f"{input1}{input2}xfade=transition=fade:duration={fade_duration}:offset={offset:.3f}{output};"
        filter_chain = filter_chain.rstrip(";")

        input_args = sum([["-i", file] for file, _ in segment_files], [])
        fade_output = os.path.join(base_dir, "video_with_fades.mp4")

        # Step 4: Create video with fades
        cmd_fade = [
            "ffmpeg", "-y",
            *input_args,
            "-filter_complex", filter_chain,
            "-map", "[vout]",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            fade_output
        ]
        subprocess.run(cmd_fade, check=True)

        # Step 5: Merge video with audio
        cmd_merge = [
            "ffmpeg", "-y",
            "-i", fade_output,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            final_video
        ]
        subprocess.run(cmd_merge, check=True)

        # Step 6: Upload to Supabase
        with open(final_video, "rb") as f:
            filename = f"video_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.mp4"
            supabase.storage.from_("videos").upload(
                path=filename,
                file=f,
                file_options={"content-type": "video/mp4"}
            )
        public_url = supabase.storage.from_("videos").get_public_url(filename)

        # Clean up
        shutil.rmtree(base_dir)

        if webhook_url: 
            data = {"task_id": task_id,"video_url": public_url}
            
            try:
                response = requests.post(webhook_url, json=data)
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
                print("Success! Response data:", response.json())
            except requests.exceptions.HTTPError as http_err:
                   print(f"HTTP error occurred: {http_err}")
            except requests.exceptions.RequestException as req_err:
                print(f"Request error occurred: {req_err}")
            except Exception as e:
               print(f"An unexpected error occurred: {e}")
        else:
            print("No URL provided. Skipping POST request.")      

        return {"task_id": task_id,"video_url": public_url}

    except Exception as e:
        return {"error": str(e)}