# Visual Identity & UI/UX Design System Reference

## 1. Overview & Aesthetic
* **Theme:** Dark Mode, Sci-Fi, Cybernetic, "Modern Matrix".
* **Vibe:** Sleek, high-tech, developer-focused, yet polished and consumer-friendly.
* **Key Metaphors:** Node-based networks, glowing energy lines, terminal/log outputs, AI processing.
* **Core Visual Treatments:** Glassmorphism (frosted glass), neon glowing elements, subtle background textures (dot grids), and high-contrast text.

## 2. Color Palette
Use these exact or approximate hex codes/variables to recreate the depth and contrast.

### Backgrounds & Surfaces
* **App Background:** `#050705` (Deepest black with a microscopic hint of green) to `#0A0E0A`.
* **Card Surface (Glassmorphism):** `rgba(255, 255, 255, 0.03)` to `rgba(255, 255, 255, 0.08)`. Requires a backdrop-blur (e.g., `blur(12px)` or `blur(16px)`).
* **Active/Accent Background Gradient:** Linear gradient from dark forest green (`#064E3B`) to vibrant neon green (`#10B981` or `#00D26A`).

### Accents (The "Neon Green" Glow)
* **Primary Neon Glow:** `#22C55E` or `#00E676`. Used for active states, progress bars, and glowing node connectors.
* **Secondary Glow (White):** `#FFFFFF` with a diffuse white shadow for neutral active connections.
* **Success/Log Icon Green:** `#4ADE80` (A slightly softer, highly legible green for small icons).

### Typography Colors
* **Text Primary:** `#FFFFFF` (Headings, primary values, active button text).
* **Text Secondary:** `#A3A3A3` or `rgba(255, 255, 255, 0.6)` (Subtitles, standard log text, inactive icons).
* **Text Tertiary:** `rgba(255, 255, 255, 0.4)` (Timestamps in logs).

## 3. Typography
* **Font Family:** Clean, modern Sans-Serif (e.g., *Inter*, *SF Pro Display*, *Geist*, or *Outfit*). 
* **Weights:**
    * Regular (400) for logs, secondary text, and small labels.
    * Medium (500) for button text and UI element titles (e.g., "AI Agent").
    * Light (300) used occasionally for large data readouts.
* **Sizing Hierarchy:**
    * Headers / Active Values: `18px` - `24px`
    * Standard UI Text: `14px` - `16px`
    * Small Data / Logs: `12px` - `13px`

## 4. UI Components & Geometry

### Cards & Panels
* **Border Radius:** Highly rounded. Use `20px` to `24px` for main panels and floating nodes.
* **Borders:** Very subtle, thin borders on glass elements to define edges: `1px solid rgba(255, 255, 255, 0.1)`. Sometimes tinted green on active elements `1px solid rgba(34, 197, 94, 0.3)`.
* **Shadows:** Extensive use of outer glows instead of drop shadows. E.g., `box-shadow: 0 0 30px rgba(34, 197, 94, 0.15)`.

### Buttons & Controls
* **Pill Buttons:** Fully rounded edges (`border-radius: 9999px`).
* **Active Button:** Green gradient background, white text, subtle inner shadow or outer glow.
* **Inactive/Tool Buttons:** Dark gray glass background, secondary text color, subtle hover state (lightening the background opacity).

### Specialized Elements
* **The "Creativity Ratio" Slider:** * Background: A fading dot-matrix pattern.
    * Track/Fill: A thin, solid white line replacing the standard thick progress bar.
    * Thumb: A glowing white/green dot.
* **Node Connectors:** Smooth bezier curves. Use CSS/SVG with stroke gradients (e.g., fading from transparent to bright green/white, back to transparent) and a drop-shadow glow filter.
* **Terminal Logs:**
    * Layout: Flexbox, row direction, aligned center.
    * Spacing: Tight vertical line-height.
    * Format: `[Timestamp (Tertiary Color)] [Green Exclamation Icon] ==> [Log Message (Secondary Color)]`.

## 5. Textures & Effects
* **Background Pattern:** A faint, dark-gray dotted grid pattern (`radial-gradient` or SVG pattern) overlaid on the absolute background. Dots should be `1px` or `2px` in size, spaced `~16px` apart, with an opacity of `0.1` to `0.2`.
* **Edge Lighting:** Use linear gradients on borders (via CSS `border-image` or pseudo-elements) to simulate a light source hitting the top-left edges of the cards.