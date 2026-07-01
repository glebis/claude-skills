# gpt-image-2 -- brand exploration for The Dalí Museum — Giraffes on Horseback Salad
# gpt-image-2 unique presets explore the brand across moods. Add --thinking medium for infographic/diagram subjects; --quality high for finals (~$0.21/img).
# DO use the exact hex codes and fonts below. DON'T add logos, real
#   brand names, or text unless the preset is text-oriented.

scripts/gpt_image_2.py --preset editorial --platform square --quality medium -y \
  "abstract brand mood board for The Dalí Museum — Giraffes on Horseback Salad, geometric composition expressing the brand's character, color palette: primary #e4501b, accent #2fb9ca, text #fefefe, background #070613, warning #faff00, danger #c4151f, muted #5f5f60, typography: Inter, Playfair Display, Oswald, softly rounded corners" \
  the-dalí-museum-giraffes-on-horseback-salad-editorial.png

scripts/gpt_image_2.py --preset bauhaus --platform square --quality medium -y \
  "abstract brand mood board for The Dalí Museum — Giraffes on Horseback Salad, geometric composition expressing the brand's character, color palette: primary #e4501b, accent #2fb9ca, text #fefefe, background #070613, warning #faff00, danger #c4151f, muted #5f5f60, typography: Inter, Playfair Display, Oswald, softly rounded corners" \
  the-dalí-museum-giraffes-on-horseback-salad-bauhaus.png

scripts/gpt_image_2.py --preset isometric --platform square --quality medium -y \
  "abstract brand mood board for The Dalí Museum — Giraffes on Horseback Salad, geometric composition expressing the brand's character, color palette: primary #e4501b, accent #2fb9ca, text #fefefe, background #070613, warning #faff00, danger #c4151f, muted #5f5f60, typography: Inter, Playfair Display, Oswald, softly rounded corners" \
  the-dalí-museum-giraffes-on-horseback-salad-isometric.png

scripts/gpt_image_2.py --preset poster --platform square --quality medium -y \
  "abstract brand mood board for The Dalí Museum — Giraffes on Horseback Salad, geometric composition expressing the brand's character, color palette: primary #e4501b, accent #2fb9ca, text #fefefe, background #070613, warning #faff00, danger #c4151f, muted #5f5f60, typography: Inter, Playfair Display, Oswald, softly rounded corners" \
  the-dalí-museum-giraffes-on-horseback-salad-poster.png

# nano-banana -- brand exploration for The Dalí Museum — Giraffes on Horseback Salad
# nano-banana's edge is accurate in-image TEXT (--model pro) and style anchoring via --reference <img>. Prefer it when the brand name/wordmark must render legibly. Add --dry-run to preview the composed prompt without an API call.
# DO use the exact hex codes and fonts below. DON'T add logos, real
#   brand names, or text unless the preset is text-oriented.

scripts/nano_banana.py --preset editorial --platform square --model pro \
  "abstract brand mood board for The Dalí Museum — Giraffes on Horseback Salad, geometric composition expressing the brand's character, color palette: primary #e4501b, accent #2fb9ca, text #fefefe, background #070613, warning #faff00, danger #c4151f, muted #5f5f60, typography: Inter, Playfair Display, Oswald, softly rounded corners" \
  the-dalí-museum-giraffes-on-horseback-salad-editorial.png

scripts/nano_banana.py --preset risograph --platform square --model pro \
  "abstract brand mood board for The Dalí Museum — Giraffes on Horseback Salad, geometric composition expressing the brand's character, color palette: primary #e4501b, accent #2fb9ca, text #fefefe, background #070613, warning #faff00, danger #c4151f, muted #5f5f60, typography: Inter, Playfair Display, Oswald, softly rounded corners" \
  the-dalí-museum-giraffes-on-horseback-salad-risograph.png

scripts/nano_banana.py --preset brutalist --platform square --model pro \
  "abstract brand mood board for The Dalí Museum — Giraffes on Horseback Salad, geometric composition expressing the brand's character, color palette: primary #e4501b, accent #2fb9ca, text #fefefe, background #070613, warning #faff00, danger #c4151f, muted #5f5f60, typography: Inter, Playfair Display, Oswald, softly rounded corners" \
  the-dalí-museum-giraffes-on-horseback-salad-brutalist.png
