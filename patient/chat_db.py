from database import create_connection

# Save message
def save_message(user_id, role, message):
    conn = create_connection()
    cursor = conn.cursor()

    query = "INSERT INTO chat_history (user_id, role, message) VALUES (%s, %s, %s)"
    cursor.execute(query, (user_id, role, message))

    conn.commit()
    conn.close()

# Load chat history
def load_chat(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    query = "SELECT role, message FROM chat_history WHERE user_id=%s ORDER BY created_at"
    cursor.execute(query, (user_id,))

    data = cursor.fetchall()
    conn.close()

    return data

# Clear chat
def clear_chat(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    query = "DELETE FROM chat_history WHERE user_id=%s"
    cursor.execute(query, (user_id,))

    conn.commit()
    conn.close()