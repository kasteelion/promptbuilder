"""Pose templates for quick pose creation."""


TEMPLATES = {
    "Blank": {
        "description": "Start from scratch",
        "content": ""
    },
    
    "Standing Confident": {
        "description": "Strong confident stance",
        "content": """Standing upright with confident posture, shoulders back and chest forward, hands on hips or arms crossed, steady direct gaze at viewer, self-assured expression"""
    },
    
    "Sitting Relaxed": {
        "description": "Casual seated position",
        "content": """Sitting comfortably with relaxed posture, one leg crossed over the other or both feet on ground, leaning back slightly, arms resting naturally, calm friendly expression"""
    },
    
    "Walking Forward": {
        "description": "Mid-stride movement",
        "content": """Walking toward viewer with natural stride, one foot forward mid-step, arms swinging naturally at sides, confident forward-facing expression, dynamic motion"""
    },
    
    "Leaning Against Wall": {
        "description": "Casual leaning pose",
        "content": """Leaning back against wall or surface with relaxed posture, one foot propped against wall or both feet crossed at ankles, arms crossed or hands in pockets, casual expression"""
    },
    
    "Arms Crossed": {
        "description": "Defensive or confident stance",
        "content": """Standing with arms firmly crossed across chest, weight evenly distributed or shifted to one hip, direct eye contact, determined or skeptical expression"""
    },
    
    "Hand on Face": {
        "description": "Thoughtful contemplative pose",
        "content": """Hand touching face in thoughtful gesture (chin, cheek, or temple), slight head tilt, contemplative or pensive expression, reflective mood"""
    },
    
    "Sitting on Desk": {
        "description": "Casual perched position",
        "content": """Sitting casually on edge of desk or table, legs dangling or one foot touching ground, hands placed beside hips for support or holding object, friendly approachable expression"""
    },
    
    "Running Action": {
        "description": "Active running motion",
        "content": """Mid-run with dynamic forward motion, arms pumping, legs in running stride, determined focused expression, hair and clothing suggesting movement"""
    },
    
    "Pointing Gesture": {
        "description": "Directional pointing pose",
        "content": """Arm extended with finger pointing in specific direction, body slightly turned toward pointing direction, engaged expression, drawing attention to something"""
    },
    
    "Hand Extended": {
        "description": "Reaching or offering gesture",
        "content": """One hand extended forward toward viewer in offering or reaching gesture, friendly welcoming expression, open body language"""
    },
    
    "Looking Over Shoulder": {
        "description": "Backward glance pose",
        "content": """Body facing away or to side with head turned to look back over shoulder at viewer, slight twist in torso, intriguing or playful expression"""
    },
    
    "Crouching Low": {
        "description": "Low crouch position",
        "content": """Crouched down low with knees bent, balanced on balls of feet, hands touching ground for support or resting on knees, alert focused expression"""
    },
    
    "Hands Behind Head": {
        "description": "Relaxed casual pose",
        "content": """Standing or sitting with hands clasped behind head, elbows out to sides, relaxed confident posture, easygoing expression"""
    },
    
    "Kneeling Position": {
        "description": "Down on one or both knees",
        "content": """Kneeling on one knee or both knees, upright torso, hands resting on raised knee or at sides, respectful or dramatic expression"""
    },
    
    "Victory Pose": {
        "description": "Triumphant celebration",
        "content": """Arms raised high in victory gesture, fists pumped or fingers in V-sign, energetic upright posture, joyful triumphant expression"""
    },
    
    "Thinking Pose": {
        "description": "Deep concentration",
        "content": """Hand on chin in classic thinking gesture, slight forward lean, furrowed brow, concentrated thoughtful expression"""
    },
    
    "Stretching": {
        "description": "Arms raised stretch",
        "content": """Arms stretched high overhead, back slightly arched, reaching upward, relaxed or energized expression, waking up or loosening up"""
    },
    
    "Defensive Stance": {
        "description": "Ready or protective position",
        "content": """Alert defensive posture with knees slightly bent, hands raised in protective position, weight forward on balls of feet, focused wary expression"""
    },
    
    "Lying Down": {
        "description": "Reclined horizontal pose",
        "content": """Lying on back or side on surface, propped up on elbows or fully reclined, legs extended or bent, relaxed peaceful expression"""
    },
    
    "Dancing Movement": {
        "description": "Dynamic dance pose",
        "content": """Mid-dance movement with graceful extended limbs, one arm raised high, body in fluid motion, joyful expressive face, dynamic energy"""
    },
    
    "Phone Conversation": {
        "description": "Talking on phone",
        "content": """Holding phone to ear with one hand, natural standing or sitting posture, engaged in conversation, speaking expression"""
    },
    
    "Working at Computer": {
        "description": "Seated at desk typing",
        "content": """Sitting at desk facing computer or laptop, hands positioned on keyboard, focused forward gaze at screen, concentrated work expression"""
    },
    
    "Coffee/Drink Hold": {
        "description": "Holding beverage casually",
        "content": """Holding coffee cup, mug, or drink in one or both hands, relaxed standing or sitting posture, enjoying beverage, content expression"""
    },
    
    "Superhero Landing": {
        "description": "Dramatic landing pose",
        "content": """Crouched low with one fist touching ground, other arm extended back for balance, dramatic powerful pose, intense determined expression"""
    }
}


def get_template_names():
    """Get list of template names for dropdown."""
    return list(TEMPLATES.keys())


def get_template(name):
    """Get template data by name.
    
    Args:
        name: Template name
        
    Returns:
        Dict with 'content' key, or None if not found
    """
    return TEMPLATES.get(name)


def get_template_description(name):
    """Get template description.
    
    Args:
        name: Template name
        
    Returns:
        Description string or empty string if not found
    """
    template = TEMPLATES.get(name)
    return template.get("description", "") if template else ""
