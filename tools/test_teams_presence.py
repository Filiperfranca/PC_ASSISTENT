import time

from app.integrations.graph_teams_provider import GraphTeamsProvider


def main():
    provider = GraphTeamsProvider()

    print("Definindo Teams como Available/Available...")
    provider.set_presence("Available", "Available")

    print("Aguardando 10 segundos...")
    time.sleep(10)

    print("Definindo Teams como Away/Away...")
    provider.set_presence("Away", "Away")


if __name__ == "__main__":
    main()