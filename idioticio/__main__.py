from idioticio import run
from yaml import load, YAMLError
from sys import argv


def main():
    config = {}

    if len(argv) > 1:
        try:
            with open(argv[1]) as config_file:
                config = load(config_file)
        except YAMLError:
            print("Unable to load config file: parse error")
            raise
        except FileNotFoundError:
            print("Unable to load config file: file not found")
        except IOError:
            print("Unable to load config file: IO error. check file type / permissions?")

    run(config=config)

if __name__ == "__main__":
    main()
