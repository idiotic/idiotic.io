from idioticio import run


def main():
    run(port=80, db="sqlite:///:memory:", config={})

if __name__ == "__main__":
    main()

