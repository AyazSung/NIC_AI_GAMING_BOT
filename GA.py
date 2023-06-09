import random
from typing import List

import time
import cv2
import gym
import numpy as np
import tensorflow as tf
import os
from MODEL_CNN import ModelCNN

# Genetic Algorithm class for OpenAi Gym environment for finding optimal weights.
class GA:
    cur_gen_scores = []
    population_main = []

    def __init__(self, population_size: int,
                 gen_limit: int,
                 p_crossover: float,
                 mut_prob: float,
                 p_mutation: float,
                 env: gym.Env,
                 number_of_weights: int,
                 model: ModelCNN):
        self.population_size = population_size
        self.cur_gen_scores = [0.0] * population_size
        self.gen_limit = gen_limit
        self.p_crossover = p_crossover
        self.mut_prob = mut_prob
        self.p_mutation = p_mutation
        self.LOW = -5
        self.UP = 5
        self.env = env
        self.number_of_weights = number_of_weights
        self.modelCNN = model

    def saving_individual(self, individual, cur_gen_idx, ind_idx):
        filename = f"Generations/Gen{cur_gen_idx}/ind{ind_idx}.txt"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            for weight in individual:
                f.write(str(weight) + "\n")

    def save_cur_generation(self, current_generation_number):
        for i in range(self.population_size):
            self.saving_individual(self.population_main[i], current_generation_number, i)

    def create_weight(self) -> float:
        return random.uniform(self.LOW, self.UP)

    def create_individual(self) -> List[float]:
        return [self.create_weight() for _ in range(self.number_of_weights)]

    def create_population(self) -> List[List[float]]:
        return [self.create_individual() for _ in range(self.population_size)]

    def crossover(self, parent1: List[float], parent2: List[float]) -> (List[float], List[float]):
        crossover_point = random.randint(0, self.number_of_weights - 1)

        parent1 = parent1.copy()
        parent2 = parent2.copy()
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent1.copy()
        for w in range(self.number_of_weights):
            if random.random() < self.p_crossover:
                child2[w] = parent2[w]

        return child1, child2

    def selection(self, population: List[List[float]], fitness) -> (List[float], List[float]):
        return random.choices(
            population=population,
            weights=fitness,
            k=2)

    def mutation(self, individual) -> List[float]:
        for i in range(self.number_of_weights):
            if random.random() < self.p_mutation:
                individual[i] = self.create_weight()
        return individual

    def read_individual(self, gen_idx, ind_idx):
        f = open(f"Generations/Gen{gen_idx}/ind{ind_idx}.txt", "r")
        weights = [float(i) for i in f.read().split("\n") if i != ""]
        f.close()
        return weights

    def read_generation(self, gen_idx):
        gen = []
        for i in range(self.population_size):
            gen.append(self.read_individual(gen_idx, i))
        return gen

    def calc_scores(self, generation):
        scores = [self.fitness(ind) for ind in generation]
        return scores

    def sort_cur_gen_by_fitness(self):
        self.cur_gen_scores = self.calc_scores(self.population_main)
        ans = [i for i in sorted(zip(self.cur_gen_scores, self.population_main), reverse=True)]
        self.population_main = [i[1] for i in ans]
        self.cur_gen_scores = [i[0] for i in ans]

    def run_ga(self) -> List[float]:
        # continue from current_generation
        f = open('current_generation.txt', 'r')
        gen_idx = int(f.read())
        f.close()
        if gen_idx == 0:
            # If no saved generations, start from beginning
            print("Creating initial population...")
            self.population_main = self.create_population()
            print("Evaluating initial population...")
            self.sort_cur_gen_by_fitness()

            print("Main population sorted.")

            print(f"Best fitness, GEN INIT : {self.cur_gen_scores[0]}")
        else:
            print("Reading the previous generation...")
            self.population_main = self.read_generation(gen_idx)
            self.sort_cur_gen_by_fitness()
        for generation in range(self.gen_limit):
            st = time.time()
            population_next = self.population_main[:2]

            print("Creating next population...")
            for _ in range(self.population_size // 2 - 1):
                # get chromosomes to create new offsprings from them
                parent1, parent2 = self.selection(self.population_main, self.cur_gen_scores)
                child1, child2 = self.crossover(parent1, parent2)
                if random.random() <= self.mut_prob:
                    child1 = self.mutation(child1)
                if random.random() <= self.mut_prob:
                    child2 = self.mutation(child2)
                population_next.append(child1)
                population_next.append(child2)

            print("Evaluating next population...")
            self.population_main = population_next[:self.population_size]
            self.sort_cur_gen_by_fitness()
            print("Next population sorted.")
            print("Saving folder with generation model weights...")
            self.save_cur_generation(gen_idx)
            f = open('current_generation.txt', 'w')
            f.write(str(gen_idx))
            f.close()
            gen_idx += 1
            best_f = self.cur_gen_scores[0]
            print(f"Best fitness, GEN {generation} : {best_f}, Time of execution: {time.time() - st}")

        return self.population_main[0]

    # Fitness value function.
    # Plays the game and returns the reward.
    def fitness(self, individual: List[float]) -> float:

        # adjusting parameters sof the model
        self.modelCNN.set_weights(individual)

        # return env to default state
        observation = self.env.reset()[0]
        done = False
        action_count = 0
        total_reward = 0
        while not done and action_count < 250:
            # get the observation and reformat
            observation = observation[35:170, 20:]
            observation = cv2.resize(observation, dsize=(70, 70), interpolation=cv2.INTER_CUBIC)
            # predict the next step to take, returns array with probabilities
            action = self.modelCNN.model.predict(np.array([observation]), verbose=0)

            # choose action with the highest probability
            action = np.argmax(action)

            # get the new state of the game
            observation, reward, truncted, terminated, info = self.env.step(action)
            action_count += 1
            done = terminated or truncted
            total_reward += reward

        return total_reward

    # Start function to start searching for optimal weights
    def find_best_weights(self) -> List[float]:
        return self.run_ga()
