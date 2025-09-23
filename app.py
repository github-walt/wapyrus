import json
from llm_interface import ask_roo

def load_signals(file_path="knowledge_base.json"):
    with open(file_path, "r") as f:
        return json.load(f)

def main():
    print("👋 Welcome to Wapyrus — your MedTech Signal Explorer!")
    signals = load_signals()

    while True:
        query = input("\nAsk Roo a question (or type 'exit' to quit):\n> ")
        if query.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        response = ask_roo(query, signals)
        print(f"\n🧠 Roo says:\n{response}")

if __name__ == "__main__":
    main()
