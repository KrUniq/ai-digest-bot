from app.handlers import build_app

def main():
    app = build_app()
    app.run_polling()

if __name__ == "__main__":
    main()
