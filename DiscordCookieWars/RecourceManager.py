import pickle


def save_object(d, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(d, f, pickle.HIGHEST_PROTOCOL)


def load_object(name):
    try:
        with open(name + '.pkl', 'rb') as f:
            d = pickle.load(f)
    except FileNotFoundError:
        print("ERROR tried to load %s but file not found" % name)
        d = None
    return d
