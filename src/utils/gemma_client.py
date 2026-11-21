import json
import os
import re
import requests
from typing import Optional, List
import time
from utils.logger import logger

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class GemmaClient:
    """
    A modular client for interacting with Gemini and Gemma models via either
    the Google GenAI SDK (Gemini Flash Cloud) or a local Ollama / OpenAI-compatible instance.

    mode:
      "auto"   — tries local first, falls back to cloud on any failure; or uses cloud if API key present
      "local"  — forces local only; returns an error string if unavailable
      "cloud"  — forces Google GenAI API (Gemini Flash)
      "gemini" — alias for "cloud"
      "ollama" — alias for "local"
    """

    def __init__(
        self,
        mode: str = "auto",
        api_key: Optional[str] = None,
        audit_logger=None,
        cloud_model: Optional[str] = None,
        ollama_model: Optional[str] = None,
        ollama_base: Optional[str] = None,
    ):
        from utils.audit_logger import default_audit_logger
        self.audit_logger = audit_logger or default_audit_logger
        self.mode = mode.lower() if mode else "auto"
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.ollama_base = ollama_base or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.openai_base = "http://localhost:8000"
        
        # Modern Gemini Flash flagship defaults
        self.cloud_model = cloud_model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.cloud_model_fallbacks = ["gemini-2.0-flash", "gemini-1.5-flash"]
        self.cloud_model_fallback = "gemini-2.0-flash"
        
        self.local_provider: Optional[str] = None  # set during detection
        self.ollama_model = ollama_model or "gemma2"

        self._detect_local()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _detect_local(self) -> None:
        """Probe for a running local inference server and record the result."""
        # 1. Try Ollama
        try:
            r = requests.get(f"{self.ollama_base}/api/tags", timeout=2)
            if r.status_code == 200:
                self.local_provider = "ollama"
                models = [m["name"] for m in r.json().get("models", [])]
                self.available_ollama_models = models
                
                # Check user-configured model first
                user_model = self.ollama_model
                user_model_latest = f"{user_model}:latest" if ":" not in user_model else user_model
                
                if user_model in models:
                    self.ollama_model = user_model
                elif user_model_latest in models:
                    self.ollama_model = user_model_latest
                else:
                    for target in ["gemma3:latest", "gemma3", "gemma2:latest", "gemma2", "gemma:latest", "llama3.2:3b", "gemma4:latest"]:
                        if target in models:
                            self.ollama_model = target
                            break
                    else:
                        logger.warning(
                            f"Ollama is running but none of the preferred "
                            f"Gemma models were found. Falling back to '{self.ollama_model}'."
                        )
                logger.info(f"Found local Ollama with model: {self.ollama_model}")
                return
        except requests.exceptions.RequestException:
            pass

        # 2. Try OpenAI-compatible server on port 8000
        try:
            r = requests.get(f"{self.openai_base}/v1/models", timeout=2)
            if r.status_code == 200:
                self.local_provider = "openai"
                print("[GemmaClient] Found OpenAI-compatible API on port 8000")
                return
        except requests.exceptions.RequestException:
            pass

        # 3. No local server found
        if self.api_key:
            if self.mode == "local":
                logger.warning("Local provider requested but not found. Fallback to Cloud disabled in 'local' mode.")
            else:
                logger.info(f"No local model found. Falling back to Google Cloud ({self.cloud_model})")
        else:
            logger.warning("No local model found and no GEMINI_API_KEY set. AI features will be disabled.")

    # ------------------------------------------------------------------
    # Private dispatch helpers
    # ------------------------------------------------------------------

    # Ollama structured output schema for audit responses.
    # Using this instead of format="json" forces exact field names.
    AUDIT_JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "score":          {"type": "integer"},
            "reasoning":      {"type": "string"},
            "recommendation": {"type": "string", "enum": ["keep", "fix", "discard"]},
            "fixed_prompt":   {"type": "string"}
        },
        "required": ["score", "reasoning", "recommendation", "fixed_prompt"]
    }

    def _build_local_payload(
        self,
        prompt: str,
        system: str,
        json_mode: bool = False,
        json_schema: dict = None,
        temperature: float = None,
        timeout: int = 120,
    ) -> tuple[dict, str]:
        """Return (payload, endpoint) for the active local provider."""
        if self.local_provider == "ollama":
            payload: dict = {
                "model": self.ollama_model,
                "prompt": prompt,
                "system": system,
                "stream": False,
            }
            # Structured schema takes priority over generic json_mode
            if json_schema:
                payload["format"] = json_schema
            elif json_mode:
                payload["format"] = "json"
            
            # Options
            opts = {}
            if temperature is not None:
                opts["temperature"] = temperature
            
            # NEW: Add num_predict if specified in extra options
            # We'll pass num_predict through via a kwargs-like approach if we wanted to be generic,
            # but for now let's just use a default or infer from context.
            # Actually, let's add it to the _call_local signature.
            return payload, f"{self.ollama_base}/api/generate"
        else:  # openai-compatible
            return {
                "model": "gemma",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            }, f"{self.openai_base}/v1/chat/completions"

    def _extract_local_text(self, res_json: dict) -> str:
        if self.local_provider == "ollama":
            return res_json.get("response", "")
        return res_json.get("choices", [{}])[0].get("message", {}).get("content", "")

    def _call_local(self, prompt: str, system: str, json_mode: bool = False,
                    json_schema: dict = None, temperature: float = None, timeout: int = 120, num_predict: int = 4096) -> str:
        """Call the local provider. Raises requests.exceptions.RequestException or RuntimeError on failure."""
        candidate_models = [self.ollama_model]
        if self.local_provider == "ollama" and hasattr(self, "available_ollama_models"):
            for alt in ["gemma3:latest", "gemma2:latest", "gemma:latest", "llama3.2:3b"]:
                if alt in self.available_ollama_models and alt not in candidate_models:
                    candidate_models.append(alt)

        last_error = None
        for cur_model in candidate_models:
            if self.local_provider == "ollama":
                self.ollama_model = cur_model

            payload, endpoint = self._build_local_payload(
                prompt, system, json_mode=json_mode, json_schema=json_schema,
                temperature=temperature, timeout=timeout
            )
            
            # Inject options
            if self.local_provider == "ollama":
                if "options" not in payload:
                    payload["options"] = {}
                payload["options"]["num_predict"] = num_predict
                if temperature is not None:
                    payload["options"]["temperature"] = temperature

            try:
                response = requests.post(endpoint, json=payload, timeout=timeout)
                response.raise_for_status()
                return self._extract_local_text(response.json())
            except requests.exceptions.HTTPError as http_err:
                error_detail = ""
                try:
                    err_json = response.json()
                    error_detail = err_json.get("error", "")
                except Exception:
                    error_detail = response.text[:200]
                
                last_error = RuntimeError(f"Local inference server error ({response.status_code}): {error_detail}")
                logger.warning(f"Local model '{cur_model}' failed ({response.status_code}: {error_detail}). Trying next local model if available...")
            except Exception as e:
                last_error = e
                logger.warning(f"Local model '{cur_model}' request failed: {e}")

        raise last_error or RuntimeError("Local inference failed on all available models.")

    def _call_cloud(
        self,
        prompt: str,
        system: str,
        json_mode: bool = False,
        json_schema: Optional[dict] = None,
        temperature: float = 0.7,
    ) -> str:
        """Call the Google GenAI API (Gemini Flash). Raises on failure."""
        if genai is None or types is None:
            raise ImportError("Google GenAI SDK not installed. Please run 'pip install google-genai'.")

        api_key = self.api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Please configure your API key in Settings or set the GEMINI_API_KEY environment variable.")

        try:
            client = genai.Client(api_key=api_key)
        except Exception as err:
            raise RuntimeError(f"Failed to initialize Google GenAI Client: {err}")

        config_kwargs = {
            "system_instruction": system,
            "temperature": temperature,
        }
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"
            if json_schema:
                config_kwargs["response_schema"] = json_schema

        config = types.GenerateContentConfig(**config_kwargs)

        candidate_models = [self.cloud_model] + [
            m for m in self.cloud_model_fallbacks if m != self.cloud_model
        ]
        last_error = None
        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    config=config,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text
                elif response and hasattr(response, "candidates") and response.candidates:
                    first_cand = response.candidates[0]
                    if hasattr(first_cand, "content") and first_cand.content and first_cand.content.parts:
                        return first_cand.content.parts[0].text
                return ""
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                    logger.error(f"Gemini API key is invalid: {e}")
                    raise RuntimeError("Gemini API key is invalid or expired. Please update your API key in Settings (Gear icon) or set a valid GEMINI_API_KEY environment variable.") from e
                logger.warning(f"Cloud model ({model_name}) failed: {e}. Trying next fallback...")

        raise RuntimeError(f"Gemini cloud inference failed on all models ({', '.join(candidate_models)}). Last error: {last_error}")

    def _log_chat(self, label: str, system: str, prompt: str, response: str):
        """Save the full interaction to the audit service."""
        if self.audit_logger:
            try:
                self.audit_logger.log_chat(label, system, prompt, response)
            except Exception as e:
                logger.error(f"Failed to log chat via AuditLogger: {e}")

    def _dispatch(
        self,
        prompt: str,
        system: str,
        json_mode: bool = False,
        json_schema: dict = None,
        temperature: float = 0.7,
        label: str = "chat",
        local_timeout: int = 120,
        num_predict: int = 4096,
    ) -> str:
        """Unified entry point for local or cloud inference."""
        response = ""
        is_cloud_forced = self.mode in ("cloud", "gemini")
        is_local_forced = self.mode in ("local", "ollama")

        try:
            if is_cloud_forced:
                response = self._call_cloud(
                    prompt, system, json_mode=json_mode, json_schema=json_schema, temperature=temperature
                )
            elif is_local_forced or (self.mode == "auto" and self.local_provider):
                response = self._call_local(
                    prompt, system, json_mode, json_schema, temperature, timeout=local_timeout, num_predict=num_predict
                )
            else:
                response = self._call_cloud(
                    prompt, system, json_mode=json_mode, json_schema=json_schema, temperature=temperature
                )
        except Exception as e:
            print(f"[AIClient] Dispatch Error ({label}): {e}")
            # Fallback to cloud if auto mode encountered a local failure
            if self.mode == "auto" and self.local_provider and not is_local_forced:
                print("[AIClient] Falling back to cloud after local error...")
                response = self._call_cloud(
                    prompt, system, json_mode=json_mode, json_schema=json_schema, temperature=temperature
                )
            else:
                raise RuntimeError(f"AI inference failed: {e}")

        self._log_chat(label, system, prompt, response)
        return response

    def get_active_provider_info(self) -> dict:
        """Get summary of current AI configuration."""
        has_key = bool(self.api_key or os.environ.get("GEMINI_API_KEY"))
        if self.mode in ("cloud", "gemini"):
            active = "Gemini Flash (Cloud)"
            model = self.cloud_model
        elif self.mode in ("local", "ollama"):
            active = f"Local ({self.local_provider or 'unavailable'})"
            model = self.ollama_model
        else:
            if self.local_provider:
                active = f"Auto (Local: {self.local_provider})"
                model = self.ollama_model
            elif has_key:
                active = f"Auto (Gemini Cloud: {self.cloud_model})"
                model = self.cloud_model
            else:
                active = "None (No API Key & No Local Server)"
                model = "N/A"

        return {
            "mode": self.mode,
            "active_provider": active,
            "model": model,
            "has_gemini_key": has_key,
            "local_provider": self.local_provider,
            "ollama_model": self.ollama_model,
            "cloud_model": self.cloud_model,
        }

    def test_connection(self) -> tuple[bool, str]:
        """Test inference with a short probe prompt."""
        try:
            resp = self._dispatch("Say 'OK' and nothing else.", "You are a test probe.", temperature=0.0, label="test_probe", local_timeout=10)
            clean = resp.strip()
            return True, f"Success! Model responded: '{clean[:60]}'"
        except Exception as e:
            return False, f"Connection test failed: {e}"

    def _best_effort_kv_parse(self, text: str) -> Optional[dict]:
        """Attempt to extract structured information from plain text key-value output."""
        data = {}
        # Parse characters array
        # e.g., "characters": ["Elena Rosales"] or "characters": [Elena Rosales]
        chars_match = re.search(r'"?characters"?\s*:\s*\[([^\]]+)\]', text, re.IGNORECASE)
        if chars_match:
            raw_chars = chars_match.group(1)
            # split by comma, strip quotes and whitespace
            chars = [c.strip().replace('"', '').replace("'", "") for c in raw_chars.split(",")]
            data["characters"] = chars
        
        # Parse single string keys (style, art_style, pose, scene_description, action_notes)
        for key in ["style", "art_style", "pose", "scene_description", "action_notes", "rebuilt_prompt", "changes_made"]:
            # Match "key": "value" or key: value
            val_match = re.search(rf'"{key}"\s*:\s*"([^"]+)"', text, re.IGNORECASE)
            if not val_match:
                val_match = re.search(rf'{key}\s*:\s*([^\n]+)', text, re.IGNORECASE)
            if val_match:
                data[key] = val_match.group(1).strip().replace('"', '').replace("'", "")
        
        # If we got at least something, return it
        return data if data else None

    def _ask_json_with_retry(
        self,
        prompt: str,
        system: str,
        label: str,
        schema: dict = None,
        retries: int = 3,
        num_predict: int = 4096,
        temperature: float = 0.7
    ) -> Optional[dict]:
        """Ask Gemma for JSON and retry if parsing fails."""
        raw = ""
        for attempt in range(retries):
            try:
                raw = self._dispatch(prompt, system, json_mode=True, json_schema=schema, label=f"{label}_att{attempt+1}", num_predict=num_predict, temperature=temperature)
                
                # Robust extraction
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                clean = match.group(0) if match else raw.strip()
                
                # Strip markdown code blocks if present
                clean = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", clean.strip(), flags=re.MULTILINE)
                
                data = json.loads(clean)
                print(f"[GemmaClient] {label} attempt {attempt+1} parsed OK.")
                return data
            except (json.JSONDecodeError, RuntimeError) as e:
                print(f"[GemmaClient] {label} attempt {attempt+1} failed: {e}")
                if attempt == retries - 1:
                    try:
                        fallback_data = self._best_effort_kv_parse(raw)
                        if fallback_data:
                            print(f"[GemmaClient] {label} fallback key-value parsing succeeded.")
                            return fallback_data
                    except Exception as fallback_err:
                        print(f"[GemmaClient] Fallback parsing failed: {fallback_err}")
                    return None
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def step_1_select_roster(self, roster_context: str, num_chars: int = 1, forced_chars: List[str] = None, forced_scenario: str = None) -> Optional[dict]:
        """Step 1: Select characters and art style."""
        rules = [
            f"1. Select EXACTLY {num_chars} characters.",
            "2. Pick ONE art style.",
            "3. NO prose. NO markdown formatting in values.",
            "4. DIVERSITY IS CRITICAL: Do NOT pick the same characters repeatedly. Explore the entire catalog.",
            "5. NO EXAMPLE LEAK: Do not pick characters or styles just because they appear in the examples.",
            "6. Return JSON: {'characters': ['Name1'], 'style': 'StyleName'}"
        ]
        
        if forced_chars:
            rules.append(f"7. YOU MUST INCLUDE these characters: {', '.join(forced_chars)}")
            
        if forced_scenario:
            rules.append(f"8. Select an art style and characters that fit this SCENARIO: '{forced_scenario}'")

        system = (
            "### ROLE: CHARACTER SCOUT\n"
            "Select characters and art style from the catalog.\n"
            "### RULES:\n" + 
            "\n".join(rules)
        )
        
        # --- Feedback Loop: Few-Shot Injection ---
        from logic.feedback_loop import FeedbackLoop
        hof = FeedbackLoop().get_hall_of_fame(limit=2)
        if hof:
            system += "\n\n### EXAMPLES OF EXCELLENT SELECTIONS:\n"
            for i, example in enumerate(hof):
                system += f"Example {i+1}:\n{example}\n\n"

        prompt = f"### CATALOG:\n{roster_context}\n\nSelect {num_chars} characters and 1 style."
        if forced_scenario:
            prompt += f"\nSCENARIO: {forced_scenario}"
            
        return self._ask_json_with_retry(prompt, system, "step_1_select_roster", num_predict=256, temperature=0.85)

    def step_2_select_gear(self, gear_context: str, selected_names: List[str]) -> Optional[dict]:
        """Step 2: Select outfits for the chosen characters."""
        system = (
            "### ROLE: COSTUME DESIGNER\n"
            "For each character, pick ONE outfit from their specific catalog.\n"
            "### RULES:\n"
            "1. ONLY use outfits listed in the catalog. DO NOT invent or alter outfit names.\n"
            "2. Pick ONE pose that makes sense for the characters and outfits.\n"
            "3. Return JSON: {'Name1': 'OutfitName', 'pose': 'PoseName'}"
        )
        prompt = f"### GEAR CATALOG:\n{gear_context}\n\nSELECTED: {', '.join(selected_names)}\n\nAssign 1 outfit to each."
        return self._ask_json_with_retry(prompt, system, "step_2_select_gear", num_predict=512)

    def step_3_finalize_composition(self, roster_data: dict, gear_data: dict, character_context: str = "") -> Optional[dict]:
        """Step 3: Finalize the scene description and action into a full composition."""
        system = (
            "### ROLE: SCENE DIRECTOR\n"
            "Assembling the final image composition. Use provided characters, style, and outfits.\n"
            "### RULES:\n"
            "1. EXACT MATCH REQUIRED: Do not alter character names, outfit names, or art style. Use the exact strings from the prompt.\n"
            "2. GENDER/TRAIT FIDELITY: Use the provided CHARACTER APPEARANCE context to ensure correct pronouns (he/she/they) and traits in the action notes.\n"
            "3. Create an immersive 'scene_description' and detailed 'action_notes' based on the pose.\n"
            "4. Return the COMPLETE JSON matching the schema."
        )
        
        # --- Feedback Loop: Few-Shot Injection ---
        from logic.feedback_loop import FeedbackLoop
        hof = FeedbackLoop().get_hall_of_fame(limit=2)
        if hof:
            system += "\n\n### EXAMPLES OF EXCELLENT COMPOSITIONS (FOR FORMAT ONLY):\n"
            system += "IMPORTANT: Use these ONLY to understand the expected detail and structure. DO NOT copy the themes, characters, or action notes from these examples.\n"
            for i, example in enumerate(hof):
                system += f"Example {i+1}:\n{example}\n\n"

        prompt = ""
        if character_context:
            prompt += f"### CHARACTER APPEARANCE CONTEXT:\n{character_context}\n\n"

        prompt += (
            f"ART STYLE: {roster_data.get('style', 'Detailed')}\n"
            f"CHARACTERS: {', '.join(roster_data.get('characters', []))}\n"
            f"GEAR ASSIGNMENTS: {json.dumps(gear_data)}\n\n"
            "Assemble final composition JSON."
        )
        return self._ask_json_with_retry(prompt, system, "step_3_finalize_composition", schema=self.COMPOSITION_JSON_SCHEMA, num_predict=2048)

    def enhance_prompt(self, prompt_text: str, style: str = "cinematic") -> str:
        """
        Enhance a structured image-generation prompt with richer descriptive language
        while strictly preserving character appearance sections.

        style:
          - "cinematic": Dramatic atmospheric lighting, volumetric depth, cinematic framing.
          - "photorealistic": 35mm/85mm optical rendering, natural film grain, authentic textures.
          - "compact": Tight, focused prompt engineering without extraneous tokens.
          - "vivid": Vibrant color contrasts, expressive moods, and dynamic visual flair.
        """
        style_instructions = {
            "cinematic": (
                "Focus on cinematic framing, volumetric lighting (e.g. golden hour, chiaroscuro, rim light), "
                "depth of field, atmospheric elements (dust motes, haze, reflections), and visual storytelling."
            ),
            "photorealistic": (
                "Focus on authentic physical textures (subtle skin pores, fabric weave, surface patina), "
                "camera optics (e.g., 50mm f/1.8 lens, natural depth of field), natural exposure, and lifelike lighting."
            ),
            "compact": (
                "Streamline and condense the prompt into dense, high-impact descriptive tokens without filler words."
            ),
            "vivid": (
                "Amplify color saturation, bold lighting contrasts, dynamic gestures, and high visual energy."
            ),
        }
        chosen_style = style_instructions.get(str(style).lower(), style_instructions["cinematic"])

        system = (
            "You are an expert Prompt Engineer for modern generative AI image models (e.g., Midjourney, Flux, Stable Diffusion, Imagen).\n"
            "Your task is to take the user's structured prompt and enhance its descriptions, making them evocative, visually compelling, and coherent.\n\n"
            f"STYLE EMPHASIS:\n{chosen_style}\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. STRICTLY maintain the exact section headers and markdown structure provided.\n"
            "2. NEVER remove, summarize, or alter any physical appearance details of the characters "
            "(hair, eyes, body type, age, skin tone, etc.). You must preserve their exact Appearance sections verbatim.\n"
            "3. You may expand and add rich descriptive language to the Outfits, the Scene/Setting, "
            "and the lighting/atmosphere/action notes.\n"
            "4. Return ONLY the enhanced prompt. Do NOT include conversational commentary or markdown meta-notes."
        )
        try:
            return self._dispatch(prompt_text, system, label="enhance_prompt")
        except RuntimeError as e:
            return f"Error: {e}"

    def generate(
        self,
        prompt_text: str,
        system_instruction: str = "You are a helpful AI assistant.",
    ) -> str:
        """Generic single-turn generation for arbitrary prompts."""
        try:
            return self._dispatch(prompt_text, system_instruction, label="generate")
        except RuntimeError as e:
            return f"Error: {e}"

    def direct_scene(
        self,
        selected_characters: list,
        current_scene: str = "",
        current_notes: str = "",
        art_style: str = "Detailed",
        user_directive: str = "",
        character_details: Optional[list] = None,
    ) -> dict:
        """
        Act as a virtual Film Director and visual artist to bring a scene to life.
        Harmonizes character personalities, physical bearing, wardrobe color contrast,
        spatial blocking, and atmospheric lighting.
        """
        char_descriptions = []
        for c in selected_characters:
            name = c.get("name") if isinstance(c, dict) else getattr(c, "name", "Character")
            outfit = c.get("outfit") if isinstance(c, dict) else getattr(c, "outfit", "Default")
            pose = c.get("pose_preset") if isinstance(c, dict) else getattr(c, "pose_preset", "Default")
            color_scheme = c.get("color_scheme") if isinstance(c, dict) else getattr(c, "color_scheme", "")
            use_sig = c.get("use_signature_color") if isinstance(c, dict) else getattr(c, "use_signature_color", False)
            char_descriptions.append(f"- {name}: Wearing '{outfit}', Pose: '{pose}', Color Scheme: '{color_scheme or 'Default'}', Signature Color: {use_sig}")

        char_summary_block = "\n".join(char_descriptions) if char_descriptions else "No characters specified yet."
        extra_bio = ""
        if character_details:
            extra_bio = "\nCHARACTER BACKGROUND & TRAITS:\n" + "\n".join(character_details)

        system = (
            "You are an acclaimed Cinematographer and Creative Director for high-fidelity generative visual art.\n"
            "Your role is to act as the creative glue: taking character identities, outfits, and color palettes, "
            "and bringing the composition to life with evocative narrative action, intentional spatial blocking, "
            "and sophisticated color contrast (e.g. rich contrasts like Maroon & Khaki, complementary pops, or warm earth tones).\n\n"
            "MANDATORY JSON FORMAT:\n"
            "Return EXACTLY this JSON structure:\n"
            "{\n"
            '  "scene_description": "<atmospheric setting, time of day, lighting, environment, color mood>",\n'
            '  "action_notes": "<specific narrative interactions, gestures, eyelines, and character spatial dynamics>",\n'
            '  "color_pairing": "<analysis of wardrobe & lighting color contrast, e.g. Maroon & Khaki or Emerald & Bronze>",\n'
            '  "director_notes": "<1 sentence on the cinematic intention and mood>"\n'
            "}"
        )

        prompt = (
            f"CHARACTERS IN SCENE:\n{char_summary_block}\n"
            f"{extra_bio}\n"
            f"CURRENT SCENE SETTING: {current_scene or 'None specified'}\n"
            f"CURRENT NOTES: {current_notes or 'None specified'}\n"
            f"ART STYLE: {art_style}\n"
            f"DIRECTOR'S CREATIVE INSTRUCTION: {user_directive or 'Bring this composition to life with emotional authenticity, natural interaction, and striking color contrast.'}\n\n"
            "Direct and script this scene into JSON."
        )

        schema = {
            "type": "object",
            "properties": {
                "scene_description": {"type": "string"},
                "action_notes": {"type": "string"},
                "color_pairing": {"type": "string"},
                "director_notes": {"type": "string"},
            },
            "required": ["scene_description", "action_notes", "color_pairing", "director_notes"],
        }

        data = self._ask_json_with_retry(prompt, system, label="direct_scene", schema=schema, temperature=0.7)
        if not data:
            data = {
                "scene_description": current_scene or "A cinematic environment with atmospheric depth and natural lighting.",
                "action_notes": current_notes or "The characters interact naturally, engaged in their surroundings.",
                "color_pairing": "Harmonious wardrobe palette with balanced light contrast.",
                "director_notes": "Directed composition maintaining character authenticity.",
            }
        return data

    def generate_director_takes(self, prompt_text: str, num_takes: int = 3) -> list:
        """
        Generate 3 distinct directorial interpretations of the prompt:
        - Take 1: Cinematic / Golden Hour Intimate
        - Take 2: Dynamic Action / Dramatic High-Contrast
        - Take 3: Stylized Editorial / Avant-Garde
        """
        system = (
            "You are an elite Hollywood Director and Visual Stylist for generative AI image production.\n"
            "Given a base prompt, produce 3 distinct, compelling 'takes' (variations).\n"
            "Each take reimagines the lighting, camera angle, color contrast, and emotional moment while preserving character identities.\n\n"
            "MANDATORY JSON FORMAT:\n"
            "Return a JSON array of objects:\n"
            "[\n"
            "  {\n"
            '    "title": "Take 1: <Descriptive Title, e.g. Golden Hour Intimate>",\n'
            '    "style_notes": "<1 sentence on camera optics, lighting, and color harmony>",\n'
            '    "prompt": "<Full enhanced prompt in continuous prose ready for generation>"\n'
            "  },\n"
            "  ...\n"
            "]"
        )
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "style_notes": {"type": "string"},
                    "prompt": {"type": "string"},
                },
                "required": ["title", "style_notes", "prompt"],
            },
        }
        prompt = f"BASE PROMPT:\n{prompt_text}\n\nProduce {num_takes} diverse cinematic takes in JSON."
        raw = self._dispatch(
            prompt=prompt,
            system=system,
            json_mode=True,
            json_schema=schema,
            temperature=0.8,
            label="Director's Takes",
        )
        try:
            cleaned = self._clean_json(raw)
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "takes" in data:
                return data["takes"]
        except Exception:
            pass

        # Fallback default takes if parsing fails or offline
        return [
            {
                "title": "Take 1: Golden Hour Intimate",
                "style_notes": "Warm 35mm shallow depth of field with soft amber backlighting and earthy tones.",
                "prompt": f"{prompt_text}\n\n[Shot in intimate warm golden hour backlight with 35mm lens, shallow depth of field, and rich earthy contrast.]",
            },
            {
                "title": "Take 2: Dynamic Action High-Contrast",
                "style_notes": "Dramatic low-angle cinematic framing, bold directional key light, and vivid complementary saturation.",
                "prompt": f"{prompt_text}\n\n[Captured in dynamic low-angle wide framing with dramatic directional key light, deep shadows, and bold color contrast.]",
            },
            {
                "title": "Take 3: Editorial Stylized & Crisp",
                "style_notes": "Clean studio rim-lighting, 85mm portrait telephoto optics, sophisticated color harmony.",
                "prompt": f"{prompt_text}\n\n[Composed with clean architectural precision, 85mm telephoto portrait sharpness, subtle rim lighting, and elegant fashion color harmonies.]",
            },
        ]

    def audit_prompt(self, prompt_text: str, catalog_context: str = "") -> dict:
        """
        Audit a prompt for thematic clashes, anachronisms, and logic errors.

        Returns a dict with keys:
          score          — int 1–10
          reasoning      — str
          recommendation — "keep" | "fix" | "discard" | "error"
          fixed_prompt   — str (may be empty)
        """
        # === SYSTEM PROMPT: FORMAT RULES FIRST, CATALOG LAST ===
        # Placing output rules at the top ensures they stay in Gemma 4's
        # attention window even when the catalog context is very large.
        system = (
            # ── Section 1: OUTPUT FORMAT (must come first) ──────────────
            "### MANDATORY OUTPUT FORMAT\n"
            "You MUST respond with EXACTLY this JSON structure — no other fields, no nesting, no prose:\n"
            '{"score": <1-10>, "reasoning": "<why>", "recommendation": "<keep|fix|discard>", "fixed_prompt": "<corrected prompt or empty>"}\n\n'

            "### OUTPUT RULES:\n"
            "1. ONLY the 4 fields above. No 'critique', 'analysis', 'suggestions', 'output', etc.\n"
            "2. 'reasoning' MUST NOT be empty — briefly explain the clash or why it works.\n"
            "3. 'recommendation' MUST be exactly one of: keep, fix, discard.\n"
            "4. If recommendation is 'keep', fixed_prompt must be empty string \"\".\n"
            "5. If recommendation is 'fix', fixed_prompt MUST contain the corrected prompt in the SAME structured format as the input (emoji lines, not prose).\n\n"

            "### EXAMPLE — Score 8 (keep):\n"
            '{"score": 8, "reasoning": "Casual outfit and park scene are harmonious. No clashes detected.", "recommendation": "keep", "fixed_prompt": ""}\n\n'

            "### EXAMPLE — Score 4 (fix):\n"
            '{"score": 4, "reasoning": "Warrior armor clashes with the quiet library scene.", "recommendation": "fix", '
            '"fixed_prompt": "🎨 **Soft Vector**\\n🎬 Cozy library interior\\n👥 **Characters**:\\n   👤 **Sasha King**: Casual Streetwear [casual, urban] • Leisurely Reading\\n📝 **Action**: Sasha King browsing shelves in a sunlit library."}\n\n'

            # ── Section 2: ROLE & EVALUATION LOGIC ─────────────────────
            "### ROLE: THEMATIC AUDITOR\n"
            "You are a critical gatekeeper for thematic consistency. Detect logic errors and 'Vibe Clashes'.\n\n"
            
            "### REASONING PROTOCOL:\n"
            "Think step-by-step about Character + Outfit + Pose + Scene before scoring.\n\n"

            "### ANTI-HALLUCINATION RULES:\n"
            "1. Judge only what is WRITTEN. If the input is empty, score 1.\n"
            "2. Do NOT invent details not explicitly listed.\n\n"

            "### CLASH CHECKLIST:\n"
            "1. Object-Scene Mismatch: Does the Pose (e.g. Bed) clash with the Scene (e.g. Boat)?\n"
            "2. Temporal/Genre Clash: Mixing eras (1920s + 2070s) or genres (Fantasy + Sci-Fi)?\n"
            "3. Tone Clash: 'Cartoon' style for a 'Gritty War' scene?\n\n"

            "### SCORING RULES:\n"
            "- Score 1: Empty, nonsense, or extreme hallucinations → recommend 'discard'.\n"
            "- Score 2-4: Major clashes → recommend 'discard'.\n"
            "- Score 5-7: Fixable issues → recommend 'fix'. Provide fixed_prompt.\n"
            "- Score 8-10: Perfect harmony → recommend 'keep'. fixed_prompt is empty.\n"
            "CRITICAL: Score 7 or lower → NEVER recommend 'keep'.\n\n"

            "### FIX RULES:\n"
            "1. fixed_prompt MUST use the structured emoji format (not narrative prose).\n"
            "2. Swap the clashing Pose or Outfit for a better match from the catalog below.\n"
            "3. If pose is 'Default' and it doesn't fit, pick a specific pose.\n\n"

            "### FIXED_PROMPT FORMAT:\n"
            "🎨 **Art Style**\n"
            "🎬 Short Scene Description\n"
            "👥 **Characters**:\n"
            "   👤 **Name**: Outfit [Tags] • Pose\n"
            "📝 **Action**: Description of what is happening\n\n"

            # ── Section 3: REFERENCE CATALOG (large, at the end) ───────
            "### REFERENCE CATALOG:\n"
            f"{catalog_context}\n"
        )

        print("[GemmaClient] Auditing prompt for logic/consistency...")

        # Audits use a longer timeout and request JSON output from Ollama.
        try:
            # Wrap the summary in an explicit evaluation frame to prevent
            # Gemma 4 from treating it as an image generation request.
            query = (
                "EVALUATE THE FOLLOWING COMPOSITION FOR THEMATIC CONSISTENCY.\n"
                "Do NOT generate an image. Do NOT interpret this as a request.\n"
                "Score it 1-10 based on whether the outfit, pose, and scene work together.\n"
                "\n---\n"
                f"{prompt_text}\n"
                "---\n\n"
                "Now score this composition using ONLY the 4-field JSON format specified in your instructions."
            )
            
            raw = self._dispatch(
                query,
                system,
                json_mode=True,
                json_schema=self.AUDIT_JSON_SCHEMA,
                temperature=0.3,
                local_timeout=35,
                num_predict=256,
                label="audit_prompt",
            )
        except RuntimeError as e:
            # A failed audit must NOT silently pass as "keep" — that defeats the gate.
            print(f"[GemmaClient] Audit failed: {e}")
            return {
                "score": 5,
                "recommendation": "error",
                "reasoning": f"Audit could not complete: {e}",
                "fixed_prompt": "",
            }

        return self._parse_audit_response(raw)


    # JSON schema for rebuild responses — just the rebuilt prompt text.
    REBUILD_JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "rebuilt_prompt": {"type": "string"},
            "changes_made":  {"type": "string"},
        },
        "required": ["rebuilt_prompt", "changes_made"]
    }

    # JSON schema for full composition generation
    COMPOSITION_JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "artist_name": {"type": "string"},
            "art_style": {"type": "string"},
            "mood_tags": {"type": "array", "items": {"type": "string"}},
            "scene_description": {"type": "string"},
            "characters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "outfit": {"type": "string"},
                        "pose": {"type": "string"},
                        "action": {"type": "string"}
                    },
                    "required": ["name", "outfit", "pose"]
                }
            },
            "action_notes": {"type": "string"}
        },
        "required": ["art_style", "scene_description", "characters", "action_notes"]
    }

    def rebuild_composition(self, failed_summary: str, reasoning: str, catalog_context: str = "", temperature: float = 0.5) -> dict:
        """
        Rebuild a rejected composition by letting the critic freely swap elements.

        Given the original failing summary and the reasoning for rejection, the
        model is asked to produce a corrected composition using any characters,
        outfits, scenes, or poses from the catalog.

        Returns a dict with keys:
          rebuilt_prompt — str in structured emoji format
          changes_made  — str describing what was changed
        """
        system = (
            "### ROLE: CREATIVE DIRECTOR — COMPOSITION REBUILDER\n"
            "A composition was rejected by the thematic auditor. Your job is to\n"
            "REBUILD it into a harmonious composition by swapping any elements that clash.\n\n"

            "### WHAT YOU CAN CHANGE (any or all):\n"
            "- Characters (pick different ones from the catalog)\n"
            "- Outfits (swap to a compatible outfit from the catalog)\n"
            "- Poses (pick a pose that fits the scene and outfit)\n"
            "- Scene description (rewrite to match the new elements)\n"
            "- Art Style (change if the current style clashes)\n\n"

            "### WHAT YOU MUST KEEP:\n"
            "- The same NUMBER of characters (if 2 were in the original, keep 2)\n"
            "- A coherent, thematically unified composition\n"
            "- The structured emoji output format\n\n"

            "### RULES:\n"
            "1. Fix the SPECIFIC clash described in the rejection reasoning.\n"
            "2. Use ONLY characters, outfits, and poses from the catalog below.\n"
            "3. Do NOT invent new characters or outfits not in the catalog.\n"
            "4. The rebuilt_prompt MUST use the structured emoji format.\n"
            "5. changes_made should be a SHORT summary of what you changed.\n\n"

            "### OUTPUT FORMAT — structured emoji lines in rebuilt_prompt:\n"
            "🎨 **Art Style Name**\n"
            "🎬 Short scene description\n"
            "👥 **Characters**:\n"
            "   👤 **Character Name**: Outfit Name [tag1, tag2] • Pose Name\n"
            "📝 **Action**: What the characters are doing together\n\n"

            "### REFERENCE CATALOG:\n"
            f"{catalog_context}\n"
        )

        query = (
            "The following composition was REJECTED by the auditor.\n\n"
            f"### REJECTED COMPOSITION:\n{failed_summary}\n\n"
            f"### REJECTION REASON:\n{reasoning}\n\n"
            "Rebuild this composition into a harmonious version. "
            "Change whatever elements are needed to eliminate the clash. "
            "Return your answer as JSON with 'rebuilt_prompt' and 'changes_made' fields."
        )

        print("[GemmaClient] Rebuilding rejected composition...")

        try:
            raw = self._dispatch(
                query,
                system,
                json_mode=True,
                json_schema=self.REBUILD_JSON_SCHEMA,
                temperature=temperature,
                local_timeout=180,
                label="rebuild_composition",
            )
        except RuntimeError as e:
            print(f"[GemmaClient] Rebuild failed: {e}")
            return {"rebuilt_prompt": "", "changes_made": f"Rebuild failed: {e}"}

        # Parse the JSON response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        clean = match.group(0) if match else raw.strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            # Best-effort extraction
            rebuilt_match = re.search(r'"rebuilt_prompt"\s*:\s*"((?:[^"\\]|\\.)*)"', clean, re.DOTALL)
            changes_match = re.search(r'"changes_made"\s*:\s*"((?:[^"\\]|\\.)*)"', clean, re.DOTALL)
            data = {
                "rebuilt_prompt": rebuilt_match.group(1) if rebuilt_match else "",
                "changes_made": changes_match.group(1) if changes_match else "",
            }

        # Unescape newlines in the rebuilt prompt (model may return literal \n)
        rebuilt = data.get("rebuilt_prompt", "")
        if "\\n" in rebuilt:
            rebuilt = rebuilt.replace("\\n", "\n")
        data["rebuilt_prompt"] = rebuilt

        changes = data.get("changes_made", "").encode('ascii', errors='replace').decode('ascii')
        print(f"[GemmaClient] Rebuild complete. Changes: {changes}")
        return data

    def generate_asset(self, asset_type: str, concept: str) -> str:
        """
        Generate a new catalog asset (Outfit, Character, Scene, etc.) as a Markdown
        string that follows the strict PromptBuilder syntax rules.
        """
        from utils.llm_export import get_content_creation_prompts

        prompts_dict = get_content_creation_prompts(None)
        guide_text = prompts_dict.get(asset_type, prompts_dict.get("Full Guide", ""))

        system = (
            "You are an expert creative assistant for a photorealistic image prompt generation system. "
            "You must follow the provided syntax rules EXACTLY. Do not add conversational filler. "
            "Only output the raw text/markdown requested."
        )
        full_prompt = f"{guide_text}\n\nCONCEPT TO GENERATE: {concept}"

        print(f"[GemmaClient] Generating asset: {asset_type} ('{concept}')")

        try:
            result = self._dispatch(
                full_prompt,
                system,
                local_timeout=180,
                label="generate_asset",
            )
        except RuntimeError as e:
            return f"Error: {e}"

        # Strip fenced code blocks the model sometimes wraps output in.
        result = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", result.strip(), flags=re.MULTILINE)
        return result.strip()

    def generate_character_markdown(self, concept: str) -> str:
        """Generate a complete character markdown file based on a concept following the Tier-based schema."""
        system_prompt = """You are an expert character designer and writer for an image generation pipeline.
Translate the user's concept into a detailed, formatted character Markdown file.

YOU MUST STRICTLY FOLLOW THIS TIER-BASED MARKDOWN SCHEMA:

### Firstname Lastname

**Photo:** firstname_lastname_photo.png

**Summary:** [2-3 sentences describing personality, presence, and overall vibe.]
**Tags:** [Comma, Separated, Traits, Including Gender and Vibe]
**Gender:** [Must be exactly 'F' or 'M']
**Signature Color:** [Hex code, e.g. #50C878]

**Traits:**
- [Distinctive trait 1, e.g. small bindi dot on forehead, tiny silver nose stud, beauty mark, or subtle freckles]
- [Distinctive trait 2]

**Appearance:**
- **Body:** [Frame type, proportions, height, build]
- **Face:** [Facial structure, eyes, resting expression]
- **Hair:** [Hair texture, style, length, color, highlights]
- **Skin:** [Tone, undertones, finish]

**Age Presentation:** [e.g. late 20s presentation; driven, capable]
**Vibe / Energy:** [e.g. Focused, Disciplined, Intense]
**Bearing:** [e.g. efficient, energetic, forward-moving bearing when active]

// Style notes for outfit creation (not included in prompts):
// - Typical makeup: [notes]
// - Style preferences: [notes]
// - Jewelry preference: [notes]
// - General vibe: [notes]

---

**Outfits:**

#### Base
- **Top:** [description]
- **Bottom:** [description]
- **Footwear:** [description]
- **Accessories:** [description]
- **Hair/Makeup:** [description]

**Affinities:**
- Styles: [2-3 art styles]
- Scenes: [2-3 scene types]
- Outfit_Tags: [2-3 outfit tags]

RULES:
1. ONLY return the markdown block. No conversational preamble or postscript.
2. Keep descriptions vivid, tactile, and tailored for image generation."""

        try:
            result = self._dispatch(concept, system_prompt, label="generate_character")
            # Strip markdown code blocks if the model adds them
            result = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", result.strip(), flags=re.MULTILINE)
            return result.strip()
        except Exception as e:
            logger.error(f"[AIClient] Character generation failed: {e}")
            return f"Error: {e}"

    # ------------------------------------------------------------------
    # Internal parsing
    # ------------------------------------------------------------------

    # Known Gemma 4 field-name variants grouped by canonical name.
    _FIELD_ALIASES = {
        "reasoning":      ["reasoning", "critique", "analysis", "reason", "strategy", "feedback", "explanation"],
        "recommendation": ["recommendation", "action", "verdict", "decision"],
        "fixed_prompt":   ["fixed_prompt", "revised_prompt", "final_prompt", "edit", "corrected_prompt"],
        "score":          ["score", "rating", "quality"],
    }

    @classmethod
    def _normalise_field_names(cls, data: dict) -> dict:
        """Map any known Gemma 4 alias back to the canonical field name."""
        normalised = {}
        for canonical, aliases in cls._FIELD_ALIASES.items():
            for alias in aliases:
                if alias in data and canonical not in normalised:
                    normalised[canonical] = data[alias]
        # Preserve any other keys (like 'output') for downstream unwrapping
        for k, v in data.items():
            if k not in normalised and k not in {a for als in cls._FIELD_ALIASES.values() for a in als}:
                normalised[k] = v
        return normalised

    @classmethod
    def _parse_audit_response(cls, raw: str) -> dict:
        """Extract and normalise the JSON blob returned by the auditor model."""
        # Grab the outermost {...} block
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        clean = match.group(0) if match else raw.strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            # Best-effort field extraction when JSON is malformed
            data = {}
            all_aliases = []
            for canonical, aliases in cls._FIELD_ALIASES.items():
                for alias in aliases:
                    if canonical == "score":
                        all_aliases.append((canonical, rf'"{alias}":\s*([\d.]+)'))
                    else:
                        all_aliases.append((canonical, rf'"{alias}":\s*"([^"]+)"'))
            for key, pattern in all_aliases:
                m = re.search(pattern, clean)
                if m and not data.get(key):
                    data[key] = m.group(1)

        # --- Alias normalisation (handles 'critique' → 'reasoning', etc.) ---
        data = cls._normalise_field_names(data)

        # --- Unwrap nested 'output' field (Gemma 4 quirk) ---
        if "output" in data and isinstance(data["output"], str) and "{" in data["output"]:
            try:
                inner = json.loads(data["output"])
                inner = cls._normalise_field_names(inner)
                for k in ["score", "reasoning", "recommendation", "fixed_prompt"]:
                    if k in inner and not data.get(k):
                        data[k] = inner[k]
            except Exception:
                pass

        # --- Score normalisation ---
        raw_score = data.get("score")
        try:
            score = float(raw_score) if raw_score is not None else None
            if score is None:
                score = 5.0
            elif 0 < score < 1:          # model returned 0–1 fraction (e.g. 0.85)
                score = score * 10
            elif score > 10:              # model returned 0–100 (e.g. 85)
                score = score / 10
            data["score"] = round(min(10.0, max(1.0, score)), 1)
        except (TypeError, ValueError):
            data["score"] = 5.0

        # --- Recommendation normalisation ---
        rec = str(data.get("recommendation", "keep")).lower()
        
        # --- Score-based Override ---
        final_score = data["score"]
        if final_score <= 4.0:
            rec = "discard"
        elif final_score <= 7.0 and "fix" not in rec and "discard" not in rec:
            rec = "fix"

        if "discard" in rec or "reject" in rec:
            data["recommendation"] = "discard"
        elif "fix" in rec:
            data["recommendation"] = "fix"
        else:
            data["recommendation"] = "keep"

        data.setdefault("reasoning", "")
        data.setdefault("fixed_prompt", "")

        print(f"[GemmaClient] Audit result: {data['recommendation']} (score: {data['score']})")
        return data


# Backward-compatible and modern aliases
AIClient = GemmaClient
