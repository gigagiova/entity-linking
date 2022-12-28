sql_queries = {
    "create_dictionary_table": """ 
    CREATE TABLE IF NOT EXISTS entities (
    idx INTEGER PRIMARY KEY,
    uid TEXT NOT NULL,
    description TEXT
    ); """,
    "insert_entities": "INSERT INTO entities VALUES(?,?, ?);",
    "select_entity_by_id": "SELECT * FROM entities WHERE idx=?",
}
