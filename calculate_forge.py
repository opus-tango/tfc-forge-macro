# Calculate the forge recipe for a given item

from collections import deque
import json
import time


actions = {
  "L": -3,
  "M": -6,
  "D": -9,
  "P": -15,
  "G": +2,
  "Y": +7,
  "O": +13,
  "R": +16,
}


def gen_set_of_hits(num):
  set = []
  if num == 1:
    for i in ["L", "M", "D"]:
      set.append([i])
  if num == 2:
    for i in ["L", "M", "D"]:
      for j in ["L", "M", "D"]:
          set.append([i, j])
  if num == 3:
    for i in ["L", "M", "D"]:
      for j in ["L", "M", "D"]:
        for k in ["L", "M", "D"]:
          set.append([i, j, k])
  return set


def find_shortest_path(target, actions, timeout_seconds=5):
    # If starting at 0 and target is 0
    if target == 0:
        return []

    # Queue stores tuples of (current_sum, path as list of action labels)
    queue = deque([(0, [])])
    # Visited set to prevent infinite loops and redundant work
    visited = {0}
    start_time = time.perf_counter()

    while queue:
        if time.perf_counter() - start_time >= timeout_seconds:
            return None

        current_sum, path = queue.popleft()

        for label, value in actions.items():
            next_sum = current_sum + value

            if next_sum == target:
                return path + [label]

            if next_sum not in visited:
                # Optional: limit the search range if target is reasonably small
                # to prevent searching forever if a solution is impossible
                if -1000 < next_sum < 1000:
                    visited.add(next_sum)
                    queue.append((next_sum, path + [label]))

    return None


def calculate_recipe(last_action, second_to_last_action, third_to_last_action, target_value):
  recipe = []
  first_target = target_value

  if last_action != "":
    first_target -= actions[last_action]
  if second_to_last_action != "":
    first_target -= actions[second_to_last_action]
  if third_to_last_action != "":
    first_target -= actions[third_to_last_action]


  path = find_shortest_path(first_target, actions)
  if path is None:
    return ["No solution found"]
  recipe.extend(path)
  if third_to_last_action != "":
    recipe.append(third_to_last_action)
  if second_to_last_action != "":
    recipe.append(second_to_last_action)
  if last_action != "":
    recipe.append(last_action)

  return recipe


def main():
  # Get the three final actions and the target value from the user
  print("Welcome to the forge recipe calculator!")

  print("Enter the three final actions required for this recipe (L, M, D, P, G, Y, O, R). Enter 'H' if any hit is allowed for that action. Hit enter without typing anything to skip an action (for example, if only two final actions are required, enter them, and then hit enter to skip the third).")
  last_action = input("Enter the last action: ")
  second_to_last_action = input("Enter the second to last action: ")
  third_to_last_action = input("Enter the third to last action: ")

  target_value = int(input("Enter the target value for the recipe: "))

  print("Calculating the recipe...")


  # Calculate the recipe variants for the given actions and target value
  solutions = []
  if last_action == "H":
    if second_to_last_action == "H":
      if third_to_last_action == "H":
        for hit in gen_set_of_hits(3):
          solutions.append(calculate_recipe(hit[0], hit[1], hit[2], target_value))
      else:
        for hit in gen_set_of_hits(2):
          solutions.append(calculate_recipe(hit[0], hit[1], third_to_last_action, target_value))
    else:
      for hit in gen_set_of_hits(1):
        solutions.append(calculate_recipe(hit[0], second_to_last_action, third_to_last_action, target_value))
  elif second_to_last_action == "H":
    if third_to_last_action == "H":
      for hit in gen_set_of_hits(2):
        solutions.append(calculate_recipe(last_action, hit[0], hit[1], target_value))
    else:
      for hit in gen_set_of_hits(1):
        solutions.append(calculate_recipe(last_action, hit[0], third_to_last_action, target_value))
  elif third_to_last_action == "H":
    for hit in gen_set_of_hits(1):
      solutions.append(calculate_recipe(last_action, second_to_last_action, hit[0], target_value))
  else:
    solutions.append(calculate_recipe(last_action, second_to_last_action, third_to_last_action, target_value))

  print(f"Found {len(solutions)} solutions")

  if len(solutions) == 0:
    print("No solutions found")
    exit()

  # Find the shortest recipe
  lengths = [len(solution) for solution in solutions]
  shortest_length_index = 0
  for index, solution in enumerate(solutions):
    if len(solution) < lengths[shortest_length_index]:
      shortest_length_index = index

  # Print the shortest recipe
  recipe = solutions[shortest_length_index]
  recipe_string = ""
  for action in recipe:
    recipe_string += action + " "
  print(f"The shortest recipe is: \n{recipe_string}")


if __name__ == "__main__":
  main()