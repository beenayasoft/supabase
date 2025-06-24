def get_client_ip(request):
    """
    Récupère l'adresse IP du client
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def determine_device_name(user_agent):
    """
    Détermine le nom de l'appareil à partir du user-agent
    """
    user_agent = user_agent.lower()
    device_name = "Inconnu"
    
    # Détection simple du type d'appareil
    if "iphone" in user_agent:
        device_name = "iPhone"
    elif "ipad" in user_agent:
        device_name = "iPad"
    elif "android" in user_agent:
        device_name = "Android"
    elif "windows" in user_agent:
        device_name = "Windows"
    elif "mac" in user_agent:
        device_name = "Mac"
    elif "linux" in user_agent:
        device_name = "Linux"
    
    return device_name 