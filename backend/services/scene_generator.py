"""
Dynamic Scene Generator Service
Generates contextually-aware scene descriptions for arrivals, returns, and transitions
Integrates with world_blueprint, world_state, character_state, and quest hooks
"""
import logging
from typing import Dict, Any, Optional, List
from .llm_client import get_openai_client

logger = logging.getLogger(__name__)


def generate_scene_description(
    scene_type: str,
    location: Dict[str, Any],
    character_state: Dict[str, Any],
    world_state: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    available_quest_hooks: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Generate dynamic scene description using LLM
    
    Args:
        scene_type: "arrival", "return", "transition", "time_skip"
        location: Location data from world_blueprint (starting_town or POI)
        character_state: Character data including level, background, reputation
        world_state: Current world state including time, weather, active_npcs
        world_blueprint: Full world blueprint for context
        available_quest_hooks: List of quest hooks to subtly inject
        
    Returns:
        Dict with keys: location, description, why_here
    """
    if not available_quest_hooks:
        available_quest_hooks = []
    
    location_name = location.get("name", "Unknown")
    location_role = location.get("role", "settlement")
    location_summary = location.get("summary", "A mysterious place")
    signature_products = location.get("signature_products", [])
    
    character_name = character_state.get("name", "Adventurer")
    character_level = character_state.get("level", 1)
    character_background = character_state.get("background", "wanderer")
    character_class = character_state.get("class", character_state.get("class_", "unknown"))
    
    time_of_day = world_state.get("time_of_day", "midday")
    weather = world_state.get("weather", "clear")
    
    # Get reputation context
    reputation = character_state.get("reputation", {})
    is_wanted = world_state.get("guards_hostile", False) or world_state.get("city_hostile", False)
    
    # Get nearby threats
    global_threat = world_blueprint.get("global_threat", {})
    early_signs = global_threat.get("early_signs_near_starting_town", [])
    
    # Build prompt
    prompt = build_scene_generator_prompt(
        scene_type=scene_type,
        location_name=location_name,
        location_role=location_role,
        location_summary=location_summary,
        signature_products=signature_products,
        character_name=character_name,
        character_level=character_level,
        character_background=character_background,
        character_class=character_class,
        time_of_day=time_of_day,
        weather=weather,
        is_wanted=is_wanted,
        reputation=reputation,
        early_signs=early_signs,
        quest_hooks=available_quest_hooks
    )
    
    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Use mini for faster/cheaper scene generation
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Generate scene description for {scene_type} at {location_name}"}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        generated_text = completion.choices[0].message.content.strip()
        
        # Parse the generated scene
        # Expected format: Location description (2-3 sentences) + arrival context (1 sentence)
        # Split into description and why_here
        sentences = generated_text.split(". ")
        
        if len(sentences) >= 2:
            # Last sentence is "why_here", rest is description
            description = ". ".join(sentences[:-1]) + "."
            why_here = sentences[-1].strip()
            if not why_here.endswith('.'):
                why_here += "."
        else:
            # Fallback: use whole text as description, generate simple why_here
            description = generated_text
            why_here = f"You arrive in {location_name}, ready for whatever awaits."
        
        logger.info(f"✅ Generated dynamic scene for {location_name} ({scene_type})")
        
        return {
            "location": location_name,
            "description": description,
            "why_here": why_here
        }
        
    except Exception as e:
        logger.error(f"❌ Scene generation failed: {e}")
        # Fallback to simple template
        return {
            "location": location_name,
            "description": location_summary,
            "why_here": f"You have arrived in {location_name} seeking adventure and fortune. The world awaits your choices."
        }


def build_scene_generator_prompt(
    scene_type: str,
    location_name: str,
    location_role: str,
    location_summary: str,
    signature_products: List[str],
    character_name: str,
    character_level: int,
    character_background: str,
    character_class: str,
    time_of_day: str,
    weather: str,
    is_wanted: bool,
    reputation: Dict[str, Any],
    early_signs: List[str],
    quest_hooks: List[Dict[str, Any]]
) -> str:
    """Build system prompt for scene generation"""
    
    # Determine character experience level
    experience_level = "inexperienced" if character_level <= 3 else "seasoned" if character_level <= 7 else "legendary"
    
    # Format quest hooks
    hooks_text = ""
    if quest_hooks:
        hooks_list = []
        for hook in quest_hooks[:2]:  # Max 2 hooks per scene
            hook_type = hook.get("type", "conversation")
            hook_desc = hook.get("description", "")
            hooks_list.append(f"- {hook_type.capitalize()}: {hook_desc}")
        hooks_text = "\n".join(hooks_list)
    
    # Format signature products
    products_text = ", ".join(signature_products[:3]) if signature_products else "various goods"
    
    prompt = f"""UNIFIED DM SYSTEM PROMPT v6.0 (Scene Generation Mode)

🚨🚨🚨 CRITICAL FAILURE CONDITIONS - YOU WILL FAIL IF: 🚨🚨🚨
1. You don't give EXACTLY 3 directions: left, right, and ahead
2. You use flowery language or banned AI phrases
3. You write more than 8 sentences
4. You use third person or omniscient narration

COUNT YOUR DIRECTIONS BEFORE RESPONDING: Must be LEFT + RIGHT + AHEAD = 3

---

SCENE TYPE: {scene_type}
- arrival: First time entering location
- return: Returning to previously visited location
- transition: Moving from one area to another within same location
- time_skip: Same location, time has passed

---

LOCATION CONTEXT:
- Name: {location_name}
- Role: {location_role}
- Base Description: {location_summary}
- Known For: {products_text}
- Time: {time_of_day}
- Weather: {weather}

CHARACTER CONTEXT:
- Name: {character_name}
- Level: {character_level} ({experience_level})
- Background: {character_background}
- Class: {character_class}
- Wanted/Hostile: {"YES - guards watching" if is_wanted else "No"}

{"AVAILABLE QUEST HOOKS (weave 1-2 subtly into description):" if quest_hooks else ""}
{hooks_text if quest_hooks else ""}

{"THREAT CONTEXT (include 1 subtle sign):" if early_signs else ""}
{chr(10).join([f"- {sign}" for sign in early_signs[:2]]) if early_signs else ""}

---

v4.1 NARRATION RULES:

POV Discipline:
✅ Use second person ("you") ONLY
✅ Describe ONLY what the player can see, hear, smell, feel
❌ NEVER use omniscient narration
❌ NEVER describe NPC thoughts or hidden information
❌ NEVER use third person

Sentence Limits:
- Travel/Scene description: 4–8 sentences (v4.1 spec)
- Max 2 sensory details per sentence
- No repeated adjectives
- No over-description

---

OUTPUT REQUIREMENTS:
- Write 4-8 sentences TOTAL
- Sentence 1: Sensory detail (sight/sound) appropriate to time/weather
- Sentences 2-4: **SPATIAL EXPLORATION CUES (YOU WILL FAIL IF YOU DON'T DO THIS):**
  * SENTENCE 2: "To your left, [location/NPC]."
  * SENTENCE 3: "To your right, [location/NPC]."
  * SENTENCE 4: "Straight ahead, [location/NPC]." OR "Ahead of you, [location/NPC]."
  * YOU MUST USE ALL THREE DIRECTIONS OR YOU FAIL
  * Each must be a separate sentence starting with the direction
- Sentences 5-8: Short, direct arrival (NO flowery language, NO metaphors, NO invented emotions)

---

STYLE RULES:
- Use second person ("You arrive...")
- **MANDATORY: Give exactly 3 spatial directions (left, right, ahead/center/straight)**
- Show don't tell - NO metaphors, NO invented emotions
- Short, direct sentences (max 15 words)
- Make quest hooks subtle (environmental clues, NPC behavior, overheard fragments)
- Match time of day (morning: fresh activity, night: quieter, shadowy)
- Simple, clear language: "You arrive in town" NOT "You step into this hub of mystery"

---

BANNED PHRASES (v4.1 spec):
❌ "you notice", "you feel a sense", "it seems that", "uncertainty dances"
❌ "shadows linger", "whispers of", "feeling like a gamble", "beyond sight"
❌ "mysterious presence", "tendrils of darkness", "shrouded in mystery"
❌ "emerge from", "filters through", "thick with opportunity"
✅ Use concrete nouns: "tavern", "market", "guard post", "alley", "blacksmith"

---

EXAMPLES:

✅ PERFECT EXAMPLE (COUNT THE DIRECTIONS - MUST BE 3):
"You enter Darkeroot as midday sun warms the streets. To your left, a blacksmith hammers at his forge. To your right, the Rusty Blade tavern door stands open. Straight ahead, the town square has market stalls. You walk into town."

Structure breakdown:
- Sentence 1: "You enter... sun warms..." (arrival + sensory)
- Sentence 2: "To your left, blacksmith..." (LEFT)
- Sentence 3: "To your right, tavern..." (RIGHT)  
- Sentence 4: "Straight ahead, market..." (AHEAD)
- Sentence 5: "You walk..." (simple arrival)

✅ GOOD (wanted status, 3 directions):
"You return to Fort Dawnlight as evening falls. To your left, guards at the gate eye passing travelers. To your right, an alley leads toward the docks. Ahead, the main road runs through the market district. You pull your hood low and walk quickly."

❌ BAD (only 1 direction, flowery language):
"You arrive in Darkeroot where shadows dance and mystery lingers. To your right, an alleyway beckons with whispered secrets. Uncertainty dances in your chest as you take your first tentative steps into this hub of intrigue." 
← WRONG: Only one direction, uses "dances", "whispered secrets", "uncertainty", invented emotions

---

CRITICAL REMINDERS:
1. ✅ Is this second person POV?
2. ✅ Did I give EXACTLY 3 spatial directions (left, right, ahead)?
3. ✅ Is my sentence count 4-8?
4. ✅ Did I avoid banned phrases?
5. ✅ Did I avoid inventing player emotions?

Generate scene description now:"""
    
    return prompt
