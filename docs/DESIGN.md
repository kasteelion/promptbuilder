# Design System: Prompt Builder "Nebula"

**Project ID:** prompt-builder-webui

## 1. Visual Theme & Atmosphere

**Mood:** Futuristic, deeply immersive, and precision-engineered.
**Aesthetic:** "Glassmorphism meets Cyber-command." Dark, rich backgrounds with subtle translucent layers and vibrant, electric accent colors that pop against the void. The interface feels like a high-tech dashboard for a creative pilot.
**Density:** Comfortable and spacious. Data is organized in distinct "cards" floating in space.

## 2. Color Palette & Roles

- **Void Black (#0f172a):** The deep, infinite background of the application.
- **Glass Panel (#1e293b, 80% Opacity):** Used for containers, cards, and sidebars. Should have a subtle backdrop blur.
- **Electric Azure (#3b82f6):** The primary action color. Used for "Generate" buttons and active states. High energy.
- **Stardust Text (#f1f5f9):** Primary text color. crisp and legible.
- **Muted Text (#94a3b8):** Secondary labels and descriptions.
- **Success Green (#10b981):** For positive status updates.
- **Warning Amber (#f59e0b):** For alerts or cautions.

## 3. Typography Rules

**Font Family:** 'Outfit', sans-serif. (Modern, geometric, approachable).
**Headings:** Bold (700), widely spaced. Uppercase for section headers to evoke technical diagrams.
**Body:** Regular (400) or Light (300). Clean and legible.

## 4. Component Stylings

- **Primary Button (The "Ignition"):**
  - Gradient background (Electric Azure to slightly darker blue).
  - Rounded-xl corners (Generous curves).
  - Subtle glow effect on hover (`box-shadow: 0 0 15px rgba(59, 130, 246, 0.5)`).
  - Text: Uppercase, tracking-wide.
- **Input Fields:**
  - Background: Darker than the panel (#020617).
  - Border: Thin, translucent white (#ffffff10).
  - Focus: Glows with Electric Azure.
  - Shape: Fully rounded or deeply pill-shaped.
- **Cards/Containers:**
  - Backdrop-filter: blur(12px).
  - Border: 1px solid rgba(255, 255, 255, 0.05).
  - Shadow: Soft, meaningful depth (`0 4px 6px -1px rgba(0, 0, 0, 0.1)`).

## 5. Layout Principles

- **Grid System:** Strict alignment but fluid sizing.
- **Spacing:** Generous padding (at least 24px) inside cards to let content breathe.
- **Visual Hierarchy:** Critical actions (Generate) are the largest and brighest elements. History and logs recede visually.
