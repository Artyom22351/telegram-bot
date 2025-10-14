# grant_priv.py

import aiosqlite
from datetime import datetime

# Установите здесь правильные флаги для привилегий
PRIVILEGES_FLAGS = {
    "Вип": "ADMIN_LEVEL_H",        # t
    "Осирис": "ADMIN_LEVEL_G",     # s
    "Анубис": "ADMIN_LEVEL_F",     # r
    "Зевс": "ADMIN_LEVEL_E",       # q
    "Один": "ADMIN_LEVEL_D",       # p
    "Тор": "ADMIN_LEVEL_C",        # o
    "Владелець": "ADMIN_RESERVATION"  # b
}

async def grant_privilege(user_id, privilege, db_path="orders.db"):
    # Убедитесь, что привилегия существует
    if privilege not in PRIVILEGES_FLAGS:
        raise ValueError(f"Привилегия '{privilege}' не существует.")

    # Получаем флаг привилегии
    flag = PRIVILEGES_FLAGS[privilege]

    # Подключаемся к базе данных
    async with aiosqlite.connect(db_path) as db:
        # Проверяем, существует ли уже запись для этого пользователя
        cursor = await db.execute("SELECT * FROM orders WHERE tg_user_id = ? AND status = 'paid'", (user_id,))
        order = await cursor.fetchone()
        
        if order:
            raise ValueError(f"Пользователь с ID {user_id} уже имеет привилегию '{privilege}'.")

        # Получаем текущую дату и время
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Вставляем новый заказ в базу данных
        await db.execute("""
            INSERT INTO orders (tg_user_id, tg_username, privilege, term, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, f"User_{user_id}", privilege, "Назавжди", 0, "paid", now))

        # Сохраняем изменения в базе данных
        await db.commit()

    # Возвращаем флаг привилегии
    return flag
