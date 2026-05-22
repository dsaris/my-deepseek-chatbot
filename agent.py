import json
from datetime import datetime
from openai import OpenAI

# ─── Definisi Tools ───────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Mendapatkan waktu dan tanggal saat ini.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Menghitung ekspresi matematika. Gunakan ini untuk kalkulasi angka.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Ekspresi matematika, contoh: '2 + 2', '10 * 5', '100 / 4'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_info",
            "description": "Mendapatkan informasi cuaca kota (simulasi).",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nama kota, contoh: 'Jakarta', 'Surabaya'"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# ─── Implementasi Tools ───────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Menjalankan tool yang dipanggil oleh AI Agent."""

    if tool_name == "get_current_time":
        now = datetime.now()
        return f"Waktu sekarang: {now.strftime('%H:%M:%S WIB, %A %d %B %Y')}"

    elif tool_name == "calculator":
        try:
            allowed = set("0123456789+-*/()., ")
            expr = tool_input.get("expression", "")
            if all(c in allowed for c in expr):
                result = eval(expr)
                return f"Hasil: {expr} = {result}"
            else:
                return "Error: Ekspresi tidak valid."
        except Exception as e:
            return f"Error kalkulasi: {str(e)}"

    elif tool_name == "get_weather_info":
        city = tool_input.get("city", "Unknown")
        weather_data = {
            "Jakarta": {"suhu": "32°C", "kondisi": "Cerah berawan", "kelembaban": "75%"},
            "Surabaya": {"suhu": "34°C", "kondisi": "Panas terik", "kelembaban": "70%"},
            "Bandung": {"suhu": "24°C", "kondisi": "Sejuk dan cerah", "kelembaban": "65%"},
            "Yogyakarta": {"suhu": "29°C", "kondisi": "Berawan", "kelembaban": "72%"},
        }
        if city in weather_data:
            d = weather_data[city]
            return f"Cuaca {city}: {d['kondisi']}, Suhu {d['suhu']}, Kelembaban {d['kelembaban']}"
        return f"Data cuaca untuk {city} tidak tersedia. Tersedia: Jakarta, Surabaya, Bandung, Yogyakarta."

    return f"Tool '{tool_name}' tidak dikenal."


# ─── Inisialisasi DeepSeek Client ─────────────────────────────────────────────

def get_client(api_key: str) -> OpenAI:
    """Membuat OpenAI client yang mengarah ke DeepSeek API."""
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"   # ← Kunci utama: ganti base_url
    )


# ─── AI Agent Runner ──────────────────────────────────────────────────────────

def run_agent(
    client: OpenAI,
    messages: list,
    model: str = "deepseek-chat"
) -> tuple[str, list]:
    """
    Menjalankan AI Agent dengan loop tool use (OpenAI-compatible).

    Returns:
        (response_text, updated_messages)
    """
    current_messages = messages.copy()

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=current_messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        msg = response.choices[0].message
        current_messages.append(msg)   # Tambahkan respons AI ke history

        # Jika tidak ada tool call → AI sudah selesai
        if not msg.tool_calls:
            return msg.content, current_messages

        # Jika ada tool call → jalankan semua tool dan kirim hasilnya
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            result = execute_tool(fn_name, fn_args)

            current_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    return "Maaf, terjadi kesalahan.", current_messages