"""Small fake user producer; no network or external service."""
USERS = {1: "Ada", 2: "Grace"}

def get_user(user_id=1):
    return {"name": USERS[int(user_id)]}
