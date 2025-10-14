flags = {
    "VIP": "ADMIN_LEVEL_H",
    "Osiris": "ADMIN_LEVEL_G",
    "Zeus": "ADMIN_LEVEL_E",
    "Odin": "ADMIN_LEVEL_D",
    "Thor": "ADMIN_LEVEL_C",
    "Anubis": "ADMIN_LEVEL_F",
    "Создатель": "ADMIN_RESERVATION"
}

def grant_privileges(user_id, privilege):
    flag = flags.get(privilege)
    if flag:
        print(f"User {user_id} granted {privilege} with flag {flag}")
        # Дополнительно логика для присваивания флага
    else:
        print(f"Invalid privilege: {privilege}")
