from pizza import Pizza, Direction

import numpy as np
import json

POSITIVE_REWARD = 3.0
NEUTRAL_REWARD  = -0.1
NEGATIVE_REWARD = -1.0
SHUFFLE_REWARD = -2.0
DOUBLE_TOGGLE_REWARD = -0.5
class ActionNotFoundException(Exception):
    pass

class GoogleEngineer:
    delta_position = {
        Direction.right: (0,1),
        Direction.down:  (1,0),
        Direction.left:  (0,-1),
        Direction.up:    (-1,0),
    }

    def __init__(self, pizza_config):
        self.pizza = Pizza(pizza_config['pizza_lines'])
        self.min_each_ingredient_per_slice = pizza_config['l']
        self.max_ingredients_per_slice = pizza_config['h']
        self.previous_action = 'none'
        self.current_step = 0
        self.previous_position = -1
        self.shuffle_count = 0
        self.double_toggle_count = 0
        self.cursor_position = (0,0)
        self.slice_mode = False
        self.valid_slices = []
        self.score = 0

    def score_of(self, slice):
        if min(self.pizza.ingredients.of(slice)) >= self.min_each_ingredient_per_slice:
            return slice.ingredients
        return 0

    def move(self, direction):
        next_cursor_position = tuple(x0+x1 for x0,x1 in zip(self.cursor_position,self.delta_position[direction]))
        if (next_cursor_position[0] >= 0 and next_cursor_position[0] < self.pizza.r and
            next_cursor_position[1] >= 0 and next_cursor_position[1] < self.pizza.c):
            if not self.current_step % 2:
                self.previous_position = self.cursor_position
            else:
                self.cursor_position = next_cursor_position
            # print(self.previous_position, self.cursor_position)
            if (self.previous_position == next_cursor_position):
                self.shuffle_count+=1

                return SHUFFLE_REWARD
            return NEUTRAL_REWARD
        self.current_step+=1
        #print(self.current_step)
        return NEGATIVE_REWARD

    def increase(self, direction):
        slice = self.pizza.slice_at(self.cursor_position)
        new_slice = self.pizza.increase(slice, direction, self.max_ingredients_per_slice)
        if (new_slice is not None and min(self.pizza.ingredients.of(new_slice)) >=
            self.min_each_ingredient_per_slice):

            if slice in self.valid_slices:
                self.valid_slices.remove(slice)
            self.valid_slices.append(new_slice)
            score = self.score_of(new_slice) - self.score_of(slice)
            self.score += score
            return score * POSITIVE_REWARD
        return NEUTRAL_REWARD if new_slice is not None else NEGATIVE_REWARD

    def do(self, action):

        if action == 'toggle':
            if self.previous_action == 'toggle':
                self.previous_action = action
                self.double_toggle_count+=1
                return DOUBLE_TOGGLE_REWARD
            self.slice_mode = not self.slice_mode
            return NEUTRAL_REWARD

        if action not in Direction.__members__:
            raise ActionNotFoundException('Action \'{}\' is not recognised.'.format(action))

        if self.slice_mode:
            self.previous_action = action
            reward = self.increase(Direction[action])
            return reward
        self.previous_action = action
        reward = self.move(Direction[action])
        return reward

    def state(self):
        return {
            'ingredients_map': self.pizza.ingredients._map.tolist(),
            'slices_map': self.pizza._map.tolist(),
            'cursor_position': self.cursor_position,
            'slice_mode': self.slice_mode,
            'min_each_ingredient_per_slice': self.min_each_ingredient_per_slice,
            'max_ingredients_per_slice': self.max_ingredients_per_slice,
        }
