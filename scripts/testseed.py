import multiprocessing as mp
import numpy as np

def seed_np():
    seed = mp.current_process()._identity[0]
    return np.random.seed(seed)

def process_data(data):
    a = np.random.random()
    cp = mp.current_process()
    print("CP: {}; data: {}, random: {:.3f}".format(cp, data, a))
   # here I'd like to have the cursor so that I can do things with the data

if __name__ == "__main__":
    pool = mp.Pool(initializer=seed_np, initargs=())
    pool.map(process_data, range(16))