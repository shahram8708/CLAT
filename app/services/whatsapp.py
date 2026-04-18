from urllib.parse import quote


def generate_whatsapp_link(phone="+919978559986", custom_message=None):
    clean_phone = "".join(ch for ch in str(phone) if ch.isdigit())
    message = custom_message or "Hi, I want to connect with Career Launcher Ahmedabad."
    encoded_message = quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_message}"


def get_default_demo_link():
    message = "Hi, I want to book a free demo class at Career Launcher Ahmedabad."
    return generate_whatsapp_link(custom_message=message)
