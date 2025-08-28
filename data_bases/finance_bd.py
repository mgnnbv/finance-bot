import aiosqlite


async def init_db():
    async with aiosqlite.connect('Finance_for_bot.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS category (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) UNIQUE
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS finance (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                data_of_operation VARCHAR(50),
                amount INTEGER,
                description VARCHAR(300),
                category_name VARCHAR(100),
                FOREIGN KEY (category_name) REFERENCES category(name)
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS subscribes (
                user_id INTEGER PRIMARY KEY,
                active_subscribe VARCHAR(50) NOT NULL,
                subscribe_status INTEGER NOT NULL
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action VARCHAR(50) NOT NULL,
                data_of_create VARCHAR(50) NOT NULL
            )
        ''')

        await db.commit()


async def add_expense(result):
    async with aiosqlite.connect("Finance_for_bot.db") as db:
        await db.execute(
            '''INSERT INTO finance (user_id, data_of_operation, amount, description, category_name)
               VALUES (?, ?, ?, ?, ?)''',
            (
                result["user_id"],
                result["data_of_operation"],
                result["chosen_amount"],
                result["chosen_description"],
                result["chosen_category"]
            )
        )
        await db.commit()


async def category_check():
    async with aiosqlite.connect('Finance_for_bot.db') as db:
        async with db.execute('''SELECT name FROM category WHERE name IS NOT NULL''') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows] if rows else []


async def report():
    async with aiosqlite.connect('Finance_for_bot.db') as db:
        async with db.execute('''SELECT id, data_of_operation, amount, description FROM finance WHERE amount IS NOT NULL''') as cursor:
            rows = await cursor.fetchall()
            return rows if rows else []
