
# Prompt Distribution Analysis

Total Prompts Analyzed: 149


## Top 10 Scenes
  Modern shopping mall, polished floors, storefronts, bright lighting, busy commercial atmosphere.: 9 (6.0%)
  Modern airport interior, floor-to-ceiling windows, departure boards, bustling travelers, bright artificial lighting.: 8 (5.4%)
  Elegant restaurant interior, soft lighting, intimate atmosphere, stylish decor, white tablecloths.: 7 (4.7%)
  Large concert stage, dramatic colored spotlights, smoke effects, microphone stand, energetic crowd visible.: 6 (4.0%)
  Pristine lab environment, stainless steel benches, microscopes, glass beakers, glowing chemical samples, cold professional lighting.: 6 (4.0%)
  Casual morning kitchen, sunny window, breakfast on counter, coffee mugs, cozy domestic vibe.: 5 (3.4%)
  Urban rooftop setting, city skyline in background, sunset lighting, Modern outdoor furniture.: 5 (3.4%)
  Clean minimalist interior, large sectional sofa, flat-screen TV, indoor plants, soft natural light, cozy domestic atmosphere.: 4 (2.7%)
  Eclectic vintage store, racks of retro clothing, antique decor, nostalgic treasure-hunt vibe.: 4 (2.7%)
  Small exam room, medical bed with paper cover, equipment on walls, sink, clinical sterile atmosphere.: 4 (2.7%)

## Top 10 Base Prompts (Art Styles)
  Sports Action: "Frozen Velocity": 107 (71.8%) ⚠️ OVERWEIGHTED
  Low-Poly 3D: 14 (9.4%)
  Anime Style: "Dynamic Cel-Shaded": 11 (7.4%)
  Classic Anime: "Clean Cel Animation": 10 (6.7%)
  Watercolor Impressionistic: 3 (2.0%)
  Chibi Style: "Super Deformed": 3 (2.0%)
  Digital Painting: "Expressive Impasto": 1 (0.7%)

## Top 10 Outfits
  Cold Weather - Athletic: 16 (10.7%)
  Retro Bowling: 13 (8.7%)
  Esports Jersey: 13 (8.7%)
  Gymnastics: 13 (8.7%)
  Tech-Athletic Compression: 13 (8.7%)
  MMA: 12 (8.1%)
  Flag Football: 10 (6.7%)
  Retro Tracksuit: 10 (6.7%)
  American Football: 10 (6.7%)
  Track and Field: 10 (6.7%)

## Top 10 Poses

## Interactions
  Custom: 99 (66.4%)

## Mermaid Distribution Flow

```mermaid
graph LR
  classDef scene fill:#f9f,stroke:#333,stroke-width:2px;
  classDef style fill:#bbf,stroke:#333,stroke-width:2px;
  classDef outfit fill:#bfb,stroke:#333,stroke-width:2px;
  S_Modern_shopping_mall,_polished_floors,_storefronts,_bright_lighting,_busy_commercial_atmosphere.[Modern shopping mall, polished floors, storefronts, bright lighting, busy commercial atmosphere.]
  class S_Modern_shopping_mall,_polished_floors,_storefronts,_bright_lighting,_busy_commercial_atmosphere. scene
  S_Modern_airport_interior,_floor_to_ceiling_windows,_departure_boards,_bustling_travelers,_bright_artificial_lighting.[Modern airport interior, floor-to-ceiling windows, departure boards, bustling travelers, bright artificial lighting.]
  class S_Modern_airport_interior,_floor_to_ceiling_windows,_departure_boards,_bustling_travelers,_bright_artificial_lighting. scene
  S_Elegant_restaurant_interior,_soft_lighting,_intimate_atmosphere,_stylish_decor,_white_tablecloths.[Elegant restaurant interior, soft lighting, intimate atmosphere, stylish decor, white tablecloths.]
  class S_Elegant_restaurant_interior,_soft_lighting,_intimate_atmosphere,_stylish_decor,_white_tablecloths. scene
  S_Large_concert_stage,_dramatic_colored_spotlights,_smoke_effects,_microphone_stand,_energetic_crowd_visible.[Large concert stage, dramatic colored spotlights, smoke effects, microphone stand, energetic crowd visible.]
  class S_Large_concert_stage,_dramatic_colored_spotlights,_smoke_effects,_microphone_stand,_energetic_crowd_visible. scene
  S_Pristine_lab_environment,_stainless_steel_benches,_microscopes,_glass_beakers,_glowing_chemical_samples,_cold_professional_lighting.[Pristine lab environment, stainless steel benches, microscopes, glass beakers, glowing chemical samples, cold professional lighting.]
  class S_Pristine_lab_environment,_stainless_steel_benches,_microscopes,_glass_beakers,_glowing_chemical_samples,_cold_professional_lighting. scene
  S_Modern_shopping_mall,_polished_floors,_storefronts,_bright_lighting,_busy_commercial_atmosphere. --> ST_Sports_Action:_"Frozen_Velocity"[Sports Action: "Frozen Velocity"]
  S_Modern_airport_interior,_floor_to_ceiling_windows,_departure_boards,_bustling_travelers,_bright_artificial_lighting. --> ST_Sports_Action:_"Frozen_Velocity"[Sports Action: "Frozen Velocity"]
  class ST_Sports_Action:_"Frozen_Velocity" style
  S_Modern_shopping_mall,_polished_floors,_storefronts,_bright_lighting,_busy_commercial_atmosphere. --> ST_Low_Poly_3D[Low-Poly 3D]
  S_Modern_airport_interior,_floor_to_ceiling_windows,_departure_boards,_bustling_travelers,_bright_artificial_lighting. --> ST_Low_Poly_3D[Low-Poly 3D]
  class ST_Low_Poly_3D style
  S_Modern_shopping_mall,_polished_floors,_storefronts,_bright_lighting,_busy_commercial_atmosphere. --> ST_Anime_Style:_"Dynamic_Cel_Shaded"[Anime Style: "Dynamic Cel-Shaded"]
  S_Modern_airport_interior,_floor_to_ceiling_windows,_departure_boards,_bustling_travelers,_bright_artificial_lighting. --> ST_Anime_Style:_"Dynamic_Cel_Shaded"[Anime Style: "Dynamic Cel-Shaded"]
  class ST_Anime_Style:_"Dynamic_Cel_Shaded" style
  S_Modern_shopping_mall,_polished_floors,_storefronts,_bright_lighting,_busy_commercial_atmosphere. --> ST_Classic_Anime:_"Clean_Cel_Animation"[Classic Anime: "Clean Cel Animation"]
  S_Modern_airport_interior,_floor_to_ceiling_windows,_departure_boards,_bustling_travelers,_bright_artificial_lighting. --> ST_Classic_Anime:_"Clean_Cel_Animation"[Classic Anime: "Clean Cel Animation"]
  class ST_Classic_Anime:_"Clean_Cel_Animation" style
  S_Modern_shopping_mall,_polished_floors,_storefronts,_bright_lighting,_busy_commercial_atmosphere. --> ST_Watercolor_Impressionistic[Watercolor Impressionistic]
  S_Modern_airport_interior,_floor_to_ceiling_windows,_departure_boards,_bustling_travelers,_bright_artificial_lighting. --> ST_Watercolor_Impressionistic[Watercolor Impressionistic]
  class ST_Watercolor_Impressionistic style
```
