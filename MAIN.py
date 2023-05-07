from typing import List

import gym as gym
from GA import GA
from MODEL_CNN import ModelCNN


# !pip install gym[atari]
# !pip install gym[accept-rom-license]


def save_weights_to_file(reward: int, weights: List[float]):
    # save best weights to txt file
    with open(f"best_weights_{reward}.txt", "w") as f:
        for weight in weights:
            f.write(str(weight) + "\n")


env = gym.make('ALE/AirRaid-v5',
               obs_type="grayscale",
               render_mode='human',
               frameskip=30,
               repeat_action_probability=0)
env.metadata['video.frames_per_second'] = 120

MODEL = ModelCNN()

GA = GA(population_size=3,
        gen_limit=2,
        p_crossover=0.7,
        p_mutation=0.4,
        env=env,
        number_of_weights=MODEL.get_number_of_weights(),
        model=MODEL)

best_weights = GA.find_best_weights()
total_reward = MODEL.play(env, best_weights)

print(f"Total reward: {total_reward}")
save_weights_to_file(int(total_reward), best_weights)

def load_weights_from_file(name) -> List[float]:
    with open(name, "r") as f:
        return [float(weight) for weight in f.readlines()]