# Natural Language Import & Console

PromptBuilder features a powerful text-based import system that allows you to load entire prompt configurations—characters, outfits, poses, scenes, and notes—directly from raw text. This is designed to bridge the gap between AI-generated creative ideas and the application's structured data.

---

## 1. How it Works

The **Prompt Summary** box in the right-hand panel now acts as a **Bi-directional Console**:

1.  **Auto-Update Mode:** As you click buttons and select items in the UI, the summary box updates automatically to show your current configuration.
2.  **Manual Edit Mode:** If you click inside the summary box and start typing, the box enters "Manual Mode." Auto-updates are paused to protect your edits.
3.  **Apply / Import:** Click the **📥 Import** button in the header (or use `File > Import from Text...`) to parse the text. The application will automatically update all UI elements (dropdowns, text areas, checkboxes) to match what you typed.

---

## 2. Supported Formats

The parser is flexible and can handle two main types of text:

### Shorthand (Summary Style)
This is the format the app generates. It's great for quick tweaks or sharing small snippets.
**Format:** `[Index] Name (Outfit, [Color Scheme], Pose)`

**Example:**
```text
[1] Diego (Base, Standing)
[2] Natsumi Maki (Cyberpunk, Anime V Sign)
Scene: A neon-drenched city street at night.
Notes: They are standing near a ramen stall.
```

### Structured Block (LLM-Friendly)
A more descriptive format that gives you explicit control over every field. This is the recommended format for LLM outputs.

**Example:**
```text
### PROMPT CONFIG ###
Base: Soft semi-realistic illustration
Scene: A gritty underground fighting arena.
---
[1] Marisol Rivera
Outfit: Pro Wrestling
Colors: The Monochromes
Pose: Hero Landing
Note: Catching her breath after a match.
---
[2] Samira Mansour
Outfit: Superhero
Sig: Yes
Pose: Brave Stand
---
Notes: Samira is offering Marisol a hand up from the mat.
```

*Note: `Sig: Yes` automatically enables the **Use Signature Color** checkbox for that character.*

---

## 3. LLM Integration (Prompt Engineering)

To have an LLM (like Gemini or GPT-4) generate scenes for you, use the following "Meta-Prompt." You should provide the LLM with your `docs/data-formats.md` or a list of your available assets first.

### Sample Meta-Prompt
> You are a creative director for an image generation project. I will provide you with a list of available characters, outfits, and poses. 
>
> Your task is to generate a compelling scene using these assets and return the configuration in the following strict format:
>
> ```text
> ### PROMPT CONFIG ###
> Base: [Pick one from available base prompts]
> Scene: [A descriptive paragraph of the environment]
> ---
> [1] [Character Name]
> Outfit: [Pick from their available outfits]
> Colors: [Optional: Pick a color scheme]
> Pose: [Pick a preset pose or provide a custom description]
> Note: [Specific action or detail for this character]
> ---
> [Additional characters if needed...]
> ---
> Notes: [Interaction details or overall stylistic notes]
> ```
>
> Please ensure character names and outfit names match the provided list exactly.

---

## 4. Tips for Success

*   **Fuzzy Matching:** You don't need to type full names. If you have "Diego Morales" in your database, typing "Diego" or "Morales" will usually find him.
*   **Custom Poses:** If you type a pose that doesn't exist in the presets, the app will automatically place that text into the **"Action / Custom Pose"** field for that character.
*   **Error Handling:** If the parser fails (e.g., due to a major typo), the app will notify you via the status bar or a popup. Check the `promptbuilder_debug.log` for technical details.
