from common.config import load_settings
from chatbot_pipeline.chat_pipeline import ChatPipeline


def main():
    settings = load_settings()
    pipeline = ChatPipeline(settings)

    print("Question: ")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        if not question:
            continue

        result = pipeline.answer(question)
        tag = "[cache]" if result["from_cache"] else "[mới]"
        print(f"\nBot {tag}: {result['answer']}")
        if result["sources"]:
            titles = ", ".join(s["title"] or s["url"] for s in result["sources"])
            print(f"Sources: {titles}")


if __name__ == "__main__":
    main()
