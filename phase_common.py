import argparse


def read_source(description: str):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("source", help="Path to the CampusRoute source file")
    args = parser.parse_args()
    with open(args.source, "r", encoding="utf-8") as f:
        return f.read()
