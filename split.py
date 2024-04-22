# writtent o split the combination content into two
import json
with open('combinations.json', 'r') as f:
    data = json.load(f)
    split_index = len(data) // 2

    first_half = data[:split_index]
    second_half = data[split_index:]

    with open('combination_1.json', 'w') as f:
        json.dump(list(first_half), f, indent=2, default=str)
        
    with open('combination_2.json', 'w') as f:
        json.dump(list(second_half), f, indent=2, default=str)