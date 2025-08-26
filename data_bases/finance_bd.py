import sqlite3
import aiosqlite

with sqlite3.connect('../Finance.db') as db:
    cursor = db.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS category (
          id INTEGER PRIMARY KEY,
          name VARCHAR(100) UNIQUE
      )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            data_of_operation VARCHAR(50),
            amount INTEGER,
            description VARCHAR(300),
            category_name VARCHAR(100),
            FOREIGN KEY (category_name) REFERENCES category(name)
        )''')


async def add_expense(result):
    async with aiosqlite.connect("../Finance.db") as db:
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
    async with aiosqlite.connect('../Finance.db') as db:
        async with db.execute('''SELECT name FROM category WHERE name IS NOT NULL''') as cursor:
            rows = await cursor.fetchall()

            return [row[0] for row in rows] if rows else False


async def report():
    async with aiosqlite.connect('../Finance.db') as db:
        async with db.execute('''SELECT id, data_of_operation, amount, description FROM finance WHERE amount IS NOT NULL''') as cursor:
            rows = await cursor.fetchall()

            return rows if rows else False
