class GlobalVars:
    def __init__(self):
        self.subscribers_vk = {}
        self.online_status_subscribers_vk = {}
        self.session = None  # Глобальная сессия
        print(self.session)
