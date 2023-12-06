from scenarios import ego_prereg


def run(times: int = 1):
    return ego_prereg.run(times, model="gpt-3.5-turbo")
