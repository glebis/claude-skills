# gpt-image-2 -- brand exploration for Monaspace
# gpt-image-2 unique presets explore the brand across moods. Add --thinking medium for infographic/diagram subjects; --quality high for finals (~$0.21/img).
# DO use the exact hex codes and fonts below. DON'T add logos, real
#   brand names, or text unless the preset is text-oriented.

scripts/gpt_image_2.py --preset editorial --platform square --quality medium -y \
  "abstract brand mood board for Monaspace, geometric composition expressing the brand's character, color palette: primary #F5B8A5, accent #BC9AFA, text #FFFFFF, background #0D1117, success #B6D162, warning #F1E170, muted #B7BFC8, typography: Monaspace Argon, ui-monospace, monospace, fully rounded pill shapes" \
  monaspace-editorial.png

scripts/gpt_image_2.py --preset bauhaus --platform square --quality medium -y \
  "abstract brand mood board for Monaspace, geometric composition expressing the brand's character, color palette: primary #F5B8A5, accent #BC9AFA, text #FFFFFF, background #0D1117, success #B6D162, warning #F1E170, muted #B7BFC8, typography: Monaspace Argon, ui-monospace, monospace, fully rounded pill shapes" \
  monaspace-bauhaus.png

scripts/gpt_image_2.py --preset isometric --platform square --quality medium -y \
  "abstract brand mood board for Monaspace, geometric composition expressing the brand's character, color palette: primary #F5B8A5, accent #BC9AFA, text #FFFFFF, background #0D1117, success #B6D162, warning #F1E170, muted #B7BFC8, typography: Monaspace Argon, ui-monospace, monospace, fully rounded pill shapes" \
  monaspace-isometric.png

scripts/gpt_image_2.py --preset poster --platform square --quality medium -y \
  "abstract brand mood board for Monaspace, geometric composition expressing the brand's character, color palette: primary #F5B8A5, accent #BC9AFA, text #FFFFFF, background #0D1117, success #B6D162, warning #F1E170, muted #B7BFC8, typography: Monaspace Argon, ui-monospace, monospace, fully rounded pill shapes" \
  monaspace-poster.png

# nano-banana -- brand exploration for Monaspace
# nano-banana's edge is accurate in-image TEXT (--model pro) and style anchoring via --reference <img>. Prefer it when the brand name/wordmark must render legibly. Add --dry-run to preview the composed prompt without an API call.
# DO use the exact hex codes and fonts below. DON'T add logos, real
#   brand names, or text unless the preset is text-oriented.

scripts/nano_banana.py --preset editorial --platform square --model pro \
  "abstract brand mood board for Monaspace, geometric composition expressing the brand's character, color palette: primary #F5B8A5, accent #BC9AFA, text #FFFFFF, background #0D1117, success #B6D162, warning #F1E170, muted #B7BFC8, typography: Monaspace Argon, ui-monospace, monospace, fully rounded pill shapes" \
  monaspace-editorial.png

scripts/nano_banana.py --preset risograph --platform square --model pro \
  "abstract brand mood board for Monaspace, geometric composition expressing the brand's character, color palette: primary #F5B8A5, accent #BC9AFA, text #FFFFFF, background #0D1117, success #B6D162, warning #F1E170, muted #B7BFC8, typography: Monaspace Argon, ui-monospace, monospace, fully rounded pill shapes" \
  monaspace-risograph.png

scripts/nano_banana.py --preset brutalist --platform square --model pro \
  "abstract brand mood board for Monaspace, geometric composition expressing the brand's character, color palette: primary #F5B8A5, accent #BC9AFA, text #FFFFFF, background #0D1117, success #B6D162, warning #F1E170, muted #B7BFC8, typography: Monaspace Argon, ui-monospace, monospace, fully rounded pill shapes" \
  monaspace-brutalist.png
