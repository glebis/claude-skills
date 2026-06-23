# gpt-image-2 -- brand exploration for Halcyon
# gpt-image-2 unique presets explore the brand across moods. Add --thinking medium for infographic/diagram subjects; --quality high for finals (~$0.21/img).
# DO use the exact hex codes and fonts below. DON'T add logos, real
#   brand names, or text unless the preset is text-oriented.

scripts/gpt_image_2.py --preset editorial --platform square --quality medium -y \
  "abstract brand mood board for Halcyon, geometric composition expressing the brand's character, color palette: primary #0E7C7B, accent #F2714E, text #13201F, background #FBF7F0, success #3E8E5A, warning #D99A2B, danger #C24330, typography: Inter, Fraunces, rounded corners" \
  halcyon-editorial.png

scripts/gpt_image_2.py --preset bauhaus --platform square --quality medium -y \
  "abstract brand mood board for Halcyon, geometric composition expressing the brand's character, color palette: primary #0E7C7B, accent #F2714E, text #13201F, background #FBF7F0, success #3E8E5A, warning #D99A2B, danger #C24330, typography: Inter, Fraunces, rounded corners" \
  halcyon-bauhaus.png

scripts/gpt_image_2.py --preset isometric --platform square --quality medium -y \
  "abstract brand mood board for Halcyon, geometric composition expressing the brand's character, color palette: primary #0E7C7B, accent #F2714E, text #13201F, background #FBF7F0, success #3E8E5A, warning #D99A2B, danger #C24330, typography: Inter, Fraunces, rounded corners" \
  halcyon-isometric.png

scripts/gpt_image_2.py --preset poster --platform square --quality medium -y \
  "abstract brand mood board for Halcyon, geometric composition expressing the brand's character, color palette: primary #0E7C7B, accent #F2714E, text #13201F, background #FBF7F0, success #3E8E5A, warning #D99A2B, danger #C24330, typography: Inter, Fraunces, rounded corners" \
  halcyon-poster.png

# nano-banana -- brand exploration for Halcyon
# nano-banana's edge is accurate in-image TEXT (--model pro) and style anchoring via --reference <img>. Prefer it when the brand name/wordmark must render legibly. Add --dry-run to preview the composed prompt without an API call.
# DO use the exact hex codes and fonts below. DON'T add logos, real
#   brand names, or text unless the preset is text-oriented.

scripts/nano_banana.py --preset editorial --platform square --model pro \
  "abstract brand mood board for Halcyon, geometric composition expressing the brand's character, color palette: primary #0E7C7B, accent #F2714E, text #13201F, background #FBF7F0, success #3E8E5A, warning #D99A2B, danger #C24330, typography: Inter, Fraunces, rounded corners" \
  halcyon-editorial.png

scripts/nano_banana.py --preset risograph --platform square --model pro \
  "abstract brand mood board for Halcyon, geometric composition expressing the brand's character, color palette: primary #0E7C7B, accent #F2714E, text #13201F, background #FBF7F0, success #3E8E5A, warning #D99A2B, danger #C24330, typography: Inter, Fraunces, rounded corners" \
  halcyon-risograph.png

scripts/nano_banana.py --preset brutalist --platform square --model pro \
  "abstract brand mood board for Halcyon, geometric composition expressing the brand's character, color palette: primary #0E7C7B, accent #F2714E, text #13201F, background #FBF7F0, success #3E8E5A, warning #D99A2B, danger #C24330, typography: Inter, Fraunces, rounded corners" \
  halcyon-brutalist.png
