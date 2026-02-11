import json
import random

RL_FILE = "rl_state.json"

def load_rl():
    try:
        with open(RL_FILE, "r") as f:
            return json.load(f)
    except:
        return {"caring":1.0, "neutral":1.0, "cheerful":1.0}

def save_rl(data):
    with open(RL_FILE, "w") as f:
        json.dump(data, f, indent=2)

def choose_style():
    data = load_rl()

    # explore sometimes
    if random.random() < 0.1:
        return random.choice(list(data.keys()))

    total = sum(data.values())
    r = random.uniform(0, total)

    upto = 0
    for k, w in data.items():
        if upto + w >= r:
            return k
        upto += w


def reward_style(style, reward):
    data = load_rl()

    if style not in data:
        data[style] = 1.0

    data[style] += reward

    if data[style] < 0.1:
        data[style] = 0.1

    save_rl(data)
