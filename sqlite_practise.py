import sqlite3

con = sqlite3.connect("tutorial.db")

# need to call a cursor object to work with the SQL 
cur = con.cursor()

# Command to execute SQL queries: cur.execute(SQL HERE)
# cur.execute("CREATE TABLE movie(title, year, score)")

# assign a query to a variable. Also, sqlite_master lets us look at what tables exist. Essentially, see what exists! 
res = cur.execute("SELECT name FROM sqlite_master")

# Fetch the resulting row from the SQL query
print (res.fetchone())

# Do an insert statement.
cur.execute("""
    INSERT INTO movie VALUES
        ('Monty Python and the Holy Grail', 1975, 8.2),
        ('And Now for Something Completely Different', 1971, 7.5)
""")

# Insert statement is not commited... 
res = cur.execute("SELECT * FROM movie")
print (res.fetchall())

# res = cur.execute("DELETE FROM movie")

#BUT if we want to commit, need to explicitly call that
# con.commit()

data = [
    ("Monty Python Live at the Hollywood Bowl", 1982, 7.9),
    ("Monty Python's The Meaning of Life", 1983, 7.5),
    ("Monty Python's Life of Brian", 1979, 8.0),
]

cur.executemany("INSERT INTO movie VALUES(?, ?, ?)", data)
con.commit()  # Remember to commit the transaction after executing INSERT.

con.close()

new_con = sqlite3.connect("tutorial.db")

new_cur = new_con.cursor()

res = new_cur.execute("SELECT title, year FROM movie ORDER BY score DESC")

title, year = res.fetchone()

print(f'The highest scoring Monty Python movie is {title!r}, released in {year}')

new_con.close()