"""Extracts the Gemma batch generation and 3-step surgical pipeline."""

import asyncio
import os
import re
import random
from typing import List, Callable, Dict, Any, Optional

from utils.ai_client import AIStudioClient
from utils.llm_export import (
    generate_llm_export_text, 
    generate_roster_context, 
    generate_character_gear_context,
    generate_character_appearance_context
)
from utils.text_parser import TextParser
from utils.audit_logger import AuditLogger
from logic.feedback_loop import FeedbackLoop
from core.models import PromptConfig, SelectedCharacterConfig

class GemmaPipelineRunner:
    """Handles the heavy-lifting of batch generation, randomizing, and Gemma criticism."""
    
    def __init__(self, ctx, app_state):
        self.ctx = ctx
        self.app_state = app_state
        self.stop_requested = False

    def stop(self):
        self.stop_requested = True

    def _generate_targeted_audit_catalog(self, config) -> str:
        """Generate a highly trimmed catalog containing only context for the active prompt."""
        lines = []
        
        # 1. Scene Constraints (always needed)
        lines.append("### SCENE CONSTRAINTS ###")
        randomizer = self.ctx.randomizer
        if randomizer and hasattr(randomizer, "scene_constraints"):
            for scene_tag, rules in sorted(randomizer.scene_constraints.items()):
                rule_str = []
                if "allowed" in rules:
                    rule_str.append(f"ALLOWED: {', '.join(rules['allowed'])}")
                if "blocked" in rules:
                    rule_str.append(f"BLOCKED: {', '.join(rules['blocked'])}")
                if rule_str:
                    lines.append(f"- {scene_tag}: {' | '.join(rule_str)}")
        lines.append("")
        
        # 2. Selected Characters details and their specific Outfits and Poses in the config
        lines.append("### CANDIDATE COMPONENTS ###")
        chars = config.selected_characters if hasattr(config, "selected_characters") else (config.get("selected_characters", []) if isinstance(config, dict) else [])
        for char in chars:
            name = getattr(char, "name", None) or (char.get("name", "") if isinstance(char, dict) else "")
            outfit_name = getattr(char, "outfit", None) or (char.get("outfit", "") if isinstance(char, dict) else "")
            pose_preset = getattr(char, "pose_preset", None) or (char.get("pose_preset", "") if isinstance(char, dict) else "")
            
            # Load character metadata to get outfit tags
            char_meta = self.ctx.characters_metadata.get(name)
            outfit_tags = []
            if char_meta:
                outfits = {}
                if hasattr(char_meta, "outfits"):
                    outfits = char_meta.outfits
                elif isinstance(char_meta, dict):
                    outfits = char_meta.get("outfits", {})
                
                # Find the outfit in the character outfits
                if outfits and outfit_name in outfits:
                    odata = outfits[outfit_name]
                    if isinstance(odata, dict):
                        outfit_tags = odata.get("tags", [])
                    elif hasattr(odata, "tags"):
                        outfit_tags = odata.tags
                
                # If not found, look up global outfit data
                if not outfit_tags:
                    from utils.outfit_summary import generate_outfit_data
                    global_outfits = generate_outfit_data()
                    mod = getattr(char_meta, "gender", "F")
                    if isinstance(char_meta, dict):
                        mod = char_meta.get("gender", "F")
                    if not mod:
                        mod = "F"
                    mod = mod.upper()
                    
                    if mod in global_outfits:
                        for cat, o_dict in global_outfits[mod].items():
                            if outfit_name in o_dict:
                                outfit_tags = o_dict[outfit_name].get("tags", [])
                                break
            
            tag_str = f" [tags: {', '.join(outfit_tags)}]" if outfit_tags else ""
            lines.append(f"- Character: {name}")
            lines.append(f"  Outfit: {outfit_name}{tag_str}")
            lines.append(f"  Pose: {pose_preset}")
            lines.append("")
            
        return "\n".join(lines)

    def _generate_targeted_rebuild_catalog(self, config) -> str:
        """Generate an optimized context catalog for rebuilding a rejected composition."""
        lines = []
        
        # 1. Scene constraints
        lines.append("### SCENE CONSTRAINTS ###")
        randomizer = self.ctx.randomizer
        if randomizer and hasattr(randomizer, "scene_constraints"):
            for scene_tag, rules in sorted(randomizer.scene_constraints.items()):
                rule_str = []
                if "allowed" in rules:
                    rule_str.append(f"ALLOWED: {', '.join(rules['allowed'])}")
                if "blocked" in rules:
                    rule_str.append(f"BLOCKED: {', '.join(rules['blocked'])}")
                if rule_str:
                    lines.append(f"- {scene_tag}: {' | '.join(rule_str)}")
        lines.append("")
        
        # 2. Eligible characters list (very compact names & tags)
        lines.append("### ELIGIBLE CHARACTERS ###")
        for name, data in sorted(self.ctx.characters_metadata.items()):
            sig = getattr(data, "signature_color", "None")
            tags_list = getattr(data, "tags", [])
            if isinstance(data, dict):
                sig = data.get("signature_color", "None")
                tags_list = data.get("tags", [])
            tags = ", ".join(tags_list[:3])
            lines.append(f"- {name} [{tags}]")
        lines.append("")
        
        # 3. Selected characters appearance and full gear context
        chars = config.selected_characters if hasattr(config, "selected_characters") else (config.get("selected_characters", []) if isinstance(config, dict) else [])
        selected_names = [getattr(char, "name", None) or (char.get("name", "") if isinstance(char, dict) else "") for char in chars]
        lines.append("### APPEARANCE & OUTFIT DETAIL FOR SELECTED CHARACTERS ###")
        lines.append(generate_character_appearance_context(self.ctx, selected_names))
        lines.append("")
        lines.append(generate_character_gear_context(self.ctx, selected_names))
        
        return "\n".join(lines)

    async def run_batch(
        self, 
        count: int, 
        match_outfits_prob: float, 
        prompts_only: bool,
        on_progress: Callable[[int, int, str], None],
        fixed_prompt: str = None,
        num_characters: int = None,
        include_scene: bool = True,
        include_notes: bool = True,
        candidates: int = 3,
        forced_characters: List[str] = None,
        forced_scenario: str = None,
        use_gemma: bool = False,
        use_critic: bool = False,
        pure_gemma: bool = False,
        character_pool: List[str] = None,
        format_type: str = "markdown"
    ) -> List[Dict[str, Any]]:
        # Initialize session-based audit logger
        audit_logger = AuditLogger(session_name="batch_gen")
        audit_logger.log_event(f"Starting batch generation: count={count}, match_outfits={match_outfits_prob}")
        
        prompts_with_meta = []
        gemma_client = self.ctx.gemma_client if (use_gemma or use_critic or pure_gemma) else None
        if gemma_client:
            gemma_client.audit_logger = audit_logger # Inject current session logger
            
        ruled_out = []
        critic_logs = []
        clash_blacklist = set()
        available_chars = list(self.ctx.characters_metadata.keys())
        feedback = FeedbackLoop()
        
        # Pre-generate catalog context for Gemma if needed
        catalog_context = ""
        if pure_gemma and gemma_client:
             on_progress(0, count, "Preparing knowledge catalog for Gemma...")
             catalog_context = generate_llm_export_text(self.ctx, is_audit=False)
             audit_logger.log_json("catalog_context", {"length": len(catalog_context)})
        
        if fixed_prompt:
            final_prompt = fixed_prompt
            if use_critic and gemma_client:
                on_progress(0, count, "Auditing fixed prompt...")
                
                # Try to generate a summary for the fixed prompt
                try:
                    config = TextParser.parse_import_text(fixed_prompt, available_chars)
                    audit_input = self.app_state.builder.generate_summary(config)
                except Exception:
                    audit_input = fixed_prompt

                # Build a targeted audit catalog for the fixed prompt if parsed successfully
                targeted_audit_catalog = ""
                try:
                    config = TextParser.parse_import_text(fixed_prompt, available_chars)
                    if config.get("selected_characters"):
                        # Convert to PromptConfig for helper
                        temp_config = PromptConfig(
                            base_prompt=config.get("base_prompt", "Detailed"),
                            scene=config.get("scene", ""),
                            notes=config.get("notes", "")
                        )
                        for char_raw in config.get("selected_characters", []):
                            temp_config.selected_characters.append(SelectedCharacterConfig(
                                name=char_raw.get("name"),
                                outfit=char_raw.get("outfit", "Base"),
                                pose_preset=char_raw.get("pose", "Default")
                            ))
                        targeted_audit_catalog = self._generate_targeted_audit_catalog(temp_config)
                except Exception:
                    pass

                if not targeted_audit_catalog:
                    targeted_audit_catalog = generate_llm_export_text(self.ctx, is_audit=True)

                audit_result = gemma_client.audit_prompt(audit_input, catalog_context=targeted_audit_catalog)
                if audit_result.get("recommendation") == "fix" and audit_result.get("fixed_prompt"):
                    fixed_raw = audit_result.get("fixed_prompt")
                    try:
                        new_config_raw = TextParser.parse_import_text(fixed_raw, available_chars)
                        if new_config_raw.get("selected_characters") and self.app_state:
                            final_prompt = self.app_state.builder.generate(new_config_raw)
                        else:
                            final_prompt = fixed_raw
                    except Exception:
                        final_prompt = fixed_raw
            
            if use_gemma and gemma_client:
                on_progress(0, count, "Enhancing fixed prompt with Gemma...")
                final_prompt = gemma_client.enhance_prompt(final_prompt)
                
            prompts_with_meta.append({
                "prompt": final_prompt,
                "config": {},
                "score": 100
            })
        else:
            on_progress(0, count, "Preparing generation...")

            builder = self.app_state.builder if self.app_state else None
            randomizer = self.ctx.randomizer

            if not builder or not randomizer:
                raise RuntimeError("Builder or Randomizer not initialized.")
            
            all_names = list(self.ctx.characters_metadata.keys())
            if len(self.ctx.characters) < len(all_names):
                on_progress(0, count, "Preparing character pool...")
                for name in all_names:
                    if self.stop_requested: break
                    if self.app_state: self.app_state.ensure_character_loaded(name)
            
            i = 0
            while i < count:
                if self.stop_requested: break
                
                on_progress(i, count, f"Generating candidate {i+1}/{count}...")
                
                valid_prompt = False
                attempts = 0
                audit = None
                internal_score = 0
                
                while not valid_prompt and attempts < 3:
                    attempts += 1
                    
                    if pure_gemma and gemma_client:
                        # 3-Step Surgical Pipeline
                        roster_data = None
                        gear_data = None
                        final_comp = None
                        
                        comp_num_chars = num_characters if num_characters is not None else random.choice([1, 2, 2, 3])
                        
                        # Step 1: Roster
                        for r1 in range(3):
                            if r1 == 0:
                                on_progress(i, count, f"Gemma Step 1: Selecting Roster ({comp_num_chars} char)")
                            else:
                                on_progress(i, count, f"Gemma Step 1: Retrying Roster ({comp_num_chars} char) (Attempt {r1+1})")
                            roster_ctx = generate_roster_context(self.ctx, character_pool=character_pool)
                            roster_data = gemma_client.step_1_select_roster(
                                roster_ctx, 
                                num_chars=comp_num_chars,
                                forced_chars=forced_characters,
                                forced_scenario=forced_scenario
                            )
                            if roster_data and roster_data.get("characters"):
                                selected_names_str = ", ".join(roster_data.get("characters", []))
                                on_progress(i, count, f"  -> Selected: {selected_names_str}")
                                break
                        
                        if not roster_data:
                            print("[GemmaPipeline] Step 1 failed after 3 retries.")
                            continue
                            
                        # Step 2: Gear
                        for r2 in range(3):
                            if r2 == 0:
                                on_progress(i, count, "Gemma Step 2: Choosing Outfits")
                            else:
                                on_progress(i, count, f"Gemma Step 2: Retrying Outfits (Attempt {r2+1})")
                            selected_names = roster_data["characters"]
                            gear_ctx = generate_character_gear_context(self.ctx, selected_names)
                            gear_data = gemma_client.step_2_select_gear(gear_ctx, selected_names)
                            if gear_data:
                                gear_str = ", ".join([f"{k.split()[0]}: {v}" for k, v in gear_data.items() if k != 'pose'])
                                on_progress(i, count, f"  -> Gear: {gear_str}")
                                break
                                
                        if not gear_data:
                            print("[GemmaPipeline] Step 2 failed after 3 retries.")
                            continue
                            
                        # Step 3: Finalize
                        appearance_ctx = generate_character_appearance_context(self.ctx, roster_data.get("characters", []))
                        for r3 in range(3):
                            if r3 == 0:
                                on_progress(i, count, "Gemma Step 3: Finalizing Composition")
                            else:
                                on_progress(i, count, f"Gemma Step 3: Retrying Composition (Attempt {r3+1})")
                            final_comp = gemma_client.step_3_finalize_composition(roster_data, gear_data, character_context=appearance_ctx)
                            if final_comp:
                                break
                                
                        if not final_comp:
                            print("[GemmaPipeline] Step 3 failed after 3 retries.")
                            continue
                            
                        config = self._parse_gemma_composition(final_comp)
                        valid_prompt = True
                    else:
                        on_progress(i, count, f"Randomizing candidate {i+1} (Attempt {attempts})...")
                        
                        # Loop to avoid session blacklisted combinations
                        for rand_attempt in range(10):
                            config = randomizer.randomize(
                                num_characters=num_characters,
                                include_scene=include_scene,
                                include_notes=include_notes,
                                match_outfits_prob=match_outfits_prob,
                                candidates=max(10, candidates),
                                forced_characters=forced_characters,
                                forced_scenario=forced_scenario,
                                character_pool=character_pool
                            )
                            if isinstance(config, dict):
                                try:
                                    from core.models import PromptConfig
                                    config = PromptConfig(**config)
                                except Exception:
                                    pass
                            
                            scene_val = getattr(config, "scene", None) or (config.get("scene", "") if isinstance(config, dict) else "")
                            scene_name = scene_val.get("name", str(scene_val)) if isinstance(scene_val, dict) else str(scene_val)
                            
                            has_blacklist_clash = False
                            chars_list = getattr(config, "selected_characters", None) or (config.get("selected_characters", []) if isinstance(config, dict) else [])
                            for char in chars_list:
                                outfit = getattr(char, "outfit", None) or (char.get("outfit", "") if isinstance(char, dict) else "")
                                pose = getattr(char, "pose_preset", None) or getattr(char, "pose", None) or (char.get("pose_preset", "") if isinstance(char, dict) else "")
                                if ("outfit_scene", outfit, scene_name) in clash_blacklist:
                                    print(f"[Blacklist] Skipping blacklisted outfit '{outfit}' in scene '{scene_name}'")
                                    has_blacklist_clash = True
                                    break
                                if ("pose_scene", pose, scene_name) in clash_blacklist:
                                    print(f"[Blacklist] Skipping blacklisted pose '{pose}' in scene '{scene_name}'")
                                    has_blacklist_clash = True
                                    break
                            
                            if not has_blacklist_clash:
                                break
                    
                    prompt_text = builder.generate(config, format_type=format_type)
                    
                    if use_critic and gemma_client:
                        if pure_gemma:
                            internal_score = 0
                        else:
                            if hasattr(config, "metadata"):
                                internal_score = config.metadata.get("score", 0)
                            else:
                                internal_score = config.get("metadata", {}).get("score", 0)
                                
                        if pure_gemma or internal_score >= 500:
                            if pure_gemma:
                                reason = "Gemma Creative Architect (Direct)"
                                score = 10
                            else:
                                reason = f"Auto-passed: randomizer confidence score {internal_score} >= 500"
                                score = 9
                                
                            audit = {
                                "score": score, "recommendation": "keep",
                                "reasoning": reason,
                                "fixed_prompt": ""
                            }
                            if not pure_gemma:
                                print(f"[Critic] Auto-passed candidate {i+1} (randomizer score: {internal_score})")
                            
                            critic_logs.append({
                                "candidate_idx": i, "attempt": attempts,
                                "score": score, "recommendation": "keep",
                                "reasoning": audit["reasoning"],
                                "audit_preview": "(Gemma Architect)" if pure_gemma else "(pre-filter auto-pass)"
                            })
                            valid_prompt = True
                            continue
                        
                        prompt_summary = builder.generate_summary(config)
                        audit_input = prompt_summary

                        # Low-score pre-filtering check (skip audit, go straight to rebuild)
                        if not pure_gemma and internal_score < 150:
                            reason = f"Pre-filtered: randomizer confidence score {internal_score} < 150"
                            print(f"[Critic] {reason}. Directing to rebuild...")
                            
                            critic_logs.append({
                                "candidate_idx": i, "attempt": attempts,
                                "score": 3, "recommendation": "rebuild",
                                "reasoning": reason,
                                "audit_preview": audit_input[:300] + "..."
                            })
                            
                            # Add to blacklist since it's a known clash
                            scene_val = getattr(config, "scene", None) or (config.get("scene", "") if isinstance(config, dict) else "")
                            scene_name = scene_val.get("name", str(scene_val)) if isinstance(scene_val, dict) else str(scene_val)
                            chars_list = getattr(config, "selected_characters", None) or (config.get("selected_characters", []) if isinstance(config, dict) else [])
                            for char in chars_list:
                                outfit = getattr(char, "outfit", None) or (char.get("outfit", "") if isinstance(char, dict) else "")
                                pose = getattr(char, "pose_preset", None) or getattr(char, "pose", None) or (char.get("pose_preset", "") if isinstance(char, dict) else "")
                                clash_blacklist.add(("outfit_scene", outfit, scene_name))
                                clash_blacklist.add(("pose_scene", pose, scene_name))
                            
                            on_progress(i, count, f"Rebuilding pre-filtered composition {i+1}...")
                            rebuild_catalog = self._generate_targeted_rebuild_catalog(config)
                            temp = 0.4 + (attempts - 1) * 0.2
                            
                            rebuild = gemma_client.rebuild_composition(
                                failed_summary=audit_input,
                                reasoning=reason,
                                catalog_context=rebuild_catalog,
                                temperature=temp
                            )
                            rebuilt_text = rebuild.get("rebuilt_prompt", "")
                            
                            if rebuilt_text:
                                try:
                                    new_config_raw = TextParser.parse_import_text(rebuilt_text, available_chars)
                                    if new_config_raw.get("selected_characters"):
                                        prompt_text = builder.generate(new_config_raw, format_type=format_type)
                                        config = new_config_raw
                                        changes = rebuild.get("changes_made", "").encode('ascii', errors='replace').decode('ascii')
                                        print(f"[Critic] Rebuilt successfully: {changes}")
                                        critic_logs.append({
                                            "candidate_idx": i, "attempt": attempts,
                                            "score": 6, "recommendation": "rebuilt",
                                            "reasoning": f"Rebuilt from low-score pre-filter. {rebuild.get('changes_made', '')}",
                                            "audit_preview": rebuilt_text[:300] + "..."
                                        })
                                        audit = {"score": 6, "recommendation": "rebuilt",
                                                 "reasoning": rebuild.get("changes_made", "")}
                                        valid_prompt = True
                                        continue
                                    else:
                                        print("[Critic] Rebuild produced no parseable characters, retrying...")
                                except Exception as e:
                                    print(f"[Critic] Rebuild parse error: {e}, retrying...")
                            else:
                                print("[Critic] Rebuild returned empty, retrying...")
                            continue

                        on_progress(i, count, f"Auditing candidate {i+1} (Attempt {attempts})...")
                        
                        # Build targeted audit catalog
                        targeted_audit_catalog = self._generate_targeted_audit_catalog(config)
                        
                        audit = gemma_client.audit_prompt(audit_input, catalog_context=targeted_audit_catalog)
                        rec = audit.get("recommendation", "keep")
                        
                        critic_logs.append({
                            "candidate_idx": i,
                            "attempt": attempts,
                            "score": audit.get("score"),
                            "recommendation": rec,
                            "reasoning": audit.get("reasoning"),
                            "audit_preview": audit_input[:300] + "..."
                        })
                        
                        if rec == "discard":
                            reason = audit.get('reasoning', '').encode('ascii', errors='replace').decode('ascii')
                            print(f"[Critic] Rejected prompt: {reason}")
                            ruled_out.append({"prompt": prompt_text, "reason": audit.get("reasoning")})
                            
                            tags = []
                            if "metadata" in config:
                                tags.extend(config["metadata"].get("scene_tags", []))
                            feedback.record_clash(audit.get("reasoning", ""), tags)
                            
                            if "template" in audit.get("reasoning", "").lower():
                                for char in config.get("selected_characters", []):
                                    if "template" in char.outfit.lower():
                                        feedback.flag_low_quality(f"{char.name} - {char.outfit}", "Critic flagged as low detail template")

                            # Add clashing combinations to blacklist
                            scene_val = getattr(config, "scene", None) or (config.get("scene", "") if isinstance(config, dict) else "")
                            scene_name = scene_val.get("name", str(scene_val)) if isinstance(scene_val, dict) else str(scene_val)
                            chars_list = getattr(config, "selected_characters", None) or (config.get("selected_characters", []) if isinstance(config, dict) else [])
                            for char in chars_list:
                                outfit = getattr(char, "outfit", None) or (char.get("outfit", "") if isinstance(char, dict) else "")
                                pose = getattr(char, "pose_preset", None) or getattr(char, "pose", None) or (char.get("pose_preset", "") if isinstance(char, dict) else "")
                                clash_blacklist.add(("outfit_scene", outfit, scene_name))
                                clash_blacklist.add(("pose_scene", pose, scene_name))
                                print(f"[Blacklist] Added blacklist rule: outfit '{outfit}' + scene '{scene_name}'")
                                print(f"[Blacklist] Added blacklist rule: pose '{pose}' + scene '{scene_name}'")

                            on_progress(i, count, f"Rebuilding rejected composition {i+1}...")
                            rebuild_catalog = self._generate_targeted_rebuild_catalog(config)
                            temp = 0.4 + (attempts - 1) * 0.2
                            
                            rebuild = gemma_client.rebuild_composition(
                                failed_summary=audit_input,
                                reasoning=audit.get("reasoning", ""),
                                catalog_context=rebuild_catalog,
                                temperature=temp
                            )
                            rebuilt_text = rebuild.get("rebuilt_prompt", "")
                            
                            if rebuilt_text:
                                try:
                                    new_config_raw = TextParser.parse_import_text(rebuilt_text, available_chars)
                                    if new_config_raw.get("selected_characters"):
                                        prompt_text = builder.generate(new_config_raw, format_type=format_type)
                                        config = new_config_raw
                                        changes = rebuild.get("changes_made", "").encode('ascii', errors='replace').decode('ascii')
                                        print(f"[Critic] Rebuilt successfully: {changes}")
                                        critic_logs.append({
                                             "candidate_idx": i, "attempt": attempts,
                                             "score": 6, "recommendation": "rebuilt",
                                             "reasoning": f"Rebuilt from discard. {rebuild.get('changes_made', '')}",
                                             "audit_preview": rebuilt_text[:300] + "..."
                                        })
                                        audit = {"score": 6, "recommendation": "rebuilt",
                                                  "reasoning": rebuild.get("changes_made", "")}
                                        valid_prompt = True
                                        continue
                                    else:
                                        print("[Critic] Rebuild produced no parseable characters, retrying...")
                                except Exception as e:
                                    print(f"[Critic] Rebuild parse error: {e}, retrying...")
                            else:
                                print("[Critic] Rebuild returned empty, retrying...")
                            continue
                        elif rec == "fix":
                            reason = audit.get('reasoning', '').encode('ascii', errors='replace').decode('ascii')
                            print(f"[Critic] Fixing prompt: {reason}")
                            fixed_raw = audit.get("fixed_prompt", prompt_text)
                            
                            # Add clashing combinations to blacklist
                            scene_val = getattr(config, "scene", None) or (config.get("scene", "") if isinstance(config, dict) else "")
                            scene_name = scene_val.get("name", str(scene_val)) if isinstance(scene_val, dict) else str(scene_val)
                            chars_list = getattr(config, "selected_characters", None) or (config.get("selected_characters", []) if isinstance(config, dict) else [])
                            for char in chars_list:
                                outfit = getattr(char, "outfit", None) or (char.get("outfit", "") if isinstance(char, dict) else "")
                                pose = getattr(char, "pose_preset", None) or getattr(char, "pose", None) or (char.get("pose_preset", "") if isinstance(char, dict) else "")
                                clash_blacklist.add(("outfit_scene", outfit, scene_name))
                                clash_blacklist.add(("pose_scene", pose, scene_name))
                                
                            try:
                                new_config_raw = TextParser.parse_import_text(fixed_raw, available_chars)
                                if new_config_raw.get("selected_characters"):
                                    prompt_text = builder.generate(new_config_raw, format_type=format_type)
                                    config = new_config_raw 
                                else:
                                    prompt_text = fixed_raw
                            except Exception as e:
                                print(f"[Critic] Error parsing fixed prompt: {e}")
                                prompt_text = fixed_raw
                            valid_prompt = True
                        else:
                            valid_prompt = True
                    else:
                        valid_prompt = True

                if not valid_prompt:
                    print(f"[Critic] Failed to find a valid prompt after 3 attempts for index {i}")
                
                if use_gemma and gemma_client:
                    on_progress(i, count, f"Enhancing prompt {i+1}/{count} with Gemma...")
                    prompt_text = gemma_client.enhance_prompt(prompt_text)
                    
                logged_config = config
                if hasattr(config, "dict"):
                    logged_config = config.dict()
                elif hasattr(config, "model_dump"):
                    logged_config = config.model_dump()
                    
                prompts_with_meta.append({
                    "prompt": prompt_text,
                    "format": format_type,
                    "config": logged_config,
                    "score": audit.get("score", 0) if audit else internal_score,
                    "audit": audit
                })

                if audit and audit.get("score", 0) >= 9:
                    tags = []
                    if "metadata" in logged_config:
                        tags.extend(logged_config["metadata"].get("scene_tags", []))
                    feedback.record_success(prompt_text, audit.get("score"), tags)

                i += 1
        
        if ruled_out:
            audit_logger.log_json("ruled_out_compositions", ruled_out)
            audit_logger.log_event(f"Logged {len(ruled_out)} rejected compositions to session folder")

        if critic_logs:
            audit_logger.log_json("critic_audit_full", critic_logs)
            audit_logger.log_event("Full audit analysis logged to session folder")

        if self.stop_requested or not prompts_with_meta:
            return prompts_with_meta

        if prompts_only:
            return prompts_with_meta

        def client_progress_shim(current, total, message):
            if not self.stop_requested:
                on_progress(current, total, message)

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(base_dir, "output", "images", "generated_images")
        user_data_dir = os.path.join(base_dir, ".config", "chrome_profile")
        
        client = AIStudioClient(
            output_dir=output_dir,
            user_data_dir=user_data_dir,
            headless=False
        )
        
        batch_prompts = [f"Generate an image of: {p['prompt']}" for p in prompts_with_meta]
        
        results = await client.generate_images(batch_prompts, progress_callback=client_progress_shim)
        
        final_results = []
        for j, (prompt, img_path) in enumerate(results):
            res = prompts_with_meta[j].copy()
            res["image_path"] = img_path
            final_results.append(res)
            
        return final_results

    def _parse_gemma_composition(self, data: dict) -> Any:
        available_chars = list(self.ctx.characters_metadata.keys())
        available_styles = list(self.ctx.base_prompts.keys())
        
        raw_style = data.get("art_style") or data.get("style", "")
        style_name = TextParser._fuzzy_match(raw_style, available_styles) or "Detailed"
        
        config = PromptConfig(
            base_prompt=style_name,
            scene=data.get("scene_description", ""),
            notes=data.get("action_notes", ""),
            metadata={
                "artist_influence": data.get("artist_name", ""),
                "mood": ", ".join(data.get("mood_tags", [])) if isinstance(data.get("mood_tags"), list) else str(data.get("mood_tags", ""))
            }
        )
        
        for char_data in data.get("characters", []):
            raw_name = char_data.get("name", "")
            clean_name = re.sub(r"^(Character|Name):\s*", "", raw_name, flags=re.IGNORECASE)
            clean_name = re.sub(r"\s*\(.*?\)\s*", "", clean_name).strip()
            
            name = TextParser._fuzzy_match(clean_name, available_chars)
            if name:
                if self.app_state:
                    self.app_state.ensure_character_loaded(name)
                
                raw_outfit = char_data.get("outfit", "Base")
                char_meta = self.ctx.characters_metadata.get(name)
                outfit_name = "Base"
                
                if char_meta:
                    outfits = {}
                    if hasattr(char_meta, "outfits"):
                        outfits = char_meta.outfits
                    elif isinstance(char_meta, dict):
                        outfits = char_meta.get("outfits", {})
                        
                    from utils.outfit_summary import generate_outfit_data
                    global_outfits = generate_outfit_data()
                    mod = getattr(char_meta, "gender", "F")
                    if isinstance(char_meta, dict):
                        mod = char_meta.get("gender", "F")
                    if not mod: mod = "F"
                    mod = mod.upper()
                    
                    global_for_mod = global_outfits.get(mod, {})
                    
                    def check_outfit_match(target: str) -> Optional[str]:
                        if isinstance(outfits, dict) and target in outfits:
                            return target
                        for cat, o_dict in global_for_mod.items():
                            if target in o_dict:
                                return target
                        if isinstance(outfits, dict):
                            for o_key in outfits.keys():
                                if target.lower() in o_key.lower() or o_key.lower() in target.lower():
                                    return o_key
                        for cat, o_dict in global_for_mod.items():
                            for o_key in o_dict.keys():
                                if target.lower() in o_key.lower() or o_key.lower() in target.lower():
                                    return o_key
                        return None

                    match = check_outfit_match(raw_outfit)
                    if match:
                        outfit_name = match

                char_config = SelectedCharacterConfig(
                    name=name,
                    outfit=outfit_name,
                    pose_preset=char_data.get("pose", "Default"),
                    action_note=char_data.get("action", "")
                )
                config.selected_characters.append(char_config)
            else:
                print(f"[GemmaPipeline] WARNING: Could not match character '{raw_name}' (cleaned: '{clean_name}') to catalog.")
                
        return config
